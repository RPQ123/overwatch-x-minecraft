package lab.owmcguest;
import com.google.gson.*;
import com.sun.jna.*;
import java.nio.*;
import java.nio.file.*;

/** Typed native meter feedback only; no code invocation or ability activation. */
final class NativeMeterReader implements AutoCloseable {
    record State(double charge,double cost,int kind){}
    record Scrap(int amount,long creation,long model){}
    private final NativeAbilityReader.Kernel kernel=Native.load("kernel32",NativeAbilityReader.Kernel.class);
    private Pointer handle;private JsonObject binding;private int pid;private long generation;
    String error="waiting for native meter binding";
    private long n(String key){return binding.get(key).getAsLong();}
    private byte[] read(long at,int size){
        if(at<0x10000||at>0x7fffffffffffL||size<1||size>8192)throw new IllegalArgumentException("meter read bounds");
        byte[] data=new byte[size];try(var count=new Memory(8)){
            if(!kernel.ReadProcessMemory(handle,Pointer.createConstant(at),data,size,count)||count.getLong(0)!=size)throw new IllegalStateException("meter read failed");
        }return data;
    }
    private static ByteBuffer bytes(byte[] data){return ByteBuffer.wrap(data).order(ByteOrder.LITTLE_ENDIAN);}
    private long q(long at){return bytes(read(at,8)).getLong();}
    private int i(long at){return bytes(read(at,4)).getInt();}
    private void verify(){
        if(kernel.WaitForSingleObject(handle,0)!=0x102||q(n("adminAddress"))!=n("admin")||i(n("admin")+0x220)!=(int)n("localId")
            ||i(n("reference")+0x94)!=(int)n("modelId")||i(n("model")+0x94)!=(int)n("modelId")||q(n("model")+0x28)!=n("admin")
            ||q(n("heroInfo")+0x98)!=n("hero")||q(n("bagAddress"))!=n("bag"))throw new IllegalArgumentException("native meter owner changed");
        for(String name:new String[]{"charge","cost"}){
            int bucket=(int)n(name+"Bucket");if(bucket<0||bucket>=16)throw new IllegalArgumentException("meter bucket");
            var h=bytes(read(n("bag")+0xa0+bucket*0x30,16));long items=h.getLong();int count=h.getInt(),capacity=h.getInt();
            if(count<1||count>capacity||capacity>512)throw new IllegalArgumentException("meter variable bounds");
            var pairs=bytes(read(items,count*16));boolean found=false;long rid=name.equals("charge")?0x0d80000000000156L:0x0d80000000000152L;
            for(int j=0;j<count;j++)if(pairs.getLong(j*16)==rid&&pairs.getLong(j*16+8)==n(name))found=true;
            if(!found||q(n(name))!=n("numericVtable"))throw new IllegalArgumentException("meter variable changed");
        }
    }
    private double value(String name){
        var b=bytes(read(n(name)+0xa0,16));int kind=b.getInt(12);double value=kind==2?b.getInt():kind==3?b.getFloat():Double.NaN;
        if(!Double.isFinite(value)||value<0||value>100000)throw new IllegalArgumentException("meter numeric bounds");return value;
    }
    State poll(HostPoseReader.Pose host,long model,long hero){
        if(host==null||host.flags()!=1||model==0||hero==0)return null;
        try{
            if(handle==null||pid!=host.pid()||generation!=host.generation()||n("modelId")!=model){
                close();String dir=System.getProperty("owmc.nativeEventsDirectory","");var path=Path.of(dir).resolve("native-meter-request-"+host.pid()+".json");
                if(dir.isBlank()||!Files.isRegularFile(path)){error="waiting for native meter binding";return null;}
                if(Files.size(path)>8192)throw new IllegalArgumentException("meter binding size");binding=JsonParser.parseString(Files.readString(path)).getAsJsonObject();
                if(n("version")!=1||n("pid")!=Integer.toUnsignedLong(host.pid())||n("modelId")!=model||n("hero")!=hero)throw new IllegalArgumentException("meter binding identity");
                handle=kernel.OpenProcess(0x100000|0x400|0x10|0x28,false,host.pid());if(handle==null)throw new IllegalStateException("meter process unavailable");
                try(var creation=new Memory(8);var exit=new Memory(8);var system=new Memory(8);var user=new Memory(8)){
                    if(!kernel.GetProcessTimes(handle,creation,exit,system,user)||creation.getLong(0)!=n("creation"))throw new IllegalArgumentException("meter process creation changed");
                }pid=host.pid();generation=host.generation();
            }
            verify();double charge=value("charge"),cost=value("cost");if(cost<=0||charge>cost)throw new IllegalArgumentException("native charge exceeds cost");
            error="";return new State(charge,cost,i(n("charge")+0xac));
        }catch(Exception failure){error=failure.toString();close();return null;}
    }
    /** Read the same entity variable bag already bound for the native meter.
     * No write is performed here; the logic owner executes Scrap Set&Notify. */
    Scrap scrap(){
        if(handle==null||binding==null||n("hero")!=0x02e0000000000006L)throw new IllegalStateException("native Scrap owner unavailable");
        verify();long primitive=0;
        for(int bucket=0;bucket<16;bucket++){
            var h=bytes(read(n("bag")+0xa0+bucket*0x30,16));long items=h.getLong();int count=h.getInt(),capacity=h.getInt();
            if(count<0||count>capacity||capacity>512)throw new IllegalArgumentException("Scrap bag bounds");
            if(count==0)continue;var pairs=bytes(read(items,count*16));
            for(int j=0;j<count;j++)if(pairs.getLong(j*16)==0x0d80000000000409L){if(primitive!=0)throw new IllegalArgumentException("duplicate Scrap variable");primitive=pairs.getLong(j*16+8);}
        }
        if(primitive==0||q(primitive)!=n("numericVtable")||q(primitive+0x80)!=n("bag")||q(primitive+0x98)!=0x0d80000000000409L)throw new IllegalArgumentException("Scrap variable identity");
        var raw=bytes(read(primitive+0xa0,16));int kind=raw.getInt(12);double amount=kind==2?raw.getInt():kind==3?raw.getFloat():Double.NaN;
        if(!Double.isFinite(amount)||amount<0||amount>200||amount!=Math.floor(amount))throw new IllegalArgumentException("Scrap value bounds");
        verify();return new Scrap((int)amount,n("creation"),n("model"));
    }
    boolean credit(State expected,double wanted){
        synchronized(NativeMeterWrites.LOCK){
        if(handle==null||binding==null||!Double.isFinite(wanted)||wanted<expected.charge()||wanted>expected.cost())return false;
        return writeCharge(expected,wanted);}
    }
    /** Beta Q spends half on entry; its missing server normally spends the
     * remaining half on confirmed fire. Cancel retains native beta behavior. */
    boolean consumeDeadeye(State expected,NativeSkillReader.State proof){
        synchronized(NativeMeterWrites.LOCK){
            if(handle==null||binding==null||proof==null||n("hero")!=NativeDeadeyeRuntime.HERO||proof.hero()!=NativeDeadeyeRuntime.HERO||proof.model()!=n("modelId")||proof.source()!=generation||!proof.active("ultimate")||proof.entries().get("fire").tick()<proof.entries().get("ultimate").tick())return false;
            return writeCharge(expected,0);
        }
    }
    private boolean writeCharge(State expected,double wanted){
        verify();if(value("cost")!=expected.cost()||value("charge")!=expected.charge()||i(n("charge")+0xac)!=expected.kind())return false;
        var out=ByteBuffer.allocate(4).order(ByteOrder.LITTLE_ENDIAN);if(expected.kind()==2)out.putInt((int)wanted);else if(expected.kind()==3)out.putFloat((float)wanted);else return false;
        try(var count=new Memory(8)){
            verify();if(!kernel.WriteProcessMemory(handle,Pointer.createConstant(n("charge")+0xa0),out.array(),4,count)||count.getLong(0)!=4)throw new IllegalStateException("meter feedback write failed");
        }return true;
    }
    @Override public void close(){if(handle!=null)kernel.CloseHandle(handle);handle=null;binding=null;pid=0;generation=0;}
}
