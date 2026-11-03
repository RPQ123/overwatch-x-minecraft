package lab.owmcguest;

import com.google.gson.JsonObject;
import com.google.gson.JsonParser;
import com.sun.jna.*;
import java.nio.*;
import java.nio.file.*;
import java.util.Arrays;

/** Read-only original McCree roll execution. It never starts a native ability. */
final class NativeRollReader implements AutoCloseable {
    record State(long source,long model,long tick,boolean active,boolean directional,double speed,double seconds) {}
    private final NativeAbilityReader.Kernel kernel=Native.load("kernel32",NativeAbilityReader.Kernel.class);
    private Pointer handle;private JsonObject binding;private int pid;private long generation;
    String error="waiting for native roll binding";
    private long n(String key){return binding.get(key).getAsLong();}
    private byte[] read(long at,int size){
        if(at<0x10000||at>0x7fffffffffffL||size<1||size>4096)throw new IllegalArgumentException("roll read bounds");
        byte[] data=new byte[size];try(var count=new Memory(8)){
            if(!kernel.ReadProcessMemory(handle,Pointer.createConstant(at),data,size,count)||count.getLong(0)!=size)throw new IllegalStateException("roll read failed");
        }return data;
    }
    private static ByteBuffer bytes(byte[] data){return ByteBuffer.wrap(data).order(ByteOrder.LITTLE_ENDIAN);}
    private long q(long at){return bytes(read(at,8)).getLong();}
    private int i(long at){return bytes(read(at,4)).getInt();}
    private void verify(){
        if(kernel.WaitForSingleObject(handle,0)!=0x102||q(n("adminAddress"))!=n("admin")||i(n("admin")+0x220)!=(int)n("localId")
          ||i(n("reference")+0x94)!=(int)n("modelId")||i(n("model")+0x94)!=(int)n("modelId")||q(n("model")+0x28)!=n("admin")
          ||q(n("heroInfo")+0x98)!=0x02e0000000000042L||q(n("script")+0x150)!=0x05800000000001f0L
          ||q(n("script")+0x160)!=n("graph")||q(n("script")+0x98)!=n("bag")
          ||q(q(q(n("script")+0x10)+0x450)+8)!=n("model"))throw new IllegalArgumentException("native roll owner changed");
    }
    private long find(long address,long wanted,boolean wide){
        byte[] header=read(address,16);var h=bytes(header);long head=h.getLong(),count=h.getLong();
        if(count<0||count>4096)throw new IllegalArgumentException("roll map bounds");
        byte[] sentinel=read(head,32);if(sentinel[25]!=1)throw new IllegalArgumentException("roll map sentinel");
        long node=bytes(sentinel).getLong(8),parent=head,found=0;
        for(int depth=0;node!=head;depth++){
            if(depth>=64)throw new IllegalArgumentException("roll map depth");
            byte[] raw=read(node,40);var b=bytes(raw);
            if(raw[25]!=0||b.getLong(8)!=parent)throw new IllegalArgumentException("roll map changed");
            long key=wide?b.getLong(32):b.getInt(32);
            if(key==wanted){found=node+40;break;}
            parent=node;node=b.getLong(wanted<key?0:16);
        }
        if(!Arrays.equals(header,read(address,16)))throw new IllegalArgumentException("roll map header changed");return found;
    }
    private long[] state(long inner,int node){
        long row=inner==0?0:find(inner,node,false);if(row==0)return new long[]{0,1};
        byte[] a=read(row,9),b=read(row,9);
        if(!Arrays.equals(a,b))throw new IllegalArgumentException("roll state changed during read");
        long tick=bytes(a).getLong();if(tick<0||a[8]<0||a[8]>1)throw new IllegalArgumentException("roll state payload");
        return new long[]{tick,a[8]};
    }
    State poll(HostPoseReader.Pose host){
        if(host==null||host.flags()!=1){error="native camera unavailable";return null;}
        try{
            if(handle==null||pid!=host.pid()||generation!=host.generation()){
                close();String dir=System.getProperty("owmc.nativeEventsDirectory","");
                var path=Path.of(dir).resolve("native-roll-request-"+host.pid()+".json");
                if(dir.isBlank()||!Files.isRegularFile(path)){error="waiting for native roll binding";return null;}
                if(Files.size(path)>8192)throw new IllegalArgumentException("roll binding size");
                binding=JsonParser.parseString(Files.readString(path)).getAsJsonObject();
                if(n("version")!=1||n("pid")!=Integer.toUnsignedLong(host.pid())||n("resource")!=0x05800000000001f0L||n("hero")!=0x02e0000000000042L||n("node")!=4)throw new IllegalArgumentException("roll binding identity");
                handle=kernel.OpenProcess(0x100000|0x400|0x10,false,host.pid());if(handle==null)throw new IllegalStateException("roll process unavailable");
                try(var creation=new Memory(8);var exit=new Memory(8);var system=new Memory(8);var user=new Memory(8)){
                    if(!kernel.GetProcessTimes(handle,creation,exit,system,user)||creation.getLong(0)!=n("creation"))throw new IllegalArgumentException("roll process creation changed");
                }pid=host.pid();generation=host.generation();
            }
            verify();
            if(q(n("speed"))!=n("numericVtable")||q(n("timeout"))!=n("timeoutVtable"))throw new IllegalArgumentException("roll configuration type changed");
            var raw=bytes(read(n("speed")+0xa0,16));int kind=raw.getInt(12);
            double speed=kind==2?raw.getInt(0):kind==3?raw.getFloat(0):Double.NaN;
            double seconds=bytes(read(n("timeout")+16,4)).getFloat();
            if(!Double.isFinite(speed)||speed<=0||speed>100||!Double.isFinite(seconds)||seconds<=0||seconds>2)throw new IllegalArgumentException("roll configuration bounds");
            long inner=find(n("logger"),n("script"),true);long[] timer=state(inner,4);
            boolean active=timer[1]==0,directional=false;
            if(active){
                long[] input=state(inner,8),forward=state(inner,11);
                boolean hasInput=input[0]==timer[0],hasForward=forward[0]==timer[0];
                if(hasInput==hasForward)throw new IllegalArgumentException("roll direction action unavailable");
                directional=hasInput;
            }
            if(!Arrays.equals(timer,state(inner,4)))throw new IllegalArgumentException("roll timer changed during read");
            verify();error="";return new State(generation,n("modelId"),timer[0],active,directional,speed,seconds);
        }catch(Exception failure){error=failure.toString();close();return null;}
    }
    @Override public void close(){if(handle!=null)kernel.CloseHandle(handle);handle=null;binding=null;pid=0;generation=0;}
}
