package lab.owmcguest;

import java.util.*;
import lab.owmcguest.HanzoCombatSite.Cell;

/** Air-only writes in one owned floor, with conservative rollback of tracked cells. */
public final class HanzoLabBlocks<S> {
    public interface Access<S>{boolean loaded(Cell c);S read(Cell c);boolean air(S state);boolean placed(S state);boolean write(Cell c,S state);}
    public record Receipt(int restored,int preservedExternalChanges,int pending,List<String> failures){}
    private final Cell center;private final int extent;private final S placed;
    private final Map<Cell,S> before=new LinkedHashMap<>();
    public HanzoLabBlocks(Cell center,int extent,S placed){this.center=center;this.extent=extent;this.placed=placed;}
    public int size(){return before.size();}
    public boolean place(Cell c,Access<S> access){
        if(c.y()!=center.y()||Math.abs((long)c.x()-center.x())>extent||Math.abs((long)c.z()-center.z())>extent)throw new IllegalArgumentException("outside owned Hanzo floor: "+c);
        if(!access.loaded(c))throw new IllegalStateException("owned floor unloaded: "+c);
        S current=access.read(c);if(!access.air(current))return false; // Existing terrain is never changed.
        if(before.containsKey(c))throw new IllegalStateException("duplicate Hanzo ownership: "+c);
        before.put(c,current);
        if(!access.write(c,placed)||!access.placed(access.read(c)))throw new IllegalStateException("owned floor placement refused: "+c);
        return true;
    }
    public Receipt restore(Access<S> access){
        int restored=0,preserved=0;var failures=new ArrayList<String>();
        for(var entry:new ArrayList<>(before.entrySet())){
            var cell=entry.getKey();
            if(!access.loaded(cell)){if(failures.size()<8)failures.add("owned chunk unloaded: "+cell);continue;}
            if(!access.placed(access.read(cell))){preserved++;before.remove(cell);continue;}
            if(!access.write(cell,entry.getValue())||!Objects.equals(access.read(cell),entry.getValue())){
                if(failures.size()<8)failures.add("owned floor restoration refused: "+cell);continue;
            }
            restored++;before.remove(cell);
        }
        return new Receipt(restored,preserved,before.size(),List.copyOf(failures));
    }
}
