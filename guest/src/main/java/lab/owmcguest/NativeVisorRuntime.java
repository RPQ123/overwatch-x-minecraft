package lab.owmcguest;

import lab.owmcguest.NativeShotProtocol.*;
import net.minecraft.server.network.ServerPlayerEntity;
import net.minecraft.util.math.*;
import net.minecraft.world.RaycastContext;
import net.minecraft.util.hit.HitResult;

/** Original Tactical Visor state admits aim correction for real factory bullets only. */
public final class NativeVisorRuntime {
    public static final long HERO=NativeVisorAim.HERO;
    public static volatile NativeVisorAim.Scope state;
    public static volatile long locks;
    public static void resetSession(){state=null;locks=0;}
    public static Vec aim(ServerPlayerEntity p,long world,Source source,Shot shot){
        var s=state;long now=System.currentTimeMillis();
        if(!NativeVisorAim.eligible(s,shot,world,source.hostGeneration(),now)
            ||!NativeEliminationRuntime.sessionMatches(p.getUuid(),world,HERO,s.model(),s.source()))return shot.velocity();
        var start=new Vec3d(shot.start().x(),shot.start().y(),shot.start().z());
        var forward=new Vec3d(shot.velocity().x(),shot.velocity().y(),shot.velocity().z()).normalize();
        Vec3d chosen=null;double best=-1,distance=Double.POSITIVE_INFINITY;int chosenId=Integer.MAX_VALUE;
        for(var entity:NativeDamageTargets.in(p.getServerWorld(),p,new Box(start,start).expand(s.radius()))){
            if(!p.getWorld().isChunkLoaded(entity.getBlockPos()))continue;
            var target=entity.getBoundingBox().getCenter();var delta=target.subtract(start);double length=delta.length();
            double cosine=NativeVisorAim.score(new Vec(forward.x,forward.y,forward.z),new Vec(delta.x,delta.y,delta.z),Math.min(s.radius(),shot.range()),s.angle());if(cosine<0)continue;
            var hit=p.getWorld().raycast(new RaycastContext(start,target,RaycastContext.ShapeType.COLLIDER,RaycastContext.FluidHandling.NONE,p));
            if(hit.getType()!=HitResult.Type.MISS&&start.squaredDistanceTo(hit.getPos())+1e-5<delta.lengthSquared())continue;
            if(cosine>best+1e-9||(Math.abs(cosine-best)<=1e-9&&(length<distance-1e-9||(Math.abs(length-distance)<=1e-9&&entity.getId()<chosenId)))){chosen=delta;best=cosine;distance=length;chosenId=entity.getId();}
        }
        if(chosen==null)return shot.velocity();locks++;var direction=chosen.normalize();return new Vec(direction.x,direction.y,direction.z);
    }
}
