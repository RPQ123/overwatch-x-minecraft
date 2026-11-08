package lab.owmcguest;

import com.google.gson.JsonObject;
import java.util.*;
import net.fabricmc.fabric.api.event.lifecycle.v1.ServerTickEvents;
import net.minecraft.entity.Entity;
import net.minecraft.entity.LivingEntity;
import net.minecraft.entity.MovementType;
import net.minecraft.entity.attribute.EntityAttributeModifier;
import net.minecraft.entity.attribute.EntityAttributes;
import net.minecraft.entity.projectile.ProjectileEntity;
import net.minecraft.entity.projectile.PersistentProjectileEntity;
import net.minecraft.entity.projectile.TridentEntity;
import net.minecraft.particle.ParticleTypes;
import net.minecraft.server.MinecraftServer;
import net.minecraft.server.network.ServerPlayerEntity;
import net.minecraft.server.world.ServerWorld;
import net.minecraft.util.Identifier;
import net.minecraft.util.hit.HitResult;
import net.minecraft.util.math.*;
import net.minecraft.world.RaycastContext;
import lab.owmcguest.NativeShotProtocol.*;

/** Native Begin authorizes MC effects; actual MC motion/contact owns landing,
 * collision, damage and saves. All mutation remains on the integrated server.
 * No native input/cooldown/meter writer or additional callback owner is installed.
 */
