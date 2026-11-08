package lab.owmcguest;

import java.util.*;
import lab.owmcguest.NativeShotProtocol.*;

/** 24919 declarations plus explicitly named Minecraft policies. No input polling.
 * Original 01c6:34 contains an on-expiry nested Volley: 25 x 9, speed80,
 * lifetime5, spread10. Rebuilding that child in MC is not a native factory event.
 * E's 50% mitigation is the requested MC adaptation (absent in this beta graph).
 */
public final class RoadhogRules {
    public static final long HERO=0x02e0000000000040L;
    public static final long SCRAP=0x040000000000029aL,SECONDARY=0x0400000000000295L,WHOLE_HOG=0x0400000000000405L;
    public static final int SPLIT_COUNT=25,HEAL_TICKS=30;
    public static final double SECONDARY_SECONDS=.15000000596046448,HEAL_NATIVE=300;
    public static final double HOOK_DAMAGE=30,HOOK_RANGE=20,HOOK_RADIUS=.5,HOOK_SPEED=40;
    public static final double BREATHER_DAMAGE_SCALE=.5; // MC policy, not a 0.8 declaration.
    private RoadhogRules(){}
    public static boolean is(Shot s){return s!=null&&s.effect()!=null&&s.effect().hero()==HERO;}
    public static boolean secondary(Shot s){return is(s)&&s.effect().resource()==SECONDARY;}
    public static boolean wholeHog(Shot s){return is(s)&&s.effect().resource()==WHOLE_HOG;}
    /** Resource-specific guard used by the decoder; rejects cross-hero borrowing. */
    public static boolean factory(long resource,int type,int status,boolean hitscan,double speed2,double life,double range,double damage){
        if(range!=100)return false;
        if(resource==SCRAP)return type==2&&status==0&&!hitscan&&Math.abs(speed2-6400)<.1&&life==5&&damage==9;
        if(resource==SECONDARY)return type==1&&status==8&&!hitscan&&Math.abs(speed2-3600)<.1&&Math.abs(life-SECONDARY_SECONDS)<1e-6&&damage==50;
        return resource==WHOLE_HOG&&type==3&&status==0&&hitscan&&Math.abs(speed2-1)<.01&&life==0&&damage==7;
    }
    private static Vec cross(Vec a,Vec b){return new Vec(a.y()*b.z()-a.z()*b.y(),a.z()*b.x()-a.x()*b.z(),a.x()*b.y()-a.y()*b.x());}
    private static Vec unit(Vec a){return a.multiply(1/Math.sqrt(a.lengthSquared()));}
    /** Fixed, uniformly covered forward cone; MC pattern, not the native RNG.
     * A split preserves its actual parent endpoint, never acquires an aim target. */
    public static List<Shot> split(Shot parent,Vec at,long firstId){
        if(!secondary(parent)||!Double.isFinite(at.lengthSquared())||firstId>=0)throw new IllegalArgumentException("Roadhog split parent");
        Vec f=unit(parent.velocity()),r=unit(cross(f,Math.abs(f.y())>.99?new Vec(1,0,0):new Vec(0,1,0))),u=cross(r,f);
        var result=new ArrayList<Shot>();
        double rotation=(Integer.toUnsignedLong(parent.identity().hashCode())%65536)/65536.*Math.PI*2;
        for(int i=0;i<SPLIT_COUNT;i++){
            double radius=i==0?0:Math.sqrt((i-.5)/(SPLIT_COUNT-1.))*Math.tan(Math.toRadians(10));
            double angle=rotation+i*Math.PI*(3-Math.sqrt(5));
            Vec d=unit(f.add(r.multiply(radius*Math.cos(angle))).add(u.multiply(radius*Math.sin(angle))));
            // effect4 is an internal derived-child marker; never admitted from a native journal.
            var effect=new Effect(HERO,SCRAP,4,0,0,0,0,0,0);
            result.add(new Shot(firstId-i,0,parent.wallMs()+Math.round(SECONDARY_SECONDS*1000),at,d.multiply(80),9,5,false,100,
                parent.identity()+":mc-split:"+i,false,false,effect));
        }
        return List.copyOf(result);
    }
    public static double nativeDamage(Shot shot,Vec contact){
        if(!is(shot))return shot.nativeDamage();
        double begin=wholeHog(shot)?30:10,end=wholeHog(shot)?40:20;
        // The nested child has no falloff block in the original declaration.
        if(shot.effect().kind()==4)return shot.nativeDamage();
        double distance=Math.sqrt(contact.subtract(shot.start()).lengthSquared());
        return shot.nativeDamage()*(1-.7*Math.clamp((distance-begin)/(end-begin),0,1));
    }
    /** Bounded strong horizontal Q impulse; vertical impulse cannot stack per pellet. */
    public static Vec knockback(Vec current,Vec direction){
        double flat=Math.hypot(direction.x(),direction.z());
        if(flat<1e-8)return current;
        double x=current.x()+direction.x()/flat*.18,z=current.z()+direction.z()/flat*.18;
        double length=Math.hypot(x,z),scale=length>1.4?1.4/length:1;
        return new Vec(x*scale,Math.min(.35,Math.max(current.y(),.16)),z*scale);
    }
    public static Vec hookGoal(Vec feet,Vec direction){
        double length=Math.hypot(direction.x(),direction.z());
        Vec flat=length<1e-8?new Vec(0,0,1):new Vec(direction.x()/length,0,direction.z()/length);
        return feet.add(flat.multiply(2.75));
    }
    public static Vec pullStep(Vec position,Vec goal){
        Vec delta=goal.subtract(position);double distance=Math.sqrt(delta.lengthSquared());
        return distance<1e-8?new Vec(0,0,0):delta.multiply(Math.min(1,distance)/distance);
    }
    /** Token budget survives repeated samples and cannot be reissued after End. */
    public static final class Healing {
        private long token;private double remaining;private int ticks;
        public void refresh(long next){if(next==0){remaining=0;return;}if(next!=token){token=next;remaining=HEAL_NATIVE*NativeShotSimulation.HP_SCALE;ticks=HEAL_TICKS;}}
        public double tick(){if(remaining<=0||ticks<=0)return 0;double n=Math.min(remaining,HEAL_NATIVE*NativeShotSimulation.HP_SCALE/HEAL_TICKS);remaining-=n;ticks--;return n;}
        public void clear(){token=0;remaining=0;ticks=0;}
    }
}
