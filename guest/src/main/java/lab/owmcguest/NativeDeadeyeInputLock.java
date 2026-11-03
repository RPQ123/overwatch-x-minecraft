package lab.owmcguest;

import java.nio.ByteBuffer;
import java.nio.ByteOrder;

/** Scoped read-only native-fire proof. It cannot start a cast or apply damage. */
public record NativeDeadeyeInputLock(long source,long model,long world,long begin,long script,long logger,long observed) {
    public static final int MAGIC=0x31594544;
    public boolean matches(long currentSource,long currentModel,long currentWorld,long now){
        return source!=0&&model>0&&model<=0xffffffffL&&world!=0&&begin>0
            &&source==currentSource&&model==currentModel&&world==currentWorld
            &&script>=0x10000&&script<=0x7fffffffffffL&&logger>=0x10000&&logger<=0x7fffffffffffL
            &&observed>0&&now>=observed&&now-observed<=150;
    }
    /** Optional OWBODY01 tail; old consumers ignore it, inactive writes clear it. */
    public static void write(ByteBuffer body,NativeDeadeyeInputLock state){
        write(body,state,true);
    }
    public static void write(ByteBuffer body,NativeDeadeyeInputLock state,boolean capability){
        if(body.capacity()<232||body.order()!=ByteOrder.LITTLE_ENDIAN)throw new IllegalArgumentException("Deadeye body extension layout");
        for(int at=176;at<232;at+=4)body.putInt(at,0);
        if(!capability)return; // cap0 retains the exact legacy all-zero tail.
        body.putInt(176,MAGIC);body.putInt(180,state==null?0:1);
        if(state!=null){body.putInt(184,(int)state.model());body.putLong(192,state.begin());body.putLong(200,state.script());
            body.putLong(208,state.logger());body.putLong(216,state.observed());body.putLong(224,state.world());}
    }
}
