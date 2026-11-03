package lab.owmcguest;
public final class UltimateCalloutGateCheck {
    private static void expect(boolean value){if(!value)throw new AssertionError();}
    public static void main(String[] args){
        var gate=new UltimateCalloutGate();
        expect(!gate.observe(1,2,3,4,100)); // attach in an already active ultimate
        expect(!gate.observe(1,2,3,4,100));
        expect(!gate.observe(1,2,3,4,0)); // inactive Begin node
        expect(!gate.observe(1,2,3,4,100)); // old Begin reappears
        expect(gate.observe(1,2,3,4,120));
        expect(!gate.observe(1,2,3,4,120)); // repeated polls/Q cannot replay
        expect(!gate.observe(1,2,3,5,130)); // dimension transition
        expect(!gate.observe(2,2,3,5,140)); // same model, new session
        expect(!gate.observe(2,2,6,5,150)); // hero rebind
        expect(gate.observe(2,2,6,5,160));
        gate.reset();expect(!gate.observe(2,2,6,5,170));
        System.out.println("Ultimate callout transition checks passed");
    }
}
