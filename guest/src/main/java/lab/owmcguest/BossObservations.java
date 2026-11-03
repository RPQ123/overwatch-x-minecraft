package lab.owmcguest;
import com.google.gson.*;
import net.minecraft.server.MinecraftServer;
import net.minecraft.entity.LivingEntity;
import net.minecraft.registry.Registries;
/** Bounded read-only evidence of actual nearby mod entities, never a combat command. */
public final class BossObservations {
    public static volatile String status="[]";
    public static void tick(MinecraftServer server){
        if(server.getTicks()%5!=0)return;var rows=new JsonArray();
        for(var p:server.getPlayerManager().getPlayerList())for(var e:p.getServerWorld().getEntitiesByClass(LivingEntity.class,p.getBoundingBox().expand(160),v->v.isAlive()&&RandomBossTravel.isBoss(v))){
            var r=new JsonObject();r.addProperty("type",Registries.ENTITY_TYPE.getId(e.getType()).toString());r.addProperty("uuid",e.getUuidAsString());r.addProperty("health",e.getHealth());r.addProperty("maximum",e.getMaxHealth());r.addProperty("x",e.getX());r.addProperty("y",e.getY());r.addProperty("z",e.getZ());r.addProperty("height",e.getHeight());r.addProperty("dimension",e.getWorld().getRegistryKey().getValue().toString());rows.add(r);
        }status=rows.toString();
    }
}
