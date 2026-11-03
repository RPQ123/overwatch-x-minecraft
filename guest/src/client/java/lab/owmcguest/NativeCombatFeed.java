package lab.owmcguest;

import java.nio.ByteBuffer;
import java.nio.ByteOrder;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.StandardCopyOption;
import java.util.concurrent.atomic.AtomicBoolean;
import net.minecraft.client.MinecraftClient;

final class NativeCombatFeed {
    private final Path directory;
    private final AtomicBoolean pending=new AtomicBoolean();
    private long next;
    volatile String error="waiting for original projectile source";
    volatile double aimDot;
    NativeCombatFeed(){String dir=System.getProperty("owmc.nativeEventsDirectory","");directory=dir.isBlank()?null:Path.of(dir);}
    void tick(MinecraftClient client,long generation){
        long now=System.currentTimeMillis();if(directory==null||now<next||pending.get()||client.player==null||client.world==null||client.getServer()==null)return;next=now+40;
        var host=HostPoseReader.INSTANCE.latest();if(host==null||host.flags()!=1)return;
        long nativeModel=NativeLocomotionController.INSTANCE.modelId(),nativeHero=NativeLocomotionController.INSTANCE.hero();
        if(nativeModel==0||nativeHero==0){error="waiting for current native combat owner";return;}
        var server=client.getServer();long world=NativeWorldIdentity.of(server,client.world.getRegistryKey());
        try{
            var path=directory.resolve("native-emissions-"+host.pid()+".json");
            if(!Files.isRegularFile(path)||Files.size(path)>524288){error="native journal missing/oversized";return;}
            var expected=new NativeShotProtocol.Expected(host.pid(),(int)ProcessHandle.current().pid(),host.generation(),generation,world,client.player.getEyeHeight(client.player.getPose()),nativeModel,nativeHero);
            var batch=NativeShotProtocol.decode(Files.readString(path),expected,now);var player=client.player.getUuid();
            for(var entry:batch.entries())if(entry.shot()!=null){var forward=new org.joml.Vector3f(0,0,-1).rotate(host.rotation());var v=entry.shot().velocity();aimDot=(forward.x*v.x()+forward.y*v.y()+forward.z*v.z())/Math.sqrt(v.lengthSquared());}
            pending.set(true);server.execute(()->{
                try{
                    long cursor=NativeCombatRuntime.accept(server,player,world,nativeModel,batch);
                    var ack=ByteBuffer.allocate(32).order(ByteOrder.LITTLE_ENDIAN);ack.put("OWACK001".getBytes(StandardCharsets.US_ASCII)).putLong(batch.source().epoch()).putLong(cursor).putInt((int)ProcessHandle.current().pid()).putInt(0);
                    var target=directory.resolve("native-emissions-"+host.pid()+".ack");var temp=target.resolveSibling(target.getFileName()+".tmp");Files.write(temp,ack.array());Files.move(temp,target,StandardCopyOption.REPLACE_EXISTING,StandardCopyOption.ATOMIC_MOVE);error="";
                }catch(Exception failure){error=failure.toString();}finally{pending.set(false);}
            });
        }catch(Exception failure){error=failure.toString();}
    }
}
