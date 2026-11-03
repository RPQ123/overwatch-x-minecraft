package lab.owmcguest;

/** Deduplicates the native teleport stream. Owner/world changes reset externally. */
final class NativeBlinkPhase {
    private double[] previous;private long captures,action;
    double[] observe(double[] total,long nextCaptures,long nextAction){
        if(previous==null||nextCaptures<captures){previous=total.clone();captures=nextCaptures;action=nextAction;return null;}
        double x=total[0]-previous[0],z=total[2]-previous[2];long count=nextCaptures-captures;
        previous=total.clone();captures=nextCaptures;
        if(count==0)return null;
        boolean fresh=nextAction>0&&nextAction!=action;action=nextAction;
        // Never combine several differently directed teleports after a long
        // client stall into a straight sweep through unknown terrain.
        if(!fresh||count!=1||!Double.isFinite(x)||!Double.isFinite(z)||x*x+z*z<4||x*x+z*z>64)return null;
        return new double[]{x,0,z};
    }
    void reset(){previous=null;captures=action=0;}
}