public final class WinstonServer implements HeroServerModule {
    public static final WinstonServer INSTANCE=new WinstonServer();
    public record Scope(UUID owner,long world,long source,long model){
        public boolean matches(UUID p,long w,long h,long m,long s){return h==WinstonRules.HERO&&owner.equals(p)&&world==w&&source==s&&model==m&&m!=0&&s!=0;}
    }
    public record Sample(long jump,long barrier,long rage,long left,long right,long jumpIntent){}
    public record View(Scope scope,long wall,Vec3d projector,boolean deployed,boolean rage,double shieldHp){}
    private static final Identifier BONUS=Identifier.of("owmcguest","winston_primal_health");
    private Scope scope;private long lease;private final long[] seen=new long[5];
    private ServerPlayerEntity buffed;private boolean raging,jumping;
    private final WinstonJumpContact jumpContact=new WinstonJumpContact();
    private int rageAge,shieldAge,throwAge;private Vec3d projector,throwVelocity;
    private ServerWorld shieldWorld;private boolean deployed;private double shieldHp;
    private long jumpCasts,landings,barrierCasts,barrierDeployments,barrierBreaks,projectilesBlocked,nativeShotsBlocked,rageCasts,fistCasts,hits,rejected;
    private double damageApplied,shieldAbsorbed;
    private volatile String json="{}";public volatile View view;
    public volatile WinstonAudioGate.Sample audio;
    private WinstonServer(){ServerTickEvents.START_WORLD_TICK.register(this::blockProjectiles);}
    @Override public String statusKey(){return "winston";}
    @Override public String status(){return json;}
    private static boolean fresh(long wall){long age=System.currentTimeMillis()-wall;return wall>0&&age>=-50&&age<=200;}
    private static Vec vector(Vec3d v){return new Vec(v.x,v.y,v.z);}
    private static Vec3d point(Vec v){return new Vec3d(v.x(),v.y(),v.z());}
    private static ServerPlayerEntity player(MinecraftServer server,Scope s){
        var p=s==null?null:server.getPlayerManager().getPlayer(s.owner());
        return p!=null&&p.isAlive()&&!p.hasVehicle()&&s.source()!=0&&s.model()!=0
            &&NativeWorldIdentity.of(server,p.getWorld().getRegistryKey())==s.world()?p:null;
    }
    public void refresh(MinecraftServer server,Scope next,long wall,Sample sample){
        var p=player(server,next);
        if(!server.isOnThread()||!fresh(wall)||p==null
            ||!NativeEliminationRuntime.sessionMatches(next.owner(),next.world(),WinstonRules.HERO,next.model(),next.source())){rejected++;WinstonDiagnostics.increment("serverScopeRejected");return;}
        if(!next.equals(scope)){retire();Arrays.fill(seen,0);scope=next;}
        lease=wall;
        if(sample.rage()>0&&sample.rage()!=seen[2]){seen[2]=sample.rage();beginRage(p);rageCasts++;}
        if(sample.rage()==0&&raging)endRage();
        if(sample.jump()>0&&sample.jump()!=seen[0]){
            seen[0]=sample.jump();jumpCasts++;
            if(jumpContact.intent()!=sample.jumpIntent())jumpContact.begin(sample.jumpIntent());
            jumpContact.confirm(sample.jumpIntent(),sample.jump());jumping=jumpContact.active();finishLanding(p);
        }
        if(sample.barrier()>0&&sample.barrier()!=seen[1]){
            seen[1]=sample.barrier();shieldWorld=p.getServerWorld();projector=p.getPos().add(0,.8,0);
            var aim=p.getRotationVec(1);throwVelocity=aim.multiply(.35).add(0,.12,0);throwAge=shieldAge=0;deployed=false;shieldHp=WinstonRules.BARRIER_HP;barrierCasts++;
        }
        if(raging){
            if(sample.left()>0&&sample.left()!=seen[3]){seen[3]=sample.left();fistCasts++;area(p,true);}
            if(sample.right()>0&&sample.right()!=seen[4]){seen[4]=sample.right();fistCasts++;area(p,true);}
        }else{seen[3]=Math.max(seen[3],sample.left());seen[4]=Math.max(seen[4],sample.right());}
        publish();
    }
    /** Movement-only anticipation: no damage, audio or cooldown is granted. */
    public void observeJump(MinecraftServer server,Scope next,long intent,long wall){
        var p=player(server,next);
        if(!server.isOnThread()||!fresh(wall)||p==null||!NativeEliminationRuntime.sessionMatches(next.owner(),next.world(),WinstonRules.HERO,next.model(),next.source()))return;
        if(!next.equals(scope)){retire();Arrays.fill(seen,0);scope=next;}
        lease=wall;jumpContact.begin(intent);jumping=jumpContact.active();
    }
    private void beginRage(ServerPlayerEntity p){
        endRage();var attribute=p.getAttributeInstance(EntityAttributes.GENERIC_MAX_HEALTH);if(attribute==null)return;
        attribute.removeModifier(BONUS);
        double bonus=WinstonRules.RAGE_BONUS*NativeShotSimulation.HP_SCALE;
        attribute.addTemporaryModifier(new EntityAttributeModifier(BONUS,bonus,EntityAttributeModifier.Operation.ADD_VALUE));
        buffed=p;raging=true;rageAge=0;p.setHealth(p.getMaxHealth());
    }
    private void endRage(){
        if(buffed!=null){var a=buffed.getAttributeInstance(EntityAttributes.GENERIC_MAX_HEALTH);if(a!=null)a.removeModifier(BONUS);
            if(buffed.isAlive())buffed.setHealth(Math.min(buffed.getHealth(),buffed.getMaxHealth()));}
        buffed=null;raging=false;rageAge=0;
    }
    public boolean primal(UUID owner,long world,long source,long model){return raging&&fresh(lease)&&scope!=null&&scope.owner().equals(owner)&&scope.world()==world&&scope.source()==source&&scope.model()==model;}
    private static boolean visible(ServerPlayerEntity p,Vec3d from,Vec3d to){
        var w=p.getServerWorld();if(!w.isChunkLoaded(BlockPos.ofFloored(to)))return false;
        var wall=w.raycast(new RaycastContext(from,to,RaycastContext.ShapeType.COLLIDER,RaycastContext.FluidHandling.NONE,p));
        return wall.getType()==HitResult.Type.MISS||from.squaredDistanceTo(wall.getPos())+.001>=from.squaredDistanceTo(to);
    }
    private void area(ServerPlayerEntity p,boolean fist){
        area(p,fist,p.getPos());
    }
    private void area(ServerPlayerEntity p,boolean fist,Vec3d center){
        var w=p.getServerWorld();var origin=fist?p.getEyePos():center.add(0,.2,0);var direction=p.getRotationVec(1).normalize();
        double radius=fist?WinstonRules.FIST_RADIUS:WinstonRules.LANDING_RADIUS;var hit=new HashSet<UUID>();
        for(var e:NativeDamageTargets.in(w,p,p.getBoundingBox().offset(center.subtract(p.getPos())).expand(radius))){
            var target=NativeDamageTargets.owner(e);if(hit.contains(target.getUuid())||p.isTeammate(target))continue;
            var box=e.getBoundingBox();var at=new Vec3d(Math.clamp(origin.x,box.minX,box.maxX),Math.clamp(origin.y,box.minY,box.maxY),Math.clamp(origin.z,box.minZ,box.maxZ));
            var delta=at.subtract(origin);double distance=delta.length();
            if(distance>radius||fist&&distance>1e-6&&direction.dotProduct(delta.normalize())<.5||!visible(p,origin,at))continue;
            hit.add(target.getUuid());
            double amount=fist?WinstonRules.FIST_DAMAGE:WinstonRules.landingDamage(distance);
            var before=target.getPos();var result=NativeDamageTargets.meleeDamage(w,e,p,amount*NativeShotSimulation.HP_SCALE);
            if(result.applied()){
                hits++;damageApplied+=result.healthLost();if(!raging)NativeUltimateRuntime.credit(result.healthLost());
                if(target.isAlive()&&!target.isRemoved()&&target.getWorld()==w&&target.getPos().squaredDistanceTo(before)<1e-8){
                    var push=WinstonRules.knockback(vector(target.getVelocity()),fist?vector(direction):vector(target.getPos().subtract(center)),fist);
                    target.setVelocity(point(push));target.velocityModified=true;
                }
            }
        }
    }
    private void tickProjector(ServerPlayerEntity p){
        if(projector==null)return;
        if(shieldWorld!=p.getServerWorld()||shieldHp<=0||deployed&&++shieldAge>=120){clearShield();return;}
        if(deployed)return;
        Vec3d end=projector.add(throwVelocity);var w=p.getServerWorld();
        if(!w.isChunkLoaded(BlockPos.ofFloored(end))||!w.getWorldBorder().contains(BlockPos.ofFloored(end))){clearShield();return;}
        var wall=w.raycast(new RaycastContext(projector,end,RaycastContext.ShapeType.COLLIDER,RaycastContext.FluidHandling.NONE,p));
        if(wall.getType()!=HitResult.Type.MISS){
            projector=wall.getPos().add(Vec3d.of(wall.getSide().getVector()).multiply(.025));deploy(p);return;
        }
        projector=end;throwVelocity=throwVelocity.add(0,-.06,0);
        if(++throwAge>=10)deploy(p);
    }
    private void deploy(ServerPlayerEntity p){
        var w=p.getServerWorld();var down=w.raycast(new RaycastContext(projector,projector.add(0,-2,0),RaycastContext.ShapeType.COLLIDER,RaycastContext.FluidHandling.NONE,p));
        if(down.getType()!=HitResult.Type.MISS)projector=down.getPos().add(0,.025,0);
        deployed=true;barrierDeployments++;shieldAge=0;throwVelocity=null;
    }
    private boolean shieldReady(ServerWorld w,UUID shooter){return fresh(lease)&&scope!=null&&projector!=null&&deployed&&shieldHp>0&&shieldWorld==w&&!scope.owner().equals(shooter);}
    private double contact(ServerWorld w,UUID shooter,Vec from,Vec to){return shieldReady(w,shooter)?WinstonBarrierGeometry.intersection(from,to,vector(projector)):Double.NaN;}
    private void absorb(double nativeDamage){
        double amount=Double.isFinite(nativeDamage)?Math.clamp(nativeDamage,0,2000):0;double lost=Math.min(shieldHp,amount);shieldHp-=lost;shieldAbsorbed+=lost;
        if(shieldHp<=0){barrierBreaks++;clearShield();}publish();
    }
    /** Called before entity ticks, so fast arrows cannot deal damage first. */
    private void blockProjectiles(ServerWorld w){
        if(projector==null||!shieldReady(w,null))return;
        for(var e:w.getOtherEntities(null,new Box(projector,projector).expand(48),x->x instanceof ProjectileEntity)){
            if(!deployed||projector==null)break;var projectile=(ProjectileEntity)e;var owner=projectile.getOwner();
            var from=e.getPos();var velocity=e.getVelocity();var to=from.add(velocity);
            double t=contact(w,owner==null?null:owner.getUuid(),vector(from),vector(to));if(!Double.isFinite(t))continue;
            var at=from.lerp(to,t);var wall=w.raycast(new RaycastContext(from,at,RaycastContext.ShapeType.COLLIDER,RaycastContext.FluidHandling.NONE,e));
            if(wall.getType()!=HitResult.Type.MISS&&from.squaredDistanceTo(wall.getPos())+.001<from.squaredDistanceTo(at))continue;
            double mcDamage=projectile instanceof TridentEntity?8:projectile instanceof PersistentProjectileEntity arrow?Math.ceil(arrow.getDamage()*velocity.length()):6;
            e.setVelocity(Vec3d.ZERO);e.discard();projectilesBlocked++;absorb(mcDamage/NativeShotSimulation.HP_SCALE);
        }
    }
    /** Nearest resolved world contact wins. A shield impact never explodes terrain. */
    public NativeShotSimulation.Hit blockNative(ServerWorld w,UUID shooter,Shot shot,Vec from,Vec to,NativeShotSimulation.Hit nearest){
        double t=contact(w,shooter,from,to);if(!Double.isFinite(t))return nearest;
        var at=from.add(to.subtract(from).multiply(t));
        if(nearest!=null&&nearest.point().subtract(from).lengthSquared()<=at.subtract(from).lengthSquared()+1e-8)return nearest;
        nativeShotsBlocked++;absorb(shot.nativeDamage());return new NativeShotSimulation.Hit(true,0,at,false);
    }
    private void clearShield(){projector=throwVelocity=null;shieldWorld=null;deployed=false;shieldHp=0;shieldAge=throwAge=0;}
    private void retire(){endRage();clearShield();jumping=false;jumpContact.reset();view=null;lease=0;}
    public void suspend(MinecraftServer server,Scope expected){if(expected.equals(scope)){retire();publish();}}
    @Override public void tick(MinecraftServer server){
        var p=player(server,scope);if(p==null||!fresh(lease)){retire();publish();return;}
        if(raging&&++rageAge>=200)endRage();
        if(jumpContact.active()){
            p.fallDistance=0;
            jumpContact.sample(p.isOnGround(),vector(p.getPos()),System.currentTimeMillis());jumping=jumpContact.active();
        }
        finishLanding(p);
        tickProjector(p);publish();
    }
    private void finishLanding(ServerPlayerEntity p){
        var contact=jumpContact.take(System.currentTimeMillis());if(contact==null)return;
        var at=point(contact);if(!p.getServerWorld().isChunkLoaded(BlockPos.ofFloored(at)))return;
        landings++;area(p,false,at);
        p.getServerWorld().spawnParticles(ParticleTypes.EXPLOSION,at.x,at.y+.15,at.z,1,0,0,0,0);
        p.getServerWorld().spawnParticles(ParticleTypes.CLOUD,at.x,at.y+.1,at.z,24,1.2,.12,1.2,.08);
    }
    private void publish(){
        long now=System.currentTimeMillis();view=scope==null||!fresh(lease)?null:new View(scope,now,projector,deployed,raging,shieldHp);
        audio=view==null?null:new WinstonAudioGate.Sample(new WinstonAudioGate.Scope(scope.owner(),scope.world(),scope.source(),scope.model()),now,
            seen[0],seen[1],seen[2],jumpCasts,landings,barrierCasts,barrierDeployments,rageCasts);
        var o=new JsonObject();o.add("client",WinstonDiagnostics.snapshot());o.addProperty("jumpCasts",jumpCasts);o.addProperty("jumping",jumping);o.addProperty("landings",landings);
        o.addProperty("barrierCasts",barrierCasts);o.addProperty("barrierDeployments",barrierDeployments);o.addProperty("barrierActive",deployed);o.addProperty("barrierHp",shieldHp);o.addProperty("barrierBreaks",barrierBreaks);
        o.addProperty("projectilesBlocked",projectilesBlocked);o.addProperty("nativeShotsBlocked",nativeShotsBlocked);o.addProperty("shieldAbsorbed",shieldAbsorbed);
        o.addProperty("rageCasts",rageCasts);o.addProperty("rageActive",raging);o.addProperty("fistCasts",fistCasts);o.addProperty("hits",hits);o.addProperty("damageApplied",damageApplied);o.addProperty("rejected",rejected);
        o.addProperty("nativeTiming","010a cooldown8; 00fa HP1000/life6/cooldown13; 0109 rage10/extra500; original ammo/reload/animations retained");
        o.addProperty("mcAdaptation","vanilla jump impulse; landing falloff/LOS; fist cone/knockback; hemisphere sweep/projectile damage conversion; temporary unsaved shield");
        json=o.toString();
    }
    @Override public void resetSession(){retire();scope=null;Arrays.fill(seen,0);publish();}
    @Override public void revalidateSession(UUID p,long w,long h,long m,long s){if(scope==null||!scope.matches(p,w,h,m,s))resetSession();}
}
