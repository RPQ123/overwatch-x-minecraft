package lab.owmcguest;

import java.util.*;
import com.google.gson.*;
import net.minecraft.block.*;
import net.minecraft.server.MinecraftServer;
import net.minecraft.server.world.ServerWorld;
import net.minecraft.util.math.*;
import lab.owmcguest.HanzoCombatSite.Cell;

/** Explicit isolated Hanzo 16m fixture: find empty air, fill only an owned floor.
 * Never clears terrain or grants/creates a native attack. */
public final class HanzoCombatLab {
    static {net.fabricmc.fabric.api.event.lifecycle.v1.ServerLifecycleEvents.SERVER_STOPPING.register(server->cleanup());}
    private static ServerWorld world;private static HanzoLabBlocks<BlockState> floor;
    private static long startSerial,cleanupSerial,lastStartWall,lastCleanupWall;
    private static JsonObject lastStart=new JsonObject(),lastCleanup=new JsonObject();
    public static volatile String status="{\"active\":false,\"ownedBlocks\":0,\"startSerial\":0,\"cleanupSerial\":0,\"state\":\"idle\"}";
    private HanzoCombatLab(){}
    private static BlockPos pos(Cell c){return new BlockPos(c.x(),c.y(),c.z());}
    private static JsonObject snapshot(boolean active,String state,String error){
        var o=new JsonObject();o.addProperty("active",active);o.addProperty("state",state);o.addProperty("ownedBlocks",floor==null?0:floor.size());
        o.addProperty("startSerial",startSerial);o.addProperty("cleanupSerial",cleanupSerial);o.addProperty("lastStartWall",lastStartWall);o.addProperty("lastCleanupWall",lastCleanupWall);
        o.add("lastStart",lastStart.deepCopy());o.add("lastCleanup",lastCleanup.deepCopy());if(error!=null)o.addProperty("error",error);return o;
    }
    private static HanzoLabBlocks.Access<BlockState> blocks(){
        var w=world;
        return new HanzoLabBlocks.Access<>(){
            public boolean loaded(Cell c){return w!=null&&w.isChunkLoaded(pos(c));}
            public BlockState read(Cell c){return w.getBlockState(pos(c));}
            public boolean air(BlockState s){return s.isAir();}
            public boolean placed(BlockState s){return s.isOf(Blocks.STONE);}
            public boolean write(Cell c,BlockState s){return w.setBlockState(pos(c),s);}
        };
    }
    public static void start(MinecraftServer server,UUID owner,Vec3d direction){
        startSerial++;lastStartWall=System.currentTimeMillis();lastStart=new JsonObject();lastStart.addProperty("owner",owner.toString());
        boolean admitted=false;
        try{
            var p=server.getPlayerManager().getPlayer(owner);
            String actual=server.getSaveProperties().getLevelName();lastStart.addProperty("save",actual);
            HanzoCombatSite.requireIsolated(Boolean.getBoolean("owmc.twilightTrial"),System.getProperty("owmc.worldName",""),actual,p!=null&&p.isAlive()&&p.isCreative());
            if(!Double.isFinite(direction.x)||!Double.isFinite(direction.y)||!Double.isFinite(direction.z)||Math.abs(direction.y)>.02)throw new IllegalArgumentException("Hanzo combat fixture needs a finite horizontal direction");
            var forward=new Vec3d(direction.x,0,direction.z).normalize();if(forward.lengthSquared()<.99)throw new IllegalArgumentException("Hanzo combat fixture direction unavailable");
            admitted=true;cleanup();if(floor!=null&&floor.size()!=0)throw new IllegalStateException("previous owned Hanzo floor cleanup pending: "+lastCleanup);
            HanzoArrowVisualLab.cleanup();NativeCombatScene.cleanup();
            var candidate=p.getServerWorld();var initial=p.getBlockPos().down();
            lastStart.addProperty("world",NativeWorldIdentity.of(server,candidate.getRegistryKey()));lastStart.add("initialFloor",new Gson().toJsonTree(new Cell(initial.getX(),initial.getY(),initial.getZ())));
            var search=HanzoCombatSite.find(initial.getX(),initial.getY(),initial.getZ(),candidate.getBottomY(),candidate.getTopY(),new HanzoCombatSite.Space(){
                public HanzoCombatSite.Blockage blocked(Cell c,boolean isFloor){
                    var at=pos(c);
                    if(!candidate.isChunkLoaded(at))return new HanzoCombatSite.Blockage("unloaded","chunk is not loaded; no chunk load requested",c);
                    if(!candidate.getWorldBorder().contains(at))return new HanzoCombatSite.Blockage("world-border","outside world border",c);
                    var state=candidate.getBlockState(at);
                    if(candidate.getBlockEntity(at)!=null)return new HanzoCombatSite.Blockage("block-entity","protected block entity: "+state,c);
                    if(state.isAir())return null;
                    if(isFloor&&state.getFluidState().isEmpty()&&state.isSideSolidFullSquare(candidate,at,Direction.UP))return null;
                    return new HanzoCombatSite.Blockage(isFloor?"unsupported-floor":"occupied-corridor",state.toString(),c);
                }
                public boolean occupied(Cell c){return !candidate.getOtherEntities(p,new Box(c.x()-18,c.y()+1,c.z()-18,c.x()+19,c.y()+6,c.z()+19),e->e instanceof net.minecraft.entity.LivingEntity&&e.isAlive()).isEmpty();}
            });
            lastStart.add("search",new Gson().toJsonTree(search));
            if(search.floor()==null)throw new IllegalStateException("no safe loaded Hanzo corridor after "+search.attempts()+" candidates; rejected="+search.rejected()+"; see lastStart.search.samples; terrain preserved");
            var site=search.floor();world=candidate;floor=new HanzoLabBlocks<>(site,HanzoCombatSite.EXTENT,Blocks.STONE.getDefaultState());
            int added=0,preserved=0;var access=blocks();
            for(int x=-18;x<=18;x++)for(int z=-18;z<=18;z++){
                if(floor.place(new Cell(site.x()+x,site.y(),site.z()+z),access))added++;else preserved++;
            }
            lastStart.addProperty("filledAirBlocks",added);lastStart.addProperty("preservedFloorBlocks",preserved);
            lastStart.addProperty("floorMinX",site.x()-18);lastStart.addProperty("floorMaxX",site.x()+18);lastStart.addProperty("floorY",site.y());
            lastStart.addProperty("floorMinZ",site.z()-18);lastStart.addProperty("floorMaxZ",site.z()+18);lastStart.addProperty("terrainCleared",0);
            p.requestTeleport(site.x()+.5,site.y()+1,site.z()+.5);p.setVelocity(Vec3d.ZERO);p.fallDistance=0;
            NativeCombatScene.meiLab(server,owner,forward,16);
            var generic=new JsonObject();NativeCombatScene.addStatus(server,generic);
            if(!generic.has("targetId")||!generic.get("testError").getAsString().isEmpty())throw new IllegalStateException("Hanzo target placement refused: "+generic.get("testError"));
            var target=world.getEntityById(generic.get("targetId").getAsInt());
            if(target==null||!target.isAlive()||!world.isSpaceEmpty(target.getBoundingBox()))throw new IllegalStateException("Hanzo target is absent or obstructed after placement");
            var ray=world.raycast(new net.minecraft.world.RaycastContext(p.getEyePos(),new Vec3d(target.getX(),p.getEyeY(),target.getZ()),net.minecraft.world.RaycastContext.ShapeType.COLLIDER,net.minecraft.world.RaycastContext.FluidHandling.NONE,p));
            if(ray.getType()!=net.minecraft.util.hit.HitResult.Type.MISS)throw new IllegalStateException("Hanzo actual aim corridor obstructed at "+ray.getPos());
            var o=snapshot(true,"ready",null);o.addProperty("targetId",target.getId());o.addProperty("targetDistance",p.getEyePos().distanceTo(new Vec3d(target.getX(),p.getEyeY(),target.getZ())));o.addProperty("corridorClear",true);status=o.toString();
        }catch(RuntimeException failure){
            if(admitted){cleanup();NativeCombatScene.cleanup();}
            lastStart.addProperty("failure",failure.toString());status=snapshot(false,"failed",failure.toString()).toString();throw failure;
        }
    }
    /** Hook before generic scene cleanup; only tracked placed cells are restored. */
    public static void cleanup(){
        lastCleanupWall=System.currentTimeMillis();cleanupSerial++;
        var receipt=floor==null?new HanzoLabBlocks.Receipt(0,0,0,List.of()):floor.restore(blocks());
        lastCleanup=new Gson().toJsonTree(receipt).getAsJsonObject();
        if(receipt.pending()==0){floor=null;world=null;}
        status=snapshot(false,"idle",receipt.pending()>0?"owned Hanzo floor restoration pending: "+receipt.failures():null).toString();
    }
}
