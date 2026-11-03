package lab.owmcguest;

/** 语音挂接：起落直接删除、原版消息边沿去重；无游戏/声音引擎依赖。 */
public final class HeroVoiceMovementCheck {
    private static void check(boolean ok,String what){if(!ok)throw new AssertionError(what);}
    public static void main(String[] args){
        for(String event:new String[]{"jump","landing","takeoff","effort","movement:jump","movement:land",
            "ability:jump","ability:jump_jet","ability:double_jump","ability:super_jump","ability:leap","ability:wall_climb","ability:landing"})
            check(!HeroVoicePolicy.allowed(event),"movement event cannot be restored: "+event);
        for(String sound:new String[]{"entity.player.small_fall","entity.player.big_fall"})
            check(HeroVoicePolicy.movementSound("minecraft",sound,"PLAYERS"),"player landing removed");
        check(!HeroVoicePolicy.movementSound("minecraft","entity.player.hurt","PLAYERS"),"combat hurt independent; fall DamageSource handled separately");
        check(!HeroVoicePolicy.movementSound("minecraft","block.stone.step","PLAYERS"),"footsteps unchanged");
        check(!HeroVoicePolicy.movementSound("minecraft","entity.player.small_fall","NEUTRAL"),"other sound category not muted");
        check(HeroVoicePolicy.movementSound("owmcguest","private.jump.grunt","VOICE"),"mapped movement grunt removed");
        check(!HeroVoicePolicy.movementSound("owmcguest","hero.hanzo.ult_cast","VOICE"),"ult voice retained");
        check(!HeroVoicePolicy.movementSound("owmcguest","hanzo.arrow.release","PLAYERS"),"weapon sound retained");
        check(!HeroVoicePolicy.movementSound("othermod","landing","PLAYERS"),"unrelated mods untouched");
        var edges=new HeroVoicePolicy.Edges();
        check(!edges.newer("castBegin",16048),"historical entry is baseline");
        check(edges.newer("castBegin",18928),"instant finished entry still triggers on new native timestamp");
        check(!edges.newer("castBegin",18928),"same entry cannot trigger during the following charge/release");
        check(!edges.newer("castBegin",0),"state regression silent");
        edges.clear();check(!edges.newer("castBegin",18928),"world/model rebind cannot replay old cast");
        System.out.println("PASS: movement removed, fall-only filter, skill/footstep guards, Hanzo message timestamp edge");
    }
}
