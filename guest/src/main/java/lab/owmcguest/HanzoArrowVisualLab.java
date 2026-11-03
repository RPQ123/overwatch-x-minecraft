package lab.owmcguest;

import java.util.*;
import com.google.gson.JsonObject;
import net.minecraft.block.*;
import net.minecraft.server.MinecraftServer;
import net.minecraft.server.world.ServerWorld;
import net.minecraft.util.math.*;

/** Opt-in reversible 10 m visual fixture. NativeCombatScene owns its existing
 * floor/villager; this fixture owns only a stone wall in previously empty air.
 * Does not grant a skill, create projectiles, change HP or fabricate attacks. */
public final class HanzoArrowVisualLab {
    private static ServerWorld world;
    private static final Map<BlockPos,BlockState> original=new LinkedHashMap<>();
    private static long cleanupSerial,lastCleanupWall,startSerial,lastStartWall;
    public static volatile String status="{\"active\":false,\"wallBlocks\":0}";
    private HanzoArrowVisualLab(){}
    public static void start(MinecraftServer server,UUID owner,Vec3d direction){
        startSerial++;lastStartWall=System.currentTimeMillis();
        try{build(server,owner,direction);}
        catch(RuntimeException failure){
            cleanup();NativeCombatScene.cleanup();
            var o=new JsonObject();o.addProperty("active",false);o.addProperty("wallBlocks",original.size());
            o.addProperty("cleanupSerial",cleanupSerial);o.addProperty("lastCleanupWall",lastCleanupWall);
            o.addProperty("startSerial",startSerial);o.addProperty("lastStartWall",lastStartWall);o.addProperty("state","failed");
            o.addProperty("error",failure.toString());status=o.toString();throw failure;
        }
    }
    private static BlockPos pos(HanzoArrowVisualLayout.Cell c){return new BlockPos(c.x(),c.y(),c.z());}
    private static void build(MinecraftServer server,UUID owner,Vec3d direction){
        cleanup();if(!original.isEmpty())throw new IllegalStateException("Hanzo visual wall restoration pending");
        var player=server.getPlayerManager().getPlayer(owner);
        if(player==null||!player.isAlive()||!player.isCreative()||!System.getProperty("owmc.worldName","").startsWith("Overwatch Twilight Switch "))throw new IllegalArgumentException("Hanzo visual fixture requires isolated creative lab");
        var candidateWorld=player.getServerWorld();var initial=player.getBlockPos().down();
        var origin=HanzoArrowVisualLayout.chooseFloor(initial.getX(),initial.getY(),initial.getZ(),candidateWorld.getBottomY(),candidateWorld.getTopY(),
            c->candidateWorld.isChunkLoaded(pos(c))&&candidateWorld.getWorldBorder().contains(pos(c)),
            c->candidateWorld.getBlockState(pos(c)).isAir(),
            c->{var p=pos(c);var state=candidateWorld.getBlockState(p);return state.isAir()||state.getFluidState().isEmpty()&&state.isSideSolidFullSquare(candidateWorld,p,Direction.UP);},
            y->candidateWorld.getOtherEntities(player,new Box(initial.getX()-12,y+1,initial.getZ()-12,initial.getX()+13,y+6,initial.getZ()+13),e->e instanceof net.minecraft.entity.LivingEntity&&e.isAlive()).isEmpty());
        player.requestTeleport(origin.x()+.5,origin.y()+1,origin.z()+.5);player.setVelocity(Vec3d.ZERO);player.fallDistance=0;
        // Isolate the three visual takes; an earlier private sonar sphere must
        // not cover the following Scatter picture. No native CD is changed.
        HanzoSonicArrowRuntime.resetSession();HanzoArrowPresentation.reset();
        NativeCombatScene.meiLab(server,owner,direction,10);
        var existing=new JsonObject();NativeCombatScene.addStatus(server,existing);
        if(!existing.has("targetId")||!existing.get("testError").getAsString().isEmpty())throw new IllegalStateException("Hanzo visual floor/target unavailable: "+existing.get("testError"));
        world=player.getServerWorld();var forward=new Vec3d(direction.x,0,direction.z).normalize();
        if(forward.lengthSquared()<.9)throw new IllegalArgumentException("Hanzo fixture horizontal direction");
        var side=new Vec3d(-forward.z,0,forward.x);var eye=player.getEyePos();var ahead=BlockPos.ofFloored(eye.add(forward.multiply(10)));
        int feetY=player.getBlockY();var center=new BlockPos(ahead.getX(),feetY+1,ahead.getZ());
        var sites=new LinkedHashSet<BlockPos>();boolean xAxis=Math.abs(forward.x)>Math.abs(forward.z);
        for(int y=0;y<4;y++)for(int width=-3;width<=3;width++)sites.add(new BlockPos(center.getX()+(xAxis?0:width),HanzoArrowVisualLayout.wallBottom(feetY)+y,center.getZ()+(xAxis?width:0)));
        int wallCount=sites.size();
        // Catch downward children at feet level, keeping even the slow mother
        // above this surface until the wall. Existing solids are never replaced.
        int existingFloor=0;
        for(int distance=4;distance<=10;distance++)for(int width=-3;width<=3;width++){
            var at=BlockPos.ofFloored(eye.add(forward.multiply(distance)).add(side.multiply(width)));
            var floor=new BlockPos(at.getX(),HanzoArrowVisualLayout.catchFloor(feetY),at.getZ());
            if(!world.isChunkLoaded(floor))throw new IllegalStateException("Hanzo catch floor unloaded");
            if(world.getBlockState(floor).isAir())sites.add(floor);else existingFloor++;
        }
        for(var pos:sites)if(!world.isChunkLoaded(pos)||!world.getBlockState(pos).isAir()||world.getBlockEntity(pos)!=null)throw new IllegalStateException("Hanzo visual wall site occupied/unloaded: "+pos+" state="+world.getBlockState(pos)+" feetY="+feetY+" eyeY="+eye.y);
        for(var pos:sites){original.put(pos,world.getBlockState(pos));world.setBlockState(pos,Blocks.STONE.getDefaultState());}
        var target=world.getEntityById(existing.get("targetId").getAsInt());
        if(target==null){cleanup();throw new IllegalStateException("Hanzo visual owned target vanished");}
        var at=eye.add(forward.multiply(10.8)).add(side.multiply(2.2));target.setPosition(at.x,at.y-.9,at.z);
        var o=new JsonObject();o.addProperty("active",true);o.addProperty("wallBlocks",original.size());o.addProperty("wallDistance",10);
        o.addProperty("cleanupSerial",cleanupSerial);o.addProperty("lastCleanupWall",lastCleanupWall);
        o.addProperty("startSerial",startSerial);o.addProperty("lastStartWall",lastStartWall);o.addProperty("state","ready");o.addProperty("originRaised",origin.y()-initial.getY());o.addProperty("feetY",feetY);o.addProperty("eyeY",eye.y);
        o.addProperty("wallBlockCount",wallCount);o.addProperty("catchFloorBlocks",sites.size()-wallCount+existingFloor);o.addProperty("preservedExistingFloor",existingFloor);o.addProperty("catchFloorY",HanzoArrowVisualLayout.catchFloor(feetY));o.addProperty("wallAxis",xAxis?"x":"z");
        o.addProperty("targetDistance",eye.distanceTo(at));o.addProperty("targetId",target.getId());o.addProperty("targetUuid",target.getUuidAsString());
        o.addProperty("world",NativeWorldIdentity.of(server,world.getRegistryKey()));o.addProperty("wallX",center.getX());o.addProperty("wallY",center.getY());o.addProperty("wallZ",center.getZ());
        o.addProperty("centerLine","wall impact; target is beside/behind it, so the entity cannot consume the center arrow");status=o.toString();
    }
    /** Add BEFORE NativeCombatScene.cleanup in the existing cleanup route. */
    public static void cleanup(){
        lastCleanupWall=System.currentTimeMillis();
        HanzoArrowPresentation.retireForFixtureCleanup(lastCleanupWall);HanzoSonicArrowRuntime.resetSession();
        int conflicts=0;
        if(world!=null)for(var e:new ArrayList<>(original.entrySet())){
            if(!world.isChunkLoaded(e.getKey()))continue;
            if(world.getBlockState(e.getKey()).isOf(Blocks.STONE))world.setBlockState(e.getKey(),e.getValue());else conflicts++;
            original.remove(e.getKey());
        }
        var o=new JsonObject();o.addProperty("active",false);o.addProperty("wallBlocks",original.size());o.addProperty("preservedExternalChanges",conflicts);
        o.addProperty("cleanupSerial",++cleanupSerial);o.addProperty("lastCleanupWall",lastCleanupWall);
        o.addProperty("startSerial",startSerial);o.addProperty("lastStartWall",lastStartWall);o.addProperty("state","idle");
        if(!original.isEmpty())o.addProperty("error","owned chunks unloaded; restoration pending");else world=null;status=o.toString();
    }
}
