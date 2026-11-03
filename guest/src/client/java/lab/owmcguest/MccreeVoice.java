package lab.owmcguest;

import net.minecraft.client.MinecraftClient;
import net.minecraft.client.sound.*;
import net.minecraft.sound.SoundCategory;
import net.minecraft.util.Identifier;

/** Original private OGG playback only after actual admitted E or new native Q. */
final class MccreeVoice {
    static final MccreeVoice INSTANCE=new MccreeVoice();
    private final java.util.Map<String,PositionedSoundInstance> sounds=new java.util.HashMap<>();
    private long flashId,flashEpoch,begin,model,world,source;
    private long flashScheduled,qScheduled;private boolean observed;private String error="";
    static volatile String status="{}";
    private void play(MinecraftClient client,String key){
        var id=Identifier.of("owmcguest","mccree."+key);
        if(client.getSoundManager().get(id)==null){error="Private original McCree voice pack unavailable";return;}
        var sound=new PositionedSoundInstance(id,SoundCategory.VOICE,1f,1f,SoundInstance.createRandom(),false,0,SoundInstance.AttenuationType.NONE,0,0,0,true);
        // 语音挂接：E/Q仍由旧入口负责，同一时刻仅一个项目人声。
        if(!HeroVoiceChannel.play(client,sound,"legacy-mccree",key.equals("deadeye")?"ult_cast":"ability:flashbang",30000))return;
        for(var old:sounds.values())client.getSoundManager().stop(old);sounds.clear();
        sounds.put(key,sound);HeroVoiceEvents.INSTANCE.legacyPlayed(client,"mccree."+key,sound);if(key.equals("deadeye"))qScheduled++;else flashScheduled++;error="";
    }
    void deadeye(MinecraftClient client,long nextSource,long nextModel,long nextWorld,long nativeBegin){
        if(nativeBegin<=0)return;
        if(nextSource!=source||nextModel!=model||nextWorld!=world){source=nextSource;model=nextModel;world=nextWorld;begin=0;}
        if(nativeBegin>begin){begin=nativeBegin;play(client,"deadeye");}
    }
    void tick(MinecraftClient client){
        var cue=NativeCombatRuntime.flashbangCue;var host=HostPoseReader.INSTANCE.latest();
        if(cue!=null&&client.player!=null&&client.world!=null&&client.getServer()!=null&&host!=null&&host.flags()==1&&NativeLocomotionController.INSTANCE.hero()==NativeDeadeyeRuntime.HERO&&cue.player().equals(client.player.getUuid())&&cue.world()==NativeWorldIdentity.of(client.getServer(),client.world.getRegistryKey())&&cue.source().pid()==host.pid()&&cue.source().hostGeneration()==host.generation()){
            if(cue.source().epoch()!=flashEpoch){flashEpoch=cue.source().epoch();flashId=0;}
            if(cue.shot().id()>flashId){flashId=cue.shot().id();long age=System.currentTimeMillis()-cue.shot().wallMs();if(age>=0&&age<=300)play(client,"flashbang");}
        }
        boolean playing=sounds.values().stream().anyMatch(s->client.getSoundManager().isPlaying(s));observed|=playing;
        var o=new com.google.gson.JsonObject();o.addProperty("ready",client.getSoundManager().get(Identifier.of("owmcguest","mccree.deadeye"))!=null&&client.getSoundManager().get(Identifier.of("owmcguest","mccree.flashbang"))!=null);o.addProperty("flashbangScheduled",flashScheduled);o.addProperty("deadeyeScheduled",qScheduled);o.addProperty("playing",playing);o.addProperty("observedPlaying",observed);o.addProperty("error",error);status=o.toString();
    }
    void reset(){var client=MinecraftClient.getInstance();for(var sound:sounds.values())client.getSoundManager().stop(sound);sounds.clear();flashId=flashEpoch=begin=model=world=source=0;}
}
