package lab.owmcguest;

import lab.owmcguest.NativeShotProtocol.Vec;

/** Left-palm presentation only. Reference poses come from the saved original
 * native hand animation, not the gun muzzle or a server collision origin.
 * This is a screen-pose adapter, not native bone evaluation. */
public final class RoadhogHookPresentation {
    private String id;private long castWall;private Vec first,frozenHand;
    public void begin(String next,long wall){id=next;castWall=wall;first=frozenHand=null;}
    public void clear(){id=null;castWall=0;first=frozenHand=null;}
    public static MuzzlePresentation.Profile profile(long phaseMs){
        // Original1920x1080 grip references: extended ~595,751; raised ~384,583.
        double t=Math.clamp((phaseMs-180)/100.,0,1);t=t*t*(3-2*t);
        return new MuzzlePresentation.Profile("Roadhog left palm/reference",-.38-.22*t,-.39+.31*t,.65,4);
    }
    public Vec hand(String next,Vec camera,MuzzlePresentation.Basis basis,double fov,double aspect,long now){
        long phase=next.equals(id)?Math.max(0,now-castWall):0;
        return camera.add(MuzzlePresentation.offset(profile(phase),basis,fov,aspect));
    }
    private static double distance(Vec a,Vec b){return Math.sqrt(a.subtract(b).lengthSquared());}
    public Vec position(String next,Vec actual,Vec hand,Vec eye,String stage){
        if(!next.equals(id))return actual;
        if("RETURN".equals(stage)){
            double t=Math.clamp(distance(actual,eye)/4,0,1);t=t*t*(3-2*t);
            return hand.add(actual.subtract(hand).multiply(t));
        }
        if(!"OUT".equals(stage))return actual; // An attached head stays on its real target.
        if(first==null){first=actual;frozenHand=hand;}
        double t=Math.clamp(distance(actual,first)/4,0,1);t=t*t*(3-2*t);
        return actual.add(frozenHand.subtract(first).multiply(1-t));
    }
}
