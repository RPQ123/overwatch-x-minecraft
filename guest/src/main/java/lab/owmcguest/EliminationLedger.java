package lab.owmcguest;

import java.util.HashMap;
import java.util.HashSet;
import java.util.UUID;

/** Actual living-victim contribution and death; discard/removal alone is not a kill. */
public final class EliminationLedger {
    private final HashMap<UUID,Long> tagged=new HashMap<>();
    private final HashSet<UUID> resolved=new HashSet<>();
    public void damage(UUID victim,double loss,long now){if(loss>0&&Double.isFinite(loss)&&!resolved.contains(victim))tagged.put(victim,now);}
    public boolean death(UUID victim,double health,long now){
        if(!Double.isFinite(health)||health>0)return false;
        var at=tagged.remove(victim);
        return at!=null&&now>=at&&now-at<=5000&&resolved.add(victim);
    }
    public void expire(long now){tagged.entrySet().removeIf(e->now-e.getValue()>5000);}
    public void clear(){tagged.clear();resolved.clear();}
}
