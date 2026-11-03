package lab.owmcguest;

import com.google.gson.*;
import com.sun.jna.*;
import java.nio.*;
import java.nio.file.*;
import java.util.*;

/** 语音挂接：只读当前原版弹药和满弹赋值节点；不执行原生函数、不写内存。 */
final class HeroVoiceAmmoReader implements AutoCloseable {
    record Sample(String slot,int ammo,int maximum,long commitTick,String evidence){}
    record Snapshot(long serial,List<Sample> samples,String error){}
    private final NativeAbilityReader.Kernel kernel=Native.load("kernel32",NativeAbilityReader.Kernel.class);
    private Pointer handle;
    private JsonObject binding;
    private long source,model,serial,nextPoll;
    private int pid;
    private Snapshot last=new Snapshot(0,List.of(),"waiting for native-voice-ammo binding");
    private static long n(JsonObject o,String key){return o.get(key).getAsLong();}
    private byte[] read(long at,int size){
        if(at<0x10000||at>0x7fffffffffffL||size<1||size>16384)throw new IllegalArgumentException("voice ammo read bounds");
        byte[] bytes=new byte[size];try(var count=new Memory(8)){
            if(!kernel.ReadProcessMemory(handle,Pointer.createConstant(at),bytes,size,count)||count.getLong(0)!=size)
                throw new IllegalStateException("voice ammo ReadProcessMemory");
        }return bytes;
    }
    private static ByteBuffer b(byte[] value){return ByteBuffer.wrap(value).order(ByteOrder.LITTLE_ENDIAN);}
    private long q(long at){return b(read(at,8)).getLong();}
    private int i(long at){return b(read(at,4)).getInt();}
    private void owner(HeroVoiceRuntime.Binding scope){
        if(kernel.WaitForSingleObject(handle,0)!=0x102||q(n(binding,"adminAddress"))!=n(binding,"admin")
            ||Integer.toUnsignedLong(i(n(binding,"admin")+0x220))!=n(binding,"localId")
            ||Integer.toUnsignedLong(i(n(binding,"reference")+0x94))!=scope.model()
            ||Integer.toUnsignedLong(i(n(binding,"model")+0x94))!=scope.model()
            ||q(n(binding,"model")+0x28)!=n(binding,"admin")||q(n(binding,"heroInfo")+0x98)!=scope.hero())
            throw new IllegalArgumentException("voice ammo current owner changed");
    }
    private void variable(JsonObject slot,String key,String vtable,String bucket,String resource){
        long bag=n(slot,"bag"),at=bag+0xa0+n(slot,bucket)*0x30;
        if(n(slot,bucket)<0||n(slot,bucket)>=16)throw new IllegalArgumentException("voice ammo bucket");
        byte[] header=read(at,16);var h=b(header);long items=h.getLong();int size=h.getInt(),capacity=h.getInt();
        if(size<0||size>capacity||capacity>512)throw new IllegalArgumentException("voice ammo variables");
        byte[] rows=size==0?new byte[0]:read(items,size*16);boolean found=false;
        for(int offset=0;offset<rows.length;offset+=16){var r=b(rows);if(r.getLong(offset)==n(slot,resource)&&r.getLong(offset+8)==n(slot,key))found=true;}
        if(!found||q(n(slot,key))!=n(slot,vtable)||!Arrays.equals(header,read(at,16)))throw new IllegalArgumentException("voice ammo numeric binding changed");
    }
    private int number(long object){
        byte[] first=read(object+0xa0,16),second=read(object+0xa0,16);
        if(!Arrays.equals(first,second))throw new IllegalArgumentException("voice ammo value changed during read");
        var data=b(first);int kind=data.getInt(12);double value=kind==2?data.getInt(0):kind==3?data.getFloat(0):Double.NaN;
        if(!Double.isFinite(value)||value<0||value>1000||value!=Math.rint(value))throw new IllegalArgumentException("voice ammo numeric bounds");
        return (int)value;
    }
    private int maximum(JsonObject slot){
        if(slot.get("capacityKind").getAsString().equals("bag")){
            variable(slot,"capacity","capacityVtable","capacityBucket","maximumResource");return number(n(slot,"capacity"));
        }
        long value=n(slot,"capacityValueAddress"),object=n(slot,"capacity");
        if(!slot.get("capacityKind").getAsString().equals("literal-int")||q(object)!=n(slot,"capacityVtable")||value<object+8||value>object+512)
            throw new IllegalArgumentException("voice ammo maximum literal");
        return i(value);
    }
    private long find(long address,long wanted,boolean wide){
        byte[] header=read(address,16);var h=b(header);long head=h.getLong(),count=h.getLong();
        if(count<0||count>4096)throw new IllegalArgumentException("voice ammo logger count");
        byte[] sentinel=read(head,32);if(sentinel[25]!=1)throw new IllegalArgumentException("voice ammo logger sentinel");
        long node=b(sentinel).getLong(8),parent=head,found=0;
        for(int depth=0;node!=head;depth++){
            if(depth>=64)throw new IllegalArgumentException("voice ammo logger depth");
            var row=b(read(node,40));if(row.get(25)!=0||row.getLong(8)!=parent)throw new IllegalArgumentException("voice ammo logger changed");
            long key=wide?row.getLong(32):row.getInt(32);
            if(key==wanted){found=node+40;break;}parent=node;node=row.getLong(wanted<key?0:16);
        }
        if(!Arrays.equals(header,read(address,16)))throw new IllegalArgumentException("voice ammo logger header changed");return found;
    }
    private long tick(long script,int index){
        long inner=find(n(binding,"logger"),script,true),row=inner==0?0:find(inner,index,false);
        if(row==0)return 0;byte[] a=read(row,9),c=read(row,9);
        if(!Arrays.equals(a,c)||b(a).getLong()<0||a[8]<0||a[8]>1)throw new IllegalArgumentException("voice ammo node snapshot");
        return b(a).getLong();
    }
    Snapshot poll(HostPoseReader.Pose host,HeroVoiceRuntime.Binding scope){
        long now=System.nanoTime();if(now<nextPoll)return last;nextPoll=now+100_000_000L;
        try{
            if(handle==null||pid!=host.pid()||source!=scope.source()||model!=scope.model()){
                close();String directory=System.getProperty("owmc.nativeEventsDirectory","");
                if(directory.isBlank())throw new IllegalStateException("native events directory missing");
                Path path=Path.of(directory).resolve("native-voice-ammo-request-"+host.pid()+".json");
                if(!Files.isRegularFile(path)||Files.size(path)>131072)throw new IllegalStateException("run prepare_hero_voice_ammo for current hero");
                binding=JsonParser.parseString(Files.readString(path)).getAsJsonObject();
                if(n(binding,"version")!=1||n(binding,"pid")!=Integer.toUnsignedLong(host.pid())||n(binding,"hero")!=scope.hero()
                    ||n(binding,"modelId")!=scope.model()||!binding.get("readOnly").getAsBoolean())throw new IllegalArgumentException("voice ammo file identity");
                handle=kernel.OpenProcess(0x100000|0x400|0x10,false,host.pid());if(handle==null)throw new IllegalStateException("voice ammo handle");
                try(var creation=new Memory(8);var exit=new Memory(8);var system=new Memory(8);var user=new Memory(8)){
                    if(!kernel.GetProcessTimes(handle,creation,exit,system,user)||creation.getLong(0)!=n(binding,"creation"))throw new IllegalArgumentException("voice ammo process creation");
                }pid=host.pid();source=scope.source();model=scope.model();
            }
            owner(scope);var samples=new ArrayList<Sample>();var slots=binding.getAsJsonArray("slots");
            if(slots.size()>8)throw new IllegalArgumentException("voice ammo slot count");
            for(var raw:slots){
                var slot=raw.getAsJsonObject();long script=n(slot,"script"),graph=n(slot,"graph");
                if(q(script+0x98)!=n(slot,"bag")||q(script+0x160)!=graph||q(script+0x150)!=n(slot,"resource")
                    ||q(q(q(script+0x10)+0x450)+8)!=n(binding,"model"))throw new IllegalArgumentException("voice ammo graph owner");
                variable(slot,"ammo","ammoVtable","bucket","currentResource");
                int maximum=maximum(slot);
                int ammo=number(n(slot,"ammo"));
                if(maximum<2||ammo>maximum||maximum!=n(slot,"maximum"))throw new IllegalArgumentException("voice ammo magazine changed");
                long storage=q(graph+0x50),flag=q(graph+0x58);if(flag!=1&&flag!=2)throw new IllegalArgumentException("voice ammo nodes storage");
                long first=q(storage),second=q(storage+8),items=flag==1?first:second,size=flag==1?second:first,commit=0;
                if(size<1||size>4096)throw new IllegalArgumentException("voice ammo nodes size");
                for(var nodeRaw:slot.getAsJsonArray("nodes")){
                    var node=nodeRaw.getAsJsonObject();int index=(int)n(node,"index");
                    if(index<0||index>=size||q(items+index*8L)!=n(node,"address")||q(n(node,"address"))!=n(node,"vtable"))
                        throw new IllegalArgumentException("voice ammo assignment node changed");
                    if(q(n(node,"maximumRefAddress"))!=n(node,"maximumConfig")||q(n(node,"maximumConfig"))!=n(node,"maximumConfigVtable")
                        ||maximum(node.getAsJsonObject("maximumBinding"))!=maximum)throw new IllegalArgumentException("voice ammo maximum reference changed");
                    commit=Math.max(commit,tick(script,index));
                }
                samples.add(new Sample(Long.toUnsignedString(script)+":"+n(slot,"currentResource"),ammo,maximum,commit,slot.get("evidence").getAsString()));
            }
            owner(scope);last=new Snapshot(++serial,List.copyOf(samples),samples.isEmpty()?"no declared reload assignment for this hero":"");
        }catch(Exception failure){close();last=new Snapshot(++serial,List.of(),failure.getMessage()==null?failure.toString():failure.getMessage());}
        return last;
    }
    void reset(){close();nextPoll=0;last=new Snapshot(++serial,List.of(),"waiting for current native ammo binding");}
    @Override public void close(){if(handle!=null)kernel.CloseHandle(handle);handle=null;binding=null;pid=0;source=model=0;}
}
