package lab.owmcguest;

import java.util.Map;
import java.util.TreeMap;

/** Diagnostic logger observations only. These counters NEVER authorize a skill.
 * A baseline (including an active baseline), lost read or reversed clock cannot
 * create a Begin. B/E may share a tick; End closes it without another cast.
 * End-only means the last-change logger missed Begin, not a successful action. */
public final class TanksNodeEvidence {
    public record Node(long tick,boolean active,boolean readable,long begins,long ends,
                       long endOnly,long baselines){}
    private final Map<String,Node> nodes=new TreeMap<>();

    public void observe(String key,long tick,boolean active){
        if(tick<0)throw new IllegalArgumentException("negative native tick");
        var old=nodes.get(key);
        long b=old==null?0:old.begins(),e=old==null?0:old.ends();
        long only=old==null?0:old.endOnly(),base=old==null?0:old.baselines();
        if(old==null||!old.readable()||tick<old.tick())base++;
        else if(tick>old.tick()){
            if(active)b++;else{e++;if(!old.active())only++;}
        }else if(old.active()&&!active)e++;
        // Same-tick inactive -> active is ambiguous: baseline it, never a Begin.
        else if(!old.active()&&active)base++;
        nodes.put(key,new Node(tick,active,true,b,e,only,base));
    }
    public void unavailable(String prefix){
        nodes.replaceAll((key,n)->key.startsWith(prefix)?new Node(n.tick(),false,false,n.begins(),n.ends(),n.endOnly(),n.baselines()):n);
    }
    public Map<String,Node> snapshot(){return Map.copyOf(nodes);}
    public void clear(){nodes.clear();}
}
