package lab.owmcguest;

import java.util.UUID;

/** MC adaptation: distribute declared native healing once per scoped execution.
 * A fresh observation may resume after a read gap, but cannot refill its budget
 * or reopen an execution for which the original logger has already reported End.
 */
public final class NativeSustainPhase {
    public static final long BASTION=0x02e0000000000015L, MEI=0x02e00000000000ddL;
    public record Scope(UUID owner,long world,long source,long model,long hero) {}
    private Scope scope;
    private long tick=-1,wall;
    private boolean executing,ended;
    private double amount,interval,remaining;

    public boolean refresh(Scope next,long stamp,boolean active,double heal,double seconds,long observed){
        if(next==null||next.owner()==null||next.world()==0||next.source()==0||next.model()==0
            ||(next.hero()!=MEI&&next.hero()!=BASTION)||stamp<0||observed<0
            ||!Double.isFinite(heal)||heal<=0||heal>1000
            ||!Double.isFinite(seconds)||seconds<.1||seconds>10)return false;
        boolean same=next.equals(scope);
        if(same&&(stamp<tick||observed<wall))return false;
        if(same&&stamp==tick){
            if(Double.compare(amount,heal)!=0||Double.compare(interval,seconds)!=0||ended&&active)return false;
        }else{
            scope=next;tick=stamp;amount=heal;interval=seconds;
            remaining=next.hero()==MEI?heal*.1:Double.POSITIVE_INFINITY;
            ended=false;
        }
        wall=observed;executing=active;ended|=!active;
        return true;
    }
    public boolean active(long now){return executing&&tick>0&&now-wall<=150&&wall-now<=50;}
    public double consume(){
        double value=Math.min(remaining,rate()/20);
        remaining=Math.max(0,remaining-value);
        return value;
    }
    public Scope scope(){return scope;}
    public long tick(){return tick;}
    public double rate(){return amount*.1/interval;}
    public double remaining(){return remaining;}
    public void clear(){scope=null;tick=-1;wall=0;executing=ended=false;amount=interval=remaining=0;}
}
