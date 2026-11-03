package lab.owmcguest;

/** Selection is a confirmed hero change, not a dimension/model rebind or hover. */
public final class HeroSelectCalloutGate {
    public static final long DELAY_MS=500; // 语音挂接：确认选人后等待0.5秒。
    private long source,hero,due,lastDelay;private boolean pending;
    public boolean observe(long source,long hero,boolean confirmed,long nowMs){
        if(!confirmed||source==0||hero==0){cancelPending();return false;}
        boolean changed=source!=this.source||hero!=this.hero;
        if(changed){this.source=source;this.hero=hero;due=nowMs+DELAY_MS;pending=true;return false;}
        if(pending&&nowMs>=due){pending=false;lastDelay=nowMs-due+DELAY_MS;return true;}
        return false;
    }
    public void cancelPending(){pending=false;}
    public boolean pending(){return pending;} // 语音挂接：选人等待期间不准入技能喊话。
    public long lastDelayMs(){return lastDelay;}
}
