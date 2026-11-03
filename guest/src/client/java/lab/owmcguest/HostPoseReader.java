package lab.owmcguest;

import com.sun.jna.Native;
import com.sun.jna.Pointer;
import com.sun.jna.WString;
import com.sun.jna.win32.StdCallLibrary;
import java.nio.ByteBuffer;
import java.nio.ByteOrder;
import java.lang.invoke.VarHandle;
import org.joml.Matrix3f;
import org.joml.Quaternionf;

/** Direction-only native camera channel. Does not teleport or drive MC physics. */
public final class HostPoseReader implements AutoCloseable {
    public static final String NAME="Local\\OWMCHostPose";
    public record Pose(long generation,long frame,int pid,int flags,float fov,float[] basis,float[] eye,int movementBits,boolean inputActive,boolean deadeyeInputGuard) {
        public Pose(long generation,long frame,int pid,int flags,float fov,float[] basis,float[] eye,int movementBits,boolean inputActive){
            this(generation,frame,pid,flags,fov,basis,eye,movementBits,inputActive,false);
        }
        public Quaternionf rotation() {return new Quaternionf().setFromNormalized(new Matrix3f().set(basis));}
    }
    interface Reader extends StdCallLibrary {
        Pointer OpenFileMappingW(int access,boolean inherit,WString name);
        Pointer MapViewOfFile(Pointer handle,int access,int high,int low,long size);
        boolean UnmapViewOfFile(Pointer address);
        boolean CloseHandle(Pointer handle);
    }
    private final Reader reader=Native.load("kernel32",Reader.class);
    private Pointer handle,memory;
    private long nextOpen;
    public static volatile Pose applied;
    public static final HostPoseReader INSTANCE=new HostPoseReader();
    static Pose decode(byte[] data,long now,boolean allowSynthetic) {
        if(data.length!=4096) throw new IllegalArgumentException("Pose size");
        var b=ByteBuffer.wrap(data).order(ByteOrder.LITTLE_ENDIAN);
        if(!new String(data,0,8,java.nio.charset.StandardCharsets.US_ASCII).equals("OWPOSE01")||b.getInt(8)!=1||b.getInt(12)!=4096||b.getInt(16)==0||b.getInt(20)!=0||b.getLong(24)==0||b.getInt(32)!=1) throw new IllegalArgumentException("Pose identity");
        long sequence=b.getLong(64),frame=b.getLong(72),wall=b.getLong(80);int flags=b.getInt(88),w=b.getInt(92),h=b.getInt(96);
        float fov=b.getFloat(104),fx=b.getFloat(108),fy=b.getFloat(112);
        if(sequence<=0||(sequence&1)!=0||frame<=0||now-wall>500||wall-now>250) throw new IllegalArgumentException("Pose sequence/freshness");
        if(flags!=1&&!(allowSynthetic&&flags==2)) throw new IllegalArgumentException("Pose provenance");
        if(w<1||h<1||w>16384||h>16384||!Float.isFinite(fov)||fov<20||fov>140||!Float.isFinite(fx)||!Float.isFinite(fy)||fx<=0||fy<=0||Math.abs(fx*w/h-fy)>.01||Math.abs(2*Math.toDegrees(Math.atan(1/fy))-fov)>.01) throw new IllegalArgumentException("Pose lens");
        float[] basis=new float[9],eye=new float[3];for(int i=0;i<9;i++) basis[i]=b.getFloat(128+i*4);for(int i=0;i<3;i++) eye[i]=b.getFloat(168+i*4);
        for(float v:eye) if(!Float.isFinite(v)||Math.abs(v)>1e7) throw new IllegalArgumentException("Pose eye");
        for(float v:basis) if(!Float.isFinite(v)) throw new IllegalArgumentException("Pose basis");
        var matrix=new Matrix3f().set(basis);
        if(Math.abs(matrix.determinant()-1)>.02) throw new IllegalArgumentException("Pose handedness");
        for(int column=0;column<3;column++) for(int other=0;other<3;other++) {
            float dot=0;for(int i=0;i<3;i++) dot+=basis[column*3+i]*basis[other*3+i];
            if(Math.abs(dot-(column==other?1:0))>.02) throw new IllegalArgumentException("Pose orthogonal basis");
        }
        int inputVersion=b.getInt(320),bits=0;boolean active=false;
        if(inputVersion==1||inputVersion==2) {
            bits=b.getInt(324);int enabled=b.getInt(328);
            if((bits&~(inputVersion==2?1023:63))!=0||(enabled!=0&&enabled!=1)) throw new IllegalArgumentException("Movement flags");
            active=flags==1&&enabled==1&&now-wall<=150;if(!active) bits=0;
        } else if(inputVersion!=0) throw new IllegalArgumentException("Movement version");
        int capabilities=b.getInt(332);
        if(capabilities!=0&&capabilities!=NativeDeadeyeInputLock.MAGIC)throw new IllegalArgumentException("Input capability identity");
        HanzoControlCapability.observe(data,now);
        return new Pose(b.getLong(24),frame,b.getInt(16),flags,fov,basis,eye,bits,active,capabilities==NativeDeadeyeInputLock.MAGIC);
    }
    public Pose latest() {
        long now=System.currentTimeMillis();
        if(memory==null) {
            if(now<nextOpen) return null;nextOpen=now+250;
            handle=reader.OpenFileMappingW(4,false,new WString(NAME));if(handle==null) return null;
            memory=reader.MapViewOfFile(handle,4,0,0,4096);if(memory==null) {reader.CloseHandle(handle);handle=null;return null;}
        }
        for(int i=0;i<3;i++) {
            long seq=memory.getLong(64);if(seq<=0||(seq&1)!=0) continue;
            long generation=memory.getLong(24);VarHandle.acquireFence();byte[] bytes=memory.getByteArray(0,4096);VarHandle.acquireFence();
            if(memory.getLong(64)!=seq||memory.getLong(24)!=generation) continue;
            try {return decode(bytes,now,Boolean.getBoolean("owmc.poseTest"));}catch(IllegalArgumentException stale) {return null;}
        }
        return null;
    }
    @Override public void close() {if(memory!=null) reader.UnmapViewOfFile(memory);if(handle!=null) reader.CloseHandle(handle);memory=null;handle=null;applied=null;}
}
