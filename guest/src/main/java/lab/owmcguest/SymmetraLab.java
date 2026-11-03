package lab.owmcguest;

import com.google.gson.JsonObject;
import java.util.LinkedHashMap;
import java.util.Map;
import java.util.UUID;
import net.minecraft.block.BlockState;
import net.minecraft.block.Blocks;
import net.minecraft.entity.EntityType;
import net.minecraft.entity.LivingEntity;
import net.minecraft.entity.attribute.EntityAttributes;
import net.minecraft.server.MinecraftServer;
import net.minecraft.server.network.ServerPlayerEntity;
import net.minecraft.server.world.ServerWorld;
import net.minecraft.util.math.BlockPos;
import net.minecraft.util.math.Vec3d;

/** Disposable MC fixtures only. Never calls signal/place/grantShield or original code.
 * shield-hit is explicitly MC diagnostic damage, not evidence of a native attack. */
public final class SymmetraLab {
    private static LivingEntity target;
    private static ServerWorld world;
    private static UUID owner;
    private static final Map<BlockPos,BlockState> blocks=new LinkedHashMap<>();
    private static Vec3d forward;
    private static String scene="",error="";
    private SymmetraLab(){}
    public static void action(MinecraftServer server,UUID id,Vec3d direction,String name){
        error="";try{run(server,id,direction,name);}catch(RuntimeException failure){error=failure.toString();throw failure;}
    }
    private static void run(MinecraftServer server,UUID id,Vec3d direction,String name){
        var p=server.getPlayerManager().getPlayer(id);
        if(p==null||!p.isCreative()||!Boolean.getBoolean("owmc.twilightTrial")
            ||!System.getProperty("owmc.worldName","").startsWith("Overwatch Twilight Switch "))
            throw new IllegalStateException("Symmetra fixture requires isolated creative Switch lab");
        if(name.equals("symmetra-cover")){requireOwner(p);cover(p);return;}
        if(name.equals("symmetra-shield-hit")){
            requireOwner(p);if(target==null||target.getAbsorptionAmount()<2)throw new IllegalStateException("No real shield to damage");
            target.damage(world.getDamageSources().generic(),2);return;
        }
        if(!java.util.Set.of("symmetra-beam-lab","symmetra-far-lab","symmetra-ally-lab","symmetra-placement").contains(name))
            throw new IllegalArgumentException(name);
        cleanup();NativeCombatScene.groundLab(server,id);
        world=p.getServerWorld();owner=id;forward=direction.multiply(1,0,1);
        var floor=BlockPos.ofFloored(p.getPos()).down();
        if(!world.isChunkLoaded(floor)||world.getBlockState(floor).getCollisionShape(world,floor).isEmpty()
            ||!world.isSpaceEmpty(p,p.getBoundingBox()))throw new IllegalStateException("No safe fixture floor");
        if(forward.lengthSquared()<.01)throw new IllegalStateException("Fixture needs horizontal aim");forward=forward.normalize();
        var at=p.getPos().add(forward.multiply(name.equals("symmetra-far-lab")?7:4));
        var e=EntityType.HUSK.create(world);if(e==null)throw new IllegalStateException("Fixture entity unavailable");
        e.refreshPositionAndAngles(at.x,at.y,at.z,0,0);
        if(!world.isChunkLoaded(e.getBlockPos())||!world.isSpaceEmpty(e,e.getBoundingBox()))throw new IllegalStateException("Occupied fixture position");
        e.setAiDisabled(true);e.setNoGravity(true);e.setSilent(true);e.setPersistent();
        e.getAttributeInstance(EntityAttributes.GENERIC_MAX_HEALTH).setBaseValue(200);e.setHealth(200);
        e.addCommandTag("owmc-symmetra-fixture");if(name.equals("symmetra-ally-lab"))e.addCommandTag("owmc-symmetra-ally");
        if(!world.spawnEntity(e))throw new IllegalStateException("Fixture spawn failed");target=e;scene=name;
    }
    private static void requireOwner(ServerPlayerEntity p){
        if(world!=p.getWorld()||!p.getUuid().equals(owner)||target==null||!target.isAlive())throw new IllegalStateException("Fixture identity changed");
    }
    private static void cover(ServerPlayerEntity p){
        var center=BlockPos.ofFloored(p.getPos().add(forward.multiply(2)));var side=new Vec3d(-forward.z,0,forward.x);
        var proposed=new LinkedHashMap<BlockPos,BlockState>();
        for(int x=-1;x<=1;x++)for(int y=0;y<3;y++){
            var at=BlockPos.ofFloored(Vec3d.ofBottomCenter(center).add(side.multiply(x))).up(y);
            if(!world.isChunkLoaded(at)||!world.getBlockState(at).isAir())throw new IllegalStateException("Cover would replace a foreign block");
            proposed.put(at,world.getBlockState(at));
        }
        proposed.forEach((at,state)->{blocks.putIfAbsent(at,state);world.setBlockState(at,Blocks.STONE.getDefaultState());});
    }
    public static JsonObject status(){
        var out=new JsonObject();out.addProperty("scene",scene);out.addProperty("active",target!=null&&target.isAlive());
        out.addProperty("error",error);
        if(target!=null){out.addProperty("health",target.getHealth());out.addProperty("absorption",target.getAbsorptionAmount());out.addProperty("uuid",target.getUuidAsString());}
        out.addProperty("coverBlocks",blocks.size());return out;
    }
    public static void cleanup(){
        if(target!=null)target.discard();target=null;
        if(world!=null)blocks.forEach((at,state)->{if(world.isChunkLoaded(at)&&world.getBlockState(at).isOf(Blocks.STONE))world.setBlockState(at,state);});
        blocks.clear();world=null;owner=null;forward=null;scene="";error="";
    }
}
