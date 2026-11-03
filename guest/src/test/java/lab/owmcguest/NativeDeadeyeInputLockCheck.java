package lab.owmcguest;
import java.nio.ByteBuffer;
import java.nio.ByteOrder;
public final class NativeDeadeyeInputLockCheck {
    private static void check(boolean value,String message){if(!value)throw new AssertionError(message);}
    public static void main(String[] args){
        var state=new NativeDeadeyeInputLock(10,0x80000123L,-20,100,0x500000,0x700000,1000);
        check(state.matches(10,0x80000123L,-20,1000),"current signed world/unsigned model scope");
        check(state.matches(10,0x80000123L,-20,1150),"fresh150ms boundary");
        check(!state.matches(10,0x80000123L,-20,1151),"stale proof expires");
        check(!state.matches(10,0x80000123L,-20,999),"future proof cannot lock");
        check(!state.matches(11,0x80000123L,-20,1000),"host restart releases");
        check(!state.matches(10,0x80000124L,-20,1000),"hero recreation releases");
        check(!state.matches(10,0x80000123L,-21,1000),"dimension changes release");
        var body=ByteBuffer.allocate(256).order(ByteOrder.LITTLE_ENDIAN);body.putInt(160,0x31594c46);
        NativeDeadeyeInputLock.write(body,state);
        check(body.getInt(176)==NativeDeadeyeInputLock.MAGIC&&body.getInt(180)==1&&body.getInt(184)==(int)0x80000123L,"extension magic/flag/model");
        check(body.getLong(192)==100&&body.getLong(200)==0x500000&&body.getLong(208)==0x700000&&body.getLong(216)==1000&&body.getLong(224)==-20,"wire native proof fields");
        NativeDeadeyeInputLock.write(body,null);
        check(body.getInt(176)==NativeDeadeyeInputLock.MAGIC&&body.getInt(180)==0&&body.getInt(160)==0x31594c46,"inactive/flight compatibility");
        for(int offset=184;offset<232;offset+=4)check(body.getInt(offset)==0,"inactive must erase old proof");
        NativeDeadeyeInputLock.write(body,state,false);
        for(int offset=176;offset<232;offset+=4)check(body.getInt(offset)==0,"new guest + legacy native retains exact zero tail");
        System.out.println("PASS: Deadeye exact scope/freshness, legacy-compatible tail and cancellation clearing");
    }
}
