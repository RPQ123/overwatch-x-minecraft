package lab.owmcguest;

import java.util.*;

/** Bounded read-only search; callers may fill air only after a site is selected. */
public final class HanzoCombatSite {
    public static final int EXTENT=18,HEADROOM=5,MAX_RISE=40,NEARBY=24;
    public record Cell(int x,int y,int z){}
    public record Blockage(String reason,String detail,Cell cell){}
    public record Attempt(Cell floor,Blockage blocked){}
    public record Search(Cell floor,int attempts,Map<String,Integer> rejected,List<Attempt> samples){}
    public interface Space {Blockage blocked(Cell cell,boolean floor);boolean occupied(Cell floor);}
    private HanzoCombatSite(){}
    public static void requireIsolated(boolean trial,String configured,String actual,boolean aliveCreative){
        if(!trial||configured==null||actual==null||!configured.startsWith("Overwatch Twilight Switch ")
            ||!actual.startsWith("Overwatch Twilight Switch ")||!aliveCreative)
            throw new IllegalArgumentException("Hanzo combat fixture requires actual isolated creative trial save; no blocks changed");
    }
    public static Search find(int x,int y,int z,int bottom,int top,Space space){
        int[][] offsets={{0,0},{NEARBY,0},{-NEARBY,0},{0,NEARBY},{0,-NEARBY},{NEARBY,NEARBY},{NEARBY,-NEARBY},{-NEARBY,NEARBY},{-NEARBY,-NEARBY}};
        int attempts=0;var rejected=new LinkedHashMap<String,Integer>();var samples=new ArrayList<Attempt>();
        for(int rise=0;rise<=MAX_RISE;rise++)for(var offset:offsets){
            var floor=new Cell(x+offset[0],y+rise,z+offset[1]);attempts++;Blockage blocked=null;
            if(floor.y()<bottom||floor.y()+HEADROOM>=top)blocked=new Blockage("world-height","insufficient floor/headroom inside dimension height",floor);
            for(int dx=-EXTENT;dx<=EXTENT&&blocked==null;dx++)for(int dz=-EXTENT;dz<=EXTENT&&blocked==null;dz++){
                blocked=space.blocked(new Cell(floor.x()+dx,floor.y(),floor.z()+dz),true);
                for(int up=1;up<=HEADROOM&&blocked==null;up++)blocked=space.blocked(new Cell(floor.x()+dx,floor.y()+up,floor.z()+dz),false);
            }
            if(blocked==null&&space.occupied(floor))blocked=new Blockage("living-entities","living entities inside selected corridor",floor);
            if(blocked==null)return new Search(floor,attempts,Map.copyOf(rejected),List.copyOf(samples));
            rejected.merge(blocked.reason(),1,Integer::sum);var attempt=new Attempt(floor,blocked);
            if(samples.size()<13)samples.add(attempt);else samples.set(12,attempt);
        }
        return new Search(null,attempts,Map.copyOf(rejected),List.copyOf(samples));
    }
}
