package lab.owmcguest;
import java.nio.*;
public final class NativeBlinkCheck {
    static void check(boolean b){if(!b)throw new AssertionError();}
    public static void main(String[] args){
        var phase=new NativeBlinkPhase();check(phase.observe(new double[]{0,0,0},0,0)==null);
        var delta=phase.observe(new double[]{0,0,-7.48},1,100);check(delta!=null&&delta[2]==-7.48);
        check(phase.observe(new double[]{0,0,-7.48},1,100)==null);
        check(phase.observe(new double[]{7.48,0,-7.48},2,100)==null); // repeated action cannot move
        check(phase.observe(new double[]{30,0,-7.48},5,200)==null); // interrupted batches never become straight sweeps
        phase.reset();check(phase.observe(new double[]{30,0,-7.48},5,200)==null);
        check(phase.observe(new double[]{37.48,0,-7.48},6,300)!=null);
        var host=new HostPoseReader.Pose(44,1,22,1,50,new float[9],new float[3],0,true);
        var b=ByteBuffer.allocate(256).order(ByteOrder.LITTLE_ENDIAN);b.put("OWFLY001".getBytes());b.putInt(8,1);b.putInt(12,256);b.putInt(16,22);b.putInt(20,33);b.putLong(24,44);b.putLong(32,55);b.putInt(48,(int)ProcessHandle.current().pid());b.putInt(52,2);b.putLong(64,2);b.putLong(72,1000);b.putDouble(96,-7.48);b.putLong(120,100);b.putLong(128,1);
        var motion=NativeFlightReader.decode(b.array(),host,55,33,1100,2);check(motion.captures()==1&&motion.actionTick()==100&&motion.total()[2]==-7.48);
        try{NativeFlightReader.decode(b.array(),host,55,33,1100);throw new AssertionError("Blink interpreted as flight");}catch(IllegalArgumentException expected){}
        b.putLong(128,-1);try{NativeFlightReader.decode(b.array(),host,55,33,1100,2);throw new AssertionError("negative capture");}catch(IllegalArgumentException expected){}
        System.out.println("PASS: native Blink stream/mode, owner baseline, replay and interrupted-batch guards");
    }
}
