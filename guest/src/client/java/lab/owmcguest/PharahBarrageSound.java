package lab.owmcguest;

import net.minecraft.client.MinecraftClient;
import net.minecraft.client.sound.*;
import net.minecraft.sound.*;
import net.minecraft.util.Identifier;

/** One private firing loop, admitted factories + real native firing state only. */
final class PharahBarrageSound {
    static final PharahBarrageSound INSTANCE=new PharahBarrageSound();
    private final NativeSkillReader skills=new NativeSkillReader();
    private FiringLoop loop;
    private static final class FiringLoop extends PositionedSoundInstance implements TickableSoundInstance {
        FiringLoop(Identifier id){super(id,SoundCategory.PLAYERS,.035f,1f,SoundInstance.createRandom(),true,0,SoundInstance.AttenuationType.NONE,0,0,0,true);}
        @Override public void tick(){volume=EarlyChineseVoices.INSTANCE.barrageSpeaking(MinecraftClient.getInstance())?.035f:.12f;}
        @Override public boolean isDone(){return false;}
    }
    private long seen,lastEmission,starts,stops;
    static volatile String status="{}";
    void tick(MinecraftClient client){
        var v=PharahBarragePresentation.view;var h=HostPoseReader.INSTANCE.latest();
        boolean valid=PharahBarrageRenderer.accepts(client,h,v);
        String error="";boolean firing=false;
        if(valid){
            var state=skills.poll(h,v.model(),0x02e0000000000008L);
            firing=state!=null&&state.active("firing");
            if(state==null)error=skills.error;
            for(var cue:v.launches())if(cue.sequence()>seen){seen=cue.sequence();lastEmission=Math.max(lastEmission,cue.shot().wallMs());}
        }
        // Loss of transport/admission stops the loop even if the old native
        // animation continues across a world transition. No key starts audio.
        long age=System.currentTimeMillis()-lastEmission;
        if(!valid||!firing||age<0||age>220){stop(client);if(!valid)skills.close();}
        else if(loop==null){
            var id=Identifier.of("owmcguest","pharah.barrage.fire");
            if(client.getSoundManager().get(id)==null)error="Private Barrage firing recording unavailable";
            else{loop=new FiringLoop(id);client.getSoundManager().play(loop);starts++;}
        }
        var o=new com.google.gson.JsonObject();o.addProperty("starts",starts);o.addProperty("stops",stops);o.addProperty("playing",loop!=null&&client.getSoundManager().isPlaying(loop));o.addProperty("firing",firing);o.addProperty("lastEmission",lastEmission);o.addProperty("error",error);status=o.toString();
    }
    private void stop(MinecraftClient c){if(loop!=null){c.getSoundManager().stop(loop);loop=null;stops++;}}
    void reset(){stop(MinecraftClient.getInstance());skills.close();lastEmission=0;}
}
