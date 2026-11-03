package lab.owmcguest;

public final class NativeRollCheck {
    private static void require(boolean ok,String message){if(!ok)throw new AssertionError(message);}
    public static void main(String[] args){
        var phase=new NativeRollPhase();
        require(!phase.observe(1,1,10,true,15,.4,0),"Attaching mid-roll cannot start movement");
        require(phase.step(0)==0,"No historical roll replay");
        phase.observe(1,1,20,false,15,.4,100);
        require(phase.observe(1,1,100,true,15,.4,200),"Fresh native Begin");
        double sum=0;
        for(int tick=0;tick<9;tick++){
            phase.observe(1,1,100,true,15,.4,200+tick*50);
            sum+=phase.step(200+tick*50);
        }
        require(Math.abs(sum-6)<1e-6,"Original 15m/s x .4s distance ceiling");
        require(!phase.observe(1,1,500,false,15,.4,650),"End timestamp is not another Begin");
        require(phase.step(650)==0,"Original End stops movement");
        phase.observe(1,1,600,true,15,.4,700);require(phase.step(801)==0,"Stale native observation cannot move");
        require(!phase.observe(1,2,700,true,15,.4,850)&&phase.step(850)==0,"Changed model cannot replay an existing roll");
        phase.observe(1,2,800,false,15,.4,900);phase.observe(1,2,900,true,15,.4,950);
        phase.invalidate();require(phase.step(950)==0,"Reader failure cancels roll");
        require(!phase.observe(1,2,900,true,15,.4,960)&&phase.step(960)==0,"Same Begin cannot restart after invalidation");
        phase.invalidate();require(!phase.observe(1,2,950,true,15,.4,970)&&phase.step(970)==0,"A roll begun while disconnected cannot be replayed on reconnect");
        double[] forward=NativeRollPhase.direction(0,false),back=NativeRollPhase.direction(2,true),diagonal=NativeRollPhase.direction(9,true);
        require(forward[0]==0&&forward[1]==1&&back[1]==-1,"Original fallback and backward branch");
        require(Math.abs(Math.hypot(diagonal[0],diagonal[1])-1)<1e-9,"Diagonal does not gain speed");
        require(NativeRollPhase.direction(3,true)==null,"Unknown/missing original throttle must not guess forward");
        var suppressed=new NativeRollPhase();suppressed.observe(1,1,1,false,15,.4,100);
        require(suppressed.observe(1,1,2,true,15,.4,200),"admitted roll before firing lock");
        suppressed.discardMotion();require(suppressed.step(200)==0,"lock consumes remaining roll displacement");
        require(!suppressed.observe(1,1,2,true,15,.4,220)&&suppressed.step(220)==0,"unlock cannot replay the same still-active Begin");
        suppressed.observe(1,1,3,false,15,.4,240);require(suppressed.observe(1,1,4,true,15,.4,260)&&suppressed.step(260)>0,"a genuinely later roll remains usable");
        System.out.println("PASS: original roll phase, stale/owner/End guards, distance ceiling and directional normalization");
    }
}
