package lab.owmcguest;

import com.google.gson.JsonObject;
import java.util.*;
import net.minecraft.block.BlockState;
import net.minecraft.block.Blocks;
import net.minecraft.entity.EntityType;
import net.minecraft.entity.LivingEntity;
import net.minecraft.entity.attribute.EntityAttributes;
import net.minecraft.entity.mob.MobEntity;
import net.minecraft.server.MinecraftServer;
import net.minecraft.server.network.ServerPlayerEntity;
import net.minecraft.server.world.ServerWorld;
import net.minecraft.util.math.BlockPos;
import net.minecraft.util.math.Box;
import net.minecraft.util.math.Vec3d;

/** Explicit isolated test fixtures only. No native write, skill call, heal/buff tick or input.
 * Reuses the existing guarded/owned ground and injury fixtures. Setup-only health edits,
 * real entities and real block collision provide receipts; they never supply a native commit.
 * Shared HTTP/status/cleanup registration remains the integrator's responsibility.
 */
public final class SupportCommitFixtures {
    private static ServerWorld world;
    private static UUID owner;
    private static String scene="",error="";
    private static MobEntity replacement;
    private static LivingEntity covered,friend;
    private static Vec3d enemyStart,coveredStart,friendStart,wallCenter,wallNormal;
    private static int wallCrossings;
    private static final Map<BlockPos,BlockState> blocks=new LinkedHashMap<>();
    private static JsonObject base(MinecraftServer server){var out=new JsonObject();NativeCombatScene.addStatus(server,out);return out;}
    private static LivingEntity target(ServerWorld w,JsonObject status){
        var e=status.has("targetId")?w.getEntityById(status.get("targetId").getAsInt()):null;return e instanceof LivingEntity living?living:null;
    }
    private static LivingEntity near(ServerWorld w,Vec3d at,LivingEntity except){
        return w.getEntitiesByClass(MobEntity.class,new Box(at.subtract(.5,.5,.5),at.add(.5,.5,.5)),
            e->e!=except&&e.getCommandTags().contains("owmc-new8-hero-probe")).stream().findFirst().orElse(null);
    }
    private static MobEntity hostile(ServerPlayerEntity p,Vec3d at){
        var mob=EntityType.HUSK.create(world);if(mob==null)throw new IllegalStateException("support hostile creation failed");
        mob.refreshPositionAndAngles(at.x,at.y,at.z,0,0);mob.setAiDisabled(true);mob.setNoGravity(true);mob.setPersistent();mob.setSilent(true);
        mob.getAttributeInstance(EntityAttributes.GENERIC_MAX_HEALTH).setBaseValue(200);
        mob.getAttributeInstance(EntityAttributes.GENERIC_ARMOR).setBaseValue(0);mob.setHealth(200);mob.addCommandTag("owmc-support-commit-probe");
        if(!world.isChunkLoaded(mob.getBlockPos())||!world.isSpaceEmpty(mob,mob.getBoundingBox())||!world.spawnEntity(mob)){
            mob.discard();throw new IllegalStateException("support hostile site occupied or refused");}
        return mob;
    }
    public static void setup(MinecraftServer server,UUID player,Vec3d direction,String name){
        cleanup();error="";
        var p=server.getPlayerManager().getPlayer(player);
        if(p==null||!p.isCreative()||!Boolean.getBoolean("owmc.twilightTrial")
                ||!System.getProperty("owmc.worldName","").startsWith("Overwatch Twilight Switch ")){error="support fixture requires isolated creative Switch lab";return;}
        var forward=direction.multiply(1,0,1);if(forward.lengthSquared()<.01){error="support fixture needs horizontal aim";return;}forward=forward.normalize();
        String alias=switch(name){
            case "mercy-pistol","zen-discord" -> "zen-body";
            case "mercy-guardian","mercy-passive","zen-harmony","zen-transcendence","lucio-boop","lucio-wallride" -> "mercy-support";
            default -> "";
        };
        if(alias.isEmpty()){error="unknown support fixture";return;}
        NativeCombatScene.heroLab(server,player,forward,alias);
        var existing=base(server);if(!existing.get("testError").getAsString().isEmpty()){error=existing.get("testError").getAsString();return;}
        if(name.equals("mercy-passive"))NativeCombatScene.sustainHurt(server,player);
        // All calls above may perform shared cleanup; only now adopt our own fixture scope.
        world=p.getServerWorld();owner=player;scene=name;var t=target(world,existing);var side=new Vec3d(-forward.z,0,forward.x);
        covered=near(world,p.getEyePos().add(forward.multiply(5)).add(side.multiply(4)).add(0,-.9,0),t);
        friend=t;
        try{
            if(name.equals("zen-discord")){
                var at=t.getPos();t.discard();replacement=hostile(p,at);
            }else if(name.equals("lucio-boop")){
                // Keep the main passive friend, move it into the cone; a separate enemy is on aim.
                friend.requestTeleport(p.getX()+forward.x*3-side.x*2,p.getEyeY()-.9,p.getZ()+forward.z*3-side.z*2);
                replacement=hostile(p,p.getEyePos().add(forward.multiply(3)).add(0,-.9,0));enemyStart=replacement.getPos();
                if(covered==null)throw new IllegalStateException("missing existing covered ally");
                covered.requestTeleport(p.getX()+forward.x*3+side.x*2,p.getEyeY()-.9,p.getZ()+forward.z*3+side.z*2);
                coveredStart=covered.getPos();friendStart=friend.getPos();
            }else if(name.equals("lucio-wallride")){
                // Loaded air only, thin lateral wall running in the actual aim direction.
                var axis=Math.abs(side.x)>Math.abs(side.z)?new BlockPos(side.x>0?1:-1,0,0):new BlockPos(0,0,side.z>0?1:-1);
                var along=Math.abs(forward.x)>Math.abs(forward.z)?new BlockPos(forward.x>0?1:-1,0,0):new BlockPos(0,0,forward.z>0?1:-1);
                var origin=p.getBlockPos().add(axis);var pending=new LinkedHashMap<BlockPos,BlockState>();
                for(int i=-2;i<=5;i++)for(int y=0;y<3;y++){
                    var at=origin.add(along.getX()*i,y,along.getZ()*i);
                    if(!world.isChunkLoaded(at)||!world.getBlockState(at).isAir())throw new IllegalStateException("support wall site occupied");
                    pending.put(at,world.getBlockState(at));
                }
                blocks.putAll(pending);for(var at:blocks.keySet())world.setBlockState(at,Blocks.STONE.getDefaultState());
                wallNormal=new Vec3d(axis.getX(),0,axis.getZ());wallCenter=Vec3d.ofCenter(origin);
                var contact=p.getPos().add(wallNormal.multiply(.19));
                if(world.isSpaceEmpty(p,p.getBoundingBox().offset(contact.subtract(p.getPos()))))p.requestTeleport(contact.x,contact.y,contact.z);
            }
        }catch(Exception failure){String why=failure.toString();cleanup();NativeCombatScene.cleanup();error=why;}
    }
    public static void addStatus(MinecraftServer server,JsonObject out){
        if(!error.isEmpty())out.addProperty("testError",error);
        if(scene.isEmpty()||world==null)return;var p=server.getPlayerManager().getPlayer(owner);
        if(p==null||p.getServerWorld()!=world){cleanup();return;}
        var lab=new JsonObject();lab.addProperty("scene",scene);lab.addProperty("playerHealth",p.getHealth());
        lab.addProperty("occludedHealth",covered==null?-1:covered.getHealth());
        lab.addProperty("targetUuid",replacement!=null?replacement.getUuidAsString():friend==null?"":friend.getUuidAsString());
        lab.addProperty("enemyDisplacement",replacement==null||enemyStart==null?0:replacement.getPos().distanceTo(enemyStart));
        lab.addProperty("coveredDisplacement",covered==null||coveredStart==null?0:covered.getPos().distanceTo(coveredStart));
        lab.addProperty("friendDisplacement",friend==null||friendStart==null?0:friend.getPos().distanceTo(friendStart));
        if(wallCenter!=null&&p.getPos().subtract(wallCenter).dotProduct(wallNormal)>.5)wallCrossings=1;
        lab.addProperty("wallCrossings",wallCrossings);out.add("supportCommitLab",lab);
        if(replacement!=null){out.addProperty("targetId",replacement.getId());out.addProperty("targetHealth",replacement.getHealth());out.addProperty("targetAlive",replacement.isAlive());}
    }
    public static void cleanup(){
        if(replacement!=null)replacement.discard();replacement=null;
        if(world!=null)for(var entry:blocks.entrySet())if(world.getBlockState(entry.getKey()).isOf(Blocks.STONE))world.setBlockState(entry.getKey(),entry.getValue());
        blocks.clear();world=null;owner=null;scene="";error="";covered=friend=null;enemyStart=coveredStart=friendStart=wallCenter=wallNormal=null;wallCrossings=0;
    }
    private SupportCommitFixtures(){}
}
