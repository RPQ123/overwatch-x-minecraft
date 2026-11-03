package lab.owmcguest;
public final class NativeAbilityContinuationGateCheck {
    static void require(boolean b,String m){if(!b)throw new AssertionError(m);}
    public static void main(String[] args){
        var g=new NativeAbilityContinuationGate();var s=new NativeAbilityContinuationGate.Scope(1,2,3);
        require(!g.observe(s,100,true,false,1000),"Picker/reconnect cannot start an old cast");
        require(!g.observe(s,100,true,true,1000),"Late input cannot replay a baseline");
        require(g.observe(s,200,true,true,1000),"New actual gameplay cast admitted");
        require(g.observe(s,200,true,false,1000),"Native cinematic input lock preserves that exact cast");
        require(!g.observe(s,300,false,false,1000),"Original End terminates continuation");
        require(!g.observe(s,300,true,true,1000),"End cannot replay as a Begin");
        require(!g.observe(s,400,true,false,1200),"New cast while input unavailable refused");
        require(!g.observe(s,400,true,true,1000),"Previously refused event stays refused");
        require(g.observe(s,500,true,true,1000),"Later genuine cast remains usable");
        require(!g.observe(new NativeAbilityContinuationGate.Scope(1,4,3),500,true,false,1000),"Old world does not authorize continued damage");
        require(!g.observe(new NativeAbilityContinuationGate.Scope(1,4,5),500,true,true,1000),"Replacement model establishes a new baseline");
        g.reset();require(!g.observe(s,600,false,true,2000),"Idle same-owner gameplay baseline");
        require(g.observe(s,700,true,false,2100),"Same-frame native input lock admits a recent gameplay frame");
        require(g.observe(s,700,true,false,4000),"Admitted same cast does not require continued input");
        require(!g.observe(s,800,false,false,4100),"End closes recent-input continuation");
        require(!g.observe(s,900,true,false,4200),"Expired gameplay cannot admit another cast");
        System.out.println("PASS: initial gameplay admission, exact cinematic continuation, End/replay and world/model refusal");
    }
}
