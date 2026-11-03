package lab.owmcguest;
import java.nio.*;
import java.util.*;
public final class HanzoControlProofCheck {
    private static final HanzoControlProof.Scope S=new HanzoControlProof.Scope(new UUID(1,2),10,11,12,13);
    private static void check(boolean value,String message){if(!value)throw new AssertionError(message);}
    private static HanzoControlProof.Request sample(HanzoControlProof g,long frame,long tick,boolean active,boolean eligible,boolean shot,boolean released,long wall){
        return g.observe(S,HanzoControlProof.HERO,frame,true,eligible,new HanzoControlProof.Phase(tick,active),shot,released,wall);
    }
    private static HanzoControlProof start(){var g=new HanzoControlProof();check(sample(g,1,0,false,true,false,false,1000)==null,"idle baseline");check(sample(g,2,100,true,true,false,false,1050)!=null,"actual Begin");return g;}
    public static void main(String[] args){
        var g=start();check(sample(g,3,100,true,true,true,false,1100)!=null,"volley at Begin does not unlock");
        check(sample(g,4,100,true,true,true,true,1550)==null,"dragon release unlocks immediately");check(g.duration(1550)==500,"observed lock duration");
        check(sample(g,5,100,true,true,true,true,1600)==null,"same cast never relocks");
        g=start();check(sample(g,3,150,false,true,true,false,1100)!=null,"native End cannot bypass initial arrow");
        check(sample(g,4,150,false,true,true,true,1150)==null,"later release unlocks immediately");
        g=start();check(sample(g,3,150,false,true,false,false,1100)==null,"cancelled cast without arrow releases");
        g=start();check(sample(g,3,100,true,false,false,false,1100)!=null&&g.locked(),"brief focus/frame gap keeps the lock");
        check(sample(g,3,100,true,false,false,false,1700)==null&&!g.locked(),"gap beyond grace releases");
        check(sample(g,4,100,true,true,true,false,1750)==null,"focus return must not re-admit the same cast");
        g=start();check(sample(g,2,100,true,true,false,false,1300)!=null,"stale frame within grace keeps lock");
        g=start();for(long w=1100;w<5050;w+=100)sample(g,(w-1000)/50,100,true,true,false,false,w);
        check(sample(g,200,100,true,true,false,false,5100)==null&&!g.locked(),"max lock always releases");
        check(sample(g,201,100,true,true,false,false,5150)==null,"same cast never relocks after max");
        g=start();var next=new HanzoControlProof.Scope(S.owner(),10,11,99,13);
        check(g.observe(next,HanzoControlProof.HERO,3,true,true,new HanzoControlProof.Phase(100,true),true,false,1100)==null,"world reset rebaselines");
        g=start();check(g.observe(S,0x02e0000000000065L,3,true,true,new HanzoControlProof.Phase(100,true),false,false,1100)==null,"hero switch releases");
        g=start();check(sample(g,1,100,true,true,false,false,1100)==null,"frame rollback releases");
        g=start();var r=sample(g,3,100,true,true,false,false,1100);var b=ByteBuffer.allocate(256).order(ByteOrder.LITTLE_ENDIAN);
        for(int i=0;i<232;i++)b.put(i,(byte)0x5a);HanzoControlProof.write(b,r);
        check(b.getInt(232)==0x325a4e48&&b.getLong(248)==100,"HNZ2 contains actual Begin, not host frame");
        for(int i=0;i<232;i++)check(b.get(i)==(byte)0x5a,"preserve all shared body fields");
        HanzoControlProof.write(b,null);for(int i=232;i<256;i++)check(b.get(i)==0,"inactive tail clears");
        check(!HanzoControlProof.current(r,S,3,1251),"request expiry");
        var pose=ByteBuffer.allocate(4096).order(ByteOrder.LITTLE_ENDIAN);pose.putInt(16,10).putLong(24,11).putLong(72,3).putLong(80,1100).putInt(336,0x315a4e48);
        HanzoControlCapability.observe(pose.array(),1100);check(!HanzoControlCapability.available(10,11,3,1100),"old HNZ1 DLL rejected");
        pose.putInt(336,HanzoControlProof.MAGIC);HanzoControlCapability.observe(pose.array(),1100);check(HanzoControlCapability.available(10,11,3,1100),"HNZ2 scoped capability");
        check(!HanzoControlCapability.available(10,11,3,1251),"capability expiry");
        System.out.println("HanzoControlProofCheck PASS: dual completion, cancellation, invalidation, rebaseline, timing, protocol and scope");
    }
}
