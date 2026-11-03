package lab.owmcguest;

/** Standalone offline check; no MC/game process, input or native memory. */
public final class TanksNodeEvidenceCheck {
    private static void require(boolean value){if(!value)throw new AssertionError("native diagnostic baseline/phase regression");}
    public static void main(String[] args){
        var d=new TanksNodeEvidence();
        d.observe("q",10,true);require(d.snapshot().get("q").begins()==0);
        d.observe("q",10,false);require(d.snapshot().get("q").ends()==1);
        d.observe("q",20,true);d.observe("q",20,true);d.observe("q",21,false);
        var n=d.snapshot().get("q");require(n.begins()==1&&n.ends()==2&&n.endOnly()==0);
        d.observe("q",22,false);require(d.snapshot().get("q").endOnly()==1);
        var immutable=d.snapshot();d.unavailable("q");require(!d.snapshot().get("q").readable()&&immutable.get("q").readable());
        d.observe("q",30,true);require(d.snapshot().get("q").begins()==1);
        d.observe("q",1,true);require(d.snapshot().get("q").begins()==1);
        d.observe("q",2,false);d.observe("q",2,true);require(d.snapshot().get("q").begins()==1);
        d.clear();d.observe("q",100,true);require(d.snapshot().get("q").begins()==0);
        System.out.println("TanksNodeEvidenceCheck: baseline, B/E, same tick, loss, reversal, immutable snapshot, scope reset passed");
    }
}
