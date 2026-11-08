package lab.owmcguest;

/** Fresh native fire plus real native cooldown; no input-created casts/timer. */
public final class GrappleCastGate {
    private long fire=-1,token;private double previous=Double.NaN;private boolean pending,cooling;
    public boolean observe(long fireTick,long castTick,boolean firing,boolean window,boolean input,double remaining){
        if(!Double.isFinite(remaining)||remaining<0||remaining>12.1){fire=Math.max(fire,fireTick);previous=Double.NaN;return false;}
        if(!pending&&remaining<=.001)cooling=false;
        boolean ready=!pending&&!cooling&&(remaining<=.001||previous<=.001);previous=remaining;
        if(fire<0){fire=fireTick;return false;}boolean fresh=fireTick>fire;fire=Math.max(fire,fireTick);
        if(!fresh||!firing||!window||!input||!ready||castTick<=token)return false;
        token=castTick;pending=true;return true;
    }
    public long token(){return token;}
    public boolean pending(){return pending;}
    public void receipt(boolean success){pending=false;cooling=success;}
    public void reset(){fire=-1;token=0;previous=Double.NaN;pending=cooling=false;}
}
