package lab.owmcguest;

import java.util.LinkedHashSet;

/** Independently rebuilt Minewatch2018 contact/decay policy, NOT Beta timing. */
public final class MeiFreezeProgress {
    public static final int CONTACTS=30,DELAY=10,FROZEN=90;
    private final LinkedHashSet<String> seen=new LinkedHashSet<>();
    private int stacks;
    private long last=-1,lastHit=-1,until=-1;
    public boolean hit(String identity,long tick){
        if(identity==null||identity.isEmpty()||tick<0||tick<last||seen.contains(identity))return false;
        advance(tick);seen.add(identity);if(seen.size()>256)seen.remove(seen.iterator().next());
        if(frozen(tick))return false;
        lastHit=tick;stacks=Math.min(CONTACTS,stacks+1);
        if(stacks==CONTACTS)until=tick+FROZEN;
        return true;
    }
    public void advance(long tick){
        if(tick<0||tick<last)return;
        if(until>=0){if(tick>=until){until=-1;stacks=0;lastHit=-1;}}
        else if(stacks>0&&lastHit>=0){
            long first=Math.max(last+1,lastHit+DELAY+1);
            if(tick>=first)stacks=(int)Math.max(0,stacks-(tick-first+1));
        }
        last=tick;
    }
    public int stacks(){return stacks;}
    public boolean frozen(long tick){return until>=0&&tick<until;}
    public long remaining(long tick){return Math.max(0,until-tick);}
    public double slow(long tick){return frozen(tick)?1:stacks==0?0:Math.min(.9,.15*(stacks/5+1));}
    public boolean empty(){return stacks==0&&until<0;}
}
