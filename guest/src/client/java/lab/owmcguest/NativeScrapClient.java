package lab.owmcguest;

import java.nio.file.*;
import net.minecraft.client.MinecraftClient;

/** File receipts use the existing logic owner. Never grant MC-only Scrap. */
final class NativeScrapClient implements AutoCloseable {
    private final NativeMeterReader reader=new NativeMeterReader();
    private long lastWrite,lastReceipt;private Path lastPath;
    static volatile String error="waiting for native Scrap";
    void tick(MinecraftClient c,HostPoseReader.Pose h,NativeTorbjornRuntime.Scope scope){
        try{
            var meter=reader.poll(h,scope.model(),NativeTorbjornController.HERO);if(meter==null){error=reader.error;return;}
            var state=reader.scrap();long now=System.currentTimeMillis();var server=c.getServer();
            server.execute(()->NativeTorbjornRuntime.nativeScrap(scope,state.amount(),now));
            var pending=NativeTorbjornRuntime.scrapCreditView;
            if(pending==null||!pending.scope().equals(scope)){clearRequest();error="";return;}
            String directory=System.getProperty("owmc.nativeEventsDirectory","");if(directory.isBlank())throw new IllegalStateException("native events directory unavailable");
            var dir=Path.of(directory);var request=new ScrapCreditProtocol.Request(h.pid(),state.creation(),pending.sequence(),now,h.generation(),scope.world(),state.model(),scope.model());
            var path=dir.resolve("native-scrap-credit-request-"+h.pid()+".bin");
            if(now-lastWrite>=50){
                var temp=path.resolveSibling(path.getFileName()+".tmp");Files.write(temp,ScrapCreditProtocol.encode(request));
                Files.move(temp,path,StandardCopyOption.REPLACE_EXISTING,StandardCopyOption.ATOMIC_MOVE);lastWrite=now;lastPath=path;
            }
            var response=dir.resolve("native-scrap-credit-ack-"+h.pid()+".bin");
            if(!Files.isRegularFile(response)||Files.size(response)!=80)return;
            ScrapCreditProtocol.Receipt receipt;
            try{receipt=ScrapCreditProtocol.decode(Files.readAllBytes(response),request,now);}catch(IllegalArgumentException stale){return;}
            if(receipt.sequence()==lastReceipt)return;lastReceipt=receipt.sequence();
            server.execute(()->NativeTorbjornRuntime.scrapReceipt(scope,receipt));
            error=receipt.phase()==3?"native Scrap Set&Notify failed; uncertain pickup is not retried":"";
        }catch(Exception failure){error=failure.toString();reader.close();}
    }
    private void clearRequest()throws java.io.IOException{
        if(lastPath!=null){Files.write(lastPath,new byte[80]);lastPath=null;lastWrite=0;}
    }
    @Override public void close(){reader.close();try{clearRequest();}catch(Exception failure){error=failure.toString();}}
}
