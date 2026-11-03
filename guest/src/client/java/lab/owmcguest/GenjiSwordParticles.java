package lab.owmcguest;

import net.minecraft.client.MinecraftClient;
import net.minecraft.particle.ParticleTypes;
import net.minecraft.util.hit.HitResult;
import net.minecraft.util.math.Vec3d;
import net.minecraft.world.RaycastContext;

/** Local MC cosmetics on an actual native sword-animation Begin, no server trip. */
final class GenjiSwordParticles {
    static void present(MinecraftClient client,HostPoseReader.Pose host,int node,long nativeTick,long observedMs){
        if(node!=47&&node!=48)return;
        var eye=client.player.getEyePos();var q=host.rotation();
        var f=new org.joml.Vector3f(0,0,-1).rotate(q);var r=new org.joml.Vector3f(1,0,0).rotate(q);
        var forward=new Vec3d(f.x,f.y,f.z);var right=new Vec3d(r.x,r.y,r.z);int count=0;
        for(var point:GenjiCombatParticles.swordGeometry(eye,forward,right,node)){
            var at=point.at();
            var wall=client.world.raycast(new RaycastContext(eye,at,RaycastContext.ShapeType.COLLIDER,RaycastContext.FluidHandling.NONE,client.player));
            if(wall.getType()!=HitResult.Type.MISS)continue;
            if(point.spark())client.world.addParticle(ParticleTypes.ELECTRIC_SPARK,at.x,at.y,at.z,0,.005,0);
            else client.world.addParticle(ParticleTypes.SWEEP_ATTACK,at.x,at.y,at.z,0,0,0);
            count++;
        }
        GenjiCombatParticles.swordPresented(count,node,nativeTick,System.currentTimeMillis()-observedMs);
    }
    private GenjiSwordParticles(){}
}
