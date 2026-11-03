package lab.owmcguest;

import lab.owmcguest.NativeShotProtocol.Vec;

/** MC displacement overlay; normal/native travel keeps its own gravity and
 * skill acceleration. This residual never suspends either mover or resets
 * flight/hover/fuel. Horizontal displacement is added after speed import. */
public final class RocketImpulseMotion {
    public static final double DRAG=.86;
    public static final int MAX_TICKS=40;
    private static final Vec ZERO=new Vec(0,0,0);
    private Vec velocity=ZERO;
    private int age=Integer.MIN_VALUE,sampledAge=Integer.MIN_VALUE,expires=Integer.MIN_VALUE;
    public void add(Vec impulse,int tick){
        if(!Double.isFinite(impulse.x())||!Double.isFinite(impulse.y())||!Double.isFinite(impulse.z()))throw new IllegalArgumentException("impulse bounds");
        advance(tick);velocity=velocity.add(impulse);expires=tick+MAX_TICKS;
    }
    private void advance(int tick){
        if(age!=Integer.MIN_VALUE&&tick<age)reset();
        if(age!=Integer.MIN_VALUE&&tick>age)velocity=velocity.multiply(Math.pow(DRAG,(long)tick-age));
        if(expires!=Integer.MIN_VALUE&&tick>=expires)velocity=ZERO;
        age=tick;
    }
    public Vec sample(int tick){
        advance(tick);if(sampledAge==tick)return ZERO;sampledAge=tick;return velocity;
    }
    public void blocked(int axes){velocity=new Vec((axes&1)!=0?0:velocity.x(),(axes&2)!=0?0:velocity.y(),(axes&4)!=0?0:velocity.z());}
    public void reset(){velocity=ZERO;age=sampledAge=expires=Integer.MIN_VALUE;}
}
