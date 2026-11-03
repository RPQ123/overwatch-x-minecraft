package lab.owmcguest;

import com.google.gson.*;
import com.sun.jna.*;
import java.nio.*;
import java.nio.file.*;
import java.util.*;

/** Current/max/enabled base slots only, with owner, creation and typed-config guards. */
final class NativeHealthReader implements AutoCloseable {
    record State(long source,long model,long hero,double maximum,double current,byte[][] raw){}
    private final NativeAbilityReader.Kernel kernel=Native.load("kernel32",NativeAbilityReader.Kernel.class);
    private Pointer handle;private JsonObject binding;private int pid;private long source;
    private double[] amounts;String error="waiting for native health binding";
    private long n(String key){return binding.get(key).getAsLong();}
    private byte[] read(long address,int size){
        if(address<0x10000||address>0x7fffffffffffL||size<1||size>4096)throw new IllegalArgumentException("health read bounds");
        byte[] out=new byte[size];try(var count=new Memory(8)){
            if(!kernel.ReadProcessMemory(handle,Pointer.createConstant(address),out,size,count)||count.getLong(0)!=size)throw new IllegalStateException("health read failed");
        }return out;
    }
    private static ByteBuffer bytes(byte[] raw){return ByteBuffer.wrap(raw).order(ByteOrder.LITTLE_ENDIAN);}
    private long q(long address){return bytes(read(address,8)).getLong();}
    private int i(long address){return bytes(read(address,4)).getInt();}
    private void verify(){
        if(kernel.WaitForSingleObject(handle,0)!=0x102||q(n("adminAddress"))!=n("admin")||i(n("admin")+0x220)!=(int)n("localId")
            ||i(n("reference")+0x94)!=(int)n("modelId")||i(n("model")+0x94)!=(int)n("modelId")||q(n("heroInfo")+0x98)!=n("hero")
            ||q(n("health"))!=n("healthVtable")||q(n("health")+8)!=n("model")||(read(n("health")+0x10,1)[0]&255)!=0x28)
            throw new IllegalArgumentException("native health owner changed");
        var list=bytes(read(n("model")+0x50,16));long items=list.getLong();int count=list.getInt(),capacity=list.getInt();
        if(count<2||count>capacity||capacity>256)throw new IllegalArgumentException("health component bounds");
        var components=bytes(read(items,count*8));int found=0;
        for(int j=0;j<count-1;j++)if(components.getLong(j*8)==n("health"))found++;
        if(found!=1)throw new IllegalArgumentException("health component left model");
        for(var item:binding.getAsJsonArray("pools")){
            var p=item.getAsJsonObject();long variable=p.get("variable").getAsLong();
            if(q(variable)!=n("numericVtable")||!Arrays.equals(read(variable+0xa0,16),HexFormat.of().parseHex(p.get("amountRaw").getAsString())))
                throw new IllegalArgumentException("native health configuration changed");
        }
    }
    State poll(HostPoseReader.Pose host,long model,long hero){
        if(host==null||host.flags()!=1||model==0||hero==0)return null;
        try{
            if(handle==null||pid!=host.pid()||source!=host.generation()||n("modelId")!=model){
                close();String dir=System.getProperty("owmc.nativeEventsDirectory","");var path=Path.of(dir).resolve("native-health-request-"+host.pid()+".json");
                if(dir.isBlank()||!Files.isRegularFile(path)){error="waiting for native health binding";return null;}
                if(Files.size(path)>8192)throw new IllegalArgumentException("health binding size");binding=JsonParser.parseString(Files.readString(path)).getAsJsonObject();
                if(n("version")!=1||n("pid")!=Integer.toUnsignedLong(host.pid())||n("modelId")!=model||n("hero")!=hero
                    ||!binding.get("executableSha256").getAsString().equals("f73a747b7d63a07402958b2b2c4587125a46ef8e181281669da009d352308e9f"))throw new IllegalArgumentException("health binding identity");
                var pools=binding.getAsJsonArray("pools");if(pools.size()!=3)throw new IllegalArgumentException("health pool count");
                amounts=new double[3];for(int j=0;j<3;j++){
                    var p=pools.get(j).getAsJsonObject();if(p.get("offset").getAsInt()!=new int[]{0x98,0x1d8,0x318}[j])throw new IllegalArgumentException("health pool offset");
                    amounts[j]=p.get("amount").getAsDouble();
                }
                handle=kernel.OpenProcess(0x100000|0x400|0x10|0x28,false,host.pid());if(handle==null)throw new IllegalStateException("health process unavailable");
                try(var creation=new Memory(8);var exit=new Memory(8);var system=new Memory(8);var user=new Memory(8)){
                    if(!kernel.GetProcessTimes(handle,creation,exit,system,user)||creation.getLong(0)!=n("creation"))throw new IllegalArgumentException("health process creation changed");
                }pid=host.pid();source=host.generation();
            }
            verify();if(n("hero")!=hero)throw new IllegalArgumentException("health hero differs");byte[][] raw=new byte[3][];double total=0;
            for(int j=0;j<3;j++){raw[j]=read(n("health")+new int[]{0x98,0x1d8,0x318}[j],320);total+=bytes(raw[j]).getFloat(8);}
            double maximum=Arrays.stream(amounts).sum();SurvivalHealthPlan.plan(raw,amounts,Math.min(total,maximum));verify();
            error="";return new State(source,model,hero,maximum,total,raw);
        }catch(Exception failure){error=failure.toString();close();return null;}
    }
    boolean write(State expected,double target){
        if(handle==null||binding==null||expected.source()!=source||expected.model()!=n("modelId"))return false;
        try{
            var plan=SurvivalHealthPlan.plan(expected.raw(),amounts,target);verify();
            for(int j=0;j<3;j++)if(!Arrays.equals(read(n("health")+new int[]{0x98,0x1d8,0x318}[j],320),expected.raw()[j]))return false;
            for(int j=0;j<3;j++){
                if(Arrays.equals(Arrays.copyOf(expected.raw()[j],12),plan[j]))continue;
                verify();try(var count=new Memory(8)){
                    if(!kernel.WriteProcessMemory(handle,Pointer.createConstant(n("health")+new int[]{0x98,0x1d8,0x318}[j]),plan[j],12,count)||count.getLong(0)!=12)throw new IllegalStateException("native health write failed");
                }
            }
            verify();return true;
        }catch(Exception failure){error=failure.toString();close();return false;}
    }
    @Override public void close(){if(handle!=null)kernel.CloseHandle(handle);handle=null;binding=null;amounts=null;pid=0;source=0;}
}
