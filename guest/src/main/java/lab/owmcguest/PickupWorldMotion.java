package lab.owmcguest;

import java.util.*;
import java.util.function.Predicate;
import net.minecraft.entity.LivingEntity;
import net.minecraft.server.world.ServerWorld;
import net.minecraft.util.hit.HitResult;
import net.minecraft.util.math.*;
import net.minecraft.world.RaycastContext;

/** One attraction/LOS/collision implementation for souls, scrap and armor. */
final class PickupWorldMotion {
    record Step(Vec3d at,double speed,boolean attracting){}
    private PickupWorldMotion(){}
    static Vec3d target(LivingEntity e){return e.getPos().add(0,Math.min(.9,e.getBoundingBox().getLengthY()*.5),0);}
    static boolean clear(ServerWorld w,LivingEntity owner,Vec3d from,Vec3d to){
        return w.isChunkLoaded(BlockPos.ofFloored(from))&&w.isChunkLoaded(BlockPos.ofFloored(to))
            &&w.getWorldBorder().contains(BlockPos.ofFloored(to))
            &&w.raycast(new RaycastContext(from,to,RaycastContext.ShapeType.COLLIDER,RaycastContext.FluidHandling.NONE,owner)).getType()==HitResult.Type.MISS;
    }
    static LivingEntity nearest(ServerWorld w,LivingEntity driver,Vec3d from,UUID locked,Predicate<LivingEntity> eligible){
        if(locked!=null&&w.getEntity(locked) instanceof LivingEntity e&&eligible.test(e)
            &&target(e).squaredDistanceTo(from)<=PickupKinematics.RADIUS*PickupKinematics.RADIUS&&clear(w,driver,from,target(e)))return e;
        return w.getEntitiesByClass(LivingEntity.class,new Box(from,from).expand(PickupKinematics.RADIUS),eligible).stream()
            .filter(e->target(e).squaredDistanceTo(from)<=PickupKinematics.RADIUS*PickupKinematics.RADIUS&&clear(w,driver,from,target(e)))
            .min(Comparator.comparingDouble((LivingEntity e)->target(e).squaredDistanceTo(from)).thenComparing(LivingEntity::getUuid)).orElse(null);
    }
    static Step toward(ServerWorld w,LivingEntity driver,Vec3d from,LivingEntity recipient,double speed){
        if(recipient==null)return new Step(from,0,false);var to=target(recipient);
        var step=PickupKinematics.toward(new NativeShotProtocol.Vec(from.x,from.y,from.z),new NativeShotProtocol.Vec(to.x,to.y,to.z),speed,clear(w,driver,from,to));
        var at=new Vec3d(step.at().x(),step.at().y(),step.at().z());
        var box=new Box(at.x-.06,at.y,at.z-.06,at.x+.06,at.y+.12,at.z+.06);
        if(!clear(w,driver,from,at)||!w.isSpaceEmpty(null,box))return new Step(from,0,false);
        return new Step(at,step.speed(),step.attracting());
    }
    static boolean touching(Vec3d at,LivingEntity e){return target(e).squaredDistanceTo(at)<=PickupKinematics.CONTACT*PickupKinematics.CONTACT;}
}
