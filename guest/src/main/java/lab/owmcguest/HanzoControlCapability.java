package lab.owmcguest;

import java.nio.*;

/** Optional host-pose capability: old compositor DLLs never partially enable Q controls. */
public final class HanzoControlCapability {
    private record Sample(int pid,long source,long frame,long wall){}
    private static volatile Sample latest;
    private HanzoControlCapability(){}
    /** Call only AFTER the ordinary HostPoseReader validates the entire packet. */
    static void observe(byte[] data,long now){
        var b=ByteBuffer.wrap(data).order(ByteOrder.LITTLE_ENDIAN);
        latest=b.getInt(336)==HanzoControlProof.MAGIC&&b.getLong(80)<=now&&now-b.getLong(80)<=150
            ?new Sample(b.getInt(16),b.getLong(24),b.getLong(72),b.getLong(80)):null;
    }
    public static boolean available(int pid,long source,long frame,long now){
        var s=latest;return s!=null&&s.pid()==pid&&s.source()==source&&s.frame()>0&&s.frame()<=frame&&now>=s.wall()&&now-s.wall()<=150;
    }
}
