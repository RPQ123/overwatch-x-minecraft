package lab.owmcguest;

import com.google.gson.JsonObject;
import java.util.UUID;
import net.minecraft.block.Blocks;
import net.minecraft.block.EndPortalFrameBlock;
import net.minecraft.block.NetherPortalBlock;
import net.minecraft.server.MinecraftServer;
import net.minecraft.server.network.ServerPlayerEntity;
import net.minecraft.server.world.ServerWorld;
import net.minecraft.util.math.BlockPos;
import net.minecraft.util.math.Direction;
import net.minecraft.util.math.Vec3d;

/** Builds vanilla portal blocks in the current Overworld without replacing distant terrain. */
public final class NativePortalRuntime {
    public static volatile long netherBuilds,endBuilds; public static volatile String status="{\"netherBuilds\":0,\"endBuilds\":0}";
    private static ServerPlayerEntity player(MinecraftServer s,UUID id){var p=s.getPlayerManager().getPlayer(id);return p!=null&&p.isAlive()?p:null;}
    private static BlockPos ahead(ServerPlayerEntity p,Vec3d f){var h=new Vec3d(f.x,0,f.z).normalize();if(h.lengthSquared()<.5)h=new Vec3d(0,0,1);return BlockPos.ofFloored(p.getPos().add(h.multiply(4))).up();}
    public static void buildNether(MinecraftServer s,UUID id,Vec3d eye,Vec3d f){var p=player(s,id);if(p==null)return;var b=ahead(p,f);var w=p.getServerWorld();clear(w,b,5,3);for(int x=-1;x<=2;x++)for(int y=0;y<=4;y++)if(x==-1||x==2||y==0||y==4)w.setBlockState(b.add(x,y,0),Blocks.OBSIDIAN.getDefaultState());var portal=Blocks.NETHER_PORTAL.getDefaultState().with(NetherPortalBlock.AXIS,Direction.Axis.X);for(int x=0;x<=1;x++)for(int y=1;y<=3;y++)w.setBlockState(b.add(x,y,0),portal);netherBuilds++;publish();}
    public static void buildEnd(MinecraftServer s,UUID id,Vec3d eye,Vec3d f){var p=player(s,id);if(p==null)return;var b=ahead(p,f).add(0,-1,0);var w=p.getServerWorld();clear(w,b,7,7);for(int x=-2;x<=2;x++)for(int z=-2;z<=2;z++){if(Math.abs(x)==2&&Math.abs(z)==2)continue;var pos=b.add(x,0,z);if(Math.abs(x)==2||Math.abs(z)==2){Direction d=Math.abs(x)==2?(x<0?Direction.EAST:Direction.WEST):(z<0?Direction.SOUTH:Direction.NORTH);w.setBlockState(pos,Blocks.END_PORTAL_FRAME.getDefaultState().with(EndPortalFrameBlock.FACING,d).with(EndPortalFrameBlock.EYE,true));}else w.setBlockState(pos,Blocks.END_PORTAL.getDefaultState());}endBuilds++;publish();}
    private static void clear(ServerWorld w,BlockPos b,int width,int depth){for(int x=-width/2;x<=width/2;x++)for(int z=-depth/2;z<=depth/2;z++)for(int y=0;y<6;y++)if(!w.getBlockState(b.add(x,y,z)).isAir())w.setBlockState(b.add(x,y,z),Blocks.AIR.getDefaultState());for(int x=-width/2;x<=width/2;x++)for(int z=-depth/2;z<=depth/2;z++)w.setBlockState(b.add(x,-1,z),Blocks.STONE_BRICKS.getDefaultState());}
    private static void publish(){var o=new JsonObject();o.addProperty("netherBuilds",netherBuilds);o.addProperty("endBuilds",endBuilds);status=o.toString();}
    public static void close(){netherBuilds=endBuilds=0;publish();}
    public static void resetSession(){netherBuilds=endBuilds=0;publish();}
}
