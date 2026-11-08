package lab.owmcguest;

/** Native fist Anim63/62 and its original 350ms hit gate. TrackTargets may
 * be absent without the OW server. Both observations own ONE MC strike. */
public final class WinstonPrimalStrike {
    private final WinstonFistPhase hit=new WinstonFistPhase(),animation=new WinstonFistPhase();
    private long swing,due,lastWall;private boolean spent;
    public long observe(long hitTick,boolean hitActive,long animTick,boolean animActive,long now){
        if(lastWall>0&&now<lastWall)reset();lastWall=now;
        long a=animation.observe(animTick,animActive),h=hit.observe(hitTick,hitActive);
        if(a>0){swing=a;due=now+(animActive?350:0);spent=false;}
        if(h>0){
            if(swing==0)return h;
            if(!spent){spent=true;return swing;}
        }
        if(swing>0&&!spent&&now>=due){spent=true;return swing;}
        return 0;
    }
    public void reset(){hit.reset();animation.reset();swing=due=lastWall=0;spent=false;}
}
