package lab.owmcguest;

import java.util.Random;

/** 语音挂接：离线验证概率/保底状态机与清退准入，不启动任何游戏。 */
public final class HeroVoiceFeedbackCheck {
    private static void check(boolean ok,String what){if(!ok)throw new AssertionError(what);}
    public static void main(String[] args){
        var edges=new HeroVoicePolicy.Edges();
        check(!edges.newer("concussive",null,true),"initial empty report is silent");
        check(edges.newer("concussive",1L,false),"first real detonation must speak");
        check(!edges.newer("concussive",1L,false),"same detonation deduplicated");
        check(!edges.newer("concussive",null,true),"missing report cannot overwrite established baseline");
        check(!edges.newer("concussive",1L,false)&&edges.newer("concussive",2L,false),"next detonation exactly once");
        edges.clear();check(!edges.newer("concussive",9L,false),"hero/world rebind with existing counter stays silent");
        check(!edges.newer("concussive",null,false)&&edges.newer("concussive",10L,false),"failed report retains baseline");
        var miss=new Random(){@Override public double nextDouble(){return .999;}};
        var gate=new HeroVoiceKillGate();
        check(!gate.observe(0,miss),"first miss");check(!gate.observe(1000,miss),"second miss");
        check(gate.observe(2000,miss)&&gate.pending(2000),"third kill guarantees");
        check(gate.pending(6500)&&gate.pending(6501)&&gate.streak()==3,"refused/cooldown cannot consume guarantee");
        gate.played(6501);check(!gate.pending(6502)&&gate.streak()==0&&gate.guarantees==1,"actual playback settles exactly once");
        gate.played(6503);check(gate.guarantees==1,"no duplicate settlement");
        long rolls=gate.rolls;
        for(long now:new long[]{7000,8000,9000})check(!gate.observe(now,miss)&&!gate.pending(now),"cooldown blocks all kill rolls/guarantees");
        check(gate.cooldownSuppressed==3&&gate.rolls==rolls&&gate.streak()==0,"cooldown cannot accumulate a delayed guarantee");
        gate.reset();check(!gate.canSpeak(16500)&&gate.cooldownRemainingMs(16500)==1,"hero/world/death reset cannot bypass cooldown");
        check(gate.canSpeak(16501),"10000ms boundary opens exactly");
        check(!gate.pending(16501),"no delayed cooldown kills at expiry");
        gate.observe(16501,miss);gate.observe(17000,miss);gate.observe(18000,miss);
        check(gate.pending(30000),"earned guarantee survives long higher-priority voice");
        gate.reset();check(!gate.pending(30001),"life/scope reset cancels pending guarantee");
        var gap=new HeroVoiceKillGate();gap.observe(0,miss);gap.observe(8001,miss);check(gap.streak()==1,"long gap resets streak");
        check(!gap.pending(7000)&&gap.streak()==0,"clock regression resets");
        var sample=new HeroVoiceKillGate();var random=new Random(20261026);int accepted=0;
        for(int i=0;i<100000;i++){sample.reset();if(sample.observe(i,random))accepted++;}
        check(accepted>34000&&accepted<36000,"single-kill probability");
        for(String event:new String[]{"pain","death","respawn","jump","effort","idle","reload","ult_charge","healing_request","comm","status:healed","status:slowed","sfx:dragon_roar","ability:blink","ability:recall","ability:grappling_hook"})
            check(!HeroVoicePolicy.allowed(event),"removed event: "+event);
        check(!HeroVoicePolicy.selectionAllowed("tracer")&&!HeroVoicePolicy.selectionAllowed("bastion")&&HeroVoicePolicy.selectionAllowed("mei"),"muted selections");
        check(HeroVoicePolicy.priority("ult_cast")>HeroVoicePolicy.priority("ability:ice_wall")&&HeroVoicePolicy.priority("ability:ice_wall")>HeroVoicePolicy.priority("kill"),"retained priorities");
        check(HeroVoicePolicy.cooldownMs("kill")==10000&&HeroVoicePolicy.cooldownMs("multikill")==10000,"shared hard cooldown");
        check(HeroVoicePolicy.fixedHash("hanzo","ult_cast").equals("ea38b68ebfa92aaa527c958f81edcb31"),"fixed Hanzo Japanese reference slice");
        check(HeroVoiceDefaultCatalog.allowed("hanzo","ult_cast",HeroVoicePolicy.HANZO_ULT_HASH),"fixed Hanzo clip retained");
        check(!HeroVoicePolicy.clipAllowed("hanzo","ult_cast","b3faba0b762d856fb3ab72218a8c87f4"),"friendly Hanzo alternate cannot play from stale manifest");
        check(!HeroVoicePolicy.clipAllowed("hanzo","ult_cast","041b1e23a19cb344ff2dba19428da7ec"),"confirmed Chinese entry cannot play");
        check(!HeroVoiceDefaultCatalog.allowed("hanzo","ult_cast","b3faba0b762d856fb3ab72218a8c87f4"),"alternate removed from default manifest");
        check(!HeroVoiceDefaultCatalog.allowed("tracer","ability:blink","eb941a93"),"stale manifest cannot restore blink");
        check(!HeroVoiceDefaultCatalog.allowed("mei","ability:ice_wall","00000000000000000000000000000000"),"unknown clip rejected");
        System.out.println("PASS: kill chance="+accepted+"/100000, strict 10000ms cooldown/hero-reset guard/no backlog, guarantee, fixed Hanzo clip, first-cast edge");
    }
}
