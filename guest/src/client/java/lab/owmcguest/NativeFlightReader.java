package lab.owmcguest;

import com.sun.jna.*;
import com.sun.jna.win32.StdCallLibrary;
import java.nio.*;
import java.util.Arrays;

/** Reads the original mover's cumulative displacement, never a copied jet equation. */
final class NativeFlightReader implements AutoCloseable {
    interface Kernel extends StdCallLibrary {
        Pointer OpenFileMappingW(int access,boolean inherit,WString name);
        Pointer MapViewOfFile(Pointer handle,int access,int high,int low,long size);
        boolean UnmapViewOfFile(Pointer memory);
        boolean CloseHandle(Pointer handle);
    }
    record Motion(long sequence,double[] total,double[] velocity,long actionTick,long captures){}
    static Motion decode(byte[] raw,HostPoseReader.Pose host,long world,long model,long now){
        return decode(raw,host,world,model,now,1);
    }
    static Motion decode(byte[] raw,HostPoseReader.Pose host,long world,long model,long now,int mode){
        if(raw.length!=256||mode<1||mode>3)throw new IllegalArgumentException("native motion size/mode");
        var b=ByteBuffer.wrap(raw).order(ByteOrder.LITTLE_ENDIAN);
        if(raw.length!=256||!new String(raw,0,8,java.nio.charset.StandardCharsets.US_ASCII).equals("OWFLY001")||b.getInt(8)!=1||b.getInt(12)!=256
           ||b.getInt(16)!=host.pid()||Integer.toUnsignedLong(b.getInt(20))!=model||b.getLong(24)!=host.generation()||b.getLong(32)!=world
           ||b.getInt(48)!=(int)ProcessHandle.current().pid()||b.getInt(52)!=mode||b.getLong(64)<=0||(b.getLong(64)&1)!=0||now-b.getLong(72)>150||b.getLong(72)>now)throw new IllegalArgumentException("native flight identity/freshness");
        double[] total=new double[3],velocity=new double[3];
        for(int i=0;i<3;i++){
            total[i]=b.getDouble(80+i*8);velocity[i]=b.getFloat(104+i*4);
            if(!Double.isFinite(total[i])||Math.abs(total[i])>30000000||!Double.isFinite(velocity[i])||Math.abs(velocity[i])>100)throw new IllegalArgumentException("native flight numeric bounds");
        }
        long action=mode==2?b.getLong(120):0,captures=mode==2?b.getLong(128):0;
        if(action<0||captures<0||(mode==2&&total[1]!=0))throw new IllegalArgumentException("native blink payload");
        return new Motion(b.getLong(64),total,velocity,action,captures);
    }
    private final Kernel kernel=Native.load("kernel32",Kernel.class);
    private Pointer handle,memory;private int pid;private long generation;
    private final int mode;
    NativeFlightReader(){this(1);}
    NativeFlightReader(int mode){this.mode=mode;}
    String error="waiting for native flight";
    Motion poll(HostPoseReader.Pose host,long world,long model){
        if(host==null||host.flags()!=1)return null;
        try{
            if(memory==null||pid!=host.pid()||generation!=host.generation()){
                close();handle=kernel.OpenFileMappingW(4,false,new WString("Local\\OWMCNativeFlight_"+host.pid()));
                if(handle==null){error="waiting for native flight producer";return null;}
                memory=kernel.MapViewOfFile(handle,4,0,0,256);if(memory==null)throw new IllegalStateException("native flight mapping unavailable");
                pid=host.pid();generation=host.generation();
            }
            long before=memory.getLong(64);var a=memory.getByteArray(0,256);long after=memory.getLong(64);
            if(before!=after||(before&1)!=0)return null;
            var motion=decode(a,host,world,model,System.currentTimeMillis(),mode);
            if(!Arrays.equals(a,memory.getByteArray(0,256)))return null;
            error="";return motion;
        }catch(Exception failure){error=failure.toString();return null;}
    }
    @Override public void close(){if(memory!=null)kernel.UnmapViewOfFile(memory);if(handle!=null)kernel.CloseHandle(handle);memory=handle=null;pid=0;generation=0;}
}
