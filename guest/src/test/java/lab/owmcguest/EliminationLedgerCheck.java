package lab.owmcguest;
import java.util.UUID;
public final class EliminationLedgerCheck {
    private static void check(boolean value,String message){if(!value)throw new AssertionError(message);}
    public static void main(String[] args){
        var ledger=new EliminationLedger();var victim=UUID.randomUUID();
        ledger.damage(victim,3.5,1000);check(!ledger.death(victim,16.5,1100),"a hit/removal is not a death");
        ledger.damage(victim,3.5,1200);check(ledger.death(victim,0,1300),"real contributed death resets");
        check(!ledger.death(victim,0,1301),"same victim resolves once");
        var assist=UUID.randomUUID();ledger.damage(assist,1,2000);check(ledger.death(assist,0,6999),"recent assist counts");
        var stale=UUID.randomUUID();ledger.damage(stale,1,2000);check(!ledger.death(stale,0,7001),"old contribution expires");
        var untouched=UUID.randomUUID();check(!ledger.death(untouched,0,3000),"unrelated death does not reset");
        ledger.damage(stale,1,8000);ledger.clear();check(!ledger.death(stale,0,8100),"world/hero reset drops old credit");
        System.out.println("PASS: actual deaths, recent contributions, no hit/discard/unrelated death reset, deduplication and session clear");
    }
}
