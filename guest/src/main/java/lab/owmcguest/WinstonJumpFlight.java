package lab.owmcguest;

/** Keeps an admitted Jump Pack under vanilla gravity/drag instead of replacing
 * its horizontal velocity with the native walk-speed import each frame. */
public final class WinstonJumpFlight {
    private int launched=-1;
    public void launch(int tick){launched=tick;}
    public boolean owns(int tick,boolean grounded,boolean allowed){
        if(launched<0)return false;
        // A same-tick ground/correction sample must not revoke the impulse
        // before vanilla gets its first movement step. Actual landing still wins.
        if(!allowed||tick<launched||tick-launched>120||grounded&&tick-launched>2){reset();return false;}
        return true;
    }
    public void reset(){launched=-1;}
}
