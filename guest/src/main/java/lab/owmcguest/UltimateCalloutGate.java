package lab.owmcguest;

/** A new binding establishes a baseline; only a later native begin edge speaks. */
public final class UltimateCalloutGate {
    private long session,source,model,world,begin;private boolean bound;
    public boolean observe(long session,long source,long model,long world,long begin){
        if(!bound||this.session!=session||this.source!=source||this.model!=model||this.world!=world){
            bound=true;this.session=session;this.source=source;this.model=model;this.world=world;this.begin=begin;return false;
        }
        // Inactive graph nodes read as zero. Retain the last actual begin tick
        // so an End/temporary zero followed by that old node cannot replay it.
        boolean edge=begin>this.begin;this.begin=Math.max(this.begin,begin);return edge;
    }
    public void reset(){bound=false;}
}
