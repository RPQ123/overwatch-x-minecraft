package lab.owmcguest;

import java.util.UUID;

public final class RecallSoundGateCheck {
    private static int checks;
    private static void require(boolean v,String why){checks++;if(!v)throw new AssertionError(why);}
    public static void main(String[] args){
        var g=new RecallSoundGate();var s=new RecallSoundGate.Scope(new UUID(0,1),2,3,4);
        require(g.claim(s,100),"authenticated native Begin gets its start sound");
        require(!g.claim(s,100),"same-frame reread does not double sound");
        require(!g.claim(s,99),"older Begin is not replayed");
        require(!g.claim(s,0),"inactive zero is silent");
        require(!g.claim(s,100),"same-scope observer reset cannot replay a completed Begin");
        require(g.claim(s,200),"later actual Recall sounds once");
        require(!g.claim(s,200),"server finish/receipt retry is not a second cue");
        require(g.claim(new RecallSoundGate.Scope(new UUID(0,1),2,3,5),100),"new model owns its own actual Begin");
        require(!g.claim(new RecallSoundGate.Scope(new UUID(0,1),2,0,5),100),"unknown source is silent");
        require(!g.claim(null,100),"missing scope is silent");
        System.out.println("RecallSoundGateCheck: "+checks+" checks passed");
    }
}
