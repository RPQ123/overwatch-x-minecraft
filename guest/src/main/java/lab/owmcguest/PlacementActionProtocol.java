package lab.owmcguest;
import java.nio.*;
import java.nio.charset.StandardCharsets;
import java.util.Arrays;
public final class PlacementActionProtocol {
    public record Request(int pid,long creation,long sequence,long wall,long generation,long world,long model,long modelId,long script,long graph,long logger,long token,int kind){}
    public record Receipt(long sequence,long wall,int kind,int phase,float remaining,float duration){}
    private PlacementActionProtocol(){}
    public static byte[] encode(Request r){
        if(r.pid()<=0||r.creation()<=0||r.sequence()<=0||r.token()<=0||r.kind()<1||r.kind()>6||r.generation()==0||r.world()==0||r.model()==0||r.modelId()==0)throw new IllegalArgumentException("placement action scope");
        var b=ByteBuffer.allocate(112).order(ByteOrder.LITTLE_ENDIAN);b.put("OWPLRQ01".getBytes(StandardCharsets.US_ASCII)).putInt(1).putInt(r.pid());
        b.putLong(r.creation()).putLong(r.sequence()).putLong(r.wall()).putLong(r.generation()).putLong(r.world()).putLong(r.model()).putLong(r.modelId()).putLong(r.script()).putLong(r.graph()).putLong(r.logger()).putLong(r.token()).putInt(r.kind()).putInt(0);return b.array();
    }
    public static Receipt decode(byte[] raw,Request r,long now){
        if(raw.length!=80||!Arrays.equals(Arrays.copyOf(raw,8),"OWPLAK01".getBytes(StandardCharsets.US_ASCII)))throw new IllegalArgumentException("placement ack format");
        var b=ByteBuffer.wrap(raw).order(ByteOrder.LITTLE_ENDIAN);long wall=b.getLong(32);int kind=b.getInt(64),phase=b.getInt(68);float remaining=b.getFloat(72),duration=b.getFloat(76);
        if(b.getInt(8)!=1||b.getInt(12)!=r.pid()||b.getLong(16)!=r.creation()||b.getLong(24)!=r.sequence()||b.getLong(40)!=r.generation()||b.getLong(48)!=r.world()||b.getLong(56)!=r.modelId()||kind!=r.kind()
            ||wall>now+50||now-wall>250||(phase!=1&&phase!=3)||!Float.isFinite(remaining)||!Float.isFinite(duration)||remaining<0||remaining>120
            ||phase==1&&((kind==5?duration!=8&&duration!=2:duration!=(kind==1?10:kind==2?8:kind==6?13:12))||remaining>duration||kind!=3&&remaining<=0))throw new IllegalArgumentException("placement ack scope/value/freshness");
        return new Receipt(r.sequence(),wall,kind,phase,remaining,duration);
    }
}
