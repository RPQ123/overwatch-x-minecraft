package lab.owmcguest;
public final class FlightToggleCheck {
    private static void require(boolean condition){if(!condition)throw new AssertionError("Flight key edge/session/focus guard");}
    public static void main(String[] args){
        var key=new FlightToggle();require(!key.poll(1,true,true));require(!key.poll(1,true,true));
        require(!key.poll(1,true,false));require(key.poll(1,true,true));require(!key.poll(1,true,true));
        require(!key.poll(1,false,true));require(!key.poll(1,true,true));require(!key.poll(1,true,false));require(key.poll(1,true,true));
        require(!key.poll(2,true,true));require(!key.poll(2,true,false));require(key.poll(2,true,true));
        System.out.println("PASS: flight press edge, no repeat, focus/session release-to-arm");
    }
}
