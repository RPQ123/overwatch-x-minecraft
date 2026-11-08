package lab.owmcguest;

import lab.owmcguest.NativeShotProtocol.Vec;

/** Owned 0.8.0.24919 declarations. Motion/knockback are explicit MC policies.
 * 010a:5 cooldown8, :39 landing50, :19 radius4; 00fa:1 hp1000,
 * :4 cooldown13, :9 lifetime6. 0109:8 duration10, :33 extra500.
 * 00fe:81/82 fists40; :25 attack1.5 (ordinary Tesla reload time).
 */
public final class WinstonRules {
    public static final long HERO=0x02e0000000000009L;
    public static final double BASE_HP=500,RAGE_BONUS=500,RAGE_SECONDS=10;
    public static final double JUMP_COOLDOWN=8,RAGE_JUMP_COOLDOWN=2,LANDING_DAMAGE=50,LANDING_RADIUS=4;
    public static final double BARRIER_HP=1000,BARRIER_RADIUS=5,BARRIER_SECONDS=6,BARRIER_COOLDOWN=13;
    public static final double FIST_DAMAGE=40,FIST_RADIUS=2.5;
    private WinstonRules(){}
    /** MC Fresnel/equator approximation over the original24919 barrier mask. */
    public static float barrierRim(float normalDot,float height){
        float edge=1-Math.clamp(Math.abs(normalDot),0,1);
        return Math.clamp(edge*edge*edge*.9f+Math.max(0,1-Math.abs(height)/.18f)*.5f,0,1);
    }
    public static Vec jump(Vec look){
        double len=Math.sqrt(look.lengthSquared());
        if(!Double.isFinite(len)||len<1e-6)throw new IllegalArgumentException("Winston look");
        // 010a's 15/30 speed declarations adapted to MC's 20Hz gravity.
        var d=look.multiply(1/len);
        return new Vec(d.x()*1.1,Math.clamp(.75+d.y()*.75,.45,1.5),d.z()*1.1);
    }
    public static double landingDamage(double distance){
        if(!Double.isFinite(distance)||distance<0||distance>LANDING_RADIUS)return 0;
        // The original 010a:15 expression falls off over5; damage is bounded
        // by the authenticated inner4m track and the declaration of50.
        return LANDING_DAMAGE*Math.clamp(1-distance/5,0,1);
    }
    public static Vec knockback(Vec velocity,Vec direction,boolean primal){
        double len=Math.hypot(direction.x(),direction.z());
        double x=len<1e-6?0:direction.x()/len,z=len<1e-6?0:direction.z()/len;
        double strength=primal?1.3:.6;
        double vx=velocity.x()+x*strength,vz=velocity.z()+z*strength;
        double scale=Math.min(1,1.8/Math.max(1e-8,Math.hypot(vx,vz)));
        return new Vec(vx*scale,Math.min(.8,Math.max(velocity.y(),primal?.5:.35)),vz*scale);
    }
    /** Bounded native Begin token. An attachment to an active phase is baseline only. */
    public static final class Phase {
        private long previous=-1,token;private boolean armed;
        public long observe(long tick,boolean active){
            if(tick<0)throw new IllegalArgumentException("native phase tick");
            if(previous<0||tick<previous){previous=tick;token=0;armed=!active;return 0;}
            if(!active){token=0;armed=true;}
            else if(tick>previous){token=tick;armed=true;}
            else if(!armed)token=0;
            previous=tick;return token;
        }
        public void reset(){previous=-1;token=0;armed=false;}
    }
}
