package lab.owmcguest;

import com.google.gson.JsonObject;
import net.minecraft.client.MinecraftClient;
import net.minecraft.client.sound.PositionedSoundInstance;
import net.minecraft.client.sound.SoundInstance;
import net.minecraft.sound.SoundCategory;
import net.minecraft.util.Identifier;

/** Preloaded private original OGG. Only the actual parent split requests it;
 * one active instance prevents retriggers/rapid fire from stacking tails. */
final class RoadhogSplitSound {
    private static final Identifier ID=Identifier.of("owmcguest","hero_voice."+RoadhogSoundCatalog.HASH);
    private PositionedSoundInstance playing;private long began,played,dropped,missing,stopped,retiredBefore;
    private String error="";
    static PositionedSoundInstance create(RoadhogSplitCues.Cue cue){
        var at=cue.at();return new PositionedSoundInstance(ID,SoundCategory.PLAYERS,RoadhogSoundCatalog.SPLIT_GAIN,1,SoundInstance.createRandom(),false,0,SoundInstance.AttenuationType.NONE,at.x(),at.y(),at.z(),false);
    }
    void tick(MinecraftClient c,RoadhogServer.Scope scope){
        long now=System.currentTimeMillis();
        // Keep ownership even while the SoundSystem is still asynchronously
        // loading the first clip. A false isPlaying must not lose its handle
        // and allow the next parent to overlap a late-starting old instance.
        if(playing!=null&&now-began>2500)stop(c);
        RoadhogSplitCues.Cue cue;
        while((cue=RoadhogSplitCues.INSTANCE.poll())!=null){
            if(c.player==null||!c.player.isAlive()||cue.wall()<=retiredBefore||!RoadhogSplitCues.current(cue,scope,now)){dropped++;continue;}
            if(c.getSoundManager().get(ID)==null){missing++;error="original24919 Roadhog split SFX not registered; private audio manifest required";continue;}
            stop(c);playing=create(cue);
            c.getSoundManager().play(playing);began=now;played++;error="";
        }
        var o=new JsonObject();o.addProperty("played",played);o.addProperty("dropped",dropped);o.addProperty("missing",missing);o.addProperty("stopped",stopped);
        o.addProperty("hash",RoadhogSoundCatalog.HASH);o.addProperty("gain",RoadhogSoundCatalog.SPLIT_GAIN);o.addProperty("attenuation","none; already-authenticated local parent split");o.addProperty("error",error);RoadhogPresentation.splitSoundStatus=o.toString();
    }
    private void stop(MinecraftClient c){if(playing!=null){c.getSoundManager().stop(playing);playing=null;stopped++;}}
    void reset(MinecraftClient c){stop(c);RoadhogSplitCues.INSTANCE.drain();retiredBefore=System.currentTimeMillis();}
}
