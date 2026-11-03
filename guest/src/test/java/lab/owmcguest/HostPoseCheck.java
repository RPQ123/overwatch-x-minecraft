package lab.owmcguest;

import java.nio.ByteBuffer;
import java.nio.ByteOrder;
import org.joml.Matrix3f;
import org.joml.Quaternionf;
import org.joml.Vector3f;

public final class HostPoseCheck {
    static byte[] packet(float yaw,float pitch,float roll) {
        var b=ByteBuffer.allocate(4096).order(ByteOrder.LITTLE_ENDIAN);b.put("OWPOSE01".getBytes(java.nio.charset.StandardCharsets.US_ASCII));
        b.putInt(8,1);b.putInt(12,4096);b.putInt(16,123);b.putLong(24,7);b.putInt(32,1);b.putLong(64,2);b.putLong(72,19);b.putLong(80,1000);b.putInt(88,2);b.putInt(92,1920);b.putInt(96,1080);
        b.putFloat(104,70);b.putFloat(108,.8033332f);b.putFloat(112,1.4281478f);
        var q=new Quaternionf().rotationYXZ((float)Math.PI-(float)Math.toRadians(yaw),-(float)Math.toRadians(pitch),(float)Math.toRadians(roll));
        float[] matrix=new Matrix3f().rotation(q).get(new float[9]);for(int i=0;i<9;i++) b.putFloat(128+i*4,matrix[i]);return b.array();
    }
    static void reject(byte[] bytes,long now,boolean synthetic) {try {HostPoseReader.decode(bytes,now,synthetic);}catch(IllegalArgumentException expected) {return;}throw new AssertionError("Invalid pose accepted");}
    public static void main(String[] args) {
        for(float yaw:new float[]{0,90,180,270}) for(float pitch:new float[]{-30,0,30}) for(float roll:new float[]{-20,0,20}) {
            var pose=HostPoseReader.decode(packet(yaw,pitch,roll),1000,true);
            var forward=new Vector3f(0,0,-1).rotate(pose.rotation());
            double yr=Math.toRadians(yaw),pr=Math.toRadians(pitch);
            if(Math.abs(forward.x+Math.sin(yr)*Math.cos(pr))>1e-5||Math.abs(forward.y+Math.sin(pr))>1e-5||Math.abs(forward.z-Math.cos(yr)*Math.cos(pr))>1e-5) throw new AssertionError("Direction mapping");
            var matrix=new Matrix3f().rotation(pose.rotation());float[] roundtrip=matrix.get(new float[9]);
            for(int i=0;i<9;i++) if(Math.abs(roundtrip[i]-pose.basis()[i])>1e-5) throw new AssertionError("Roll/basis roundtrip");
        }
        var valid=packet(0,0,0);reject(valid,1501,true);reject(valid,749,true);reject(valid,1000,false);
        var b=ByteBuffer.wrap(valid).order(ByteOrder.LITTLE_ENDIAN);b.putLong(64,3);reject(valid,1000,true);b.putLong(64,2);
        b.putFloat(128,Float.NaN);reject(valid,1000,true);valid=packet(0,0,0);b=ByteBuffer.wrap(valid).order(ByteOrder.LITTLE_ENDIAN);b.putFloat(128,1);reject(valid,1000,true);
        valid=packet(0,0,0);b=ByteBuffer.wrap(valid).order(ByteOrder.LITTLE_ENDIAN);b.putInt(32,0);reject(valid,1000,true);
        valid=packet(0,0,0);b=ByteBuffer.wrap(valid).order(ByteOrder.LITTLE_ENDIAN);b.putInt(320,1);b.putInt(324,17);b.putInt(328,1);
        if(HostPoseReader.decode(valid,1000,true).movementBits()!=0) throw new AssertionError("Synthetic camera cannot drive movement");
        b.putInt(88,1);var input=HostPoseReader.decode(valid,1000,false);
        if(!input.inputActive()||input.movementBits()!=17) throw new AssertionError("Native forward/jump intent");
        if(HostPoseReader.decode(valid,1151,false).movementBits()!=0) throw new AssertionError("Movement watchdog must release before camera stale limit");
        b.putInt(328,0);if(HostPoseReader.decode(valid,1000,false).movementBits()!=0) throw new AssertionError("Focus loss must release movement");
        b.putInt(324,64);reject(valid,1000,false);b.putInt(320,2);b.putInt(328,1);
        if(HostPoseReader.decode(valid,1000,false).movementBits()!=64)throw new AssertionError("Explicit flight intent");
        b.putInt(324,128);if(HostPoseReader.decode(valid,1000,false).movementBits()!=128)throw new AssertionError("Explicit melee intent");
        b.putInt(324,256);if(HostPoseReader.decode(valid,1000,false).movementBits()!=256)throw new AssertionError("Explicit nether portal intent");
        b.putInt(324,512);if(HostPoseReader.decode(valid,1000,false).movementBits()!=512)throw new AssertionError("Explicit end portal intent");
        if(HostPoseReader.decode(valid,1000,false).deadeyeInputGuard())throw new AssertionError("Legacy compositor cannot advertise the new control guard");
        b.putInt(332,NativeDeadeyeInputLock.MAGIC);if(!HostPoseReader.decode(valid,1000,false).deadeyeInputGuard())throw new AssertionError("Matched control guard capability");
        b.putInt(332,1);reject(valid,1000,false);b.putInt(332,0);
        b.putInt(324,0);b.putInt(320,3);reject(valid,1000,false);
        System.out.println("PASS: 36 camera direction/pitch/roll roundtrips, stale/future/odd/NaN/reflected/inactive/synthetic guards.");
    }
}
