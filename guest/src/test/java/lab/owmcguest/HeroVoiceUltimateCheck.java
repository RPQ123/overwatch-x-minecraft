package lab.owmcguest;

/** 语音挂接：真实充满边沿、抢占规则、已恢复白名单，无游戏依赖。 */
public final class HeroVoiceUltimateCheck {
    private static void check(boolean ok,String what){if(!ok)throw new AssertionError(what);}
    public static void main(String[] args){
        var meter=new HeroVoicePolicy.Meter();
        check(!meter.observe(100,100),"initial full/rebind cannot claim a new full cycle");
        check(!meter.observe(99,100)&&meter.observe(100,100),"99 to 100 is a real full transition");
        check(!meter.observe(100,100)&&!meter.observe(100,100),"held full speaks once");
        check(!meter.observe(99.99,100)&&meter.observe(100,100),"next cycle has no arbitrary time/90percent requirement");
        check(!meter.observe(0,100)&&!meter.observe(50,100)&&meter.observe(100,100),"normal drained/recharged cycle");
        check(!meter.observe(Double.NaN,100)&&!meter.observe(100,100),"invalid read resets baseline rather than replaying full");
        check(!meter.observe(99,100)&&!meter.observe(200,200),"cost/form change establishes baseline");
        meter.reset();check(!meter.observe(100,100),"new hero/world full is silent");
        for(String event:new String[]{"ult_cast","ult_ready"}){
            check(HeroVoicePolicy.allowed(event)&&HeroVoicePolicy.interrupts(event),"critical voice can preempt any voice");
            for(String lower:new String[]{"select","ability:ice_wall","kill","multikill"})
                check(HeroVoicePolicy.priority(event)>HeroVoicePolicy.priority(lower),"both ultimate announcements are highest");
        }
        for(String event:new String[]{"select","ability:ice_wall","kill","multikill"})
            check(!HeroVoicePolicy.interrupts(event),"ordinary voice cannot interrupt even a lower-ranked one");
        check(HeroVoicePolicy.priority("ult_cast")>HeroVoicePolicy.priority("ult_ready"),"same-frame Q takes precedence over readiness");
        check(HeroVoicePolicy.cooldownMs("ult_cast")==10000&&HeroVoicePolicy.cooldownMs("ult_ready")==0,"Q cooldown retained; readiness is edge-only");
        check(!HeroVoicePolicy.selectionAllowed("bastion")&&!HeroVoicePolicy.selectionAllowed("tracer"),"muted selections retained");
        check(HeroVoiceDefaultCatalog.allowed("bastion","ult_cast","5a449ed346d47a7e0180fdda14770b6e"),"Bastion Q exception restored");
        check(HeroVoiceDefaultCatalog.allowed("bastion","ult_ready","337a98557c065b741efa89f5c1800c97"),"Bastion official electronic ready cue restored");
        check(HeroVoiceDefaultCatalog.allowed("tracer","ult_ready","3844cff1fcc089365aa1690433a8eda4"),"muted selection cannot mute ready/Q");
        check(!HeroVoiceDefaultCatalog.allowed("bastion","jump","5a449ed346d47a7e0180fdda14770b6e"),"restored cue cannot be retagged as movement");
        System.out.println("PASS: exact full-cycle edges, only critical voices preempt, 10s Q cooldown, Bastion/Tracer event-specific restoration");
    }
}
