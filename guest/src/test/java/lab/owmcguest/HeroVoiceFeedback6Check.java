package lab.owmcguest;

/** 语音挂接：不启动游戏，验证变形Begin/End与死神原版/认证回执的实际播放去重边界。 */
public final class HeroVoiceFeedback6Check {
    private static void check(boolean ok,String what){if(!ok)throw new AssertionError(what);}
    public static void main(String[] args){
        var gate=new UltimateCalloutGate();
        check(!gate.observe(1,2,3,4,0),"baseline before transform");
        check(gate.observe(1,2,3,4,60848),"transform Begin must speak before Tank62348");
        check(!gate.observe(1,2,3,4,0)&&!gate.observe(1,2,3,4,60848),"End/old active cannot repeat");
        var raw=new UltimateCalloutGate();var fallback=new UltimateCalloutGate();var cooldown=new HeroVoiceSkillCooldowns();
        check(!raw.observe(1,2,3,4,0)&&!fallback.observe(1,2,3,4,0),"separate native/runtime baselines");
        check(raw.observe(1,2,3,4,100)&&cooldown.admit("reaper","ult_cast",1000),"native animation Begin");cooldown.played("reaper","ult_cast",1000);
        check(fallback.observe(1,2,3,4,105)&&!cooldown.admit("reaper","ult_cast",1050),"later same-cast server receipt cannot double-play");
        check(!raw.observe(1,2,3,5,100)&&!fallback.observe(1,2,3,5,105),"world change cannot replay an ongoing cast");
        check(HeroVoicePolicy.fixedHash("reaper","ult_cast").equals("a81b42c757722f46f7e007d3916caa1f"),"fixed verified Chinese callout");
        check(!HeroVoiceDefaultCatalog.allowed("reaper","ult_cast",HeroVoicePolicy.REAPER_ULT_HASH),"legacy-owned Q must not duplicate into generic bank");
        check(!HeroVoicePolicy.clipAllowed("reaper","ult_cast","b031608e8fc727950f02d2590d05f48c"),"unconfirmed English slot forbidden");
        check(HeroVoicePolicy.legacyOwned(2,"ult_cast"),"only existing Early owner plays Reaper Q");
        System.out.println("PASS: transform Begin, same-cast native/runtime dedup, world baseline, fixed verified Chinese callout/no unconfirmed English");
    }
}
