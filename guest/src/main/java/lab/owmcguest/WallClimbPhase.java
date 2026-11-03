package lab.owmcguest;

/** MC contact-driven motor limits. These are adapter settings, not inferred
 * original-game constants or evidence of native climbing animation. */
public final class WallClimbPhase {
    public static final double SPEED_PER_TICK=.30,MAX_RISE=6.0;
    public static boolean hero(long hero){return hero==0x02e0000000000029L||hero==0x02e0000000000005L;}
    public static boolean wallAdmission(boolean contact,boolean tallEnough,boolean alreadyClimbing){
        return contact&&(tallEnough||alreadyClimbing);
    }
    private long generation,lastTick=-1;
    private double startY;
    private int ticks;
    private boolean active,exhausted;
    public double step(long source,long tick,boolean grounded,boolean request,
                       boolean wall,boolean eligible,double y) {
        if(!Double.isFinite(y)||source==0||tick<0){invalidate();return 0;}
        if(generation!=source){generation=source;active=false;exhausted=!grounded;lastTick=-1;}
        if(tick==lastTick)return 0;
        if(tick<lastTick){invalidate();return 0;}
        lastTick=tick;
        if(grounded&&!active){exhausted=false;ticks=0;}
        if(!eligible||!request||!wall){if(active)exhausted=true;active=false;return 0;}
        if(exhausted)return 0;
        if(!active){startY=y;ticks=0;active=true;}
        double remaining=MAX_RISE-(y-startY);
        if(++ticks>30||remaining<=1e-5||y<startY-1){blocked();return 0;}
        return Math.min(SPEED_PER_TICK,remaining);
    }
    public boolean active(){return active;}
    public void blocked(){active=false;exhausted=true;}
    public void invalidate(){active=false;exhausted=true;generation=0;lastTick=-1;}
}
