package lab.owmcguest;

import java.nio.ByteBuffer;
import java.nio.ByteOrder;
import java.util.*;

/** Guarded extension of the existing health-slot contract for original Primal's
 * one extra500 pool. Unknown layouts fail closed; metadata is never rewritten.
 */
public final class WinstonHealthPools {
    public record Write(int pool,int offset,byte[] bytes){}
    public record Plan(double maximum,double current,List<Write> writes){}
    private WinstonHealthPools(){}
    public static Plan plan(byte[][] raw,double[] base,boolean primal,double target){
        if(raw.length!=3||base.length!=3)throw new IllegalArgumentException("Winston health shape");
        record Slot(int pool,int offset,boolean enabled,double maximum,double current){}
        var slots=new ArrayList<Slot>();double maximum=0,current=0;int extras=0;
        double original=Arrays.stream(base).sum();if(original!=WinstonRules.BASE_HP)throw new IllegalArgumentException("Winston base health differs");
        for(int j=0;j<3;j++){
            if(raw[j].length!=320)throw new IllegalArgumentException("Winston health slot bytes");
            var b=ByteBuffer.wrap(raw[j]).order(ByteOrder.LITTLE_ENDIAN);
            for(int at=0;at<320;at+=20){
                int enabled=b.getInt(at);float max=b.getFloat(at+4),hp=b.getFloat(at+8);
                if((enabled!=0&&enabled!=1)||!Float.isFinite(max)||!Float.isFinite(hp)||hp<0||max<hp||max>1000
                    ||enabled==0&&(max!=0||hp!=0))throw new IllegalArgumentException("Winston pool values");
                if(at==0){
                    // Some original pool instances fold the real bonus into
                    // the base slot. Accept exactly +500 under a fresh Q lease;
                    // never create a slot or overwrite its native metadata.
                    if(primal&&base[j]>0&&max==base[j]+WinstonRules.RAGE_BONUS){if(++extras>1)throw new IllegalArgumentException("Multiple Winston bonuses");}
                    else if(max!=base[j])throw new IllegalArgumentException("Winston base pool changed");
                    if(enabled!=(base[j]>0?1:0))throw new IllegalArgumentException("Winston base pool disabled");
                }
                else if(enabled!=0){if(!primal||max!=WinstonRules.RAGE_BONUS||++extras>1)throw new IllegalArgumentException("Unrecognized Winston bonus pool");}
                if(enabled!=0){slots.add(new Slot(j,at,true,max,hp));maximum+=max;current+=hp;}
            }
        }
        if(primal&&extras!=1)throw new IllegalArgumentException("Original Primal500 health pool not present");
        if(!Double.isNaN(target)&&!Double.isFinite(target))throw new IllegalArgumentException("Winston nonfinite health target");
        var writes=new ArrayList<Write>();
        if(Double.isFinite(target)){
            if(target<0||target>maximum+.001)throw new IllegalArgumentException("Winston target health");
            for(var slot:slots){
                double hp=Math.min(slot.maximum(),target);target=Math.max(0,target-hp);
                writes.add(new Write(slot.pool(),slot.offset(),ByteBuffer.allocate(12).order(ByteOrder.LITTLE_ENDIAN).putInt(1).putFloat((float)slot.maximum()).putFloat((float)hp).array()));
            }
        }
        return new Plan(maximum,current,List.copyOf(writes));
    }
}
