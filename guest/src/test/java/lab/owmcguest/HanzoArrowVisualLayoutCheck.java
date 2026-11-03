package lab.owmcguest;

import java.util.function.Predicate;
import lab.owmcguest.HanzoArrowVisualLayout.Cell;

public final class HanzoArrowVisualLayoutCheck {
    private static void check(boolean ok,String message){if(!ok)throw new AssertionError(message);}
    public static void main(String[] args){
        // Grounded/crouched/swimming eye heights can put old eyeFloor-1 into floor63.
        var ground=HanzoArrowVisualLayout.chooseFloor(0,63,0,-64,320,c->true,c->c.y()>63,c->c.y()>=63,y->true);
        check(ground.y()==63,"existing full floor remains usable without raising");
        check(HanzoArrowVisualLayout.wallBottom(64)==64&&HanzoArrowVisualLayout.catchFloor(64)==63,"wall never overlaps floor regardless of eye pose");
        Predicate<Cell> clear=c->c.y()>63&&!(c.x()==10&&c.z()==3&&c.y()<=66);
        var raised=HanzoArrowVisualLayout.chooseFloor(0,63,0,-64,320,c->true,clear,c->true,y->true);
        check(raised.y()==66,"near-wall obstruction selects clear air above it without replacing terrain");
        var entity=HanzoArrowVisualLayout.chooseFloor(0,63,0,-64,320,c->true,c->true,c->true,y->y>63);
        check(entity.y()==64,"occupied living-entity corridor is not admitted");
        try{HanzoArrowVisualLayout.chooseFloor(0,63,0,-64,320,c->c.x()<10,c->true,c->true,y->true);throw new AssertionError("unloaded wall accepted");}
        catch(IllegalStateException expected){}
        try{HanzoArrowVisualLayout.chooseFloor(0,318,0,-64,320,c->true,c->true,c->true,y->true);throw new AssertionError("top boundary accepted");}
        catch(IllegalStateException expected){}
        System.out.println("HanzoArrowVisualLayoutCheck passed (ground floor, wall obstruction, entities, loaded bounds)");
    }
}
