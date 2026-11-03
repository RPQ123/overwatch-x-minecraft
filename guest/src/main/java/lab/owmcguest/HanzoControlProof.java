package lab.owmcguest;

import java.nio.*;
import java.util.*;

/** MC adaptation requested by the user: suppress movement/look for the original Q cast. */
public final class HanzoControlProof {
    public static final long HERO=0x02e0000000000005L;
    public static final int MAGIC=0x325a4e48; // HNZ2 rejects the old HNZ1 free-camera DLL.
    public record Scope(UUID owner,int pid,long source,long world,long model){}
    public record Request(Scope scope,long observed,long frame,long begin){}
    public record Phase(long tick,boolean active){}
    private Scope scope;private long frame,frameWall,lastTick=-1,begin,startedWall,endedWall,releasedWall,nativeEnd;
    private boolean gameplay,locked,shot;private String reason="idle";private long lastDuration,lastGood;
    // 用户要求：开大期间稳定锁定。短暂失焦/帧抖动 GRACE 内不解锁；最长 MAX_LOCK 保底解锁。
    public static final long GRACE_MS=500,MAX_LOCK_MS=4000;
    public boolean holding(long now){return locked&&now-lastGood<=GRACE_MS&&now-startedWall<MAX_LOCK_MS;}
    public Request observe(Scope next,long hero,long nextFrame,boolean inputActive,boolean eligible,
                           Phase nativeCast,boolean shotSeen,boolean released,long now){
        if(locked&&now-startedWall>=MAX_LOCK_MS){
            locked=false;lastDuration=now-startedWall;reason="max lock reached";return null; // 保留基线，同一施法不再上锁
        }
        boolean sameScope=next==null||next.equals(scope);
        boolean transientGap=next==null||!eligible||nativeCast==null||nativeCast.tick()<0||(nextFrame==frame&&now-frameWall>150);
        if(locked&&hero==HERO&&sameScope&&transientGap){
            if(now-lastGood<=GRACE_MS)return new Request(scope,now,frame,begin);
            reset();reason="lock lost: focus/frames unavailable beyond grace";return null;
        }
        if(next==null||next.owner()==null||next.pid()<=0||next.source()==0||next.world()==0||next.model()<=0||next.model()>0xffffffffL
            ||hero!=HERO||nextFrame<=0||!eligible||nativeCast==null||nativeCast.tick()<0){reset();return null;}
        if(!next.equals(scope)){reset();scope=next;}
        if(nextFrame<frame){reset();return null;}
        if(nextFrame!=frame){frame=nextFrame;frameWall=now;}
        if(now<frameWall||now-frameWall>150){reset();return null;}
        if(lastTick<0){lastTick=nativeCast.tick();gameplay=inputActive&&!nativeCast.active();reason=nativeCast.active()?"pre-existing cast; wait for idle":"idle baseline";return null;}
        if(nativeCast.tick()<lastTick){reset();return null;}
        if(!locked&&nativeCast.active()&&nativeCast.tick()>lastTick&&gameplay){
            locked=true;begin=nativeCast.tick();startedWall=now;endedWall=releasedWall=nativeEnd=0;shot=false;reason="native Begin";
        }
        lastTick=nativeCast.tick();lastGood=now;
        if(locked){
            shot|=shotSeen;
            if(!nativeCast.active()&&nativeCast.tick()>=begin&&endedWall==0){endedWall=now;nativeEnd=nativeCast.tick();}
            // 用户要求：按下 Q（原版 Begin）即固定，龙一释放（起始箭飞出化龙，约0.5s）就取消固定。
            // 注：原版 volley 节点与 Begin 同帧，不能当作“射出”时刻。未射出就结束（取消）也解锁。
            if(released&&shot&&releasedWall==0)releasedWall=now;
            if(releasedWall>0||(endedWall>0&&!shot)){
                locked=false;lastDuration=now-startedWall;reason=releasedWall>0?"dragon released":"native End; cast cancelled without arrow";
            }
        }
        if(!nativeCast.active()&&inputActive)gameplay=true;
        return locked?new Request(scope,now,frame,begin):null;
    }
    public long begin(){return begin;}
    public boolean locked(){return locked;}
    public long startedWall(){return startedWall;}
    public long endedWall(){return endedWall;}
    public long nativeEnd(){return nativeEnd;}
    public long releasedWall(){return releasedWall;}
    public long duration(long now){return locked?Math.max(0,now-startedWall):lastDuration;}
    public String reason(){return reason;}
    public void reset(){scope=null;frame=frameWall=begin=startedWall=endedWall=releasedWall=nativeEnd=0;lastTick=-1;lastGood=0;gameplay=locked=shot=false;reason="scope reset";}
    public static boolean current(Request r,Scope current,long frame,long now){
        return r!=null&&r.begin()>0&&r.scope().equals(current)&&r.frame()>0&&r.frame()<=frame&&now>=r.observed()&&now-r.observed()<=150;
    }
    public static void write(ByteBuffer b,Request r){
        if(b.capacity()<256||b.order()!=ByteOrder.LITTLE_ENDIAN)throw new IllegalArgumentException("Hanzo body tail layout");
        for(int at=232;at<256;at+=4)b.putInt(at,0);
        if(r!=null){b.putInt(232,MAGIC);b.putInt(236,(int)r.scope().model());b.putLong(240,r.observed());b.putLong(248,r.begin());}
    }
}
