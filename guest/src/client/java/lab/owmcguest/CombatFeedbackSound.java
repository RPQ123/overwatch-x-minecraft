package lab.owmcguest;

import net.minecraft.client.MinecraftClient;
import net.minecraft.client.sound.*;
import net.minecraft.sound.SoundCategory;
import net.minecraft.util.Identifier;

/** Private original hit/elimination cues, scoped to the current first person. */
final class CombatFeedbackSound {
    static final CombatFeedbackSound INSTANCE=new CombatFeedbackSound();
    private final java.util.List<PositionedSoundInstance> tails=new java.util.ArrayList<>();
    private long hits,kills,dropped,lastHit;private String error="";
    static volatile String status="{}";
    void tick(MinecraftClient client){
        tails.removeIf(s->!client.getSoundManager().isPlaying(s));
        var h=HostPoseReader.INSTANCE.latest();long now=System.currentTimeMillis();
        NativeCombatFeedback.Cue cue;
        while((cue=NativeCombatFeedback.poll())!=null){
            if(h==null||!h.inputActive()||client.world==null||client.player==null||client.getServer()==null||!client.player.isAlive()
                ||!cue.owner().equals(client.player.getUuid())||cue.world()!=NativeWorldIdentity.of(client.getServer(),client.world.getRegistryKey())
                ||cue.generation()!=h.generation()||cue.hero()!=NativeLocomotionController.INSTANCE.hero()||cue.model()!=NativeLocomotionController.INSTANCE.modelId()
                ||now-cue.wall()>250||now<cue.wall()-50){dropped++;continue;}
            // One rapid beam/pellet group may hit many times in one tick. Kills
            // remain separate, including distinct Deadeye shots at native cadence.
            if(!cue.kill()&&now-lastHit<50)continue;
            var id=Identifier.of("owmcguest",cue.kill()?"combat.elimination":"combat.hit");
            if(client.getSoundManager().get(id)==null){error="Private OW1 combat sound pack unavailable";continue;}
            var sound=new PositionedSoundInstance(id,SoundCategory.PLAYERS,cue.kill()?.85f:.65f,1f,SoundInstance.createRandom(),false,0,SoundInstance.AttenuationType.NONE,0,0,0,true);
            if(tails.size()>=24)client.getSoundManager().stop(tails.remove(0));
            tails.add(sound);client.getSoundManager().play(sound);
            if(cue.kill())kills++;else{hits++;lastHit=now;}error="";
        }
        var o=new com.google.gson.JsonObject();o.addProperty("hits",hits);o.addProperty("kills",kills);o.addProperty("dropped",dropped);o.addProperty("tails",tails.size());o.addProperty("error",error);status=o.toString();
    }
    void reset(){var c=MinecraftClient.getInstance();for(var s:tails)c.getSoundManager().stop(s);tails.clear();lastHit=0;}
}
