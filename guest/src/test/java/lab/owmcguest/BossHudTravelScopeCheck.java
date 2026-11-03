package lab.owmcguest;
import java.util.*;
public class BossHudTravelScopeCheck {
    private static void check(boolean b){if(!b)throw new AssertionError();}
    public static void main(String[] args){
        var a=UUID.randomUUID();var b=UUID.randomUUID();BossHudTravelScope.reset();long old=BossHudTravelScope.epoch();
        BossHudTravelScope.begin(List.of(a));check(!BossHudTravelScope.visible(a)&&BossHudTravelScope.visible(b)&&BossHudTravelScope.epoch()!=old);
        BossHudTravelScope.added(b);BossHudTravelScope.finish(true);check(!BossHudTravelScope.visible(a)&&BossHudTravelScope.visible(b));
        BossHudTravelScope.added(a);check(BossHudTravelScope.visible(a));
        BossHudTravelScope.begin(List.of(a,b));BossHudTravelScope.finish(false);check(BossHudTravelScope.visible(a)&&BossHudTravelScope.visible(b));
        BossHudTravelScope.begin(List.of(a));BossHudTravelScope.added(a);BossHudTravelScope.finish(true);check(BossHudTravelScope.visible(a));
        BossHudTravelScope.begin(List.of(a));BossHudTravelScope.removed(a);check(BossHudTravelScope.retired()==0);BossHudTravelScope.reset();
        System.out.println("PASS: old HUD retirement, failed travel rollback, actual ADD re-admission and async epoch invalidation");
    }
}
