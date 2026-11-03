package lab.owmcguest;

import java.util.UUID;

/** Pulse-only cursor: a same-pawn reader reset must not erase its idle baseline.
 * New identities and stale first samples still establish a baseline, never a bomb.
 */
public final class NativePulseGate {
    public record Scope(UUID owner,long source,long world,long model) {}
    private final NativeDeploymentGate gate=new NativeDeploymentGate();
    private Scope scope;
    private long observedWall;
    private static boolean valid(Scope s){return s!=null&&s.owner()!=null&&s.source()!=0&&s.world()!=0&&s.model()!=0;}
    public boolean bound(Scope next){return valid(next)&&next.equals(scope);}
    /** Called before NativeSessionGuard clears the freshly read locomotion owner. */
    public void prime(Scope next,long cast,long deploy,long now){
        if(!valid(next)||cast<0||deploy<0||now<0)return;
        if(bound(next))return;
        gate.reset();scope=next;observedWall=now;
        gate.observe(new NativeDeploymentGate.Scope(next.source(),next.world(),next.model()),cast,false,deploy,now);
    }
    public boolean observe(Scope next,long cast,boolean casting,long deploy,long now,boolean inputActive){
        if(!valid(next)||cast<0||deploy<0||now<0)return false;
        if(!bound(next)||now<observedWall||now-observedWall>800){
            reset();prime(next,cast,deploy,now);return false;
        }
        observedWall=now;
        // Foreground admits a new native Begin. A previously admitted Begin
        // can join its own Volley through a brief focus/ability-camera change.
        return gate.observe(new NativeDeploymentGate.Scope(next.source(),next.world(),next.model()),
                            cast,casting&&inputActive,deploy,now);
    }
    public void reset(){gate.reset();scope=null;observedWall=0;}
}
