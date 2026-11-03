package lab.owmcguest;

import net.minecraft.client.MinecraftClient;
import net.minecraft.client.sound.PositionedSoundInstance;
import net.minecraft.client.sound.SoundInstance;
import net.minecraft.sound.SoundCategory;
import net.minecraft.util.Identifier;

/** Local private resource pack; no copyrighted sound is bundled into the mod jar. */
final class GenjiUltimateVoice {
    static final GenjiUltimateVoice INSTANCE=new GenjiUltimateVoice();
    private static final Identifier EVENT=Identifier.of("owmcguest","genji.dragonblade");
    private PositionedSoundInstance sound;
    private long scheduled;private boolean observedPlaying;private String error="",lastRecording="";
    void play(MinecraftClient client){
        if(client.getSoundManager().get(EVENT)==null){error="private voice pack unavailable";return;}
        var next=new PositionedSoundInstance(EVENT,SoundCategory.VOICE,1f,1f,SoundInstance.createRandom(),false,0,SoundInstance.AttenuationType.NONE,0,0,0,true);
        // 语音挂接：原中/日随机素材不变，统一仲裁且只记一次播放。
        if(!HeroVoiceChannel.play(client,next,"legacy-genji","ult_cast",30000))return;
        stop(client);sound=next;HeroVoiceEvents.INSTANCE.legacyPlayed(client,"genji.dragonblade",sound);lastRecording=sound.getSound().getIdentifier().toString();scheduled++;error="";
    }
    void stop(MinecraftClient client){if(sound!=null){client.getSoundManager().stop(sound);sound=null;}}
    static volatile String status="{}";
    void tick(MinecraftClient client){
        boolean playing=sound!=null&&client.getSoundManager().isPlaying(sound);observedPlaying|=playing;
        var json=new com.google.gson.JsonObject();json.addProperty("ready",client.getSoundManager().get(EVENT)!=null);json.addProperty("scheduled",scheduled);json.addProperty("playing",playing);json.addProperty("observedPlaying",observedPlaying);json.addProperty("lastRecording",lastRecording);json.addProperty("error",error);status=json.toString();
    }
}
