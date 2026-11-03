package lab.owmcguest;

import java.util.function.Predicate;
import java.util.function.IntPredicate;

/** Pure geometry for the explicit Hanzo fixture; never replaces occupied terrain. */
public final class HanzoArrowVisualLayout {
    public static final int EXTENT=12,HEADROOM=5,MAX_RISE=40;
    public record Cell(int x,int y,int z){}
    private HanzoArrowVisualLayout(){}
    public static Cell chooseFloor(int x,int initialY,int z,int bottom,int top,Predicate<Cell> available,
                                   Predicate<Cell> air,Predicate<Cell> supportOrAir,IntPredicate noEntities){
        for(int rise=0;rise<=MAX_RISE;rise++){
            int y=initialY+rise;if(y<bottom||y+HEADROOM>=top)continue;
            boolean clear=true;
            for(int dx=-EXTENT;dx<=EXTENT&&clear;dx++)for(int dz=-EXTENT;dz<=EXTENT&&clear;dz++){
                var floor=new Cell(x+dx,y,z+dz);clear=available.test(floor)&&supportOrAir.test(floor);
                for(int up=1;up<=HEADROOM&&clear;up++){
                    var cell=new Cell(x+dx,y+up,z+dz);clear=available.test(cell)&&air.test(cell);
                }
            }
            if(clear&&noEntities.test(y))return new Cell(x,y,z);
        }
        throw new IllegalStateException("Hanzo visual found no loaded empty 25x25x5 corridor within 40 blocks; terrain preserved");
    }
    /** Eye height varies with pose; wall bottom and catch floor use feet instead. */
    public static int wallBottom(int feetY){return feetY;}
    public static int catchFloor(int feetY){return feetY-1;}
}
