package lab.owmcguest;

import com.google.gson.*;
import com.sun.jna.*;
import java.nio.*;
import java.nio.file.*;
import java.util.*;

/** Bounded read-only native Begin/End snapshots for measured original skill nodes. */
final class NativeSkillReader implements AutoCloseable {
    record Entry(long tick,boolean active){}
    record Geometry(double damage,double radius,double[] offset,double eye){}
    record Healing(double amount,double interval){}
    record State(long source,long model,long hero,Map<String,Entry> entries,Geometry geometry){
        boolean active(String name){var e=entries.get(name);return e!=null&&e.active();}
    }
    private final NativeAbilityReader.Kernel kernel=Native.load("kernel32",NativeAbilityReader.Kernel.class);
    private final boolean melee,sustain,biotic,pulse,recall,wraith,shadow,grapple,venom,blizzard;
    /** 表驱动的新技能绑定：名称 -> 英雄、原版 graph、节点名->索引（与 tools/prepare_native_*.py 写出的 JSON 一致）。 */
    record Spec(long hero,long resource,Map<String,Integer> states){
        boolean matches(JsonObject s){if(s.size()!=states.size())return false;
            for(var e:states.entrySet()){var o=s.getAsJsonObject(e.getKey());if(o==null||o.get("index").getAsInt()!=e.getValue())return false;}return true;}
    }
    /** 新英雄模块在静态初始化时调用 register 登记自己的规格，无需修改本文件。 */
    static void register(String name,Spec spec){if(GENERIC.putIfAbsent(name,spec)!=null&&!GENERIC.get(name).equals(spec))throw new IllegalStateException("duplicate skill spec "+name);}
    static final Map<String,Spec> GENERIC=new java.util.concurrent.ConcurrentHashMap<>(Map.of(
        "junkPrimary",new Spec(0x02e0000000000065L,0x058000000000022bL,Map.of("volley",31)),
        "junkMine",new Spec(0x02e0000000000065L,0x058000000000096aL,Map.of("throw",12,"anim",6)),
        "junkTrap",new Spec(0x02e0000000000065L,0x05800000000009baL,Map.of("throw",7,"anim",14)),
        "iceWall",new Spec(0x02e00000000000ddL,0x0580000000000622L,Map.of("preview",2,"confirm",19)),
        "torbTurret",new Spec(0x02e0000000000006L,0x05800000000000f4L,Map.of("ghost",22,"anim",29)),
        "torbArmor",new Spec(0x02e0000000000006L,0x05800000000001ccL,Map.of("throw",5)),
        "hanzoSkills",new Spec(0x02e0000000000005L,0x05800000000000b9L,Map.of("scatter",26,"dragon",76))));
    private final Spec spec;private final String purposeName;
    NativeSkillReader(){this(false);}
    NativeSkillReader(boolean melee){this.spec=null;this.purposeName="";this.melee=melee;this.sustain=false;this.biotic=false;this.pulse=false;this.recall=false;this.wraith=false;this.shadow=false;this.grapple=false;this.venom=false;this.blizzard=false;}
    NativeSkillReader(String purpose){spec=GENERIC.get(purpose);purposeName=purpose;if(spec!=null){melee=sustain=biotic=pulse=recall=wraith=shadow=grapple=venom=blizzard=false;return;}if(!java.util.Set.of("sustain","biotic","pulse","recall","wraith","shadow","grapple","venom","blizzard").contains(purpose))throw new IllegalArgumentException("skill purpose");melee=false;sustain=purpose.equals("sustain");biotic=purpose.equals("biotic");pulse=purpose.equals("pulse");recall=purpose.equals("recall");wraith=purpose.equals("wraith");shadow=purpose.equals("shadow");grapple=purpose.equals("grapple");venom=purpose.equals("venom");blizzard=purpose.equals("blizzard");}
    private Pointer handle;private JsonObject binding;private int pid;private long generation;
    String error="waiting for native skill binding";
    private long n(String key){return binding.get(key).getAsLong();}
    /** Addresses from the same binding just verified by poll/deadeyeGeometry. */
    long[] deadeyeInputBinding(){
        if(binding==null||n("hero")!=NativeDeadeyeRuntime.HERO)throw new IllegalStateException("Deadeye input binding absent");
        return new long[]{n("script"),n("logger")};
    }
    private byte[] read(long at,int size){
        if(at<0x10000||at>0x7fffffffffffL||size<1||size>4096)throw new IllegalArgumentException("skill read bounds");
        byte[] data=new byte[size];try(var count=new Memory(8)){
            if(!kernel.ReadProcessMemory(handle,Pointer.createConstant(at),data,size,count)||count.getLong(0)!=size)throw new IllegalStateException("skill read failed");
        }return data;
    }
    private static ByteBuffer bytes(byte[] data){return ByteBuffer.wrap(data).order(ByteOrder.LITTLE_ENDIAN);}
    private long q(long at){return bytes(read(at,8)).getLong();}
    private int i(long at){return bytes(read(at,4)).getInt();}
    private void verify(){
        if(kernel.WaitForSingleObject(handle,0)!=0x102||q(n("adminAddress"))!=n("admin")||i(n("admin")+0x220)!=(int)n("localId")
            ||i(n("reference")+0x94)!=(int)n("modelId")||i(n("model")+0x94)!=(int)n("modelId")||q(n("model")+0x28)!=n("admin")
            ||q(n("heroInfo")+0x98)!=n("hero")||q(n("script")+0x150)!=n("resource")||q(n("script")+0x160)!=n("graph")
            ||q(n("script")+0x98)!=n("bag")||q(q(q(n("script")+0x10)+0x450)+8)!=n("model"))throw new IllegalArgumentException("native skill owner changed");
        long storage=q(n("graph")+0x50),flag=q(n("graph")+0x58);
        if(flag!=1&&flag!=2)throw new IllegalArgumentException("skill node storage");
        long first=q(storage),second=q(storage+8),items=flag==1?first:second,count=flag==1?second:first;
        if(count<1||count>4096)throw new IllegalArgumentException("skill node count");
        for(var field:binding.getAsJsonObject("states").entrySet()){
            var node=field.getValue().getAsJsonObject();int index=node.get("index").getAsInt();long address=node.get("address").getAsLong();
            if(index<0||index>=count||q(items+index*8L)!=address||q(address)!=node.get("vtable").getAsLong())throw new IllegalArgumentException("skill definition changed");
        }
    }
    private long find(long address,long wanted,boolean wide){
        byte[] header=read(address,16);var h=bytes(header);long head=h.getLong(),count=h.getLong();
        if(count<0||count>4096)throw new IllegalArgumentException("skill map bounds");
        byte[] sentinel=read(head,32);if(sentinel[25]!=1)throw new IllegalArgumentException("skill map sentinel");
        long node=bytes(sentinel).getLong(8),parent=head,found=0;
        for(int depth=0;node!=head;depth++){
            if(depth>=64)throw new IllegalArgumentException("skill map depth");
            byte[] raw=read(node,40);var b=bytes(raw);
            if(raw[25]!=0||b.getLong(8)!=parent)throw new IllegalArgumentException("skill map changed");
            long key=wide?b.getLong(32):b.getInt(32);
            if(key==wanted){found=node+40;break;}parent=node;node=b.getLong(wanted<key?0:16);
        }
        if(!Arrays.equals(header,read(address,16)))throw new IllegalArgumentException("skill map header changed");return found;
    }
    private Entry state(long inner,int node){
        long row=inner==0?0:find(inner,node,false);if(row==0)return new Entry(0,false);
        byte[] a=read(row,9),b=read(row,9);if(!Arrays.equals(a,b))throw new IllegalArgumentException("skill state changed during read");
        long tick=bytes(a).getLong();if(tick<0||a[8]<0||a[8]>1)throw new IllegalArgumentException("skill state payload");
        return new Entry(tick,a[8]==0);
    }
    private Geometry geometry(){
        int bucket=(int)n("damageBucket");if(bucket<0||bucket>=16)throw new IllegalArgumentException("melee damage bucket");
        var h=bytes(read(n("bag")+0xa0+bucket*0x30,16));long items=h.getLong();int count=h.getInt(),capacity=h.getInt();
        if(count<1||count>capacity||capacity>256)throw new IllegalArgumentException("melee damage members");
        var pairs=bytes(read(items,count*16));boolean found=false;
        for(int j=0;j<count;j++)if(pairs.getLong(j*16)==0x0d800000000001dcL&&pairs.getLong(j*16+8)==n("damage"))found=true;
        var states=binding.getAsJsonObject("states");long strike=states.getAsJsonObject("strike").get("address").getAsLong(),modify=states.getAsJsonObject("modify").get("address").getAsLong();
        if(!found||q(n("damage"))!=n("numericVtable")||q(strike+0x130)!=n("offset")||q(strike+0x140)!=n("radius")
            ||q(modify+0x108)!=n("health")||q(n("health")+0x38)!=n("damageConfig")||q(n("radius"))!=n("radiusVtable")||q(n("offset"))!=n("offsetVtable"))throw new IllegalArgumentException("native melee configuration changed");
        var raw=bytes(read(n("damage")+0xa0,16));int kind=raw.getInt(12);double damage=kind==2?raw.getInt():kind==3?raw.getFloat():Double.NaN;
        var vector=bytes(read(n("offset")+16,12));double[] offset={vector.getFloat(),vector.getFloat(),vector.getFloat()};double radius=i(n("radius")+16),eye=binding.get("eye").getAsDouble();
        if(!Double.isFinite(damage)||damage<=0||damage>1000||radius!=1||!Arrays.equals(offset,new double[]{0,1.5,1.5})||!Double.isFinite(eye)||eye<.5||eye>2.5)throw new IllegalArgumentException("native melee numeric bounds");
        return new Geometry(damage,radius,offset,eye);
    }
    private long array(long address,long wantedCount){
        long storage=q(address),flag=q(address+8);if(flag!=1&&flag!=2)throw new IllegalArgumentException("healing array storage");
        long a=q(storage),b=q(storage+8),count=flag==1?b:a;
        if(count!=wantedCount)throw new IllegalArgumentException("healing array count");return flag==1?a:b;
    }
    Healing healing(){
        try{
            if(!sustain||binding==null)throw new IllegalArgumentException("healing binding unavailable");verify();
            var v=binding.getAsJsonObject("healing");java.util.function.ToLongFunction<String> at=k->v.get(k).getAsLong();
            long node=binding.getAsJsonObject("states").getAsJsonObject("heal").get("address").getAsLong();
            long health=at.applyAsLong("health"),amount=at.applyAsLong("amount"),interval=at.applyAsLong("interval"),target=at.applyAsLong("target");
            if(q(node+0x108)!=health||q(health+0x38)!=amount||q(amount)!=at.applyAsLong("amountVtable")||q(node+0x100)!=interval||q(interval)!=at.applyAsLong("intervalVtable")
                ||q(node+0x110)!=target||q(target)!=at.applyAsLong("targetVtable"))throw new IllegalArgumentException("healing source changed");
            double value=i(amount+16),duration;
            if(n("hero")==0x02e0000000000015L){duration=i(interval+16);if(duration!=1)throw new IllegalArgumentException("repair interval changed");}
            else{
                long code=array(interval+0x20,6),constants=array(interval+0x40,1),dynamics=array(interval+0x30,1),config=at.applyAsLong("dynamicConfig"),numeric=at.applyAsLong("duration");
                if(code!=at.applyAsLong("code")||constants!=at.applyAsLong("constants")||dynamics!=at.applyAsLong("dynamics")||q(dynamics)!=config||q(config)!=at.applyAsLong("dynamicVtable")
                    ||!Arrays.equals(read(code,6),new byte[]{31,0,70,0,101,0})||i(constants)!=Float.floatToRawIntBits(.1f)||q(numeric)!=at.applyAsLong("numericVtable"))throw new IllegalArgumentException("Cryo duration expression changed");
                long path=array(config+0x10,1);if(q(path+8)!=0x0d80000000000237L)throw new IllegalArgumentException("Cryo duration path changed");
                int bucket=(int)at.applyAsLong("durationBucket");if(bucket<0||bucket>=16)throw new IllegalArgumentException("Cryo duration bucket");
                var h=bytes(read(n("bag")+0xa0+bucket*0x30,16));long items=h.getLong();int count=h.getInt(),capacity=h.getInt();
                if(count<1||count>capacity||capacity>256)throw new IllegalArgumentException("Cryo duration membership bounds");
                var pairs=bytes(read(items,count*16));boolean found=false;for(int j=0;j<count;j++)if(pairs.getLong(j*16)==0x0d80000000000237L&&pairs.getLong(j*16+8)==numeric)found=true;
                if(!found)throw new IllegalArgumentException("Cryo duration membership changed");
                var raw=bytes(read(numeric+0xa0,16));int kind=raw.getInt(12);duration=(kind==2?raw.getInt():kind==3?raw.getFloat():Double.NaN)-.1f;
            }
            if(!Double.isFinite(value)||value<=0||value>1000||!Double.isFinite(duration)||duration<.1||duration>10)throw new IllegalArgumentException("healing numeric bounds");
            verify();return new Healing(value,duration);
        }catch(Exception failure){error=failure.toString();close();return null;}
    }
    java.util.List<double[]> deflectBoxes(){
        try{
            if(melee||binding==null||n("hero")!=0x02e0000000000029L)throw new IllegalArgumentException("Deflect owner unavailable");verify();
            var definition=binding.getAsJsonObject("deflectBoxes");long field=definition.get("field").getAsLong(),storage=q(field),flag=q(field+8);
            long node=binding.getAsJsonObject("states").getAsJsonObject("deflect").get("address").getAsLong();
            if(field!=node+0x100||(flag!=1&&flag!=2))throw new IllegalArgumentException("Deflect box field changed");
            long a=q(storage),b=q(storage+8),items=flag==1?a:b,count=flag==1?b:a;
            if(count!=3||items!=definition.get("items").getAsLong())throw new IllegalArgumentException("Deflect box list changed");
            var configs=definition.getAsJsonArray("boxes");if(configs.size()!=3)throw new IllegalArgumentException("Deflect box binding count");
            java.util.List<double[]> boxes=new java.util.ArrayList<>();
            for(int j=0;j<3;j++){
                var config=configs.get(j).getAsJsonObject();long first=q(items+j*16L),second=q(items+j*16L+8);
                if(first!=config.get("first").getAsLong()||second!=config.get("second").getAsLong()||q(first)!=config.get("firstVtable").getAsLong()||q(second)!=config.get("secondVtable").getAsLong())throw new IllegalArgumentException("Deflect corner owner changed");
                var lo=bytes(read(first+16,12));var hi=bytes(read(second+16,12));double[] box=new double[6];
                for(int k=0;k<3;k++){double x=lo.getFloat(),y=hi.getFloat();if(!Double.isFinite(x)||!Double.isFinite(y)||Math.abs(x)>8||Math.abs(y)>8)throw new IllegalArgumentException("Deflect corner bounds");box[k]=Math.min(x,y);box[k+3]=Math.max(x,y);}boxes.add(box);
            }
            verify();return java.util.List.copyOf(boxes);
        }catch(Exception failure){error=failure.toString();close();return null;}
    }
    double[] visorGeometry(){
        try{
            if(binding==null||n("hero")!=0x02e000000000006eL)throw new IllegalArgumentException("Visor owner unavailable");verify();
            var geometry=binding.getAsJsonObject("visorGeometry");double[] values=new double[2];int j=0;
            long node=binding.getAsJsonObject("states").getAsJsonObject("visor").get("address").getAsLong();
            for(String name:new String[]{"radius","angle"}){
                var g=geometry.getAsJsonObject(name);long field=g.get("field").getAsLong(),object=g.get("object").getAsLong();
                if(field!=node+(name.equals("radius")?0x140:0x108)||q(field)!=object||q(object)!=g.get("vtable").getAsLong())throw new IllegalArgumentException("Visor geometry changed");
                long address=g.get("valueAddress").getAsLong();boolean integer=g.get("integer").getAsBoolean();
                if(integer?address!=object+16:(array(object+0x40,1)!=address||!Arrays.equals(read(array(object+0x20,3),3),new byte[]{70,0,0})))throw new IllegalArgumentException("Visor literal expression changed");
                double value=integer?i(address):Float.intBitsToFloat(i(address));
                if(value!=45||value!=g.get("value").getAsDouble())throw new IllegalArgumentException("Visor numeric geometry changed");values[j++]=value;
            }verify();return values;
        }catch(Exception failure){error=failure.toString();close();return null;}
    }
    double[] deadeyeGeometry(){
        try{
            if(binding==null||n("hero")!=NativeDeadeyeRuntime.HERO)throw new IllegalArgumentException("Deadeye owner unavailable");verify();
            var geometry=binding.getAsJsonObject("deadeyeGeometry");double[] values=new double[5];int j=0;
            long storage=q(n("graph")+0x50),flag=q(n("graph")+0x58),items=q(storage+(flag==1?0:8)),count=q(storage+(flag==1?8:0));
            for(String name:new String[]{"radius","angle","rate","cap"}){
                var g=geometry.getAsJsonObject(name);long node=g.get("node").getAsLong(),definition=g.get("definition").getAsLong(),field=g.get("field").getAsLong(),object=g.get("object").getAsLong();
                int offset=switch(name){case "radius"->0x140;case "angle"->0x108;case "rate"->0x118;default->0x128;};
                double expected=switch(name){case "radius"->70;case "angle"->105;case "rate"->160;default->1000;};
                if(node>=count||q(items+node*8)!=definition||field!=definition+offset||q(field)!=object||q(object)!=g.get("vtable").getAsLong()||i(object+16)!=expected||g.get("value").getAsDouble()!=expected)throw new IllegalArgumentException("Deadeye original parameter changed");
                values[j++]=expected;
            }
            var g=geometry.getAsJsonObject("duration");long object=g.get("object").getAsLong();int bucket=g.get("bucket").getAsInt();
            if(bucket<0||bucket>15||q(object)!=g.get("vtable").getAsLong())throw new IllegalArgumentException("Deadeye duration owner");
            var h=bytes(read(n("bag")+0xa0+bucket*0x30,16));long array=h.getLong();int size=h.getInt(),capacity=h.getInt();
            if(size<1||size>capacity||capacity>512)throw new IllegalArgumentException("Deadeye duration members");
            var pairs=bytes(read(array,size*16));boolean found=false;
            for(int k=0;k<size;k++)if(pairs.getLong(k*16)==0x0d80000000000237L&&pairs.getLong(k*16+8)==object)found=true;
            var raw=bytes(read(object+0xa0,16));int type=raw.getInt(12);double duration=type==2?raw.getInt():type==3?raw.getFloat():Double.NaN;
            if(!found||duration!=10||g.get("value").getAsDouble()!=10)throw new IllegalArgumentException("Deadeye duration changed");
            values[4]=duration;verify();return values;
        }catch(Exception e){error=e.toString();close();return null;}
    }
    double[] bioticParameters(){
        try{
            if(!biotic||binding==null)throw new IllegalArgumentException("Biotic binding unavailable");verify();
            long graph=n("fieldGraph");if(q(graph)!=n("fieldGraphVtable"))throw new IllegalArgumentException("Biotic field graph changed");
            long items=array(graph+0x50,14);double[] out=new double[3];int at=0;
            for(String name:new String[]{"duration","radius","amount"}){
                var d=binding.getAsJsonObject("fieldParameters").getAsJsonObject(name);long node=d.get("node").getAsLong(),field=d.get("field").getAsLong(),value=d.get("valueObject").getAsLong();
                int index=d.get("index").getAsInt();double expected=name.equals("amount")?40:5;
                if(index!=at+2||q(items+index*8L)!=node||q(node)!=d.get("nodeVtable").getAsLong()||field!=node+0xa0
                    ||q(field)!=value||q(value)!=d.get("valueVtable").getAsLong()||i(value+16)!=expected||d.get("value").getAsDouble()!=expected)throw new IllegalArgumentException("Biotic field constant changed");
                out[at++]=expected;
            }verify();return out;
        }catch(Exception e){error=e.toString();close();return null;}
    }
    double[] reaperParameters(){
        try{
            if(binding==null||n("hero")!=NativeReaperRuntime.HERO)throw new IllegalArgumentException("Death Blossom binding unavailable");verify();
            var parameters=binding.getAsJsonObject("reaperParameters");long items=array(n("graph")+0x50,54);double[] out=new double[2];int j=0;
            for(String name:new String[]{"range","duration"}){
                var d=parameters.getAsJsonObject(name);int index=name.equals("range")?48:9,offset=name.equals("range")?0x130:0x120,expected=name.equals("range")?8:3;
                long definition=d.get("definition").getAsLong(),field=d.get("field").getAsLong(),obj=d.get("object").getAsLong();
                if(d.get("node").getAsInt()!=index||q(items+index*8L)!=definition||field!=definition+offset||q(field)!=obj||q(obj)!=d.get("vtable").getAsLong()||i(obj+16)!=expected||d.get("value").getAsDouble()!=expected)throw new IllegalArgumentException("Death Blossom declared parameter changed");out[j++]=expected;
            }verify();return out;
        }catch(Exception e){error=e.toString();close();return null;}
    }
    double infraDuration(){
        if(binding==null||n("hero")!=NativeInfraSightState.HERO)throw new IllegalArgumentException("Infra-Sight owner missing");
        verify();var d=binding.getAsJsonObject("infraDuration");long field=d.get("field").getAsLong(),obj=d.get("object").getAsLong();
        long node=binding.getAsJsonObject("states").getAsJsonObject("infraAnimation").get("address").getAsLong();
        if(field!=node+0x120||q(field)!=obj||q(obj)!=d.get("vtable").getAsLong()||i(obj+16)!=15||d.get("value").getAsInt()!=15)throw new IllegalArgumentException("Infra-Sight literal duration changed");
        verify();return 15;
    }
    State poll(HostPoseReader.Pose host,long model,long hero){
        if(host==null||host.flags()!=1||model==0){error="native skill camera unavailable";return null;}
        try{
            if(handle==null||pid!=host.pid()||generation!=host.generation()||n("modelId")!=model||n("hero")!=hero){
                close();String dir=System.getProperty("owmc.nativeEventsDirectory","");var path=Path.of(dir).resolve((spec!=null?"native-"+purposeName+"-request-":melee?"native-melee-request-":sustain?"native-sustain-request-":biotic?"native-biotic-request-":pulse?"native-pulse-request-":recall?"native-recall-request-":wraith?"native-wraith-request-":shadow?"native-shadow-request-":grapple?"native-grapple-request-":venom?"native-venom-request-":blizzard?"native-blizzard-request-":"native-skills-request-")+host.pid()+".json");
                if(dir.isBlank()||!Files.isRegularFile(path)){error="waiting for native skill binding";return null;}
                if(Files.size(path)>8192)throw new IllegalArgumentException("skill binding size");
                binding=JsonParser.parseString(Files.readString(path)).getAsJsonObject();
                boolean bastion=hero==0x02e0000000000015L,genji=hero==0x02e0000000000029L,pharah=hero==0x02e0000000000008L,soldier=hero==0x02e000000000006eL,mccree=hero==0x02e0000000000042L,reaper=hero==NativeReaperRuntime.HERO,widow=hero==NativeInfraSightState.HERO,torb=hero==0x02e0000000000006L;
                if(n("version")!=1||n("pid")!=Integer.toUnsignedLong(host.pid())||n("modelId")!=model||n("hero")!=hero
                    ||(spec!=null?hero!=spec.hero():melee?!NativeMeleeRuntime.supported(hero):sustain?(!bastion&&hero!=0x02e00000000000ddL):biotic?!soldier:pulse||recall?hero!=NativePulseRuntime.HERO:wraith||shadow?!reaper:grapple||venom?!widow:blizzard?hero!=NativeMeiFreezeRuntime.HERO:(!bastion&&!genji&&!pharah&&!soldier&&!mccree&&!reaper&&!widow&&!torb))||n("resource")!=(spec!=null?spec.resource():melee?0x0580000000000043L:sustain?(bastion?0x0580000000000153L:0x05800000000005feL):biotic?0x0580000000000257L:pulse?0x0580000000000034L:recall?0x058000000000001aL:wraith?0x0580000000000020L:shadow?0x05800000000000f2L:grapple?0x058000000000005aL:venom?0x0580000000000056L:blizzard?0x058000000000064aL:torb?0x05800000000001c2L:widow?0x0580000000000067L:reaper?0x0580000000000044L:bastion?0x058000000000012fL:genji?0x05800000000003a3L:soldier?0x0580000000000259L:mccree?0x058000000000022fL:0x058000000000002bL))throw new IllegalArgumentException("skill binding identity");
                var states=binding.getAsJsonObject("states");
                if(spec!=null?!spec.matches(states):melee?(states.size()!=2||states.getAsJsonObject("strike").get("index").getAsInt()!=13||states.getAsJsonObject("modify").get("index").getAsInt()!=12)
                    :sustain?(states.size()!=1||states.getAsJsonObject("heal").get("index").getAsInt()!=(bastion?2:30))
                    :biotic?(states.size()!=3||states.getAsJsonObject("deploy").get("index").getAsInt()!=6||states.getAsJsonObject("cast").get("index").getAsInt()!=20||states.getAsJsonObject("windup").get("index").getAsInt()!=11)
                    :pulse?(states.size()!=2||states.getAsJsonObject("deploy").get("index").getAsInt()!=1||states.getAsJsonObject("cast").get("index").getAsInt()!=3)
                    :recall?(states.size()!=2||states.getAsJsonObject("cast").get("index").getAsInt()!=31||states.getAsJsonObject("animation").get("index").getAsInt()!=9)
                    :shadow?(states.size()!=10||states.getAsJsonObject("aim").get("index").getAsInt()!=2||states.getAsJsonObject("confirm").get("index").getAsInt()!=47||states.getAsJsonObject("cast").get("index").getAsInt()!=52||states.getAsJsonObject("out").get("index").getAsInt()!=25||states.getAsJsonObject("in").get("index").getAsInt()!=26||states.getAsJsonObject("waitOut").get("index").getAsInt()!=17||states.getAsJsonObject("waitIn").get("index").getAsInt()!=18)
                    :grapple?(states.size()!=3||states.getAsJsonObject("cast").get("index").getAsInt()!=81||states.getAsJsonObject("window").get("index").getAsInt()!=57||states.getAsJsonObject("fire").get("index").getAsInt()!=61)
                    :blizzard?(states.size()!=2||states.getAsJsonObject("volley").get("index").getAsInt()!=10||states.getAsJsonObject("windup").get("index").getAsInt()!=1)
                    :venom?(states.size()!=3||states.getAsJsonObject("cast").get("index").getAsInt()!=24||states.getAsJsonObject("throw").get("index").getAsInt()!=1||states.getAsJsonObject("anim").get("index").getAsInt()!=2)
                    :wraith?(states.size()!=2||states.getAsJsonObject("cast").get("index").getAsInt()!=20||states.getAsJsonObject("animation").get("index").getAsInt()!=3)
                    :torb?(states.size()!=5||states.getAsJsonObject("ultimate").get("index").getAsInt()!=21||states.getAsJsonObject("coreAnimation").get("index").getAsInt()!=30||states.getAsJsonObject("coreArmor").get("index").getAsInt()!=19||states.getAsJsonObject("coreEffect").get("index").getAsInt()!=20||states.getAsJsonObject("coreTimer").get("index").getAsInt()!=17)
                    :widow?(states.size()!=4||states.getAsJsonObject("ultimate").get("index").getAsInt()!=18||states.getAsJsonObject("infraAnimation").get("index").getAsInt()!=6||states.getAsJsonObject("infraEffect").get("index").getAsInt()!=13||states.getAsJsonObject("infraTimer").get("index").getAsInt()!=10)
                    :reaper?(states.size()!=3||states.getAsJsonObject("ultimate").get("index").getAsInt()!=49||states.getAsJsonObject("firing").get("index").getAsInt()!=48||states.getAsJsonObject("animation").get("index").getAsInt()!=9)
                    :bastion?(states.size()!=3||states.getAsJsonObject("recon").get("index").getAsInt()!=8||states.getAsJsonObject("sentry").get("index").getAsInt()!=9||states.getAsJsonObject("tank").get("index").getAsInt()!=105)
                    :genji?(states.size()!=1||states.getAsJsonObject("deflect").get("index").getAsInt()!=30)
                    :soldier?(states.size()!=2||states.getAsJsonObject("ultimate").get("index").getAsInt()!=15||states.getAsJsonObject("visor").get("index").getAsInt()!=12)
                    :mccree?(states.size()!=4||states.getAsJsonObject("ultimate").get("index").getAsInt()!=18||states.getAsJsonObject("tracking").get("index").getAsInt()!=27||states.getAsJsonObject("fire").get("index").getAsInt()!=44||states.getAsJsonObject("shotAnimation").get("index").getAsInt()!=69)
                    :(states.size()!=3||states.getAsJsonObject("barrage").get("index").getAsInt()!=12||states.getAsJsonObject("windup").get("index").getAsInt()!=13||states.getAsJsonObject("firing").get("index").getAsInt()!=2))throw new IllegalArgumentException("skill profile differs");
                handle=kernel.OpenProcess(0x100000|0x400|0x10,false,host.pid());if(handle==null)throw new IllegalStateException("skill process unavailable");
                try(var creation=new Memory(8);var exit=new Memory(8);var system=new Memory(8);var user=new Memory(8)){
                    if(!kernel.GetProcessTimes(handle,creation,exit,system,user)||creation.getLong(0)!=n("creation"))throw new IllegalArgumentException("skill process creation changed");
                }pid=host.pid();generation=host.generation();
            }
            verify();long inner=find(n("logger"),n("script"),true);Map<String,Entry> snapshot=new HashMap<>();
            for(var field:binding.getAsJsonObject("states").entrySet())snapshot.put(field.getKey(),state(inner,field.getValue().getAsJsonObject().get("index").getAsInt()));
            for(var field:binding.getAsJsonObject("states").entrySet())if(!snapshot.get(field.getKey()).equals(state(inner,field.getValue().getAsJsonObject().get("index").getAsInt())))throw new IllegalArgumentException("native skill snapshot changed");
            verify();if(spec==null&&!melee&&!grapple&&!venom&&hero==NativeInfraSightState.HERO&&infraDuration()!=15)throw new IllegalArgumentException("Infra-Sight duration unavailable");var geometry=melee?geometry():null;error="";return new State(generation,model,hero,Map.copyOf(snapshot),geometry);
        }catch(Exception failure){error=failure.toString();close();return null;}
    }
    @Override public void close(){if(handle!=null)kernel.CloseHandle(handle);handle=null;binding=null;pid=0;generation=0;}
    byte[] shadowReceipt(NativeShadowRuntime.Receipt result){
        verify();var s=result.scope();long now=System.currentTimeMillis();
        if(!shadow||result.aim()<=0||result.confirm()<result.aim()||result.wall()>now+50||now-result.wall()>250||s.model()!=n("modelId")||s.source()!=generation||result.phase()<1||result.phase()>3)throw new IllegalArgumentException("Shadow Step receipt scope");
        var b=ByteBuffer.allocate(80).order(ByteOrder.LITTLE_ENDIAN);b.put("OWSHDA01".getBytes(java.nio.charset.StandardCharsets.US_ASCII)).putInt(1).putInt(pid);
        b.putLong(n("creation")).putLong(generation).putLong(s.world()).putLong(s.model()).putLong(result.aim()).putLong(result.confirm()).putLong(result.wall()).putInt(result.phase()).putInt(0);verify();return b.array();
    }
    byte[] recallCompletion(NativeRecallRuntime.Completion result){
        verify();var s=result.scope();long now=System.currentTimeMillis();
        if(!recall||n("hero")!=NativeRecallRuntime.HERO||result.begin()<=0||result.wall()>now+50||now-result.wall()>1000||s.model()!=n("modelId")||s.source()!=generation)throw new IllegalArgumentException("Recall completion scope");
        var b=ByteBuffer.allocate(72).order(ByteOrder.LITTLE_ENDIAN);b.put("OWRECA01".getBytes(java.nio.charset.StandardCharsets.US_ASCII)).putInt(1).putInt(pid);
        b.putLong(n("creation")).putLong(generation).putLong(s.world()).putLong(s.model()).putLong(result.begin()).putLong(result.wall()).putInt(result.moved()?2:3).putInt(0);verify();return b.array();
    }
    byte[] deadeyePresentation(long sequence,long world,long begin,int ordinal){
        verify();if(n("hero")!=NativeDeadeyeRuntime.HERO||sequence<=0||ordinal<1||ordinal>NativeDeadeyeRuntime.MAX_TARGETS)throw new IllegalArgumentException("Deadeye animation request scope");
        var original=binding.getAsJsonObject("deadeyePresentation");byte[] prefix=HexFormat.of().parseHex(original.get("prefix").getAsString());
        if(prefix.length!=32||!Arrays.equals(read(original.get("function").getAsLong(),32),prefix))throw new IllegalArgumentException("Original animation UI function changed");
        var b=ByteBuffer.allocate(168).order(ByteOrder.LITTLE_ENDIAN);b.put("OWDEYE01".getBytes(java.nio.charset.StandardCharsets.US_ASCII)).putInt(2).putInt(pid);
        b.putLong(n("creation")).putLong(sequence).putLong(System.currentTimeMillis()).putLong(generation).putLong(world).putLong(n("admin")).putLong(n("model")).putLong(n("modelId"));
        b.putLong(n("script")).putLong(n("graph")).putLong(original.get("function").getAsLong()).putLong(n("logger")).putLong(begin).putInt(69).putInt(ordinal).put(prefix).putLong(NativeDeadeyeRuntime.presentationAcknowledged);verify();return b.array();
    }
}
