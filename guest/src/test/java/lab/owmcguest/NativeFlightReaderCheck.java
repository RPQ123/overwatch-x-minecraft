package lab.owmcguest;
import java.nio.*;
public final class NativeFlightReaderCheck {
    static void check(boolean condition){if(!condition)throw new AssertionError();}
    public static void main(String[] args){
        var host=new HostPoseReader.Pose(44,1,22,1,50,new float[9],new float[3],0,true);
        var b=ByteBuffer.allocate(256).order(ByteOrder.LITTLE_ENDIAN);b.put("OWFLY001".getBytes());b.putInt(8,1);b.putInt(12,256);b.putInt(16,22);b.putInt(20,33);b.putLong(24,44);b.putLong(32,55);b.putInt(48,(int)ProcessHandle.current().pid());b.putInt(52,1);b.putLong(64,2);b.putLong(72,1000);b.putDouble(88,1.5);b.putFloat(108,20);
        var value=NativeFlightReader.decode(b.array(),host,55,33,1100);check(value.total()[1]==1.5&&value.velocity()[1]==20);
        for(int offset:new int[]{16,20,24,32,48,52,64}){
            var data=b.array().clone();data[offset]^=1;
            try{NativeFlightReader.decode(data,host,55,33,1100);throw new AssertionError("identity admitted at"+offset);}catch(IllegalArgumentException expected){}
        }
        try{NativeFlightReader.decode(b.array(),host,55,33,1151);throw new AssertionError("stale");}catch(IllegalArgumentException expected){}
        b.putInt(52,3);b.putFloat(104,8.25f);b.putFloat(108,0);
        check(NativeFlightReader.decode(b.array(),host,55,33,1100,3).velocity()[0]==8.25);
        try{NativeFlightReader.decode(b.array(),host,55,33,1100);throw new AssertionError("motor read as Pharah flight");}catch(IllegalArgumentException expected){}
        b.putInt(52,1);b.putFloat(108,Float.NaN);try{NativeFlightReader.decode(b.array(),host,55,33,1100);throw new AssertionError("NaN");}catch(IllegalArgumentException expected){}
        System.out.println("PASS: original flight motion, source/model/world/seqlock/stale/nonfinite guards");
    }
}
