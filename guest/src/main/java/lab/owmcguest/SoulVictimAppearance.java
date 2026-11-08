package lab.owmcguest;

import java.util.*;
import net.minecraft.entity.*;
import net.minecraft.entity.data.DataTracker;

/** Ephemeral appearance only. getChangedEntries copies non-default tracked
 * values without consuming dirty network entries. Never NBT-save a victim or
 * retain its server entity/world for a client render. */
public record SoulVictimAppearance(int entityId,UUID victim,EntityType<?> type,
        List<DataTracker.SerializedEntry<?>> tracked,net.minecraft.util.math.Vec3d position,float yaw,float pitch,int age,String error){
    public SoulVictimAppearance{tracked=List.copyOf(tracked);}
    public static SoulVictimAppearance capture(LivingEntity victim){
        try{
            var entries=victim.getDataTracker().getChangedEntries();
            if(entries!=null&&entries.size()>256)throw new IllegalArgumentException("appearance tracker limit");
            return new SoulVictimAppearance(victim.getId(),victim.getUuid(),victim.getType(),entries==null?List.of():entries,victim.getPos(),victim.getYaw(),victim.getPitch(),victim.age,"");
        }catch(RuntimeException failure){return new SoulVictimAppearance(victim.getId(),victim.getUuid(),victim.getType(),List.of(),victim.getPos(),victim.getYaw(),victim.getPitch(),victim.age,failure.getClass().getSimpleName());}
    }
}
