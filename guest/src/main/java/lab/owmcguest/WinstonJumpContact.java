package lab.owmcguest;

/** Server-observed landing can precede the native CD ACK after prediction.
 * Cache the real contact; release it once only after the matching receipt. */
public final class WinstonJumpContact {
    private long intent,receipt,landedAt;private int ticks;private boolean airborne,done;
    private NativeShotProtocol.Vec landing;
    public void begin(long id){if(id<=0||id==intent)return;reset();intent=id;}
    public void confirm(long id,long sequence){if(id==intent&&sequence>0)receipt=sequence;}
    public void sample(boolean grounded,NativeShotProtocol.Vec at,long now){
        if(intent==0||landing!=null||done)return;
        if(++ticks>120){reset();return;}
        if(!grounded)airborne=true;
        else if(airborne){landing=at;landedAt=now;}
    }
    public NativeShotProtocol.Vec take(long now){
        if(landing==null||receipt==0||done)return null;
        done=true;return now>=landedAt&&now-landedAt<=1000?landing:null;
    }
    public boolean active(){return intent>0&&landing==null&&!done;}
    public boolean confirmed(){return receipt>0;}
    public long intent(){return intent;}
    public void reset(){intent=receipt=landedAt=0;ticks=0;airborne=done=false;landing=null;}
}
