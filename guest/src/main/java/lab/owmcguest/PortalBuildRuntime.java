package lab.owmcguest;

import com.google.gson.*;
import java.util.*;
import java.util.function.BooleanSupplier;
import net.minecraft.block.*;
import net.minecraft.registry.*;
import net.minecraft.server.MinecraftServer;
import net.minecraft.server.world.ServerWorld;
import net.minecraft.server.network.ServerPlayerEntity;
import net.minecraft.util.Identifier;
import net.minecraft.util.math.*;

/** A bounded explicit creative convenience; all portal collision belongs to vanilla/the mod. */
public final class PortalBuildRuntime {
    public static volatile String status="{}";
    private static long requests,completed;private static String error="";private static JsonObject last;
    private record Undo(ServerWorld world,UUID owner,Map<BlockPos,BlockState> before,Map<BlockPos,BlockState> after){}
    private static Undo undo;private static long testUndone;
    public static void build(MinecraftServer server,UUID owner,String selected,Vec3d direction,BooleanSupplier admitted){
        requests++;error="";last=new JsonObject();
        var before=new LinkedHashMap<BlockPos,BlockState>();ServerWorld world=null;
        try{
            var p=server.getPlayerManager().getPlayer(owner);
            if(p==null||!p.isAlive()||!SurvivalRuntime.permitted(p)||!server.isSingleplayer()||!admitted.getAsBoolean())throw new IllegalStateException("Current offline creative admission required");
            var entry=PortalCatalog.entries.stream().filter(e->e.id().equals(selected)).findFirst().orElseThrow();
            if(entry.kind().equals("twilight")){TwilightForestTrial.buildPlayerPortal(server,owner,direction);var result=JsonParser.parseString(TwilightForestTrial.status).getAsJsonObject();if(result.has("error")&&!result.get("error").getAsString().isEmpty())throw new IllegalStateException(result.get("error").getAsString());last.addProperty("portal",selected);last.addProperty("delegated",true);completed++;publish();return;}
            world=p.getServerWorld();var flat=new Vec3d(direction.x,0,direction.z).normalize();
            if(flat.lengthSquared()<.5)throw new IllegalStateException("Look horizontally before building a portal");
            var base=BlockPos.ofFloored(p.getPos().add(flat.multiply(6))).down();
            for(int x=-4;x<=4;x++)for(int z=-4;z<=4;z++)for(int y=-3;y<=7;y++){
                var at=base.add(x,y,z);
                if(at.getY()<world.getBottomY()||at.getY()>=world.getTopY()||!world.isChunkLoaded(at)||!world.getWorldBorder().contains(at))throw new IllegalStateException("Portal area must be loaded and inside the world");
                if(world.getBlockEntity(at)!=null||world.getBlockState(at).getHardness(world,at)<0)throw new IllegalStateException("Protected block or container in front; original terrain preserved");
                before.put(at,world.getBlockState(at));
            }
            for(int x=-3;x<=3;x++)for(int z=-3;z<=3;z++){
                world.setBlockState(base.add(x,0,z),Blocks.STONE_BRICKS.getDefaultState());
                for(int y=1;y<=6;y++)world.setBlockState(base.add(x,y,z),Blocks.AIR.getDefaultState());
            }
            if(entry.kind().equals("aoa")){
                var block=Registries.BLOCK.get(Identifier.of(entry.block()));
                if(world.getRegistryKey()!=net.minecraft.world.World.OVERWORLD)ModApi.call(block,"createPortalFrameAndSpace",world,p,base.up());
                else {
                    // The author's automatic return-frame API deliberately does nothing
                    // in Overworld. This explicit creative builder uses its real blocks
                    // and the actual installed5x6 frame; collision stays in the mod.
                    var frame=((Block)ModApi.call(block,"getPortalFrame")).getDefaultState();
                    var axis=Math.abs(flat.x)>=Math.abs(flat.z)?Direction.Axis.X:Direction.Axis.Z;
                    var active=block.getDefaultState().with(net.minecraft.state.property.Properties.HORIZONTAL_AXIS,axis);
                    for(int side=-2;side<=2;side++)for(int y=0;y<=5;y++){
                        var at=base.add(axis==Direction.Axis.Z?side:0,y,axis==Direction.Axis.X?side:0);
                        world.setBlockState(at,Math.abs(side)==2||y==0||y==5?frame:active,Block.NOTIFY_LISTENERS);
                    }
                    last.addProperty("explicitOverworldFrame",true);
                }
            }else if(entry.kind().equals("end")){
                for(int x=-2;x<=2;x++)for(int z=-2;z<=2;z++){
                    if(Math.abs(x)==2&&Math.abs(z)==2)continue;
                    if(Math.abs(x)==2||Math.abs(z)==2){Direction d=Math.abs(x)==2?(x<0?Direction.EAST:Direction.WEST):(z<0?Direction.SOUTH:Direction.NORTH);world.setBlockState(base.add(x,0,z),Blocks.END_PORTAL_FRAME.getDefaultState().with(EndPortalFrameBlock.FACING,d).with(EndPortalFrameBlock.EYE,true));}
                    else world.setBlockState(base.add(x,0,z),Blocks.END_PORTAL.getDefaultState());
                }
            }else{
                boolean alongX=Math.abs(flat.z)>=Math.abs(flat.x);Block frame=entry.kind().equals("aether")?Blocks.GLOWSTONE:Blocks.OBSIDIAN;
                for(int side=-1;side<=2;side++)for(int y=0;y<=4;y++)if(side==-1||side==2||y==0||y==4)world.setBlockState(base.add(alongX?side:0,y,alongX?0:side),frame.getDefaultState());
                var inside=base.up();var axis=alongX?Direction.Axis.X:Direction.Axis.Z;
                if(entry.kind().equals("aether")){
                    var shape=ModApi.call(Class.forName("com.aetherteam.aether.block.portal.AetherPortalShape"),"findEmptyAetherPortalShape",world,inside,axis);
                    if(!(shape instanceof Optional<?> optional)||optional.isEmpty())throw new IllegalStateException("Original Aether portal shape rejected the frame");
                    ModApi.call(optional.get(),"createPortalBlocks");
                }else for(int side=0;side<=1;side++)for(int y=1;y<=3;y++)world.setBlockState(base.add(alongX?side:0,y,alongX?0:side),Blocks.NETHER_PORTAL.getDefaultState().with(NetherPortalBlock.AXIS,axis));
            }
            int count=0;for(var at:before.keySet())if(Registries.BLOCK.getId(world.getBlockState(at).getBlock()).toString().equals(entry.block()))count++;
            if(count==0)throw new IllegalStateException("No actual original portal blocks survived activation");
            var changed=new LinkedHashMap<BlockPos,BlockState>();var expected=new LinkedHashMap<BlockPos,BlockState>();for(var pair:before.entrySet()){var actual=world.getBlockState(pair.getKey());if(!actual.equals(pair.getValue())){changed.put(pair.getKey(),pair.getValue());expected.put(pair.getKey(),actual);}}
            undo=new Undo(world,owner,changed,expected);
            completed++;last.addProperty("portal",selected);last.addProperty("block",entry.block());last.addProperty("dimension",world.getRegistryKey().getValue().toString());last.addProperty("targetDimension",entry.dimension());last.addProperty("x",base.getX());last.addProperty("y",base.getY());last.addProperty("z",base.getZ());last.addProperty("portalBlocks",count);last.addProperty("nativePortal",true);
        }catch(Exception e){error=e.getClass().getSimpleName()+": "+e.getMessage();if(world!=null)for(var pair:before.entrySet())world.setBlockState(pair.getKey(),pair.getValue(),Block.NOTIFY_ALL);}
        publish();
    }
    /** Revert only the unchanged blocks of our last explicit build, only in the disposable lab. */
    public static void undoTest(MinecraftServer server,UUID owner){
        try{var p=server.getPlayerManager().getPlayer(owner);var u=undo;
            if(!server.isSingleplayer()||!Boolean.getBoolean("owmc.twilightTrial")||!System.getProperty("owmc.worldName","").startsWith("Overwatch Twilight Switch ")||p==null||!p.isCreative()||u==null||!u.owner.equals(owner)||p.getServerWorld()!=u.world)throw new IllegalStateException("No owned reversible portal in this Switch lab");
            for(var row:u.after.entrySet())if(!u.world.isChunkLoaded(row.getKey())||(u.world.getBlockEntity(row.getKey())!=null&&!(row.getValue().isOf(Blocks.END_PORTAL)&&u.world.getBlockEntity(row.getKey()) instanceof net.minecraft.block.entity.EndPortalBlockEntity))||!u.world.getBlockState(row.getKey()).equals(row.getValue()))throw new IllegalStateException("Portal changed after construction; test undo refused");
            for(var row:u.before.entrySet())u.world.setBlockState(row.getKey(),row.getValue(),Block.NOTIFY_LISTENERS);
            undo=null;testUndone++;error="";
        }catch(Exception e){error=e.toString();}publish();
    }
    private static void publish(){var out=new JsonObject();out.addProperty("requests",requests);out.addProperty("completed",completed);out.addProperty("testUndone",testUndone);out.addProperty("error",error);out.add("last",last==null?new JsonObject():last);status=out.toString();}
}
