package lab.owmcguest;

import net.fabricmc.fabric.api.client.rendering.v1.*;
import net.minecraft.client.MinecraftClient;
import net.minecraft.client.render.*;
import net.minecraft.util.math.*;
import java.util.*;

/** Original 072c LOD0/samplers; existing three-strand launch/path is MC presentation. */
final class HelixRocketRenderer {
    private record Frame(PharahRocketPresentation.Basis basis,double fov,double aspect){}
    private static final Map<Long,Frame> launches=new HashMap<>();
    private static final Set<Long> seen=new HashSet<>();
    private static Object source;private static long world,model;
    static volatile long frames,models;
    // 1883 already contains THREE missiles: 186 vertices per separated X band.
    // Audited by models_20261026_jobs.py, including no cross-band triangles.
    private static final float[][] PART_CENTERS={{-.12951134f,.026479013f,-.023515387f},
        {-.052893832f,.13169499f,.009406159f},{.12852736f,.14529651f,.023515388f}};
    private static Vec3d vec(NativeShotProtocol.Vec v){return new Vec3d(v.x(),v.y(),v.z());}
    private static Vec3d position(NativeShotProtocol.Shot shot,Frame f,double age,int index){
        var direction=vec(shot.velocity()).normalize();var orbit=HelixPresentation.strand(age,index);var offset=HelixPresentation.launch(age,f.fov(),f.aspect());
        return vec(shot.start()).add(vec(shot.velocity()).multiply(age)).add(direction.multiply(offset.forward()))
            .add(vec(f.basis().right()).multiply(offset.right()+orbit.x())).add(vec(f.basis().up()).multiply(offset.up()+orbit.y()));
    }
    static void register(){WorldRenderEvents.AFTER_ENTITIES.register(ctx->{
        var c=MinecraftClient.getInstance();var h=HostPoseReader.INSTANCE.latest();var s=NativeCombatRuntime.rocketView;
        if(!Boolean.getBoolean("owmc.frameExport")||s==null||h==null||c.player==null||!c.player.isAlive()||c.world==null||c.getServer()==null||ctx.matrixStack()==null||!h.inputActive()||h.flags()!=1
            ||NativeLocomotionController.INSTANCE.hero()!=0x02e000000000006eL||s.model()!=NativeLocomotionController.INSTANCE.modelId()
            ||s.world()!=NativeWorldIdentity.of(c.getServer(),c.world.getRegistryKey())||s.source().pid()!=h.pid()||s.source().hostGeneration()!=h.generation()||!s.player().equals(c.player.getUuid()))return;
        if(!s.source().equals(source)||s.world()!=world||s.model()!=model){source=s.source();world=s.world();model=s.model();launches.clear();seen.clear();}
        if(s.shots().isEmpty()){launches.clear();return;}
        var ms=ctx.matrixStack();var camera=ctx.camera().getPos();var buffers=c.getBufferBuilders().getEntityVertexConsumers();boolean drew=false;
        var rotation=ctx.camera().getRotation();var rr=new org.joml.Vector3f(1,0,0).rotate(rotation);long now=System.currentTimeMillis();
        var active=new HashSet<Long>();
        for(var shot:s.shots()){
            if(!shot.helix())continue;double age=(now-shot.wallMs())/1000.,speed=Math.sqrt(shot.velocity().lengthSquared());
            if(age<0||age>shot.lifetime()||age*speed>=shot.range()||speed<1)continue;
            var frame=launches.get(shot.id());
            if(frame==null){if(age>.18)continue;frame=new Frame(PharahRocketPresentation.basis(shot.velocity(),new NativeShotProtocol.Vec(rr.x,rr.y,rr.z)),h.fov(),(double)c.getWindow().getFramebufferWidth()/c.getWindow().getFramebufferHeight());launches.put(shot.id(),frame);}
            active.add(shot.id());var direction=vec(shot.velocity()).normalize();
            boolean shotDrew=false;
            var pack=OriginalMeshPack.get("soldier-helix");
            var ends=new Vec3d[]{position(shot,frame,age,0),position(shot,frame,age,1),position(shot,frame,age,2)};
            if(!java.util.Arrays.stream(ends).allMatch(at->c.world.isChunkLoaded(BlockPos.ofFloored(at))))continue;
            if(pack!=null){
                var base=ends[0].add(ends[1]).add(ends[2]).multiply(1/3.);
                var turn=new org.joml.Quaternionf().rotationTo(0,0,1,(float)direction.x,(float)direction.y,(float)direction.z);
                var delta=new org.joml.Vector3f[3];
                for(int i=0;i<3;i++){var d=ends[i].subtract(base);delta[i]=new org.joml.Vector3f((float)d.x,(float)d.y,(float)d.z);}
                ms.push();
                try{
                    ms.translate(base.x-camera.x,base.y-camera.y,base.z-camera.z);
                    pack.drawEffect(buffers,ms.peek(),(p,n)->{
                        int part=p.x<-.09f?0:p.x<.04f?1:2;var center=PART_CENTERS[part];
                        p.sub(center[0],center[1],center[2]).rotate(turn).add(delta[part]);n.rotate(turn);
                    },Float.NEGATIVE_INFINITY);
                    shotDrew=true;
                }finally{ms.pop();}
            }
            for(int strand=0;strand<3;strand++){
                var at=position(shot,frame,age,strand);if(!c.world.isChunkLoaded(BlockPos.ofFloored(at)))continue;
                // Sample the same cosmetic helix; original particle templates
                // replace the old hand-drawn ribbons, not the collision path.
                for(int i=0;i<6;i++){
                    double t=Math.max(0,age-i*.012);if(t<=0)break;
                    var trail=position(shot,frame,t,strand);
                    shotDrew|=OriginalWorldRenderer.mesh(ctx,"soldier-helix-trail",trail,null,true,.10f,.10f,.10f,(float)(1-i/6.));
                }
            }
            if(!shotDrew)continue;drew=true;
            if(seen.size()>4096)seen.clear();if(seen.add(shot.id())){models++;NativeCombatRuntime.helixModelsShown++;}
        }
        launches.keySet().retainAll(active);if(drew){frames++;NativeCombatRuntime.helixRenderFrames++;}
    });}
}
