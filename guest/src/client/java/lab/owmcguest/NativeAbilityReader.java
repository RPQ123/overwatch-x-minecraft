package lab.owmcguest;

import com.google.gson.JsonObject;
import com.google.gson.JsonParser;
import com.sun.jna.*;
import com.sun.jna.win32.StdCallLibrary;
import java.nio.*;
import java.nio.file.*;
import java.util.Arrays;

/** Read-only original MoveTo execution. No native code invocation, hooks, keys or coordinate writes. */
final class NativeAbilityReader implements AutoCloseable {
    interface Kernel extends StdCallLibrary {
        Pointer OpenProcess(int access,boolean inherit,int pid);
        boolean ReadProcessMemory(Pointer process,Pointer address,byte[] data,long size,Pointer count);
        boolean GetProcessTimes(Pointer process,Pointer creation,Pointer exit,Pointer kernel,Pointer user);
        int WaitForSingleObject(Pointer process,int timeout);
        boolean CloseHandle(Pointer handle);
        boolean WriteProcessMemory(Pointer process,Pointer address,byte[] data,long size,Pointer count);
    }
    record State(long source,long model,long tick,boolean active,double speed,double damage) {}
    private final Kernel kernel=Native.load("kernel32",Kernel.class);
    private Pointer handle;private JsonObject binding;private int pid;private long generation;
    private final boolean ultimate;
    NativeAbilityReader(){this(false);}
    NativeAbilityReader(boolean ultimate){this.ultimate=ultimate;}
    volatile String error="waiting for native dash binding";
    private long n(String key){return binding.get(key).getAsLong();}
    private byte[] read(long address,int size){
        if(address<0x10000||address>0x7fffffffffffL||size<1||size>4096)throw new IllegalArgumentException("native read bounds");
        byte[] data=new byte[size];try(var count=new Memory(8)){
            if(!kernel.ReadProcessMemory(handle,Pointer.createConstant(address),data,size,count)||count.getLong(0)!=size)throw new IllegalStateException("native read failed");
        }return data;
    }
    private static ByteBuffer bytes(byte[] data){return ByteBuffer.wrap(data).order(ByteOrder.LITTLE_ENDIAN);}
    private long pointer(long address){return bytes(read(address,8)).getLong();}
    private long find(long address,long wanted,boolean wide){
        var header=read(address,16);var h=bytes(header);long head=h.getLong(),count=h.getLong();
        if(count<0||count>4096)throw new IllegalArgumentException("native map bound");
        var sentinel=read(head,32);if(sentinel[25]!=1)throw new IllegalArgumentException("native map sentinel");
        long node=bytes(sentinel).getLong(8),parent=head,found=0;
        for(int depth=0;node!=head;depth++){
            if(depth>=64)throw new IllegalArgumentException("native map depth");
            var raw=read(node,40);var b=bytes(raw);if(raw[25]!=0||b.getLong(8)!=parent)throw new IllegalArgumentException("native map changed");
            long key=wide?b.getLong(32):b.getInt(32);
            if(key==wanted){found=node+40;break;}
            parent=node;node=b.getLong(wanted<key?0:16);
        }
        if(!Arrays.equals(header,read(address,16)))throw new IllegalArgumentException("native map header changed");return found;
    }
    private void verifyOwner(){
        // Departed models/scripts can stay allocated with intact IDs. The
        // live controller reference, not existence of the old object, owns it.
        if(pointer(n("controller")+0x28)!=n("admin")||bytes(read(n("controller")+0x94,4)).getInt()!=(int)n("localId")
           ||pointer(n("reference")+8)!=n("controller")||bytes(read(n("reference")+0x94,4)).getInt()!=(int)n("modelId")
           ||pointer(n("heroInfo")+8)!=n("controller")||pointer(n("heroInfo")+0x98)!=0x02e0000000000029L
           ||pointer(n("script")+0x160)!=n("graph"))throw new IllegalArgumentException("native hero/ability changed");
        if(kernel.WaitForSingleObject(handle,0)!=0x102||pointer(n("adminAddress"))!=n("admin")||bytes(read(n("admin")+0x220,4)).getInt()!=((int)n("localId"))||pointer(n("model")+0x28)!=n("admin")||bytes(read(n("model")+0x94,4)).getInt()!=((int)n("modelId"))||pointer(n("script")+0x98)!=n("bag")||pointer(n("script")+0x150)!=0x05800000000001dbL)throw new IllegalArgumentException("native hero/ability changed");
    }
    State poll(HostPoseReader.Pose host){
        if(host==null||host.flags()!=1){error="native camera unavailable";return null;}
        try{
            if(handle==null||pid!=host.pid()||generation!=host.generation()){
                close();String dir=System.getProperty("owmc.nativeEventsDirectory","");
                if(dir.isBlank()){error="native ability binding directory unavailable";return null;}
                var path=Path.of(dir).resolve((ultimate?"native-ultimate-request-":"native-dash-request-")+host.pid()+".json");
                if(!Files.isRegularFile(path)){error="waiting for native ability binding";return null;}
                if(Files.size(path)>8192)throw new IllegalArgumentException("native ability binding size");
                binding=JsonParser.parseString(Files.readString(path)).getAsJsonObject();
                if(n("version")!=2||n("pid")!=Integer.toUnsignedLong(host.pid())||n("resource")!=0x05800000000001dbL||n("node")!=6)throw new IllegalArgumentException("native ability request identity");
                handle=kernel.OpenProcess(0x100000|0x400|0x10|0x28,false,host.pid());if(handle==null)throw new IllegalStateException("native ability handle unavailable");
                try(var creation=new Memory(8);var exit=new Memory(8);var system=new Memory(8);var user=new Memory(8)){
                    if(!kernel.GetProcessTimes(handle,creation,exit,system,user)||creation.getLong(0)!=n("creation"))throw new IllegalArgumentException("native process creation changed");
                }pid=host.pid();generation=host.generation();
            }
            verifyOwner();
            if(pointer(n("speed"))!=n("speedVtable")||pointer(n("damage"))!=n("damageVtable"))throw new IllegalArgumentException("native ability numeric types changed");
            double speed=bytes(read(n("speed")+16,4)).getInt();var value=bytes(read(n("damage")+0xa0,16));int type=value.getInt(12);double damage=type==2?value.getInt(0):type==3?value.getFloat(0):Double.NaN;
            if(!Double.isFinite(damage)||damage<=0||damage>10000||speed<=0||speed>100)throw new IllegalArgumentException("native ability numeric bounds");
            long inner=find(n("logger"),n("script"),true);long row=inner==0?0:find(inner,6,false);
            // Establish an idle baseline before the first original Shift. Returning
            // null here made that first real Begin look like a pre-existing dash.
            if(row==0){error="";return new State(generation,n("modelId"),0,false,speed,damage);}
            var raw=read(row,9);var repeat=read(row,9);
            if(!Arrays.equals(raw,repeat)){error="native ability snapshot changed";return null;}
            long tick=bytes(raw).getLong();if(tick<0||(raw[8]!=0&&raw[8]!=1))throw new IllegalArgumentException("native ability payload");
            error="";return new State(generation,n("modelId"),tick,raw[8]==0,speed,damage);
        }catch(Exception failure){error=failure.toString();close();return null;}
    }
    record Ultimate(long source,long model,long begin,long timer,boolean timerActive,long left,long right,long leftAnimation,long rightAnimation,double damage,double charge,double cost,int chargeType){}
    boolean resetCooldown(State expected){
        if(ultimate||handle==null||binding==null||generation!=expected.source()||n("modelId")!=expected.model()||expected.active())return false;
        verifyOwner();long state=n("cooldownState");
        if(pointer(state)!=n("cooldownVtable")||pointer(state+0x78)!=n("script")||bytes(read(state+0x70,4)).getInt()!=n("cooldownStateIndex")||pointer(n("script")+0x160)!=n("graph"))throw new IllegalArgumentException("native cooldown owner changed");
        float remaining=bytes(read(state+0x150,4)).getFloat();
        if(!Float.isFinite(remaining)||remaining<0||remaining>8.1f)throw new IllegalArgumentException("native cooldown bounds");
        if(remaining==0)return true;
        for(long address:new long[]{state+0x144,state+0x146})if((read(address,1)[0]&255)>1)throw new IllegalArgumentException("native cooldown mirror flags changed");
        try(var written=new Memory(8)){
            verifyOwner();
            if(!kernel.WriteProcessMemory(handle,Pointer.createConstant(state+0x150),new byte[4],4,written)||written.getLong(0)!=4)throw new IllegalStateException("native cooldown reset failed");
            for(long address:new long[]{state+0x144,state+0x146})
                if(!kernel.WriteProcessMemory(handle,Pointer.createConstant(address),new byte[]{1},1,written)||written.getLong(0)!=1)throw new IllegalStateException("native cooldown mirror refresh failed");
        }
        return true;
    }
    long stateTick(long script,int node,boolean activeOnly){
        long inner=find(n("logger"),script,true),row=inner==0?0:find(inner,node,false);if(row==0)return 0;
        byte[] a=read(row,9),b=read(row,9);if(!Arrays.equals(a,b))return 0;
        long tick=bytes(a).getLong();if(tick<0||a[8]<0||a[8]>1)throw new IllegalArgumentException("native ultimate state");
        return activeOnly&&a[8]!=0?0:tick;
    }
    private double number(String key){
        if(pointer(n(key))!=n("numericVtable"))throw new IllegalArgumentException("native numeric owner");
        var b=bytes(read(n(key)+0xa0,16));double v=b.getInt(12)==2?b.getInt():b.getInt(12)==3?b.getFloat():Double.NaN;
        if(!Double.isFinite(v)||v<0||v>100000)throw new IllegalArgumentException("native numeric value");return v;
    }
    Ultimate ultimate(HostPoseReader.Pose host){
        if(!ultimate||host==null||host.flags()!=1)return null;
        poll(host);if(handle==null||binding==null)return null;
        try{
            if(pointer(n("ultimateScript")+0x150)!=0x0580000000000317L||pointer(n("ultimateScript")+0x98)!=n("ultimateBag")||pointer(n("weaponScript")+0x150)!=0x0580000000000304L||pointer(n("weaponScript")+0x98)!=n("weaponBag")||pointer(n("entityBagAddress"))!=n("entityBag"))throw new IllegalArgumentException("native ultimate ownership changed");
            double charge=number("charge"),cost=number("cost"),damage=number("swordDamage");
            if(cost!=1200||charge>cost||damage!=120)throw new IllegalArgumentException("native Genji calibration changed");
            var animations=binding.getAsJsonArray("swordAnimation");
            if(animations==null||animations.size()!=2)throw new IllegalArgumentException("native sword animation binding missing");
            for(int index=0;index<2;index++){
                var a=animations.get(index).getAsJsonObject();long address=a.get("address").getAsLong(),config=a.get("config").getAsLong();
                if(a.get("index").getAsInt()!=47+index||pointer(address)!=a.get("vtable").getAsLong()
                    ||pointer(a.get("field").getAsLong())!=config||pointer(config)!=a.get("configVtable").getAsLong()
                    ||pointer(config+0x18)!=a.get("alias").getAsLong())throw new IllegalArgumentException("native sword animation changed");
            }
            int kind=bytes(read(n("charge")+0xac,4)).getInt();
            // The original logger updates the timestamp at both Begin and End.
            // Only active tracking states are swings; End must never hit twice.
            return new Ultimate(host.generation(),n("modelId"),stateTick(n("ultimateScript"),17,true),stateTick(n("ultimateScript"),8,false),stateTick(n("ultimateScript"),8,true)>0,stateTick(n("weaponScript"),57,true),stateTick(n("weaponScript"),58,true),stateTick(n("weaponScript"),47,true),stateTick(n("weaponScript"),48,true),damage,charge,cost,kind);
        }catch(Exception failure){error=failure.toString();close();return null;}
    }
    void charge(Ultimate expected,double wanted){
        synchronized(NativeMeterWrites.LOCK){
        if(handle==null||!ultimate)throw new IllegalStateException("charge binding unavailable");
        verifyOwner();
        if(generation!=expected.source()||n("modelId")!=expected.model())return;
        double current=number("charge");int kind=bytes(read(n("charge")+0xac,4)).getInt();
        if(current!=expected.charge()||kind!=expected.chargeType()||wanted<current||wanted>expected.cost())return;
        var out=ByteBuffer.allocate(4).order(ByteOrder.LITTLE_ENDIAN);if(kind==2)out.putInt((int)wanted);else if(kind==3)out.putFloat((float)wanted);else throw new IllegalArgumentException("charge type");
        verifyOwner();
        try(var written=new Memory(8)){
            if(!kernel.WriteProcessMemory(handle,Pointer.createConstant(n("charge")+0xa0),out.array(),4,written)||written.getLong(0)!=4)throw new IllegalStateException("native charge write failed");
        }
        }
    }
    @Override public void close(){if(handle!=null)kernel.CloseHandle(handle);handle=null;binding=null;pid=0;generation=0;}
}
