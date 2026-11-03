package lab.owmcguest;

import com.google.gson.JsonObject;
import java.nio.file.Files;
import java.nio.file.Path;
import net.minecraft.block.Blocks;
import net.minecraft.block.EndPortalFrameBlock;
import net.minecraft.block.NetherPortalBlock;
import net.minecraft.server.MinecraftServer;
import net.minecraft.server.network.ServerPlayerEntity;
import net.minecraft.server.world.ServerWorld;
import net.minecraft.registry.tag.StructureTags;
import net.minecraft.util.math.BlockPos;
import net.minecraft.util.math.Direction;
import net.minecraft.util.math.Box;
import net.minecraft.util.math.Vec3d;
import net.minecraft.world.Heightmap;
import net.minecraft.util.WorldSavePath;

/** One-time setup for the selected natural save: village spawn plus two portals. */
public final class VillageWorldSetup {
    private static boolean attempted;
    public static volatile String status="{\"ready\":false}";

    public static void tick(MinecraftServer server){
        if(attempted||!Boolean.getBoolean("owmc.villagePortals"))return;
        var player=server.getPlayerManager().getPlayerList().stream().findFirst().orElse(null);if(player==null)return;
        attempted=true;
        try {setup(server,player);}catch(Exception e){status="{\"ready\":false,\"error\":"+new com.google.gson.Gson().toJson(e.toString())+"}";System.err.println("[OWMCGuest] Village portal setup: "+e);}
    }
    private static void setup(MinecraftServer server,ServerPlayerEntity player) throws Exception {
        var marker=server.getSavePath(WorldSavePath.ROOT).resolve("owmc-village-portals-v1");
        if(Files.isRegularFile(marker)){status=Files.readString(marker);return;}
        ServerWorld world=server.getOverworld();var origin=player.getBlockPos();var village=world.locateStructure(StructureTags.VILLAGE,origin,100,false);
        if(village==null)throw new IllegalStateException("no village within 100 chunks of spawn");
        var portal=pad(world,village.add(32,0,24),5,3);var end=pad(world,village.add(-32,0,24),7,7);
        platform(world,portal,5,3);platform(world,end,7,7);
        buildNether(world,portal);buildEnd(world,end);
        var landing=world.getTopPosition(Heightmap.Type.MOTION_BLOCKING_NO_LEAVES,village.add(0,0,8));
        if(world.isSpaceEmpty(new Box(Vec3d.of(landing),Vec3d.of(landing.add(1,3,1)))))player.requestTeleport(landing.getX()+.5,landing.getY(),landing.getZ()+.5);
        var out=new JsonObject();out.addProperty("ready",true);out.addProperty("village",village.toShortString());out.addProperty("netherPortal",portal.toShortString());out.addProperty("endPortal",end.toShortString());status=out.toString();
        Files.writeString(marker,status+"\n");
        System.out.println("[OWMCGuest] Natural village and portals ready: "+status);
    }
    private static BlockPos pad(ServerWorld world,BlockPos near,int width,int depth){
        for(int radius=0;radius<=48;radius+=2)for(int dx=-radius;dx<=radius;dx+=2)for(int dz=-radius;dz<=radius;dz+=2){
            if(Math.max(Math.abs(dx),Math.abs(dz))!=radius)continue;
            var top=world.getTopPosition(Heightmap.Type.MOTION_BLOCKING_NO_LEAVES,near.add(dx,0,dz));
            var box=new Box(Vec3d.of(top.add(-width/2,0,-depth/2)),Vec3d.of(top.add((width+1)/2,5,(depth+1)/2)));
            if(world.isSpaceEmpty(box))return top;
        }
        var fallback=world.getTopPosition(Heightmap.Type.MOTION_BLOCKING_NO_LEAVES,near);platform(world,fallback,width,depth);return fallback;
    }
    private static void platform(ServerWorld world,BlockPos top,int width,int depth){
        for(int x=-width/2;x<=width/2;x++)for(int z=-depth/2;z<=depth/2;z++)world.setBlockState(top.add(x,-1,z),Blocks.STONE_BRICKS.getDefaultState());
    }
    private static void buildNether(ServerWorld world,BlockPos base){
        for(int x=-1;x<=2;x++)for(int y=0;y<=4;y++)if(x==-1||x==2||y==0||y==4)world.setBlockState(base.add(x,y,0),Blocks.OBSIDIAN.getDefaultState());
        var portal=Blocks.NETHER_PORTAL.getDefaultState().with(NetherPortalBlock.AXIS,Direction.Axis.X);for(int x=0;x<=1;x++)for(int y=1;y<=3;y++)world.setBlockState(base.add(x,y,0),portal);
    }
    private static void buildEnd(ServerWorld world,BlockPos base){
        for(int x=-2;x<=2;x++)for(int z=-2;z<=2;z++){
            if(Math.abs(x)==2&&Math.abs(z)==2)continue;
            boolean frame=Math.abs(x)==2||Math.abs(z)==2;
            var pos=base.add(x,0,z);if(frame){Direction facing=Math.abs(x)==2?(x<0?Direction.EAST:Direction.WEST):(z<0?Direction.SOUTH:Direction.NORTH);world.setBlockState(pos,Blocks.END_PORTAL_FRAME.getDefaultState().with(EndPortalFrameBlock.FACING,facing).with(EndPortalFrameBlock.EYE,true));}else world.setBlockState(pos,Blocks.END_PORTAL.getDefaultState());
        }
    }
    public static void reset(){attempted=false;status="{\"ready\":false}";}
}
