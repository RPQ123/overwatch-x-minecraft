package lab.owmcguest;

import java.util.UUID;

/** First-use, reader-rebind and no-replay scenarios; no native/game processes. */
public final class NativePulseGateCheck {
    private static int checks;
    private static void require(boolean v,String why){checks++;if(!v)throw new AssertionError(why);}
    private static NativePulseGate.Scope scope(long source,long world,long model){return new NativePulseGate.Scope(new UUID(0,1),source,world,model);}
    public static void main(String[] args){
        var g=new NativePulseGate();var a=scope(1,2,3);
        require(!g.observe(a,100,true,267,1000,true),"historical first active sample cannot invent a bomb");
        require(!g.observe(a,100,true,267,1050,true),"historical snapshot remains rejected");
        g.reset();g.prime(a,0,0,2000);
        // Prime occurs before the session guard; the reader can close/reopen,
        // but its first normal sample now joins actual new Anim+Volley.
        require(g.observe(a,100,true,267,2100,true),"first genuine Q after priming must work, even in one poll");
        require(!g.observe(a,100,true,267,2150,true),"reader rebind cannot duplicate same native Volley");
        require(!g.observe(a,735,false,267,2200,true),"native End cannot produce another bomb");
        require(!g.observe(a,1000,true,267,2250,true),"new windup waits for original Volley");
        require(g.observe(a,1000,true,1167,2300,false),"already observed windup survives brief input confirmation loss");
        require(!g.observe(a,1000,true,1167,2350,true),"focus return does not replay Volley");
        g.reset();g.prime(a,0,0,3000);
        require(!g.observe(a,100,true,0,3050,false),"background Begin cannot arm a new bomb");
        require(!g.observe(a,100,true,267,3100,true),"returning focus cannot admit an old background Begin");
        require(!g.observe(scope(1,2,4),500,true,667,3150,true),"new model establishes a new baseline");
        require(!g.observe(scope(1,5,4),500,true,667,3200,true),"new world establishes a new baseline");
        require(!g.observe(scope(6,5,4),500,true,667,3250,true),"new source establishes a new baseline");
        var other=new NativePulseGate.Scope(new UUID(0,9),6,5,4);
        require(!g.observe(other,800,true,967,3300,true),"new MC owner cannot inherit the cursor");
        g.reset();g.prime(a,0,0,4000);
        require(!g.observe(a,100,true,267,4900,true),"long unobserved interval re-baselines rather than replays");
        require(!g.observe(a,1000,true,267,4950,true),"fresh later windup after rebaseline");
        require(g.observe(a,1000,true,1167,5000,true),"fresh later cast remains usable");
        require(!g.observe(a,2000,true,1167,5050,true),"windup alone has no effect");
        require(!g.observe(a,2000,true,2701,5100,true),"unrelated late Volley cannot join this cast");
        require(!g.observe(null,0,false,0,5150,true),"unknown scope admits nothing");
        System.out.println("NativePulseGateCheck: "+checks+" checks passed");
    }
}
