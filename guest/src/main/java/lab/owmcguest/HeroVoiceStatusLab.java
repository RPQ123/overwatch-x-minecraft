package lab.owmcguest;

import com.google.gson.JsonObject;
import net.minecraft.entity.effect.StatusEffectInstance;
import net.minecraft.entity.effect.StatusEffects;
import net.minecraft.server.MinecraftServer;
import java.util.UUID;

/** 语音挂接：仅隔离Switch场景使用的MC效果实验，不直接触发语音或原版节点。 */
public final class HeroVoiceStatusLab {
    public static volatile String status="{}";
    private HeroVoiceStatusLab(){}
    public static void apply(MinecraftServer server,UUID owner,String kind){
        var p=server.getPlayerManager().getPlayer(owner);String error="";
        if(!server.isOnThread()||!Boolean.getBoolean("owmc.twilightTrial")||!Boolean.getBoolean("owmc.creativeWorld")
            ||!System.getProperty("owmc.worldName","").startsWith("Overwatch Twilight Switch ")||p==null||!p.isAlive()||!p.isCreative())error="isolated creative Switch lab required";
        else{
            var effect=switch(kind){
                case "slowed" -> StatusEffects.SLOWNESS;
                case "poisoned" -> StatusEffects.POISON;
                case "debuffed" -> StatusEffects.WEAKNESS;
                case "damage_boosted" -> StatusEffects.STRENGTH;
                default -> null;
            };
            if(effect==null)error="unsupported MC status fixture";
            else if(p.hasStatusEffect(effect))error="effect already present; no overwrite";
            else if(p.getHealth()<8)error="need healthy player for reversible effect lab";
            else p.addStatusEffect(new StatusEffectInstance(effect,60,0,false,true,true));
        }
        var out=new JsonObject();out.addProperty("kind",kind);out.addProperty("applied",error.isEmpty());out.addProperty("error",error);
        out.addProperty("durationTicks",60);out.addProperty("policy","MC适配: 真实效果自然到期；不伪造stun或冻结技能提交");status=out.toString();
    }
}
