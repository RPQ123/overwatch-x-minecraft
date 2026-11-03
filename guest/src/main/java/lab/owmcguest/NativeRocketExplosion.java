package lab.owmcguest;

import java.util.LinkedHashMap;
import net.minecraft.entity.Entity;
import net.minecraft.server.network.ServerPlayerEntity;
import net.minecraft.server.world.ServerWorld;
import net.minecraft.util.math.BlockPos;
import net.minecraft.util.math.Box;
import net.minecraft.util.math.Vec3d;
import net.minecraft.world.BlockView;
import net.minecraft.world.World;
import net.minecraft.block.BlockState;
import net.minecraft.world.explosion.Explosion;
import net.minecraft.world.explosion.ExplosionBehavior;
import lab.owmcguest.NativeShotProtocol.Shot;
import lab.owmcguest.NativeShotSimulation.Hit;

/** Measured native damage; user MC terrain strength is a separate vanilla blast. */
public final class NativeRocketExplosion {
    public static long detonations,blocksDestroyed;
    public static long tankDetonations;
    public static double directHealthLost,splashHealthLost;
    private static final double RADIUS=2.5;
    public static double falloff(double distance){
        if(!Double.isFinite(distance)||distance<0||distance>RADIUS)return 0;
        return distance<=.5?1:1-(distance-.5)/2*.875;
    }
    public static double explode(ServerWorld world,ServerPlayerEntity player,Shot shot,Hit hit){
        var point=hit.point();var at=new Vec3d(point.x(),point.y(),point.z());
        var effect=shot.effect();double radius=effect==null?RADIUS:effect.radius(),splash=effect==null?80:effect.splash();
        double strength=NativeExplosionTerrain.strength(shot);int reach=(int)Math.ceil(strength*2)+1;
        if(!hit.loaded()||!world.isChunkLoaded(BlockPos.ofFloored(at)))return 0;
        var center=BlockPos.ofFloored(at);
        // Vanilla blast rays can reach beyond the impact chunk. Never let a
        // shot synchronously generate neighboring terrain.
        for(int x=(center.getX()-reach)>>4;x<=(center.getX()+reach)>>4;x++)
            for(int z=(center.getZ()-reach)>>4;z<=(center.getZ()+reach)>>4;z++)
                if(!world.isChunkLoaded(new BlockPos(x<<4,center.getY(),z<<4)))return 0;
        // Move just outside the impacted surface for exposure queries.
        var velocity=shot.velocity();var origin=at.subtract(new Vec3d(velocity.x(),velocity.y(),velocity.z()).normalize().multiply(.02));
        double lost=0;
        if(!hit.block()){
            var direct=NativeDamageTargets.resolve(world,(int)hit.target());
            if(direct!=null){
                // Direct damage may teleport/remove a vanilla target. Resolve
                // its original reaction before collecting current splash boxes.
                double directLost=NativeDamageTargets.projectileDamage(world,direct,player,shot.nativeDamage()*NativeShotSimulation.HP_SCALE).healthLost();
                directHealthLost+=directLost;lost+=directLost;
            }
        }
        var amounts=new LinkedHashMap<Entity,Double>();
        for(var entity:NativeDamageTargets.in(world,player,new Box(at,at).expand(radius))){
            if(!world.isChunkLoaded(entity.getBlockPos()))continue;
            var box=entity.getBoundingBox();var closest=new Vec3d(
                Math.clamp(at.x,box.minX,box.maxX),Math.clamp(at.y,box.minY,box.maxY),Math.clamp(at.z,box.minZ,box.maxZ));
            double distance=closest.distanceTo(at),scale=effect==null?falloff(distance):NativeBlastFalloff.scale(distance,effect.innerRadius(),radius,effect.outerScale());if(scale==0)continue;
            double amount=splash*NativeShotSimulation.HP_SCALE*scale*Explosion.getExposure(origin,entity);
            // Multipart boxes contribute splash once per actual damage owner.
            var victim=NativeDamageTargets.owner(entity);
            var previous=amounts.keySet().stream().filter(e->NativeDamageTargets.owner(e)==victim).findFirst();
            if(previous.isPresent())amounts.merge(previous.get(),amount,Math::max);else amounts.put(entity,amount);
        }
        for(var entry:amounts.entrySet()){
            // Let each real entity/part apply its own explosion immunity and armor.
            double splashLost=NativeDamageTargets.explosionDamage(world,entry.getKey(),player,entry.getValue()).healthLost();
            splashHealthLost+=splashLost;lost+=splashLost;
        }
        // Terrain strength is an explicit MC adaptation, not an OW terrain stat.
        // Vanilla handles resistance, drops, particles and sound; entity damage
        // was applied above, so this blast cannot apply it a second time.
        var before=new LinkedHashMap<BlockPos,BlockState>();
        for(var pos:BlockPos.iterate(center.add(-reach,-reach,-reach),center.add(reach,reach,reach)))
            if(world.isChunkLoaded(pos)&&!world.getBlockState(pos).isAir())before.put(pos.toImmutable(),world.getBlockState(pos));
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
        // Every admitted shot explosion now has user-requested MC terrain work.
        // Keep the native damage/rings untouched and suppress vanilla entity
        // damage/knockback above. Barrage retains its dedicated orange burst;
        // its low-strength synced vanilla packet now also supplies the small
        // explosion flash requested for real ground hits, like Helix.
        // Crucial: this ServerWorld overload sends ExplosionS2CPacket; the old
        // inherited overload with an extra particles boolean did not.
        world.createExplosion(player,null,behavior,at.x,at.y,at.z,(float)strength,false,
            World.ExplosionSourceType.TNT,
            net.minecraft.particle.ParticleTypes.EXPLOSION,
            net.minecraft.particle.ParticleTypes.EXPLOSION_EMITTER,
            net.minecraft.sound.SoundEvents.ENTITY_GENERIC_EXPLODE);
        if(shot.helix())world.spawnParticles(net.minecraft.particle.ParticleTypes.ELECTRIC_SPARK,at.x,at.y,at.z,12,.2,.2,.2,.08);
        if(shot.tankShell())tankDetonations++;
        detonations++;for(var entry:before.entrySet())if(world.getBlockState(entry.getKey()).isAir())blocksDestroyed++;
        return lost;
    }
}
