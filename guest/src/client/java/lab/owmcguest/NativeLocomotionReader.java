package lab.owmcguest;

import com.google.gson.JsonObject;
import com.google.gson.JsonParser;
import com.sun.jna.*;
import java.nio.*;
import java.nio.file.*;

/** Read original base definitions AND six current computed mover speed limits. */
final class NativeLocomotionReader implements AutoCloseable {
    private final NativeAbilityReader.Kernel kernel=Native.load("kernel32",NativeAbilityReader.Kernel.class);
    private Pointer handle;private JsonObject binding;private int pid;private long generation;
    private double[] baseSpeeds,nativeVelocity;
    private final Runnable afterComputedReadForFixture;
    NativeLocomotionReader(){this(null);}
    /** Deterministically change self-process fixture memory between the two reads. */
    NativeLocomotionReader(Runnable afterComputedReadForFixture){this.afterComputedReadForFixture=afterComputedReadForFixture;}
    String error="waiting for native locomotion binding";
    private long n(String key){return binding.get(key).getAsLong();}
    boolean genji(){return binding!=null&&n("hero")==0x02e0000000000029L;}
    long hero(){return binding==null?0:n("hero");}
    long modelId(){return binding==null?0:n("modelId");}
    double[] baseSpeeds(){return baseSpeeds==null?null:baseSpeeds.clone();}
    double[] nativeVelocity(){return nativeVelocity==null?null:nativeVelocity.clone();}
    private ByteBuffer read(long address,int size){
        if(address<0x10000||address>0x7fffffffffffL||size<1||size>4096)throw new IllegalArgumentException("locomotion read bounds");
        byte[] data=new byte[size];try(var count=new Memory(8)){
            if(!kernel.ReadProcessMemory(handle,Pointer.createConstant(address),data,size,count)||count.getLong(0)!=size)throw new IllegalStateException("locomotion read failed");
        }return ByteBuffer.wrap(data).order(ByteOrder.LITTLE_ENDIAN);
    }
    private long ptr(long address){return read(address,8).getLong();}
    private long verifyCurrent(){
        if(kernel.WaitForSingleObject(handle,0)!=0x102||ptr(n("adminAddress"))!=n("admin")||read(n("admin")+0x220,4).getInt()!=(int)n("localId")||read(n("reference")+0x94,4).getInt()!=(int)n("modelId")||read(n("model")+0x94,4).getInt()!=(int)n("modelId")||ptr(n("heroInfo")+0x98)!=n("hero")||(ptr(n("model")+0x30)&~63L)!=n("entry")||ptr(n("entry"))!=n("definition")||ptr(n("mover"))!=n("moverVtable"))throw new IllegalArgumentException("native locomotion hero changed");
        long runtime=n("runtimeMover");
        if(ptr(runtime)!=n("runtimeMoverVtable")||ptr(runtime+8)!=n("model")||read(runtime+0x10,1).get()!=0x15)throw new IllegalArgumentException("native computed mover owner changed");
        var list=read(n("model")+0x50,16);long items=list.getLong();int count=list.getInt(),capacity=list.getInt();
        if(count<2||count>capacity||capacity>256)throw new IllegalArgumentException("native mover component list bounds");
        var components=read(items,count*8);int found=0;
        for(int j=0;j<count-1;j++){
            long component=components.getLong(j*8);
            if(component==runtime)found++;
            else if(component!=0&&read(component+0x10,1).get()==0x15&&ptr(component+8)==n("model"))throw new IllegalArgumentException("native computed mover is not unique");
        }
        if(found!=1)throw new IllegalArgumentException("native computed mover left current model");
        return runtime;
    }
    double[] poll(HostPoseReader.Pose host){
        if(host==null||host.flags()!=1){error="native camera unavailable";return null;}
        try{
            if(handle==null||pid!=host.pid()||generation!=host.generation()){
                close();var file=Path.of(System.getProperty("owmc.nativeEventsDirectory","")).resolve("native-locomotion-request-"+host.pid()+".json");
                if(!Files.isRegularFile(file)){error="waiting for native locomotion binding";return null;}
                if(Files.size(file)>8192)throw new IllegalArgumentException("locomotion binding size");
                binding=JsonParser.parseString(Files.readString(file)).getAsJsonObject();
                if(n("version")!=2||n("pid")!=Integer.toUnsignedLong(host.pid()))throw new IllegalArgumentException("locomotion request identity");
                handle=kernel.OpenProcess(0x100000|0x400|0x10,false,host.pid());if(handle==null)throw new IllegalStateException("locomotion process unavailable");
                try(var creation=new Memory(8);var exit=new Memory(8);var system=new Memory(8);var user=new Memory(8)){
                    if(!kernel.GetProcessTimes(handle,creation,exit,system,user)||creation.getLong(0)!=n("creation"))throw new IllegalArgumentException("locomotion process creation changed");
                }pid=host.pid();generation=host.generation();
            }
            long runtime=verifyCurrent();
            String[] names={"m_speedRunForward","m_speedRunBackward","m_speedRunStrafe","m_speedCrouchForward","m_speedCrouchBackward","m_speedCrouchStrafe"};
            double[] speeds=new double[6];var fields=binding.getAsJsonObject("fields");
            for(int i=0;i<6;i++){
                var field=fields.getAsJsonObject(names[i]);long address=field.get("address").getAsLong();
                if(address!=n("mover")+field.get("offset").getAsInt()||address<n("mover")+8||address>n("mover")+0x8c)throw new IllegalArgumentException("native speed field address");
                speeds[i]=read(address,4).getFloat();
                if(!Double.isFinite(speeds[i])||speeds[i]<=0||speeds[i]>30)throw new IllegalArgumentException("native speed value");
            }
            ByteBuffer a=null;
            for(int attempt=0;attempt<3;attempt++){
                var first=read(runtime+0x300,24);
                if(afterComputedReadForFixture!=null)afterComputedReadForFixture.run();
                var second=read(runtime+0x300,24);
                if(java.util.Arrays.equals(first.array(),second.array())){a=second;break;}
            }
            // A modifier changing is not a new hero. Revalidate identity even
            // after an incoherent read; never retain a departed model's scope.
            verifyCurrent();
            if(a==null){baseSpeeds=speeds;nativeVelocity=null;error="native computed speeds changed during bounded read";return null;}
            double[] effective=new double[6];
            for(int i=0;i<6;i++){
                effective[i]=a.getFloat(i*4);
                if(!Double.isFinite(effective[i])||effective[i]<0||effective[i]>speeds[i]*3)throw new IllegalArgumentException("native computed speed value");
            }
            var velocity=read(runtime+0x7e0+0x230,12);nativeVelocity=new double[]{velocity.getFloat(),velocity.getFloat(),velocity.getFloat()};
            for(double v:nativeVelocity)if(!Double.isFinite(v)||Math.abs(v)>100)throw new IllegalArgumentException("native mover velocity value");
            verifyCurrent();
            baseSpeeds=speeds;error="";return effective;
        }catch(Exception failure){error=failure.toString();close();return null;}
    }
    @Override public void close(){if(handle!=null)kernel.CloseHandle(handle);handle=null;binding=null;baseSpeeds=nativeVelocity=null;pid=0;generation=0;}
}
