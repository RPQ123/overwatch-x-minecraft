package lab.owmcguest;

import net.minecraft.entity.LivingEntity;
import net.minecraft.particle.*;
import net.minecraft.block.Blocks;
import net.minecraft.server.world.ServerWorld;
import net.minecraft.util.math.Vec3d;

/** User-requested MC blood-like burst; only an actually lethal Deadeye receipt. */
public final class DeadeyeKillEffects {
    public static volatile long bursts;
    public static void lethal(ServerWorld world,LivingEntity victim,Vec3d eye){
        var box=victim.getBoundingBox();var at=new Vec3d(victim.getX(),box.minY+(box.maxY-box.minY)*.62,victim.getZ());
        if(!world.isChunkLoaded(victim.getBlockPos()))return;
        var away=at.subtract(eye).normalize();
        // Vanilla/Fabric particle engine: short red fragments have gravity and
        // depth testing. No decal entities, persistent pools or extra render mod.
        var fragments=new BlockStateParticleEffect(ParticleTypes.BLOCK,Blocks.REDSTONE_BLOCK.getDefaultState());
        world.spawnParticles(fragments,at.x,at.y,at.z,22,.19,.25,.19,.14);
        world.spawnParticles(CombatParticles.DEADEYE_BLOOD,at.x,at.y,at.z,20,.18,.22,.18,.13);
        for(int i=0;i<7;i++){
            double spread=(i-3)*.045;
            world.spawnParticles(CombatParticles.DEADEYE_BLOOD,at.x,at.y,at.z,0,away.x*.38+spread,.08+Math.abs(spread),away.z*.38-spread,1);
        }
        world.spawnParticles(ParticleTypes.CRIT,at.x,at.y,at.z,5,.12,.16,.12,.12);bursts++;
    }
}
