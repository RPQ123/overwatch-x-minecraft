package lab.owmcguest;

import lab.owmcguest.NativeShotProtocol.*;

/** User 2026-10-26 MC adaptation, AFTER native protocol validation. Never relax
 * the measured native speed/proof checks or manufacture additional admissions. */
public final class RocketFlightTuning {
    public static final double SPEED_SCALE=.75;
    private RocketFlightTuning(){}
    public static boolean applies(Shot s){
        return s.rocket()||s.barrage()||s.tankShell()||s.effect()!=null
            &&s.effect().hero()==0x02e0000000000008L&&s.effect().resource()==0x040000000000010fL&&s.effect().kind()==3;
    }
    public static Shot adapt(Shot s){
        if(!applies(s))return s;
        return new Shot(s.id(),s.nativeEntity(),s.wallMs(),s.start(),s.velocity().multiply(SPEED_SCALE),
            s.nativeDamage(),s.lifetime(),s.hitscan(),s.range(),s.identity(),s.beam(),s.rocket(),s.effect(),s.waves());
    }
    /** Called on the original batch once at the simulation boundary. Replay
     * starts with the original lastBatch, so speed cannot compound on replay. */
    public static Batch adapt(Batch b){
        return new Batch(b.source(),b.acknowledged(),b.lastId(),b.entries().stream()
            .map(e->e.shot()==null?e:new Entry(e.id(),adapt(e.shot()),e.rejection())).toList());
    }
}
