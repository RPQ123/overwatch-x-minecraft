package lab.owmcguest;

import java.util.LinkedHashMap;
import java.util.UUID;

/** Server damage contributions only. Removal/despawn is deliberately not death. */
public final class CombatFeedbackLedger {
    private record Entry(long damaged,boolean resolved){}
    private final LinkedHashMap<UUID,Entry> entries=new LinkedHashMap<>();
    public boolean damage(UUID victim,double lost,double health,long now){
        if(victim==null||!Double.isFinite(lost)||lost<=0||!Double.isFinite(health))return false;
        expire(now);var old=entries.get(victim);if(old!=null&&old.resolved())return false;
        entries.put(victim,new Entry(now,false));
        if(entries.size()>4096)entries.remove(entries.keySet().iterator().next());
        return true;
    }
    public boolean death(UUID victim,double health,long now){
        var old=entries.get(victim);
        if(old==null||old.resolved()||!Double.isFinite(health)||health>0||now<old.damaged()||now-old.damaged()>5000)return false;
        // Retain the resolved identity for the entire contribution window, so
        // multiple body parts and the same tick's splash cannot repeat a kill.
        entries.put(victim,new Entry(old.damaged(),true));return true;
    }
    public boolean tracking(UUID id,long now){var e=entries.get(id);return e!=null&&!e.resolved()&&now>=e.damaged()&&now-e.damaged()<=5000;}
    public void expire(long now){entries.values().removeIf(e->now-e.damaged()>5000);}
    public void clear(){entries.clear();}
}
