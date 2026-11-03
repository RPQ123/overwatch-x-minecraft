package lab.owmcguest;
import com.google.gson.*;
import com.sun.jna.*;
import java.nio.file.Files;

/** Actual Win64 fixture reads/writes, restricted to one guarded four-byte meter. */
public final class NativeMeterReaderCheck {
    static void require(boolean ok,String message){if(!ok)throw new AssertionError(message);}
    public static void main(String[] args)throws Exception{
        var dir=Files.createTempDirectory("owmc-meter-reader-");String previous=System.getProperty("owmc.nativeEventsDirectory");
        int pid=(int)ProcessHandle.current().pid();var file=dir.resolve("native-meter-request-"+pid+".json");
        var kernel=Native.load("kernel32",NativeAbilityReader.Kernel.class);var handle=kernel.OpenProcess(0x400,false,pid);
        try(var admin=new Memory(0x230);var adminAddress=new Memory(8);var reference=new Memory(0x98);
            var model=new Memory(0x98);var heroInfo=new Memory(0xa0);var bagAddress=new Memory(8);var bag=new Memory(0x3a0);
            var charge=new Memory(0xb0);var cost=new Memory(0xb0);var vtable=new Memory(8);var pairs=new Memory(32);
            var creation=new Memory(8);var exit=new Memory(8);var system=new Memory(8);var user=new Memory(8);
            var reader=new NativeMeterReader()){
            for(var m:new Memory[]{admin,adminAddress,reference,model,heroInfo,bagAddress,bag,charge,cost,vtable,pairs})m.clear();
            require(kernel.GetProcessTimes(handle,creation,exit,system,user),"Fixture creation identity");
            adminAddress.setLong(0,Pointer.nativeValue(admin));admin.setInt(0x220,17);
            reference.setInt(0x94,19);model.setInt(0x94,19);model.setLong(0x28,Pointer.nativeValue(admin));
            heroInfo.setLong(0x98,0x02e0000000000008L);bagAddress.setLong(0,Pointer.nativeValue(bag));
            bag.setLong(0xa0,Pointer.nativeValue(pairs));bag.setInt(0xa8,2);bag.setInt(0xac,2);
            pairs.setLong(0,0x0d80000000000156L);pairs.setLong(8,Pointer.nativeValue(charge));pairs.setLong(16,0x0d80000000000152L);pairs.setLong(24,Pointer.nativeValue(cost));
            charge.setLong(0,Pointer.nativeValue(vtable));charge.setInt(0xa0,17);charge.setInt(0xa4,0x12345678);charge.setInt(0xac,2);
            cost.setLong(0,Pointer.nativeValue(vtable));cost.setInt(0xa0,1500);cost.setInt(0xac,2);
            var b=new JsonObject();b.addProperty("version",1);b.addProperty("pid",pid);b.addProperty("creation",creation.getLong(0));
            b.addProperty("hero",0x02e0000000000008L);b.addProperty("localId",17);b.addProperty("modelId",19);b.addProperty("chargeBucket",0);b.addProperty("costBucket",0);
            String[] names={"admin","adminAddress","reference","model","heroInfo","bagAddress","bag","charge","cost","numericVtable"};
            Memory[] values={admin,adminAddress,reference,model,heroInfo,bagAddress,bag,charge,cost,vtable};
            for(int j=0;j<names.length;j++)b.addProperty(names[j],Pointer.nativeValue(values[j]));
            Files.writeString(file,b.toString());System.setProperty("owmc.nativeEventsDirectory",dir.toString());
            var pose=new HostPoseReader.Pose(42,1,pid,1,70,new float[]{1,0,0,0,1,0,0,0,1},new float[]{0,0,0},0,false);
            var state=reader.poll(pose,19,0x02e0000000000008L);require(state!=null&&state.charge()==17&&state.cost()==1500,"Typed current meter");
            require(reader.credit(state,52)&&charge.getInt(0xa0)==52&&charge.getInt(0xa4)==0x12345678&&charge.getInt(0xac)==2,"Only four numeric payload bytes change");
            require(!reader.credit(state,100)&&charge.getInt(0xa0)==52,"Changed native charge refuses stale credit");
            var latest=reader.poll(pose,19,0x02e0000000000008L);require(!reader.credit(latest,1501)&&!reader.credit(latest,Double.NaN)&&!reader.credit(latest,51),"Overfill, NaN and negative credit refused");
            charge.setFloat(0xa0,50.5f);charge.setInt(0xac,3);state=reader.poll(pose,19,0x02e0000000000008L);
            require(reader.credit(state,51.25)&&charge.getFloat(0xa0)==51.25f&&charge.getInt(0xac)==3,"Float meter retains original primitive kind");
            pairs.setLong(0,123);require(reader.poll(pose,19,0x02e0000000000008L)==null,"Stale bag membership refused");pairs.setLong(0,0x0d80000000000156L);
            reference.setInt(0x94,20);require(reader.poll(pose,19,0x02e0000000000008L)==null,"Replaced hero refused");reference.setInt(0x94,19);
            charge.setFloat(0xa0,Float.NaN);require(reader.poll(pose,19,0x02e0000000000008L)==null,"Native NaN refused");charge.setFloat(0xa0,51.25f);
            require(reader.poll(pose,19,0x02e0000000000008L)!=null,"Valid owner reconnects");reader.close();
            b.addProperty("creation",creation.getLong(0)-1);Files.writeString(file,b.toString());require(reader.poll(pose,19,0x02e0000000000008L)==null,"PID reuse refused");
        }finally{
            kernel.CloseHandle(handle);if(previous==null)System.clearProperty("owmc.nativeEventsDirectory");else System.setProperty("owmc.nativeEventsDirectory",previous);
            Files.deleteIfExists(file);Files.deleteIfExists(dir);
        }
        System.out.println("PASS: typed original meter feedback, four-byte writes, stale credit/owner/bag/creation and numeric bounds");
    }
}
