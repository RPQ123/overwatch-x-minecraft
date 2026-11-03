package lab.owmcguest;

import net.minecraft.client.MinecraftClient;
import net.minecraft.entity.MovementType;
import net.minecraft.util.math.Vec3d;

/** Widowmaker Grappling Hook. Original Shift owns admission, animation, cooldown and HUD;
 * a fresh original fire animation (node61 Begin) triggers one MC hook test and pull.
 * No server exists for the original hook physics, so MC supplies them (WidowGrapplePull). */
public final class NativeGrappleController implements AutoCloseable {
    public static final NativeGrappleController INSTANCE=new NativeGrappleController();
    static final long HERO=0x02e000000000000aL;
    private final NativeSkillReader reader=new NativeSkillReader("grapple");
    private final NativeSkillReader venomReader=new NativeSkillReader("venom");private long lastThrow=-1;
    private WidowGrapplePull.Pull pull;private Vec3d last;
    private long scopeSource,scopeModel,scopeWorld,lastFire=-1,frame,frameWall;
    private int stalled;private long casts,hooks,misses,arrivals,timeouts,blocked;
    static volatile String error="";
    public static volatile String status="{\"pulling\":false}";

    void tick(MinecraftClient c){
        var h=HostPoseReader.INSTANCE.latest();long hero=NativeLocomotionController.INSTANCE.hero(),model=NativeLocomotionController.INSTANCE.modelId();
        if(h==null||h.flags()!=1||c.player==null||!c.player.isAlive()||c.world==null||c.getServer()==null||hero!=HERO){resetSession();return;}
        long now=System.currentTimeMillis();if(h.frame()!=frame){frame=h.frame();frameWall=now;}if(now-frameWall>150){pull=null;last=null;return;}  // 来源过期即停拉
        long world=NativeWorldIdentity.of(c.getServer(),c.world.getRegistryKey());
        if(scopeSource!=h.generation()||scopeModel!=model||scopeWorld!=world){resetSession();scopeSource=h.generation();scopeModel=model;scopeWorld=world;}
        var state=reader.poll(h,model,hero);if(state==null){error=reader.error;lastFire=-1;return;}error="";  // 读取失败后重建基线
        pollVenom(c,h,model,hero,world);
        var fire=state.entries().get("fire");
        // First sample is a baseline: attaching to an already running cast never starts a pull.
        if(lastFire<0){lastFire=fire.tick();publish();return;}
        if(fire.tick()>lastFire&&fire.active()&&state.active("window")){
            lastFire=fire.tick();casts++;
            if(pull==null){var p=WidowGrapplePull.aim(c.player,now);if(p!=null){pull=p;last=null;stalled=0;hooks++;}else misses++;}
        }else if(fire.tick()>lastFire)lastFire=fire.tick();
        publish();
    }
    /** Venom Mine: a fresh original WeaponVolley1 tick inside the cast admits one MC throw. */
    private void pollVenom(MinecraftClient c,HostPoseReader.Pose h,long model,long hero,long world){
        var v=venomReader.poll(h,model,hero);if(v==null){lastThrow=-1;return;}var t=v.entries().get("throw");
        if(lastThrow<0){lastThrow=t.tick();return;}
        if(t.tick()>lastThrow){lastThrow=t.tick();
            if(v.active("cast")){var server=c.getServer();var scope=new NativeVenomRuntime.Scope(c.player.getUuid(),world,h.generation(),model);server.execute(()->NativeVenomRuntime.cast(server,scope));}}
    }
    /** Called from the travel hook; true when the pull owns this tick's movement. */
    public boolean travel(MinecraftClient c){
        var p=c.player;if(pull==null||p==null)return false;
        if(!p.isAlive()||p.hasVehicle()||NativeLocomotionController.INSTANCE.hero()!=HERO){end(null);return false;}
        long now=System.currentTimeMillis();var step=WidowGrapplePull.step(p,pull,now);
        if(step==null){if(now-pull.started()>WidowGrapplePull.MAX_MS)timeouts++;else arrivals++;end(p);return false;}
        var before=p.getPos();p.setVelocity(Vec3d.ZERO);p.move(MovementType.SELF,step);var moved=p.getPos().subtract(before);
        stalled=moved.lengthSquared()<.0025?stalled+1:0;
        if(stalled>=3){blocked++;end(p);return true;}
        last=moved;p.setVelocity(moved);p.fallDistance=0;rope(c,p);publish();return true;
    }
    /** 绳索呈现：原版绳索画在隐藏的 OW 地图里，这里在 MC 里从右手位置到锚点画一串细小深色粒子。 */
    private static final net.minecraft.particle.DustParticleEffect ROPE=new net.minecraft.particle.DustParticleEffect(new org.joml.Vector3f(.12f,.12f,.14f),.45f);
    private void rope(MinecraftClient c,net.minecraft.client.network.ClientPlayerEntity p){
        if(pull==null||c.world==null)return;var right=p.getRotationVec(1).crossProduct(new Vec3d(0,1,0));if(right.lengthSquared()<1e-4)right=new Vec3d(1,0,0);
        var from=p.getEyePos().add(right.normalize().multiply(.35)).add(0,-.3,0);var to=pull.anchor();double len=from.distanceTo(to);int n=(int)Math.min(80,len*4);
        for(int i=0;i<=n;i++){var at=from.lerp(to,i/(double)Math.max(1,n));c.world.addParticle(ROPE,at.x,at.y,at.z,0,0,0);}
    }
    private void end(net.minecraft.client.network.ClientPlayerEntity p){
        if(p!=null&&pull!=null){p.setVelocity(WidowGrapplePull.release(p,pull,last));p.fallDistance=0;}
        pull=null;last=null;stalled=0;publish();
    }
    private void publish(){
        var o=new com.google.gson.JsonObject();o.addProperty("pulling",pull!=null);o.addProperty("casts",casts);o.addProperty("hooks",hooks);
        o.addProperty("misses",misses);o.addProperty("arrivals",arrivals);o.addProperty("timeouts",timeouts);o.addProperty("blocked",blocked);
        o.addProperty("range",WidowGrapplePull.RANGE);if(pull!=null){o.addProperty("ledge",pull.ledge());o.addProperty("x",pull.anchor().x);o.addProperty("y",pull.anchor().y);o.addProperty("z",pull.anchor().z);}
        
        // integrator/models: only real state/geometry, never input-derived effects.
var c=MinecraftClient.getInstance();
        if(pull!=null&&c.player!=null&&scopeSource!=0&&scopeModel!=0&&scopeWorld!=0){
            var f=OriginalEffectFrames.frame(c.player.getUuid(),scopeWorld,scopeSource,scopeModel,frameWall);
            var e=OriginalEffectFrames.body(f,"widow-hook",pull.anchor(),new Vec3d(1,1,1),1,false);
            e.add("direction",OriginalEffectFrames.vec(pull.anchor().subtract(c.player.getEyePos())));e.addProperty("axis","z");
            OriginalEffectFrames.body(f,"widow-grapple-flash",pull.anchor(),new Vec3d(.35,.35,.35),.7f,true);
            o.add("models",f);
        }
        status=o.toString();
    }
    void resetSession(){reader.close();venomReader.close();lastThrow=-1;pull=null;last=null;stalled=0;lastFire=-1;frame=frameWall=0;scopeSource=scopeModel=scopeWorld=0;error="";publish();}
    @Override public void close(){resetSession();}
}
