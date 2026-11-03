package lab.owmcguest;
import lab.owmcguest.NativeShotProtocol.Vec;
public final class LoadedRayPrefixCheck {
    static void check(boolean b){if(!b)throw new AssertionError();}
    public static void main(String[] args){
        var a=new Vec(1,50,1);var clip=LoadedRayPrefix.clip(a,new Vec(181,50,1),(x,z)->x<8);
        check(!clip.complete()&&clip.fraction()*180>126.999&&clip.fraction()*180<127);
        check(clip.fraction()*180>6); // a six-block target remains in the query
        check(LoadedRayPrefix.clip(a,new Vec(7,50,1),(x,z)->true).complete());
        clip=LoadedRayPrefix.clip(a,new Vec(-181,50,1),(x,z)->x>=-8);check(!clip.complete()&&1-clip.fraction()*182>-128);
        check(LoadedRayPrefix.clip(a,new Vec(1,500,1),(x,z)->true).complete());
        clip=LoadedRayPrefix.clip(new Vec(15.99,0,16.01),new Vec(16.01,0,15.99),(x,z)->x!=1||z!=0);check(!clip.complete());
        check(LoadedRayPrefix.clip(a,new Vec(181,50,1),(x,z)->false).fraction()==0);
        System.out.println("PASS: loaded ray prefix preserves near hits, positive/negative/vertical/corner and unavailable-start guards");
    }
}
