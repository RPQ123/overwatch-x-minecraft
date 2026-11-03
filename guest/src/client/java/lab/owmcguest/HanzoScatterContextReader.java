package lab.owmcguest;

import com.google.gson.*;
import com.sun.jna.*;
import java.nio.*;
import java.nio.file.*;
import java.util.*;

/** Read-only parameter enrichment of the existing Volley26 signal. Never enables
 * calibration, writes native memory, calls native evaluators or creates attacks. */
final class HanzoScatterContextReader implements AutoCloseable {
    private final NativeAbilityReader.Kernel kernel=Native.load("kernel32",NativeAbilityReader.Kernel.class);
    private Pointer handle;private JsonObject binding;private int pid;private long generation;
    private final Set<String> seen=new LinkedHashSet<>();
    private long n(String key){return binding.get(key).getAsLong();}
    private static ByteBuffer bytes(byte[] data){return ByteBuffer.wrap(data).order(ByteOrder.LITTLE_ENDIAN);}
    private byte[] read(long at,int length){
        if(at<0x10000||at>0x7fffffffffffL||length<1||length>4096)throw new IllegalArgumentException("Scatter memory bounds");
        byte[] data=new byte[length];try(var count=new Memory(8)){
            if(!kernel.ReadProcessMemory(handle,Pointer.createConstant(at),data,length,count)||count.getLong(0)!=length)throw new IllegalStateException("Scatter memory unavailable");
        }return data;
    }
    private long q(long at){return bytes(read(at,8)).getLong();}
    private int i(long at){return bytes(read(at,4)).getInt();}
    private void verify(){
        if(kernel.WaitForSingleObject(handle,0)!=0x102||q(n("adminAddress"))!=n("admin")||i(n("admin")+0x220)!=(int)n("localId")
            ||i(n("reference")+0x94)!=(int)n("modelId")||i(n("model")+0x94)!=(int)n("modelId")||q(n("model")+0x28)!=n("admin")
            ||q(n("heroInfo")+0x98)!=HanzoScatterContext.HERO||q(n("script")+0x150)!=0x05800000000000b9L
            ||q(n("script")+0x160)!=n("graph")||q(n("script")+0x98)!=n("bag")||q(q(q(n("script")+0x10)+0x450)+8)!=n("model"))throw new IllegalArgumentException("Scatter native owner changed");
        var guards=binding.getAsJsonArray("byteGuards");if(guards==null||guards.size()==0||guards.size()>192)throw new IllegalArgumentException("Scatter expression guards absent/bounds");
        int guardedBytes=0;
        for(var item:guards){var guard=item.getAsJsonObject();byte[] expected=HexFormat.of().parseHex(guard.get("hex").getAsString());
            guardedBytes+=expected.length;
            if(expected.length>4096||guardedBytes>16384||!Arrays.equals(expected,read(guard.get("address").getAsLong(),expected.length)))throw new IllegalArgumentException("Scatter pinned declaration changed");
        }
    }
    private long find(long address,long wanted,boolean wide){
        byte[] header=read(address,16);var h=bytes(header);long head=h.getLong(),count=h.getLong();
        if(count<0||count>4096)throw new IllegalArgumentException("Scatter logger map bounds");
        byte[] sentinel=read(head,32);if(sentinel[25]!=1)throw new IllegalArgumentException("Scatter logger sentinel");
        long node=bytes(sentinel).getLong(8),parent=head,found=0;
        for(int depth=0;node!=head;depth++){
            if(depth>=64)throw new IllegalArgumentException("Scatter logger depth");var raw=read(node,40);var b=bytes(raw);
            if(raw[25]!=0||b.getLong(8)!=parent)throw new IllegalArgumentException("Scatter logger changed");
            long key=wide?b.getLong(32):b.getInt(32);if(key==wanted){found=node+40;break;}parent=node;node=b.getLong(wanted<key?0:16);
        }
        if(!Arrays.equals(header,read(address,16)))throw new IllegalArgumentException("Scatter logger header changed");return found;
    }
    private void verifyTick(long tick){
        long inner=find(n("logger"),n("script"),true),state=inner==0?0:find(inner,26,false);
        if(state==0)throw new IllegalArgumentException("Scatter native node receipt absent");
        byte[] a=read(state,9),b=read(state,9);
        if(!Arrays.equals(a,b)||bytes(a).getLong()!=tick||a[8]<0||a[8]>1)throw new IllegalArgumentException("Scatter native node tick changed");
    }
    private record Primitive(long object,double value){}
    private Map<Long,Primitive> numbers(){
        Set<Long> wanted=Set.of(0x0d800000000002a5L,0x0d800000000001dcL,0x0d80000000000980L);var found=new HashMap<Long,Primitive>();
        for(int bucket=0;bucket<16;bucket++){
            long at=n("bag")+0xa0+bucket*0x30L;byte[] header=read(at,16);var b=bytes(header);long items=b.getLong();int count=b.getInt(),capacity=b.getInt();
            if(count<0||count>capacity||capacity>256)throw new IllegalArgumentException("Scatter numeric map bounds");
            if(count>0){var entries=bytes(read(items,count*16));for(int j=0;j<count;j++){
                long key=entries.getLong(j*16),object=entries.getLong(j*16+8);if(!wanted.contains(key))continue;
                if(found.containsKey(key)||q(object)!=n("numericVtable"))throw new IllegalArgumentException("Scatter numeric source not unique/typed: "+Long.toHexString(key));
                byte[] raw=read(object+0xa0,16);var value=bytes(raw);int kind=value.getInt(12);double scalar=kind==2?value.getInt():kind==3?value.getFloat():Double.NaN;
                if(!Double.isFinite(scalar)||!Arrays.equals(raw,read(object+0xa0,16)))throw new IllegalArgumentException("Scatter numeric value changed/type: "+Long.toHexString(key));
                found.put(key,new Primitive(object,scalar));
            }}
            if(!Arrays.equals(header,read(at,16)))throw new IllegalArgumentException("Scatter numeric map changed");
        }
        if(found.size()!=3)throw new IllegalArgumentException("typed native q2a5/1dc/980 unavailable");return Map.copyOf(found);
    }
    HanzoScatterContext.Parameters poll(HostPoseReader.Pose host,long model,long nodeTick){
        try{
            String directory=System.getProperty("owmc.nativeEventsDirectory","");if(directory.isBlank())throw new IllegalArgumentException("Scatter parameter directory unavailable");
            var root=Path.of(directory);
            if(binding==null||pid!=host.pid()||generation!=host.generation()||n("modelId")!=model){
                close();var path=root.resolve("native-hanzoScatterContext-request-"+host.pid()+".json");
                if(!Files.isRegularFile(path)||Files.size(path)>65536)throw new IllegalArgumentException("Scatter context binding absent; unchanged MC fallback");
                binding=JsonParser.parseString(Files.readString(path)).getAsJsonObject();
                if(n("version")!=1||n("pid")!=Integer.toUnsignedLong(host.pid())||n("hero")!=HanzoScatterContext.HERO||n("modelId")!=model)throw new IllegalArgumentException("Scatter context binding identity");
                if(!binding.get("available").getAsBoolean())throw new IllegalArgumentException(binding.get("reason").getAsString());
                handle=kernel.OpenProcess(0x100000|0x1000|0x10,false,host.pid());if(handle==null)throw new IllegalStateException("Scatter read-only process unavailable");
                try(var creation=new Memory(8);var exit=new Memory(8);var system=new Memory(8);var user=new Memory(8)){
                    if(!kernel.GetProcessTimes(handle,creation,exit,system,user)||creation.getLong(0)!=n("creation"))throw new IllegalArgumentException("Scatter process creation changed");
                }pid=host.pid();generation=host.generation();
            }
            var path=root.resolve("native-emissions-"+host.pid()+".json");if(Files.size(path)>524288)throw new IllegalArgumentException("Scatter factory report bounds");
            var report=JsonParser.parseString(Files.readString(path)).getAsJsonObject();
            if(!report.get("factoryCalibration").getAsBoolean())throw new IllegalArgumentException("factory parameter transport disabled; unchanged MC fallback");
            verify();verifyTick(nodeTick);var first=numbers();verify();verifyTick(nodeTick);var second=numbers();
            if(!first.equals(second))throw new IllegalArgumentException("Scatter q/1dc/980 changed during snapshot");verify();verifyTick(nodeTick);
            long now=System.currentTimeMillis();var values=new HanzoScatterContext.Numbers(first.get(0x0d800000000002a5L).value(),first.get(0x0d800000000001dcL).value(),first.get(0x0d80000000000980L).value(),now);
            var expected=new HanzoScatterContext.Expected(pid,n("creation"),generation,model,n("volleyKey"),nodeTick);
            var result=HanzoScatterContext.resolve(report,expected,values,now);
            if(!seen.add(result.identity()))throw new IllegalArgumentException("Scatter factory parameter replay refused");
            if(seen.size()>512)seen.remove(seen.iterator().next());return result;
        }catch(Exception failure){String reason=failure.toString();close();return HanzoScatterContext.fallback(reason);}
    }
    @Override public void close(){if(handle!=null)kernel.CloseHandle(handle);handle=null;binding=null;pid=0;generation=0;seen.clear();}
}
