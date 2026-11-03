package lab.owmcguest;

import java.util.Random;

/** 语音挂接：MC真实击杀才抽样；连杀保底在实际播出后结算，不绕过原冷却/声道。 */
public final class HeroVoiceKillGate {
    public static final double SINGLE_KILL_CHANCE=.35;
    public static final int GUARANTEE_KILLS=3;
    public static final long STREAK_GAP_MS=8000;
    public static final long COOLDOWN_MS=10000; // 语音挂接：所有英雄、击杀/多杀共用硬冷却。
    private long lastKill=-1;
    private long lastSpoken=-1;
    private int streak;
    public long rolls,randomAccepted,randomSkipped,guarantees,played,expired,cooldownSuppressed;
    public long cooldownRemainingMs(long now){return lastSpoken<0?0:Math.max(0,COOLDOWN_MS-Math.max(0,now-lastSpoken));}
    public boolean canSpeak(long now){return cooldownRemainingMs(now)==0;}
    public boolean observe(long now,Random random){
        // 语音挂接：冷却内不抽样、不累计连杀、不补播旧击杀。
        if(!canSpeak(now)){cooldownSuppressed++;return false;}
        expire(now);
        lastKill=now;streak++;
        if(streak>=GUARANTEE_KILLS)return true;
        rolls++;
        if(random.nextDouble()<SINGLE_KILL_CHANCE){randomAccepted++;return true;}
        randomSkipped++;return false;
    }
    public boolean pending(long now){expire(now);return canSpeak(now)&&streak>=GUARANTEE_KILLS;}
    public int streak(){return streak;}
    public void played(long now){
        if(!canSpeak(now))return;
        boolean guaranteed=pending(now);
        played++;
        if(guaranteed)guarantees++;
        lastSpoken=now;reset();
    }
    private void expire(long now){
        // 语音挂接：8秒只限定连杀累计；已赚取的保底等待原冷却/高优先级结束，不自行吞掉。
        if(lastKill>=0&&(now<lastKill||streak<GUARANTEE_KILLS&&now-lastKill>STREAK_GAP_MS)){
            if(streak>=GUARANTEE_KILLS)expired++;
            streak=0;lastKill=-1;
        }
    }
    public void reset(){streak=0;lastKill=-1;} // 语音挂接：切人/死亡只取消累计，不能重置10秒硬冷却。
}
