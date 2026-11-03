package lab.owmcguest;

import java.util.LinkedHashMap;
import net.minecraft.block.BlockState;
import net.minecraft.entity.Entity;
import net.minecraft.particle.ParticleTypes;
import net.minecraft.server.network.ServerPlayerEntity;
import net.minecraft.server.world.ServerWorld;
import net.minecraft.sound.SoundEvents;
import net.minecraft.util.math.BlockPos;
import net.minecraft.util.math.Vec3d;
import net.minecraft.world.BlockView;
import net.minecraft.world.World;
import net.minecraft.world.explosion.Explosion;
import net.minecraft.world.explosion.ExplosionBehavior;

/** Terrain-only user rule, after a skill's original damage/cover/impulse work. */
public final class NativeTerrainBurst {
    public record Result(boolean applied,int blocksDestroyed,String rejection){}
    private NativeTerrainBurst(){}
    static boolean validStrength(double strength){return Double.isFinite(strength)&&strength>0&&strength<=4;}
    static int reach(double strength){
        if(!validStrength(strength))throw new IllegalArgumentException("terrain burst strength");
        // Vanilla empty-air rays travel at most ~1.734*power before their
        // energy is spent. Two times power plus one safely encloses all rays.
        return (int)Math.ceil(strength*2)+1;
    }
    public static Result explode(ServerWorld world,ServerPlayerEntity player,Vec3d at,double strength){
        if(world==null||player==null||at==null||!validStrength(strength)||!Double.isFinite(at.x)||!Double.isFinite(at.y)||!Double.isFinite(at.z)
            ||Math.abs(at.x)>29999984||Math.abs(at.z)>29999984||Math.abs(at.y)>30000000)return new Result(false,0,"terrain burst bounds");
        if(player.getServerWorld()!=world||!world.getServer().isOnThread())return new Result(false,0,"terrain burst player/world/thread changed");
        var center=BlockPos.ofFloored(at);int reach=reach(strength);
        // Do this before querying any states or constructing the vanilla blast.
        // An unloaded outer ray cancels all terrain work; it cannot load chunks.
        for(int x=(center.getX()-reach)>>4;x<=(center.getX()+reach)>>4;x++)
            for(int z=(center.getZ()-reach)>>4;z<=(center.getZ()+reach)>>4;z++)
                if(!world.isChunkLoaded(new BlockPos(x<<4,center.getY(),z<<4)))return new Result(false,0,"terrain burst unloaded radius");
        var before=new LinkedHashMap<BlockPos,BlockState>();
        for(var pos:BlockPos.iterate(center.add(-reach,-reach,-reach),center.add(reach,reach,reach)))
            if(!world.getBlockState(pos).isAir())before.put(pos.toImmutable(),world.getBlockState(pos));
        var behavior=new ExplosionBehavior(){
            @Override public boolean shouldDamage(Explosion explosion,Entity entity){return false;}
            @Override public float getKnockbackModifier(Entity entity){return 0;}
            @Override public boolean canDestroyBlock(Explosion explosion,BlockView view,BlockPos pos,BlockState state,float power){
                return world.isChunkLoaded(pos)&&NativeExplosionTerrain.breakable(state.getHardness(world,pos))&&super.canDestroyBlock(explosion,view,pos,state,power);
            }
            @Override public java.util.Optional<Float> getBlastResistance(Explosion explosion,BlockView view,BlockPos pos,BlockState state,net.minecraft.fluid.FluidState fluid){
                return world.isChunkLoaded(pos)?super.getBlastResistance(explosion,view,pos,state,fluid):java.util.Optional.of(Float.MAX_VALUE);
            }
        };
        // Intentionally use World's particles=false overload here, unlike
        // projectile presentation. On ServerWorld it emits no extra sound,
        // particles or ExplosionS2CPacket, but actual vanilla onExploded still
        // calls setBlockState(NOTIFY_ALL). Normal BlockUpdate/ChunkDeltaUpdate
        // packets synchronize the changed blocks; existing skill audio remains.
        world.createExplosion(player,null,behavior,at.x,at.y,at.z,(float)strength,false,World.ExplosionSourceType.TNT,false,
            ParticleTypes.SMOKE,ParticleTypes.SMOKE,SoundEvents.ENTITY_GENERIC_EXPLODE);
        int removed=0;for(var pos:before.keySet())if(world.getBlockState(pos).isAir())removed++;
        return new Result(true,removed,"");
    }
}
