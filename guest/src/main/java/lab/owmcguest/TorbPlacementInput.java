package lab.owmcguest;

/** Edges are accepted only inside a fresh original preview. No animation-end
 * placement, held-click placement, repeat placement or cross-scope replay. */
public final class TorbPlacementInput {
    public enum Action{NONE,CONFIRM,CANCEL}
    private boolean initialized,ghost,closed,pending;private int previous;
    private long token;
    public Action sample(boolean valid,boolean nativeGhost,boolean ready,long nativeToken,int keys){
        if(!valid){reset();return Action.NONE;}
        if(!initialized){initialized=true;previous=keys;ghost=nativeGhost;token=nativeToken;return Action.NONE;}
        int edge=keys&~previous;previous=keys;
        if(!nativeGhost){ghost=false;closed=false;pending=false;token=nativeToken;return Action.NONE;}
        if(!ghost||nativeToken!=token){ghost=true;closed=false;pending=false;token=nativeToken;return Action.NONE;}
        if(closed||pending)return Action.NONE;
        if((edge&6)!=0){closed=true;return Action.CANCEL;} // Shift or native RMB
        if(ready&&(edge&1)!=0){pending=true;return Action.CONFIRM;}
        return Action.NONE;
    }
    public boolean preview(){return initialized&&ghost&&!closed&&!pending;}
    public void confirmed(boolean accepted){pending=false;if(accepted)closed=true;}
    public void reset(){initialized=ghost=closed=pending=false;previous=0;token=0;}
}
