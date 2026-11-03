package lab.owmcguest;

import net.minecraft.client.MinecraftClient;
import net.minecraft.client.sound.*;
import net.minecraft.sound.SoundCategory;
import net.minecraft.util.Identifier;

/** A real landed field owns its sound instance, so expiry cannot leave a tail. */
final class BioticFieldSound {
    static final BioticFieldSound INSTANCE=new BioticFieldSound();
    private PositionedSoundInstance loop;private String identity="";
    private long starts,stops;
    static volatile String status="{}";
    private static final class FieldLoop extends PositionedSoundInstance implements TickableSoundInstance {
        FieldLoop(Identifier id,NativeBioticRuntime.View v){super(id,SoundCategory.PLAYERS,.3f,1f,SoundInstance.createRandom(),true,0,SoundInstance.AttenuationType.LINEAR,v.at().x,v.at().y,v.at().z,false);}
        @Override public void tick(){volume=EarlyChineseVoices.INSTANCE.bioticSpeaking(MinecraftClient.getInstance())?.12f:.3f;}
        @Override public boolean isDone(){return false;}
    }
    void tick(MinecraftClient client){
        var v=NativeBioticRuntime.view;var h=HostPoseReader.INSTANCE.latest();
        boolean valid=v!=null&&v.landed()&&h!=null&&client.player!=null&&client.world!=null&&client.getServer()!=null
            &&v.source()==h.generation()&&v.model()==NativeLocomotionController.INSTANCE.modelId()&&NativeLocomotionController.INSTANCE.hero()==NativeBioticRuntime.HERO
            &&v.owner().equals(client.player.getUuid())&&v.world()==NativeWorldIdentity.of(client.getServer(),client.world.getRegistryKey())&&System.currentTimeMillis()-v.wall()<250;
        String next=valid?v.source()+":"+v.world()+":"+v.model()+":"+v.nativeTick():"";
        if(!valid||!identity.equals(next))stop(client);
        String error="";
        if(valid&&loop==null){
            var id=Identifier.of("owmcguest","soldier76.bioticfield.loop");
            if(client.getSoundManager().get(id)==null){id=Identifier.ofVanilla("block.beacon.ambient");error="Private OW1 field loop unavailable; vanilla fallback";}
            loop=new FieldLoop(id,v);identity=next;client.getSoundManager().play(loop);starts++;
        }
        var out=new com.google.gson.JsonObject();out.addProperty("starts",starts);out.addProperty("stops",stops);out.addProperty("playing",loop!=null&&client.getSoundManager().isPlaying(loop));out.addProperty("error",error);status=out.toString();
    }
    private void stop(MinecraftClient client){if(loop!=null){client.getSoundManager().stop(loop);loop=null;stops++;}identity="";}
    void reset(){stop(MinecraftClient.getInstance());}
}
