package lab.owmcguest;

public final class NativeSpawnHealthGateCheck {
    private static void require(boolean v,String message){if(!v)throw new AssertionError(message);}
    public static void main(String[] args){
        var gate=new NativeSpawnHealthGate();var p=java.util.UUID.randomUUID();
        require(!gate.claim(p,1,2,3,false),"Picker hover cannot heal");
        require(gate.claim(p,1,2,3,true),"First confirmed pawn initializes");
        require(!gate.claim(p,1,2,3,true),"Same pawn cannot heal actual combat injury again");
        require(!gate.claim(p,1,0,0,false),"Reader gap cannot become a spawn");
        require(!gate.claim(p,1,2,3,true),"Reader reconnect preserves the used spawn receipt");
        require(gate.claim(p,1,4,5,true),"New confirmed hero initializes once");
        require(gate.claim(p,1,4,6,true),"Actual model recreation is a new pawn");
        require(!gate.claim(p,1,4,6,true),"Forced same-pawn refresh is not a new spawn");
        require(gate.claim(p,2,4,6,true),"New native process generation has independent ownership");
        gate.reset();require(gate.claim(p,2,4,6,true),"A new MC connection may initialize its player");
        System.out.println("Native spawn health lifecycle checks passed");
    }
}
