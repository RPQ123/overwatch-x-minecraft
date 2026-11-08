package lab.owmcguest;

import net.minecraft.client.MinecraftClient;
import net.minecraft.util.math.Vec3d;
import net.minecraft.world.RaycastContext;
import lab.owmcguest.NativeShotProtocol.*;

/** Bind only validated native launches to their original first-person aperture.
 * Existing renderers share the same cosmetic transform, including old Pharah
 * and Helix offsets. All collision/damage inputs remain the real Shot values. */
final class NativeMuzzleOrigins {
    private record Seed(MuzzlePresentation.Scope scope,long hero,long resource,long alternate,long wall,Vec start,Vec camera,MuzzlePresentation.Basis basis,double fov,double aspect){}
    private static final java.util.Map<String,Seed> seeds=new java.util.concurrent.ConcurrentHashMap<>();private static MuzzlePresentation.Scope seedScope;
    private static final java.util.Set<String> bound=java.util.concurrent.ConcurrentHashMap.newKeySet();
    private static long nextCalibration,calibrationStamp=-1;private static java.nio.file.Path calibrationPath;
    private static void calibration(){
        long now=System.currentTimeMillis();if(now<nextCalibration)return;nextCalibration=now+2000;
        var path=PrivateAssetPaths.meshes().resolve("muzzle-calibration.json");
        try{if(!java.nio.file.Files.isRegularFile(path))return;long stamp=java.nio.file.Files.getLastModifiedTime(path).toMillis();
            if(path.equals(calibrationPath)&&stamp==calibrationStamp)return;
            if(java.nio.file.Files.size(path)>32768)throw new IllegalArgumentException("calibration file size");
            MuzzleCalibration.install(java.nio.file.Files.readString(path));calibrationPath=path;calibrationStamp=stamp;
        }catch(Exception e){MuzzleCalibration.failed(e.toString());}
    }
    private static Vec vec(Vec3d p){return new Vec(p.x,p.y,p.z);}
    static Vec3d point(Vec p){return new Vec3d(p.x(),p.y(),p.z());}
    static MuzzlePresentation.Scope scope(MinecraftClient c,HostPoseReader.Pose h){
        return new MuzzlePresentation.Scope(c.player.getUuid(),NativeWorldIdentity.of(c.getServer(),c.world.getRegistryKey()),NativeLocomotionController.INSTANCE.modelId(),h.generation());
    }
    static void shot(MinecraftClient c,HostPoseReader.Pose h,long hero,Shot shot){
        long resource=shot.effect()==null?0:shot.effect().resource();
        if(shot.effect()!=null&&(shot.effect().kind()==2||shot.effect().kind()==3))resource=-1;
        if(c.player==null)return;
        remember(c,h,shot.identity(),hero,resource,shot.id(),shot.wallMs(),shot.start(),vec(c.player.getEyePos()));
    }
    static void thrown(MinecraftClient c,HostPoseReader.Pose h,String id,long hero,Vec3d actualStart,boolean hand){
        remember(c,h,id,hero,hand?-1:0,0,System.currentTimeMillis(),vec(actualStart),vec(c.player.getEyePos()));
    }
    private static void remember(MinecraftClient c,HostPoseReader.Pose h,String id,long hero,long resource,long alternate,long wall,Vec start,Vec camera){
        calibration();
        if(h==null||h.flags()!=1||!h.inputActive()||c.player==null||c.world==null||c.getServer()==null||!c.player.isAlive())return;
        var rotation=h.rotation();var f=new org.joml.Vector3f(0,0,-1).rotate(rotation);var r=new org.joml.Vector3f(1,0,0).rotate(rotation);var u=new org.joml.Vector3f(0,1,0).rotate(rotation);
        var b=new MuzzlePresentation.Basis(new Vec(f.x,f.y,f.z),new Vec(r.x,r.y,r.z),new Vec(u.x,u.y,u.z));var p=MuzzlePresentation.profile(hero,resource,alternate);if(p==null)return;
        double aspect=(double)c.getWindow().getFramebufferWidth()/c.getWindow().getFramebufferHeight();var scope=scope(c,h);
        if(!scope.equals(seedScope)){seeds.clear();bound.clear();seedScope=scope;}
        if(seeds.size()>2048)seeds.clear();if(bound.size()>16384)bound.clear();
        if(!bound.contains(id))seeds.putIfAbsent(id,new Seed(scope,hero,resource,alternate,wall,start,camera,b,h.fov(),aspect));
        var delta=camera.add(MuzzlePresentation.offset(p,b,h.fov(),aspect)).subtract(start);
        var hit=c.world.raycast(new RaycastContext(point(start),point(start.add(delta)),RaycastContext.ShapeType.COLLIDER,RaycastContext.FluidHandling.NONE,c.player));
        if(hit.getType()!=net.minecraft.util.hit.HitResult.Type.MISS){double length=Math.sqrt(delta.lengthSquared());delta=delta.multiply(length>1e-7?Math.max(0,point(start).distanceTo(hit.getPos())/length-.02):0);}
        MuzzlePresentation.remember(scope,id,hero,wall,start,delta,p);
    }
    static Vec3d at(String id,Vec3d actual){
        return at(id,actual,false);
    }
    static Vec3d firstVisibleTank(String id,Vec3d actual){
        return at(id,actual,true);
    }
    private static Vec3d at(String id,Vec3d actual,boolean tank){
        var key=MuzzlePresentation.launchKey(id);var seed=seeds.remove(key);var c=MinecraftClient.getInstance();var h=HostPoseReader.INSTANCE.latest();
        if(seed!=null&&h!=null&&c.player!=null&&c.world!=null&&c.getServer()!=null&&seed.scope().equals(scope(c,h))){
            bound.add(key);
            long now=System.currentTimeMillis();var p=MuzzleCalibration.at(seed.hero(),seed.resource(),seed.alternate(),now-seed.wall());
            // Use the render camera, not the physical factory origin (tank
            // starts below the eye). Freeze this aperture on its first draw.
            var camera=vec(c.gameRenderer.getCamera().getPos());var rotation=c.gameRenderer.getCamera().getRotation();
            var f=new org.joml.Vector3f(0,0,-1).rotate(rotation);var r=new org.joml.Vector3f(1,0,0).rotate(rotation);var u=new org.joml.Vector3f(0,1,0).rotate(rotation);
            var basis=new MuzzlePresentation.Basis(new Vec(f.x,f.y,f.z),new Vec(r.x,r.y,r.z),new Vec(u.x,u.y,u.z));
            var muzzle=camera.add(MuzzlePresentation.offset(p,basis,seed.fov(),seed.aspect()));var delta=muzzle.subtract(seed.start());
            var hit=c.world.raycast(new RaycastContext(point(seed.start()),point(seed.start().add(delta)),RaycastContext.ShapeType.COLLIDER,RaycastContext.FluidHandling.NONE,c.player));
            if(hit.getType()!=net.minecraft.util.hit.HitResult.Type.MISS){double length=Math.sqrt(delta.lengthSquared());delta=delta.multiply(length>1e-7?Math.max(0,point(seed.start()).distanceTo(hit.getPos())/length-.02):0);}
            muzzle=seed.start().add(delta);
            var direction=vec(actual).subtract(seed.start());if(direction.lengthSquared()<1e-12)direction=seed.basis().forward();
            if(tank)MuzzlePresentation.reanchorVisible(id,vec(actual),muzzle,direction,now);
            else MuzzlePresentation.reanchor(id,delta,now);
            var relative=muzzle.subtract(camera);var b=basis;
            double z=relative.x()*b.forward().x()+relative.y()*b.forward().y()+relative.z()*b.forward().z(),x=relative.x()*b.right().x()+relative.y()*b.right().y()+relative.z()*b.right().z(),y=relative.x()*b.up().x()+relative.y()*b.up().y()+relative.z()*b.up().z();
            double half=Math.tan(Math.toRadians(seed.fov())/2),w=c.getWindow().getFramebufferWidth(),height=c.getWindow().getFramebufferHeight();
            if(z>1e-6)MuzzlePresentation.noteAnchor(id,seed.hero(),seed.resource(),seed.wall(),now,(x/z/half/seed.aspect()+1)*w/2,(1-y/z/half)*height/2,w,height);
        }
        return point(MuzzlePresentation.position(id,vec(actual)));
    }
}
