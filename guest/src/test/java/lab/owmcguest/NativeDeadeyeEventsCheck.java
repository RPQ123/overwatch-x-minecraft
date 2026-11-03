package lab.owmcguest;
public final class NativeDeadeyeEventsCheck {
    private static void check(boolean b,String m){if(!b)throw new AssertionError(m);}
    public static void main(String[] args){
        var g=new NativeDeadeyeEvents();
        check(!g.observe(1,2,3,10,true,11).fire(),"mid-Q first read is a baseline");
        g.observe(1,2,3,10,false,11);
        check(g.observe(1,2,3,20,true,11).started(),"new native activation admits Q");
        check(!g.firing(),"charging remains movable/lookable");
        check(!g.observe(1,2,3,20,true,11).fire(),"charging alone cannot shoot");
        check(g.observe(1,2,3,20,true,25).fire(),"actual later native fire action shoots");
        check(g.firing(),"native confirmed fire enters control lock");
        check(!g.observe(1,2,3,20,true,25).fire(),"persistent action cannot replay");
        check(g.firing(),"lock persists between acknowledged shots until original End");
        var completed=new NativeDeadeyeEvents();
        completed.observe(1,2,3,10,false,11);
        completed.observe(1,2,3,20,true,11);
        check(completed.observe(1,2,3,20,true,25).fire()&&completed.firing(),"completed cast has an actual firing latch");
        check(!completed.observe(1,2,3,20,false,25).fire()&&!completed.firing(),"root End releases an already firing cast without replay");
        check(!completed.observe(1,2,3,20,false,25).fire()&&!completed.firing(),"persistent End remains released");
        check(!g.observe(1,2,4,20,true,25).fire(),"dimension transition establishes fresh baseline");
        check(!g.firing(),"old-world control lock cannot cross a dimension");
        g.observe(1,2,4,20,false,25);g.observe(1,2,4,30,true,25);
        check(!g.observe(1,2,4,30,false,25).fire(),"cancel/expiry never shoot");
        check(!g.firing(),"original End releases control lock");
        check(!g.observe(1,9,4,2,true,40).fire(),"new native model discards departed actions");
        g.reset();check(!g.observe(1,9,4,50,true,55).fire(),"lost reader/session cannot replay a current Q");
        check(!g.firing(),"reader reset cannot adopt old fire as a control lock");
        System.out.println("PASS: Deadeye native Begin/fire, baseline, cancel/expiry, replay, world/model/reset guards");
    }
}
