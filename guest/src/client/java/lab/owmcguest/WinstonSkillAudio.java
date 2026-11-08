package lab.owmcguest;

import com.google.gson.JsonObject;
import java.util.*;
import net.minecraft.client.MinecraftClient;
import net.minecraft.client.sound.PositionedSoundInstance;
import net.minecraft.client.sound.SoundInstance;
import net.minecraft.sound.SoundCategory;

/** Original, bounded one-shots. VO continues through the sole HeroVoiceChannel.
 * Observe native Effect ownership for100ms before supplementing a missing effect. */
final class WinstonSkillAudio {
    private record Pending(WinstonAudioGate.Sample cast,long wall) {}
    private record Playing(PositionedSoundInstance sound,long began,long end) {}
    private final WinstonAudioGate gate=new WinstonAudioGate();
    private final EnumMap<WinstonAudioGate.Event,Pending> pending=new EnumMap<>(WinstonAudioGate.Event.class);
    private final EnumMap<WinstonAudioGate.Event,Playing> playing=new EnumMap<>(WinstonAudioGate.Event.class);
    private final Map<String,Long> starts=new TreeMap<>();
    private WinstonAudioGate.Scope scope;
    private long nativeOwned,unknown,missing,expired;
    private String error="",lastEvent="",lastHash="";
    void tick(MinecraftClient client,HeroVoiceRuntime.Binding binding,List<HeroVoiceAssets.Clip> clips){
        long now=System.currentTimeMillis();var s=WinstonServer.INSTANCE.audio;
        var next=binding==null||binding.hero()!=WinstonRules.HERO?null:new WinstonAudioGate.Scope(binding.player(),binding.world(),binding.source(),binding.model());
        if(next==null||s==null||!next.equals(s.scope())||now<s.wall()||now-s.wall()>200||client.player==null||!client.player.isAlive()){
            reset(client);return;
        }
        if(!next.equals(scope)){reset(client);scope=next;}
        var events=gate.observe(s,next,now);
        for(var event:events)if(WinstonAudioCatalog.event(event)!=null)pending.put(event,new Pending(s,now));
        playing.entrySet().removeIf(entry->{var p=entry.getValue();return now>p.end()||now-p.began()>350&&!client.getSoundManager().isPlaying(p.sound());});
        for(var event:List.copyOf(pending.keySet())){
            var cue=pending.get(event);long age=now-cue.wall();if(age<100)continue;pending.remove(event);
            if(age>300){expired++;continue;}
            var owner=WinstonAudioGate.owner(cue.cast(),WinstonClient.nativeAudio,event,now);
            if(owner==WinstonAudioGate.Owner.NATIVE){nativeOwned++;continue;}
            if(owner==WinstonAudioGate.Owner.UNKNOWN){unknown++;error="native Winston audio ownership unavailable";continue;}
            String name=WinstonAudioCatalog.event(event),hash=WinstonAudioCatalog.SFX.get(name);
            var clip=clips.stream().filter(c->c.hero().equals("winston")&&c.event().equals(name)&&c.hash().equals(hash)).findFirst().orElse(null);
            if(clip==null||client.getSoundManager().get(clip.id())==null){missing++;error="missing original Winston SFX: "+name;continue;}
            var old=playing.remove(event);if(old!=null)client.getSoundManager().stop(old.sound());
            // Landing's decoded peak1.048 remains below.734 at gain.70.
            // Keep the original packets/pitch and the native ownership gate.
            var sound=new PositionedSoundInstance(clip.id(),SoundCategory.PLAYERS,WinstonAudioCatalog.gain(event),1f,SoundInstance.createRandom(),false,0,SoundInstance.AttenuationType.NONE,0,0,0,true);
            client.getSoundManager().play(sound);playing.put(event,new Playing(sound,now,now+Math.min(5000,clip.durationMs()+350)));
            starts.merge(name,1L,Long::sum);lastEvent=name;lastHash=hash;error="";
        }
    }
    JsonObject status(){
        var out=new JsonObject();var counts=new JsonObject();starts.forEach(counts::addProperty);out.add("starts",counts);
        out.addProperty("enabled",true);out.addProperty("sourceBuild",24919);
        out.addProperty("nativeOwned",nativeOwned);out.addProperty("unknownOwnership",unknown);out.addProperty("missing",missing);out.addProperty("expired",expired);
        out.addProperty("active",playing.size());out.addProperty("pending",pending.size());out.addProperty("lastEvent",lastEvent);out.addProperty("lastHash",lastHash);out.addProperty("error",error);
        return out;
    }
    void reset(MinecraftClient client){for(var p:playing.values())client.getSoundManager().stop(p.sound());playing.clear();pending.clear();gate.reset();scope=null;}
}
