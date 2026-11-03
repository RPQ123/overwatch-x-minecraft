package lab.owmcguest;

/** An observed native cast followed by its Volley, never a key or old logger row. */
public final class NativeDeploymentGate {
    public record Scope(long source,long world,long model){}
    private Scope scope;
    private long cast,deploy,pending,pendingWall;
    public boolean observe(Scope next,long castTick,boolean casting,long deployTick,long now){
        if(next==null||next.source()==0||next.world()==0||next.model()==0||castTick<0||deployTick<0){reset();return false;}
        if(!next.equals(scope)){
            scope=next;cast=castTick;deploy=deployTick;pending=pendingWall=0;return false;
        }
        if(castTick<cast||deployTick<deploy){cast=castTick;deploy=deployTick;pending=pendingWall=0;return false;}
        if(castTick>cast){
            cast=castTick;
            if(casting){pending=castTick;pendingWall=now;}
        }
        if(pending!=0&&(now<pendingWall||now-pendingWall>800))pending=0;
        if(deployTick<=deploy)return false;
        deploy=deployTick;
        if(pending==0||deployTick<pending||deployTick-pending>600)return false;
        pending=0;return true;
    }
    public void reset(){scope=null;cast=deploy=pending=pendingWall=0;}
}
