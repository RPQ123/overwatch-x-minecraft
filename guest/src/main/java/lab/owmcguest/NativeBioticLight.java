package lab.owmcguest;

import java.util.Comparator;
import net.minecraft.block.*;
import net.minecraft.server.world.ChunkTicketType;
import net.minecraft.server.world.ServerWorld;
import net.minecraft.state.property.Properties;
import net.minecraft.util.math.*;

/** Real MC block light, not a fullbright-only sprite. One owned air cell and a
 * bounded chunk ticket keep expiry/leave/reset cleanup possible without loading
 * arbitrary terrain. A player edit is never replaced during cleanup. */
final class NativeBioticLight {
    static final int LEVEL=14;
    private static final ChunkTicketType<Long> TICKET=ChunkTicketType.create("owmc_biotic_light",Comparator.<Long>naturalOrder(),160);
    private static final BlockState LIGHT=Blocks.LIGHT.getDefaultState().with(Properties.LEVEL_15,LEVEL);
    private ServerWorld world;
    private BlockPos position;
    private BlockState previous;
    private long ticketId;
    long placed,removed,conflicts;
    boolean active(){return world!=null;}
    void update(ServerWorld nextWorld,Vec3d at,boolean visible,long cast){
        var nextPos=BlockPos.ofFloored(at);
        if(world!=null&&(world!=nextWorld||!position.equals(nextPos)||!visible))clear();
        if(!visible||world!=null||!nextWorld.isChunkLoaded(nextPos))return;
        var old=nextWorld.getBlockState(nextPos);
        if(!old.isAir()||!nextWorld.getFluidState(nextPos).isEmpty()||nextWorld.getBlockEntity(nextPos)!=null)return;
        var chunk=new ChunkPos(nextPos);nextWorld.getChunkManager().addTicket(TICKET,chunk,0,cast);
        if(!nextWorld.setBlockState(nextPos,LIGHT,Block.NOTIFY_ALL)){
            nextWorld.getChunkManager().removeTicket(TICKET,chunk,0,cast);return;
        }
        world=nextWorld;position=nextPos.toImmutable();previous=old;ticketId=cast;placed++;
    }
    void clear(){
        if(world==null)return;
        // The ticket was acquired while this chunk was already loaded and is
        // held until AFTER restoration. No unloaded-chunk generation is needed.
        if(world.getBlockState(position).equals(LIGHT)){
            world.setBlockState(position,previous,Block.NOTIFY_ALL);removed++;
        }else conflicts++;
        world.getChunkManager().removeTicket(TICKET,new ChunkPos(position),0,ticketId);
        world=null;position=null;previous=null;
    }
}
