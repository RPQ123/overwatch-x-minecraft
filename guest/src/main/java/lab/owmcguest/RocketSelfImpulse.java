package lab.owmcguest;

import lab.owmcguest.NativeShotProtocol.*;

/** Shared self-only MC blast adapter, in blocks/tick. No damage is applied.
 * Use the player center direction (including Y), linear distance falloff and
 * actual pre-terrain MC exposure. A shot at one's feet therefore launches up. */
public final class RocketSelfImpulse {
    // 2026-10-27 user MC adaptation: +50% on all three axes, shared by mines.
    public static final double PREVIOUS_MAX_IMPULSE=1.10,BOOST=1.50,MAX_IMPULSE=PREVIOUS_MAX_IMPULSE*BOOST;
    private RocketSelfImpulse(){}
    public static long hero(Shot s){
        return s.rocket()?0x02e0000000000008L:s.helix()?0x02e000000000006eL:s.tankShell()?0x02e0000000000015L:0;
    }
    public static Vec calculate(Vec blast,Vec playerCenter,double radius,double exposure){
        var delta=playerCenter.subtract(blast);double distance=Math.sqrt(delta.lengthSquared());
        if(!Double.isFinite(distance)||!Double.isFinite(radius)||radius<=0||distance>=radius
            ||!Double.isFinite(exposure)||exposure<=0)return new Vec(0,0,0);
        double magnitude=MAX_IMPULSE*(1-distance/radius)*Math.min(1,exposure);
        return distance<1e-6?new Vec(0,magnitude,0):delta.multiply(magnitude/distance);
    }
}
