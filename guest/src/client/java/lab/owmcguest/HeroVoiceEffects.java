package lab.owmcguest;

import com.google.gson.JsonObject;
import java.util.List;
import net.minecraft.client.MinecraftClient;

/** W3 only: certified Winston SFX; other retired supplemental effects stay off. */
final class HeroVoiceEffects {
    private long discarded;
    private final WinstonSkillAudio winston=new WinstonSkillAudio();
    boolean busy(MinecraftClient client){return false;}
    void tick(MinecraftClient client,HeroVoiceRuntime.Binding next,List<HeroVoiceAssets.Clip> clips){
        while(NativeHanzoSkillRuntime.pollDragonRoar()!=null)discarded++;
        winston.tick(client,next,clips);
    }
    JsonObject status(MinecraftClient client){
        var out=new JsonObject();out.addProperty("enabled",false);out.addProperty("dragonRoar",0);
        out.addProperty("playing",false);out.addProperty("discarded",discarded);out.addProperty("error","");out.add("winston",winston.status());return out;
    }
    void reset(MinecraftClient client){winston.reset(client);}
}
