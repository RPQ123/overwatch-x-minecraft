package lab.owmcguest;

/** W5 prediction is movement only. Damage/audio still require the native CD ACK.
 * A native cast or late ACK repairs a missed key sample without a second leap. */
public final class WinstonJumpLaunch {
    private boolean inputBaseline,held;
    private long serial,intent,created,nativeToken,lastNative,receipt,applied,committed;
    public boolean input(boolean down,boolean permitted,boolean ready,long now){
        if(!permitted){inputBaseline=false;held=false;return false;}
        if(!inputBaseline){inputBaseline=true;held=down;return false;}
        boolean edge=down&&!held;held=down;
        if(!edge||!ready||waiting(now))return false;
        begin(now);return true;
    }
    private void begin(long now){intent=++serial;created=now;nativeToken=receipt=0;}
    public boolean waiting(long now){return intent>0&&receipt==0&&now>=created&&now-created<(nativeToken==0?600:1000);}
    public boolean nativeCast(long token,long now){
        if(token<=0||token<=lastNative)return false;lastNative=token;
        if(intent==0||nativeToken!=0||now<created||now-created>1000)begin(now);
        nativeToken=token;return needsLaunch();
    }
    public void confirm(long sequence,long token,long now){
        if(sequence<=0||token<=0||sequence==committed)return;
        if(intent==0||nativeToken!=0&&nativeToken!=token)begin(now);
        nativeToken=token;lastNative=Math.max(lastNative,token);receipt=sequence;
    }
    public boolean needsLaunch(){return intent>0&&applied!=intent;}
    public void launched(){if(intent>0)applied=intent;}
    public long takeCommit(){
        if(receipt<=0||applied!=intent||receipt==committed)return 0;
        committed=receipt;return receipt;
    }
    public long created(){return created;}
    public long token(){return nativeToken;}
    public long intent(){return intent;}
    public void revokeInput(){inputBaseline=false;held=false;}
    public void reset(){inputBaseline=held=false;serial=intent=created=nativeToken=lastNative=receipt=applied=committed=0;}
}
