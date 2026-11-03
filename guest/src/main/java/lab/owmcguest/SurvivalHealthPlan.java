package lab.owmcguest;

import java.nio.ByteBuffer;
import java.nio.ByteOrder;

/** Conversion and pool ordering shared by the actual writer and offline checks. */
public final class SurvivalHealthPlan {
    public static final double SCALE=.1;
    private SurvivalHealthPlan(){}
    public static byte[][] plan(byte[][] before,double[] maximum,double wanted){
        if(before.length!=3||maximum.length!=3||!Double.isFinite(wanted))throw new IllegalArgumentException("health shape/value");
        double total=0;for(double v:maximum){if(!Double.isFinite(v)||v<0||v>10000)throw new IllegalArgumentException("health maximum");total+=v;}
        if(total<=0||total>10000||wanted<0||wanted>total+.001)throw new IllegalArgumentException("health total");
        byte[][] result=new byte[3][];
        for(int i=0;i<3;i++){
            if(before[i].length!=320)throw new IllegalArgumentException("health slot size");
            var raw=ByteBuffer.wrap(before[i]).order(ByteOrder.LITTLE_ENDIAN);
            int enabled=raw.getInt(0);float max=raw.getFloat(4),current=raw.getFloat(8);
            if((enabled!=0&&enabled!=1)||!Float.isFinite(max)||!Float.isFinite(current)||current<0||max<current||max>10000
                ||enabled==0&&(max!=0||current!=0))throw new IllegalArgumentException("health slot values");
            for(int j=1;j<16;j++)if(raw.getInt(j*20)!=0)throw new IllegalArgumentException("additional native health pools");
            if(maximum[i]==0&&(enabled!=0||max!=0||current!=0))throw new IllegalArgumentException("unexpected native health pool");
            double part=Math.min(maximum[i],wanted);wanted=Math.max(0,wanted-part);
            result[i]=ByteBuffer.allocate(12).order(ByteOrder.LITTLE_ENDIAN).putInt(maximum[i]>0?1:0).putFloat((float)maximum[i]).putFloat((float)part).array();
        }
        return result;
    }
}
