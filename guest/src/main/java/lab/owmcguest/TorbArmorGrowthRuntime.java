package lab.owmcguest;

import java.lang.ref.WeakReference;
import java.util.*;
import com.google.gson.*;
import net.minecraft.entity.LivingEntity;
import net.minecraft.entity.attribute.*;
import net.minecraft.server.MinecraftServer;
import net.minecraft.server.world.ServerWorld;
import net.minecraft.util.Identifier;
import net.minecraft.util.hit.HitResult;
import net.minecraft.util.math.*;
import net.minecraft.world.RaycastContext;

/** Armor-pack easter egg. Vanilla synced scale owns BOTH model and collision.
 * A temporary modifier is deliberately not serialized into a permanent giant.
 * No space means no pickup. Never resize into blocks or stack our modifier. */
public final class TorbArmorGrowthRuntime {
    public static final int DURATION=600;
    private static final Identifier ID=Identifier.of("owmcguest","torb_armor_growth");
    private record Buff(WeakReference<LivingEntity> entity,int until){}
    private static final Map<UUID,Buff> buffs=new LinkedHashMap<>();
    private static long applied,expired,refreshed,blocked,earlyEnds;
    private static String lastType="",lastRecipient="";private static double beforeWidth,afterWidth,beforeHeight,afterHeight;
    private static boolean serializedGrowthModifier;
    public static volatile String status="{}";
    private TorbArmorGrowthRuntime(){}
    public static boolean canRefresh(LivingEntity entity,int tick){
        var buff=buffs.get(entity.getUuid());var attribute=entity.getAttributeInstance(EntityAttributes.GENERIC_SCALE);
        return buff!=null&&buff.entity().get()==entity&&buff.until()>tick&&entity.isAlive()&&attribute!=null&&attribute.hasModifier(ID);
    }
    private static boolean fits(ServerWorld w,LivingEntity e,Box b){
        return w.getWorldBorder().contains(b)&&w.isChunkLoaded(BlockPos.ofFloored(b.minX,b.minY,b.minZ))
            &&w.isChunkLoaded(BlockPos.ofFloored(b.maxX,b.maxY,b.maxZ))&&w.isSpaceEmpty(e,b);
    }
    private static Box twice(LivingEntity e,Vec3d at){
        var b=e.getBoundingBox();double x=b.getLengthX(),z=b.getLengthZ();
        return new Box(at.x-x,at.y,at.z-z,at.x+x,at.y+b.getLengthY()*2,at.z+z);
    }
    private static Vec3d safePlace(ServerWorld w,LivingEntity e){
        var at=e.getPos();if(fits(w,e,twice(e,at)))return at;
        for(double distance:new double[]{.5,1,1.5})for(var direction:new Vec3d[]{new Vec3d(1,0,0),new Vec3d(-1,0,0),new Vec3d(0,0,1),new Vec3d(0,0,-1)}){
            var next=at.add(direction.multiply(distance));
            var floor=w.raycast(new RaycastContext(next.add(0,.75,0),next.add(0,-.75,0),RaycastContext.ShapeType.COLLIDER,RaycastContext.FluidHandling.NONE,e));
            if(floor.getType()!=HitResult.Type.BLOCK||((net.minecraft.util.hit.BlockHitResult)floor).getSide()!=Direction.UP)continue;
            next=new Vec3d(next.x,floor.getPos().y+.001,next.z);
            if(fits(w,e,twice(e,next)))return next;
        }
        return null;
    }
    public static boolean apply(ServerWorld w,LivingEntity entity,int tick){
        var attribute=entity.getAttributeInstance(EntityAttributes.GENERIC_SCALE);
        if(attribute==null||!entity.isAlive()||entity.getWorld()!=w)return false;
        var previous=buffs.get(entity.getUuid());
        if(previous!=null&&attribute.hasModifier(ID)){
            if(!fits(w,entity,entity.getBoundingBox())){blocked++;publish();return false;}
            buffs.put(entity.getUuid(),new Buff(new WeakReference<>(entity),tick+DURATION));refreshed++;publish();return true;
        }
        // Preserve another owner of this identifier; a vanilla capped scale is
        // not reported as an exact2x transformation.
        if(attribute.hasModifier(ID)||attribute.getValue()>8||buffs.size()>=128)return false;
        var destination=safePlace(w,entity);if(destination==null){blocked++;publish();return false;}
        var original=entity.getPos();beforeWidth=entity.getBoundingBox().getLengthX();beforeHeight=entity.getBoundingBox().getLengthY();
        if(destination.squaredDistanceTo(original)>1e-10)entity.requestTeleport(destination.x,destination.y,destination.z);
        attribute.addTemporaryModifier(new EntityAttributeModifier(ID,1,EntityAttributeModifier.Operation.ADD_MULTIPLIED_TOTAL));
        entity.calculateDimensions();
        if(!fits(w,entity,entity.getBoundingBox())){
            attribute.removeModifier(ID);entity.calculateDimensions();entity.requestTeleport(original.x,original.y,original.z);blocked++;publish();return false;
        }
        afterWidth=entity.getBoundingBox().getLengthX();afterHeight=entity.getBoundingBox().getLengthY();
        serializedGrowthModifier=entity.writeNbt(new net.minecraft.nbt.NbtCompound()).toString().contains(ID.toString());
        buffs.put(entity.getUuid(),new Buff(new WeakReference<>(entity),tick+DURATION));applied++;
        lastRecipient=entity.getUuidAsString();lastType=net.minecraft.registry.Registries.ENTITY_TYPE.getId(entity.getType()).toString();publish();return true;
    }
    private static void restore(LivingEntity entity){
        if(entity==null)return;var a=entity.getAttributeInstance(EntityAttributes.GENERIC_SCALE);
        if(a!=null&&a.hasModifier(ID)){a.removeModifier(ID);entity.calculateDimensions();}
    }
    public static void tick(MinecraftServer server){
        var iterator=buffs.entrySet().iterator();
        while(iterator.hasNext()){
            var entry=iterator.next();var b=entry.getValue();var e=b.entity().get();
            boolean timed=server.getTicks()>=b.until();
            if(timed||e==null||!e.isAlive()||e.isRemoved()){
                restore(e);iterator.remove();if(timed)expired++;else earlyEnds++;
            }
        }
        publish();
    }
    public static void close(){for(var b:buffs.values())restore(b.entity().get());buffs.clear();publish();}
    private static void publish(){
        var o=new JsonObject();o.addProperty("active",buffs.size());o.addProperty("durationTicks",DURATION);
        o.addProperty("applied",applied);o.addProperty("expired",expired);o.addProperty("refreshed",refreshed);o.addProperty("blocked",blocked);o.addProperty("earlyEnds",earlyEnds);
        o.addProperty("lastType",lastType);o.addProperty("lastRecipient",lastRecipient);o.addProperty("beforeWidth",beforeWidth);o.addProperty("afterWidth",afterWidth);o.addProperty("beforeHeight",beforeHeight);o.addProperty("afterHeight",afterHeight);
        o.addProperty("serializedGrowthModifier",serializedGrowthModifier);
        var recipients=new JsonArray();for(var entry:buffs.entrySet()){
            var e=entry.getValue().entity().get();if(e==null)continue;var row=new JsonObject();row.addProperty("id",entry.getKey().toString());row.addProperty("type",net.minecraft.registry.Registries.ENTITY_TYPE.getId(e.getType()).toString());
            row.addProperty("entityId",e.getId());row.addProperty("until",entry.getValue().until());row.addProperty("scale",e.getAttributeValue(EntityAttributes.GENERIC_SCALE));row.addProperty("width",e.getBoundingBox().getLengthX());row.addProperty("height",e.getBoundingBox().getLengthY());row.addProperty("alive",e.isAlive());row.addProperty("removed",e.isRemoved());recipients.add(row);
        }o.add("recipients",recipients);status=o.toString();
    }
}
