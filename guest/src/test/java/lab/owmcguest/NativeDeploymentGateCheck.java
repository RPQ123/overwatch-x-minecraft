package lab.owmcguest;

public final class NativeDeploymentGateCheck {
    private static void require(boolean v,String message){if(!v)throw new AssertionError(message);}
    public static void main(String[] args){
        var gate=new NativeDeploymentGate();var a=new NativeDeploymentGate.Scope(1,2,3);
        require(!gate.observe(a,100,true,267,1000),"Reconnect during a historical cast must not deploy");
        require(!gate.observe(a,735,false,267,1300),"Historical End must not arm");
        require(!gate.observe(a,1000,true,267,2000),"A real windup alone does not deploy");
        require(gate.observe(a,1000,true,1167,2167),"Joined real cast/Volley deploys once");
        require(!gate.observe(a,1000,true,1167,2190),"Polling cannot duplicate");
        require(!gate.observe(a,1635,false,1167,2635),"Original cast End cannot deploy twice");
        gate.observe(a,2000,true,1167,3000);
        require(!gate.observe(a,2635,false,2167,3900),"Delayed transport cannot authorize a late deployment");
        gate.observe(a,3000,true,2167,4000);
        require(!gate.observe(a,3000,true,3700,4100),"A Volley unrelated to this windup is rejected");
        require(!gate.observe(new NativeDeploymentGate.Scope(1,4,3),3000,true,3700,4200),"New world rejects old cast");
        require(!gate.observe(new NativeDeploymentGate.Scope(1,4,5),3000,true,3700,4300),"New hero model rejects old cast");
        require(!gate.observe(null,0,false,0,4400),"Missing identity revokes");
        System.out.println("Native deployment lifecycle checks passed");
    }
}
