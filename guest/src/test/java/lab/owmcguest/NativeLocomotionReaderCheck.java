package lab.owmcguest;
import com.google.gson.JsonObject;
import com.sun.jna.*;
import java.nio.file.Files;
public final class NativeLocomotionReaderCheck {
    static void require(boolean value){if(!value)throw new AssertionError("Native locomotion identity/value guard");}
    public static void main(String[] args)throws Exception{
        var dir=Files.createTempDirectory("owmc-locomotion-check-");var previous=System.getProperty("owmc.nativeEventsDirectory");
        int pid=(int)ProcessHandle.current().pid();var file=dir.resolve("native-locomotion-request-"+pid+".json");
        var kernel=Native.load("kernel32",NativeAbilityReader.Kernel.class);var handle=kernel.OpenProcess(0x400,false,pid);
        var afterRead=new java.util.concurrent.atomic.AtomicReference<Runnable>();
        var computedReads=new java.util.concurrent.atomic.AtomicInteger();
        try(var memory=new Memory(8192);var creation=new Memory(8);var exit=new Memory(8);var system=new Memory(8);var user=new Memory(8);var reader=new NativeLocomotionReader(()->{
            computedReads.incrementAndGet();var mutation=afterRead.get();if(mutation!=null)mutation.run();
        })){
            memory.clear();long base=Pointer.nativeValue(memory),entry=(base+0x780+63)&~63L;
            long admin=base+0x100,model=base+0x400,reference=base+0x500,heroInfo=base+0x600,definition=base+0x900,mover=base+0xa00;
            memory.setLong(0,admin);memory.setInt(admin-base+0x220,17);memory.setInt(model-base+0x94,19);memory.setInt(reference-base+0x94,19);
            memory.setLong(heroInfo-base+0x98,41);memory.setLong(model-base+0x30,entry|1);memory.setLong(entry-base,definition);memory.setLong(mover-base,base+0xb00);
            long runtime=base+0x1000,components=base+0x1c00;
            memory.setLong(runtime-base,base+0x1f00);memory.setLong(runtime-base+8,model);memory.setByte(runtime-base+0x10,(byte)0x15);
            memory.setLong(model-base+0x50,components);memory.setInt(model-base+0x58,2);memory.setInt(model-base+0x5c,2);memory.setLong(components-base,runtime);
            var b=new JsonObject();b.addProperty("version",2);b.addProperty("pid",pid);require(kernel.GetProcessTimes(handle,creation,exit,system,user));b.addProperty("creation",creation.getLong(0));
            b.addProperty("runtimeMover",runtime);b.addProperty("runtimeMoverVtable",base+0x1f00);
            String[] names={"adminAddress","admin","model","reference","heroInfo","entry","definition","mover","moverVtable","localId","modelId","hero"};
            long[] values={base,admin,model,reference,heroInfo,entry,definition,mover,base+0xb00,17,19,41};for(int i=0;i<names.length;i++)b.addProperty(names[i],values[i]);
            var fields=new JsonObject();String[] speeds={"m_speedRunForward","m_speedRunBackward","m_speedRunStrafe","m_speedCrouchForward","m_speedCrouchBackward","m_speedCrouchStrafe"};
            for(int i=0;i<6;i++){var f=new JsonObject();f.addProperty("address",mover+56+i*4);f.addProperty("offset",56+i*4);fields.add(speeds[i],f);memory.setFloat(mover-base+56+i*4,i<3?6:3);memory.setFloat(runtime-base+0x300+i*4,i<3?6:3);}
            b.add("fields",fields);Files.writeString(file,b.toString());System.setProperty("owmc.nativeEventsDirectory",dir.toString());
            var pose=new HostPoseReader.Pose(42,1,pid,1,70,new float[]{1,0,0,0,1,0,0,0,1},new float[]{0,0,0},0,false);
            require(reader.poll(null)==null);require(reader.poll(pose)[0]==6&&reader.error.isEmpty());
            memory.setInt(reference-base+0x94,20);require(reader.poll(pose)==null);memory.setInt(reference-base+0x94,19);
            memory.setFloat(mover-base+56,Float.NaN);require(reader.poll(pose)==null);memory.setFloat(mover-base+56,6);
            require(reader.poll(pose)[0]==6);memory.setLong(heroInfo-base+0x98,42);require(reader.poll(pose)==null);
            memory.setLong(heroInfo-base+0x98,41);memory.setFloat(runtime-base+0x300,2.1f);
            require(Math.abs(reader.poll(pose)[0]-2.1)<1e-6&&reader.baseSpeeds()[0]==6); // native scope modifier
            memory.setFloat(runtime-base+0x300,0);require(reader.poll(pose)[0]==0); // native root
            memory.setFloat(runtime-base+0x300,9);require(reader.poll(pose)[0]==9); // native sprint
            memory.setFloat(runtime-base+0x300,-1);require(reader.poll(pose)==null);
            memory.setFloat(runtime-base+0x300,Float.NaN);require(reader.poll(pose)==null);
            memory.setFloat(runtime-base+0x300,19);require(reader.poll(pose)==null);
            memory.setFloat(runtime-base+0x300,6);memory.setLong(runtime-base+8,model+8);require(reader.poll(pose)==null);
            memory.setLong(runtime-base+8,model);memory.setLong(components-base,0);require(reader.poll(pose)==null);
            memory.setLong(components-base,runtime);require(reader.poll(pose)[0]==6);

            // A single live scope change resolves in the same poll's bounded retry.
            int before=computedReads.get();
            afterRead.set(()->{memory.setFloat(runtime-base+0x300,2.1f);afterRead.set(null);});
            require(Math.abs(reader.poll(pose)[0]-2.1)<1e-6&&computedReads.get()-before==2);
            require(reader.hero()==41&&reader.modelId()==19&&reader.error.isEmpty());

            // Unsettled values suppress movement, not the verified hero identity.
            afterRead.set(()->memory.setFloat(runtime-base+0x300,memory.getFloat(runtime-base+0x300)==6?2.1f:6));
            before=computedReads.get();require(reader.poll(pose)==null&&computedReads.get()-before==3);
            require(reader.hero()==41&&reader.modelId()==19&&reader.nativeVelocity()==null);
            require(reader.error.contains("bounded read"));
            afterRead.set(null);memory.setFloat(runtime-base+0x300,6);
            require(reader.poll(pose)[0]==6&&reader.hero()==41&&reader.modelId()==19&&reader.error.isEmpty());

            // A real model change during a torn read must still revoke old scope.
            afterRead.set(()->{memory.setFloat(runtime-base+0x300,memory.getFloat(runtime-base+0x300)==6?2.1f:6);memory.setInt(reference-base+0x94,20);});
            require(reader.poll(pose)==null&&reader.hero()==0&&reader.modelId()==0);
            afterRead.set(null);memory.setInt(reference-base+0x94,19);memory.setFloat(runtime-base+0x300,6);
            require(reader.poll(pose)[0]==6);

            // Even a coherent speed pair cannot outlive its mover owner.
            afterRead.set(()->memory.setLong(runtime-base+8,model+8));
            require(reader.poll(pose)==null&&reader.hero()==0&&reader.modelId()==0);
            afterRead.set(null);memory.setLong(runtime-base+8,model);
            require(reader.poll(pose)[0]==6);
        }finally{kernel.CloseHandle(handle);if(previous==null)System.clearProperty("owmc.nativeEventsDirectory");else System.setProperty("owmc.nativeEventsDirectory",previous);Files.deleteIfExists(file);Files.deleteIfExists(dir);}
        System.out.println("PASS: Win64 mover identity, computed modifiers, bounded coherent retries without false hero reset, and real owner-change refusal");
    }
}
