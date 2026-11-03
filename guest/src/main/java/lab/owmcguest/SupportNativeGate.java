package lab.owmcguest;

/** Baseline/phase gate for support heroes. No key, timer or inferred target is a trigger.
 * A state already active at the first read must end before a NEW Begin is admitted.
 * Interruptions/regressions discard that admission. Pulses are deduplicated at End.
 */
final class SupportNativeGate {
    enum Edge {NONE,BEGIN,END,PULSE,RESET}
    private boolean sampled,active,admitted,baselineActive;
    private long tick,lastPulse;
    Edge sample(long next,boolean on,boolean pulse){
        if(next<0){clear();return Edge.RESET;}
        boolean regressed=sampled&&next<tick;
        if(!sampled||regressed){sampled=true;tick=next;active=on;baselineActive=on;admitted=false;lastPulse=next;return regressed?Edge.RESET:Edge.NONE;}
        long before=tick;boolean was=active;tick=next;active=on;
        if(next==0||(next==before&&on==was))return Edge.NONE;
        if(baselineActive){if(!on){baselineActive=false;lastPulse=next;}return Edge.NONE;}
        if(pulse){if(!on&&next>lastPulse){lastPulse=next;return Edge.PULSE;}return Edge.NONE;}
        if(on&&!was){admitted=true;return Edge.BEGIN;}
        if(!on&&was&&admitted){admitted=false;return Edge.END;}
        return Edge.NONE;
    }
    boolean active(){return admitted&&active;}
    void clear(){sampled=active=admitted=baselineActive=false;tick=lastPulse=0;}
}
