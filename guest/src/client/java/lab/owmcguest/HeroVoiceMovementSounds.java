package lab.owmcguest;

import com.google.gson.JsonObject;
import java.util.UUID;
import java.util.concurrent.ConcurrentHashMap;
import java.util.concurrent.atomic.AtomicLong;
import net.minecraft.client.MinecraftClient;
import net.minecraft.client.sound.SoundInstance;
import net.minecraft.entity.Entity;

/** 语音挂接：删除MC本玩家起落相关语气声；不改变跳跃、伤害、怪物声音或技能物理。 */
public final class HeroVoiceMovementSounds {
    private record Scope(UUID player,String world,long wall) {}
    private static volatile Scope scope;
    private static final ConcurrentHashMap<String,AtomicLong> blocked=new ConcurrentHashMap<>();
    private HeroVoiceMovementSounds(){}
    static void bind(HeroVoiceRuntime.Binding binding){
        var client=MinecraftClient.getInstance();
        scope=binding==null||client.world==null?null:new Scope(binding.player(),client.world.getRegistryKey().getValue().toString(),binding.wall());
    }
    private static Scope current(){var s=scope;long age=s==null?Long.MAX_VALUE:System.currentTimeMillis()-s.wall();return age>=0&&age<=250?s:null;}
    public static boolean activePlayer(Entity player){
        var s=current();return s!=null&&s.player().equals(player.getUuid())&&s.world().equals(player.getWorld().getRegistryKey().getValue().toString());
    }
    private static void blocked(String id){blocked.computeIfAbsent(id,key->new AtomicLong()).incrementAndGet();}
    public static boolean suppress(SoundInstance sound){
        if(current()==null)return false;
        var id=sound.getId();boolean suppress=HeroVoicePolicy.movementSound(id.getNamespace(),id.getPath(),sound.getCategory().name());
        if(suppress)blocked(id.toString());return suppress;
    }
    public static void fallHurtSuppressed(){blocked("minecraft:fall_damage_hurt_vocal");}
    static JsonObject status(){var out=new JsonObject();out.addProperty("mcMovementVocalPolicy","delete; no cooldown");var counts=new JsonObject();blocked.forEach((key,value)->counts.addProperty(key,value.get()));out.add("blocked",counts);return out;}
}
