package lab.owmcguest;

import net.minecraft.client.MinecraftClient;
import net.minecraft.client.sound.*;
import net.minecraft.sound.SoundCategory;
import net.minecraft.util.Identifier;

/** Private original-beta shot recording. Only an accepted native Begin queues it. */
final class DeadeyeShotSound {
    static final DeadeyeShotSound INSTANCE=new DeadeyeShotSound();
    private final java.util.List<PositionedSoundInstance> tails=new java.util.ArrayList<>();
    private long lastSequence,scheduled,dropped;private String error="";
    static volatile String status="{}";
    void tick(MinecraftClient client){
        tails.removeIf(s->!client.getSoundManager().isPlaying(s));
        NativeDeadeyeRuntime.ShotCue cue;
        while((cue=NativeDeadeyeRuntime.pollShotCue())!=null){
            if(cue.sequence()<=lastSequence)continue;
            lastSequence=cue.sequence();
            if(!NativeDeadeyeController.INSTANCE.acceptsCue(client,cue)){dropped++;continue;}
            var id=Identifier.of("owmcguest","mccree.shot");
            if(client.getSoundManager().get(id)==null){error="Private beta shot recording unavailable";continue;}
            var sound=new PositionedSoundInstance(id,SoundCategory.PLAYERS,1f,1f,SoundInstance.createRandom(),false,0,SoundInstance.AttenuationType.NONE,0,0,0,true);
            tails.add(sound);client.getSoundManager().play(sound);scheduled++;error="";
        }
        var o=new com.google.gson.JsonObject();o.addProperty("scheduled",scheduled);o.addProperty("dropped",dropped);o.addProperty("tails",tails.size());o.addProperty("error",error);status=o.toString();
    }
    void reset(){var c=MinecraftClient.getInstance();for(var s:tails)c.getSoundManager().stop(s);tails.clear();}
}
