package lab.owmcguest;

import net.minecraft.client.MinecraftClient;
import net.minecraft.client.sound.PositionedSoundInstance;

/** 语音挂接：所有新旧入口共用唯一人声；仅停止本声道自己持有的声音。 */
final class HeroVoiceChannel {
    private static PositionedSoundInstance current;
    private static long started,deadline;
    private static int rank;
    static final HeroVoiceSkillCooldowns skillCooldowns=new HeroVoiceSkillCooldowns(); // 语音挂接：不可随reset清零。
    static long preempted,refused;
    static String owner="",event="";
    private HeroVoiceChannel() {}
    static boolean busy(MinecraftClient client){
        if(current==null)return false;
        long now=System.nanoTime();
        if(now>deadline||now-started>350_000_000L&&!client.getSoundManager().isPlaying(current)){reset(client);return false;}
        return true;
    }
    static boolean play(MinecraftClient client,PositionedSoundInstance sound,String nextOwner,String nextEvent,long durationMs){
        // 语音挂接：最后一道播放准入，旧入口也不能绕过全英雄清退规则。
        int next=HeroVoicePolicy.priority(nextEvent);if(!HeroVoicePolicy.allowed(nextEvent)||next==0)return false;
        if(nextEvent.equals("select")&&!HeroVoicePolicy.selectionAllowed(HeroVoicePolicy.heroName(NativeLocomotionController.INSTANCE.hero())))return false;
        String hero=HeroVoicePolicy.heroName(NativeLocomotionController.INSTANCE.hero());
        if(!skillCooldowns.admit(hero,nextEvent,System.nanoTime()/1_000_000))return false;
        if(busy(client)){
            if(!HeroVoicePolicy.interrupts(nextEvent)){refused++;return false;} // 语音挂接：技能/选人/击杀彼此不抢占。
            client.getSoundManager().stop(current);preempted++;
        }
        current=sound;rank=next;owner=nextOwner;event=nextEvent;started=System.nanoTime();deadline=started+(Math.max(500,durationMs)+1000)*1_000_000L;
        client.getSoundManager().play(sound);
        skillCooldowns.played(hero,nextEvent,System.nanoTime()/1_000_000);return true;
    }
    static boolean playing(MinecraftClient client){return current!=null&&client.getSoundManager().isPlaying(current);}
    static void reset(MinecraftClient client){if(current!=null)client.getSoundManager().stop(current);current=null;rank=0;owner=event="";started=deadline=0;}
}
