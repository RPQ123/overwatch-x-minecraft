package lab.owmcguest;

import com.google.gson.*;
import com.sun.jna.*;
import java.nio.*;
import java.nio.file.*;
import java.util.*;
import java.util.function.BooleanSupplier;

/** Explicit F11 convenience. Reuses the measured ability-state layout from
 * NativeAbilityReader.resetCooldown; never invokes native callbacks or changes definitions. */
final class NativeCooldownRefill {
    private final NativeAbilityReader.Kernel kernel=Native.load("kernel32",NativeAbilityReader.Kernel.class);
    private Pointer handle;
    private JsonObject binding;
    private long component,vtable;
    private byte[] scriptsHeader,scripts;
    private BooleanSupplier admitted;
    private record Slot(long state,long script,long graph,long resource,int index,long definition,byte[] stateHeader,byte[] states){}
    private long n(String key){return binding.get(key).getAsLong();}
    private byte[] read(long at,int size){
        if(at<0x10000||at>0x7fffffffffffL||size<1||size>32768)throw new IllegalStateException("cooldown read bounds");
        byte[] data=new byte[size];try(var count=new Memory(8)){
            if(!kernel.ReadProcessMemory(handle,Pointer.createConstant(at),data,size,count)||count.getLong(0)!=size)throw new IllegalStateException("cooldown read failed");
        }return data;
    }
    private static ByteBuffer bytes(byte[] data){return ByteBuffer.wrap(data).order(ByteOrder.LITTLE_ENDIAN);}
    private long q(long at){return bytes(read(at,8)).getLong();}
    private int i(long at){return bytes(read(at,4)).getInt();}
    private byte[] vector(long at,int limit){
        var h=bytes(read(at,16));long data=h.getLong();int count=h.getInt(),capacity=h.getInt();
        if(count<0||count>capacity||capacity>limit)throw new IllegalStateException("cooldown vector bounds");
        return count==0?new byte[0]:read(data,count*8);
    }
    private long[] definitions(long graph){
        var h=bytes(read(graph+0x60,16));long storage=h.getLong(),flag=h.getLong();
        if(storage==0)return new long[0];
        if(flag!=1&&flag!=2)throw new IllegalStateException("cooldown definition storage");
        var b=bytes(read(storage,16));long first=b.getLong(),second=b.getLong(),count=flag==1?second:first,items=flag==1?first:second;
        if(count<0||count>4096)throw new IllegalStateException("cooldown definition bounds");
        long[] result=new long[(int)count];if(count>0){var values=bytes(read(items,(int)count*8));for(int k=0;k<count;k++)result[k]=values.getLong();}return result;
    }
    private void verifyOwner(){
        if(!admitted.getAsBoolean()||kernel.WaitForSingleObject(handle,0)!=0x102||q(n("adminAddress"))!=n("admin")||i(n("admin")+0x220)!=(int)n("localId")
            ||i(n("reference")+0x94)!=(int)n("modelId")||i(n("model")+0x94)!=(int)n("modelId")||q(n("model")+0x28)!=n("admin")||q(n("heroInfo")+0x98)!=n("hero"))
            throw new IllegalStateException("cooldown current owner changed");
        long controller=q(n("reference")+8);
        if(q(controller+0x28)!=n("admin")||i(controller+0x94)!=(int)n("localId")||q(n("heroInfo")+8)!=controller)throw new IllegalStateException("cooldown controller changed");
        var components=bytes(vector(n("model")+0x50,256));int found=0;
        for(int k=0;k<components.capacity()/8-1;k++)if(components.getLong(k*8)==component)found++;
        if(found!=1||q(component+8)!=n("model")||(read(component+0x10,1)[0]&255)!=0x23)throw new IllegalStateException("cooldown script component changed");
    }
    private float verify(Slot slot){
        verifyOwner();
        if(!Arrays.equals(scriptsHeader,read(component+0x1b0,16))||!Arrays.equals(scripts,vector(component+0x1b0,512))
            ||q(slot.script()+0x160)!=slot.graph()||q(slot.script()+0x150)!=slot.resource()||q(q(q(slot.script()+0x10)+0x450)+8)!=n("model")
            ||!Arrays.equals(slot.stateHeader(),read(slot.script()+0xa0,16))||!Arrays.equals(slot.states(),vector(slot.script()+0xa0,4096))
            ||q(slot.state())!=vtable||q(slot.state()+0x78)!=slot.script()||i(slot.state()+0x70)!=slot.index())throw new IllegalStateException("cooldown state owner changed");
        var defs=definitions(slot.graph());
        if(slot.index()<0||slot.index()>=defs.length||defs[slot.index()]!=slot.definition())throw new IllegalStateException("cooldown graph membership changed");
        float remaining=bytes(read(slot.state()+0x150,4)).getFloat();
        if(!Float.isFinite(remaining)||remaining<0||remaining>120)throw new IllegalStateException("cooldown seconds bounds");
        for(int offset:new int[]{0x144,0x146})if((read(slot.state()+offset,1)[0]&255)>1)throw new IllegalStateException("cooldown mirror flags changed");
        return remaining;
    }
    private void write(long at,byte[] value){try(var count=new Memory(8)){
        if(!kernel.WriteProcessMemory(handle,Pointer.createConstant(at),value,value.length,count)||count.getLong(0)!=value.length)throw new IllegalStateException("cooldown write failed");
    }}
    int restore(HostPoseReader.Pose host,long model,long hero,BooleanSupplier fresh){
        if(host==null||host.flags()!=1||model==0||hero==0||!fresh.getAsBoolean())throw new IllegalStateException("cooldown native admission required");
        try{
            var dir=System.getProperty("owmc.nativeEventsDirectory","");if(dir.isBlank())throw new IllegalStateException("cooldown binding unavailable");
            var path=Path.of(dir).resolve("native-locomotion-request-"+host.pid()+".json");
            if(!Files.isRegularFile(path)||Files.size(path)>8192)throw new IllegalStateException("cooldown binding unavailable");
            binding=JsonParser.parseString(Files.readString(path)).getAsJsonObject();admitted=fresh;
            if(n("version")!=2||n("pid")!=Integer.toUnsignedLong(host.pid())||n("modelId")!=model||n("hero")!=hero)throw new IllegalStateException("cooldown binding identity");
            handle=kernel.OpenProcess(0x100000|0x400|0x10|0x28,false,host.pid());if(handle==null)throw new IllegalStateException("cooldown process unavailable");
            try(var creation=new Memory(8);var exit=new Memory(8);var system=new Memory(8);var user=new Memory(8)){
                if(!kernel.GetProcessTimes(handle,creation,exit,system,user)||creation.getLong(0)!=n("creation"))throw new IllegalStateException("cooldown process creation changed");
            }
            var components=bytes(vector(n("model")+0x50,256));component=0;
            for(int k=0;k<components.capacity()/8-1;k++){
                long value=components.getLong(k*8);
                if(value!=0&&(read(value+0x10,1)[0]&255)==0x23){if(component!=0)throw new IllegalStateException("cooldown duplicate script component");component=value;}
            }
            if(component==0)throw new IllegalStateException("cooldown script component absent");
            verifyOwner();vtable=n("adminAddress")-0x17b7f90L+0x15d7c98L;
            scriptsHeader=read(component+0x1b0,16);scripts=vector(component+0x1b0,512);var pointers=bytes(scripts);var slots=new ArrayList<Slot>();var seen=new HashSet<Long>();
            int inspected=0;
            for(int k=0;k<pointers.capacity()/8;k++){
                long script=pointers.getLong(k*8);if(script==0)continue;
                long graph=q(script+0x160),resource=q(script+0x150);if((resource>>>48)!=0x0580)throw new IllegalStateException("cooldown resource type");
                byte[] header=read(script+0xa0,16),states=vector(script+0xa0,4096);var values=bytes(states);var defs=definitions(graph);
                inspected+=values.capacity()/8;if(inspected>32768)throw new IllegalStateException("cooldown scan bound");
                for(int j=0;j<values.capacity()/8;j++){
                    long state=values.getLong(j*8);if(state==0||q(state)!=vtable)continue;
                    int index=i(state+0x70);
                    if(index<0||index>=defs.length||!seen.add(state)||slots.size()>=128)throw new IllegalStateException("cooldown state membership");
                    var slot=new Slot(state,script,graph,resource,index,defs[index],header,states);verify(slot);slots.add(slot);
                }
            }
            if(slots.isEmpty())throw new IllegalStateException("cooldown ability states absent");
            synchronized(NativeMeterWrites.LOCK){
                // Preflight every slot before the first write. Revalidate each current owner immediately before writing.
                for(var slot:slots)verify(slot);
                for(var slot:slots){verify(slot);write(slot.state()+0x150,new byte[4]);verifyOwner();write(slot.state()+0x144,new byte[]{1});verifyOwner();write(slot.state()+0x146,new byte[]{1});if(verify(slot)!=0)throw new IllegalStateException("cooldown readback differs");}
            }
            return slots.size();
        }catch(java.io.IOException failure){throw new IllegalStateException("cooldown binding read failed",failure);}
        finally{if(handle!=null)kernel.CloseHandle(handle);handle=null;binding=null;}
    }
}
