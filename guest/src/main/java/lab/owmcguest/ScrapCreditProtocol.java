package lab.owmcguest;

import java.nio.*;
import java.nio.charset.StandardCharsets;
import java.util.Arrays;

/** Binary contract with the existing native body owner. Only a real pickup
 * reservation supplies a sequence; a request is never itself a credit. */
public final class ScrapCreditProtocol {
    public record Request(int pid,long creation,long sequence,long wall,long generation,long world,long model,long modelId){}
    public record Receipt(long sequence,long wall,int phase,int before,int after,int credited){}
    private ScrapCreditProtocol(){}
    public static byte[] encode(Request r){
        if(r.pid()<=0||r.creation()<=0||r.sequence()<=0||r.wall()<=0||r.generation()==0||r.world()==0||r.model()==0||r.modelId()==0)throw new IllegalArgumentException("scrap request scope");
        var b=ByteBuffer.allocate(80).order(ByteOrder.LITTLE_ENDIAN);b.put("OWSCRP01".getBytes(StandardCharsets.US_ASCII)).putInt(1).putInt(r.pid());
        b.putLong(r.creation()).putLong(r.sequence()).putLong(r.wall()).putLong(r.generation()).putLong(r.world()).putLong(r.model()).putLong(r.modelId()).putInt(25).putInt(0);return b.array();
    }
    public static Receipt decode(byte[] raw,Request expected,long now){
        if(raw.length!=80||!Arrays.equals(Arrays.copyOf(raw,8),"OWSCRA01".getBytes(StandardCharsets.US_ASCII)))throw new IllegalArgumentException("scrap receipt format");
        var b=ByteBuffer.wrap(raw).order(ByteOrder.LITTLE_ENDIAN);
        if(b.getInt(8)!=1||b.getInt(12)!=expected.pid()||b.getLong(16)!=expected.creation()||b.getLong(24)!=expected.sequence()
            ||b.getLong(40)!=expected.generation()||b.getLong(48)!=expected.world()||b.getLong(56)!=expected.modelId())throw new IllegalArgumentException("scrap receipt scope");
        long wall=b.getLong(32);int phase=b.getInt(64),before=b.getInt(68),after=b.getInt(72),credited=b.getInt(76);
        if(wall>now+50||now-wall>250||phase<1||phase>3||before<0||before>200||after<0||after>200||credited<0||credited>25
            ||phase==1&&(credited<=0||after-before!=credited||after!=Math.min(200,before+25))
            ||phase!=1&&(credited!=0||before!=after)||phase==2&&before!=200)throw new IllegalArgumentException("scrap receipt value/freshness");
        return new Receipt(expected.sequence(),wall,phase,before,after,credited);
    }
}
