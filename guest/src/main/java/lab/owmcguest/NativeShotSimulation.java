package lab.owmcguest;

import java.util.ArrayList;
import java.util.HashSet;
import java.util.LinkedHashMap;
import lab.owmcguest.NativeShotProtocol.*;

/** Original Genji projectiles and McCree rays; Minecraft supplies collision queries. */
public final class NativeShotSimulation {
    public static final double HP_SCALE=.1;
    public record Hit(boolean block,long target,Vec point,boolean loaded,Vec normal) {
        public Hit(boolean block,long target,Vec point){this(block,target,point,true,null);}
        public Hit(boolean block,long target,Vec point,boolean loaded){this(block,target,point,loaded,null);}
    }
    public interface WorldAccess {
        Hit trace(Vec start,Vec end);
        default Vec aim(Shot shot){return shot.velocity();}
        /** Presentation follows the same swept segment; it never supplies damage. */
        default void present(Shot shot,Vec start,Vec end,Hit hit) {}
        /** One resolved contact after retirement, independent of presentation. */
        default void impact(Shot shot,Hit hit) {}
        default java.util.List<Hit> beam(Vec start,Vec direction,double range){throw new UnsupportedOperationException("native beam collision unavailable");}
        double damage(Hit hit,double minecraftHp,long nativeEntity);
        default double beamDamage(Hit hit,double minecraftHp){return damage(hit,minecraftHp,0);}
        /** Real server explosion only after this flight has been retired. */
        default double explode(Shot shot,Hit hit){throw new UnsupportedOperationException("rocket explosion unavailable");}
        default double weaponHit(Shot shot,Hit hit){return damage(hit,shot.nativeDamage()*HP_SCALE,shot.nativeEntity());}
        default double armoryExplosion(Shot shot,Hit hit){throw new UnsupportedOperationException("armory explosion unavailable");}
        default double controlImpact(Shot shot,Hit hit){throw new UnsupportedOperationException("Flashbang impact unavailable");}
    }
    private static final class Flight {final Shot shot;Vec position,velocity;double elapsed,distance;int bounces;Flight(Shot s){shot=s;position=s.start();velocity=s.velocity();}}
    private final LinkedHashMap<Long,Flight> flights=new LinkedHashMap<>();
    private final HashSet<String> seen=new HashSet<>();
    private Source source;
    private java.util.List<Shot> admissions=java.util.List.of();
    public java.util.List<Shot> admissions(){return admissions;}
    private long cursor;
    public long admitted,rejected,duplicates,blockHits,entityHits,expired,explosions;
    public double damageApplied;
    public String lastRejection="";
    public long admit(Batch batch){
        var fresh=new ArrayList<Shot>();admissions=java.util.List.of();
        if(!batch.source().equals(source)){flights.clear();seen.clear();source=batch.source();cursor=batch.acknowledged();}
        if(batch.acknowledged()>cursor)throw new IllegalArgumentException("source acknowledged an unprocessed prefix");
        for(var entry:batch.entries()){
            if(entry.id()<=cursor){duplicates++;continue;}
            if(entry.id()!=cursor+1)throw new IllegalArgumentException("consumer gap");
            cursor=entry.id();
            if(entry.shot()==null){rejected++;lastRejection=entry.rejection();continue;}
            if(!seen.add(entry.shot().identity())){duplicates++;continue;}
            if(seen.size()>1048576||flights.size()>=512)throw new IllegalStateException("combat capacity");
            flights.put(entry.id(),new Flight(entry.shot()));fresh.add(entry.shot());admitted++;
        }
        admissions=java.util.List.copyOf(fresh);
        return cursor;
    }
    public void tick(WorldAccess world,long now){
        for(var flight:new ArrayList<>(flights.values())){
            if(flight.shot.effect()!=null&&!flight.shot.hitscan()){
                tickArmory(flight,world,now);continue;
            }
            if(flight.shot.beam()){
                flights.remove(flight.shot.id());
                var targets=world.beam(flight.shot.start(),flight.shot.velocity(),flight.shot.range());
                if(targets.isEmpty())world.present(flight.shot,flight.shot.start(),flight.shot.start().add(flight.shot.velocity().multiply(flight.shot.range())),null);
                for(var hit:targets){
                    world.present(flight.shot,flight.shot.start(),hit.point(),hit);
                    if(hit.block())blockHits++;else{entityHits++;damageApplied+=world.beamDamage(hit,flight.shot.nativeDamage()*flight.shot.lifetime()*HP_SCALE);}
                }
                continue;
            }
            double elapsed=Math.min(flight.shot.lifetime(),Math.max(0,(now-flight.shot.wallMs())/1000.0));
            if(flight.shot.rocket())elapsed=Math.min(elapsed,flight.shot.range()/Math.sqrt(flight.shot.velocity().lengthSquared()));
            if(!flight.shot.hitscan()&&elapsed<=flight.elapsed)continue;
            var direction=flight.shot.hitscan()?world.aim(flight.shot):flight.shot.velocity();
            var end=flight.shot.start().add(direction.multiply(flight.shot.hitscan()?flight.shot.range():elapsed));
            var hit=world.trace(flight.position,end);
            world.present(flight.shot,flight.position,hit==null?end:hit.point(),hit);
            if(hit!=null){
                flights.remove(flight.shot.id()); // Resolve before an external callback; never retry a hit.
                world.impact(flight.shot,hit);
                if(hit.block())blockHits++;else entityHits++;
                if(flight.shot.rocket()){
                    if(hit.loaded()){explosions++;damageApplied+=world.explode(flight.shot,hit);}
                }else if(flight.shot.effect()!=null&&flight.shot.effect().splash()>0&&hit.loaded()){explosions++;damageApplied+=world.armoryExplosion(flight.shot,hit);}
                else if(!hit.block())damageApplied+=world.weaponHit(flight.shot,hit);
            } else {
                flight.position=end;flight.elapsed=elapsed;
                if(flight.shot.hitscan()||elapsed>=flight.shot.lifetime()||(flight.shot.rocket()&&elapsed*Math.sqrt(flight.shot.velocity().lengthSquared())>=flight.shot.range()-1e-6)){flights.remove(flight.shot.id());expired++;}
            }
        }
    }
    private void tickArmory(Flight f,WorldAccess world,long now){
        var shot=f.shot;var effect=shot.effect();double duration=effect.fuse()>0?Math.min(shot.lifetime(),effect.fuse()):shot.lifetime();
        double until=Math.min(duration,Math.max(0,(now-shot.wallMs())/1000.0));
        while(f.elapsed+1e-7<until&&flights.containsKey(shot.id())){
            double dt=Math.min(shot.barrage()?.005:.025,until-f.elapsed);var end=shot.barrage()?PharahBarrageMotion.position(shot,f.elapsed+dt):f.position.add(f.velocity.multiply(dt)).add(new Vec(0,-.5*effect.gravity()*dt*dt,0));
            double segment=Math.sqrt(end.subtract(f.position).lengthSquared());
            if(f.distance+segment>shot.range()){
                end=f.position.add(end.subtract(f.position).multiply(Math.max(0,shot.range()-f.distance)/Math.max(1e-9,segment)));segment=shot.range()-f.distance;
            }
            var hit=world.trace(f.position,end);world.present(shot,f.position,hit==null?end:hit.point(),hit);f.elapsed+=dt;f.distance+=segment;
            f.velocity=f.velocity.add(new Vec(0,-effect.gravity()*dt,0));
            if(hit!=null){
                if(hit.block())blockHits++;else entityHits++;
                if(hit.loaded()&&hit.block()&&hit.normal()!=null&&f.bounces<effect.bounces()){
                    var n=hit.normal();double dot=f.velocity.x()*n.x()+f.velocity.y()*n.y()+f.velocity.z()*n.z();
                    f.velocity=f.velocity.subtract(n.multiply(2*dot)).multiply(.65);f.position=hit.point().add(n.multiply(.03));f.bounces++;
                }else{
                    flights.remove(shot.id());
                    world.impact(shot,hit);
                    if(hit.loaded()){
                        if(effect.kind()==2||effect.kind()==3){explosions++;damageApplied+=world.controlImpact(shot,hit);}
                        else if(effect.splash()>0){explosions++;damageApplied+=world.armoryExplosion(shot,hit);}
                        else if(!hit.block())damageApplied+=world.weaponHit(shot,hit);
                    }
                }
            }else f.position=end;
            if(flights.containsKey(shot.id())&&f.distance>=shot.range()-1e-6){
                flights.remove(shot.id());expired++;
                if(effect.kind()==2){explosions++;damageApplied+=world.controlImpact(shot,new Hit(true,0,f.position));}
            }
        }
        if(flights.containsKey(shot.id())&&f.elapsed>=duration-1e-7){
            flights.remove(shot.id());expired++;
            if(effect.fuse()>0&&effect.splash()>0){explosions++;damageApplied+=world.armoryExplosion(shot,new Hit(true,0,f.position));}
        }
    }
    public long cursor(){return cursor;}
    public int active(){return flights.size();}
    public java.util.List<Shot> activeProjectiles(){
        return flights.values().stream().map(f->f.shot).filter(s->!s.hitscan()&&!s.beam()).toList();
    }
    public void clear(){flights.clear();seen.clear();admissions=java.util.List.of();source=null;cursor=0;lastRejection="";}
}
