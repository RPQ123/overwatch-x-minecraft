package lab.owmcguest;

/** 语音挂接：独立英雄/事件、10秒边界、成功播放才开始计时。纯离线，不连接游戏。 */
public final class HeroVoiceSkillCooldownCheck {
    private static void check(boolean value,String what){if(!value)throw new AssertionError(what);}
    public static void main(String[] args){
        var c=new HeroVoiceSkillCooldowns();
        check(c.admit("hanzo","ult_cast",0),"first cast admitted");
        check(c.admit("hanzo","ult_cast",1),"admission alone must not reserve cooldown");
        c.played("hanzo","ult_cast",1);
        check(!c.admit("hanzo","ult_cast",10000)&&c.remaining("hanzo","ult_cast",10000)==1,"9999ms blocked");
        check(c.admit("hanzo","ult_cast",10001),"10000ms admitted");
        check(c.admit("hanzo","ability:scatter_arrow",2),"different skill independent");
        check(c.admit("mei","ult_cast",2),"different hero independent");
        c.played("hanzo","ability:scatter_arrow",2);
        check(!c.admit("hanzo","ability:scatter_arrow",3),"ability cooldown");
        check(!c.admit("hanzo","ult_cast",3),"other skill did not clear ult cooldown");
        c.played("mei","ult_cast",3);
        check(!c.admit("mei","ult_cast",4),"second hero has own cooldown");
        check(c.admit("hanzo","select",3)&&c.admit("hanzo","kill",3),"selection/kill use their own policies");
        check(HeroVoicePolicy.cooldownMs("ability:ice_wall")==10000&&HeroVoicePolicy.cooldownMs("ult_cast")==10000,"all skill policies aligned");
        check(c.active(4).size()==3&&c.suppressed().get("hanzo:ult_cast")==2,"diagnostics per hero/event");
        check(!c.admit("hanzo","ult_cast",0),"clock regression never bypasses cooldown");
        System.out.println("PASS: per-hero/event skill cooldown, 9999/10000ms boundary, success-only timer, independent events, diagnostics");
    }
}
