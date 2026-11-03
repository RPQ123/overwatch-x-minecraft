package lab.owmcguest;

import com.google.gson.JsonObject;
import com.sun.jna.*;
import java.nio.file.*;
import java.util.*;

/** Owned Win64 self-process fixture: no game/input; checks the real bounded native writer. */
public final class NativeCooldownRefillCheck {
    private static void require(boolean ok,String reason){if(!ok)throw new AssertionError(reason);}
    private static void denied(Runnable work,String reason){try{work.run();throw new AssertionError(reason);}catch(IllegalStateException expected){}}
    public static void main(String[] args)throws Exception{
        var dir=Files.createTempDirectory("owmc-cooldown-check-");String old=System.getProperty("owmc.nativeEventsDirectory");
        int pid=(int)ProcessHandle.current().pid();long hero=0x02e0000000000008L;
        var path=dir.resolve("native-locomotion-request-"+pid+".json");
        var kernel=Native.load("kernel32",NativeAbilityReader.Kernel.class);var process=kernel.OpenProcess(0x400,false,pid);
        var allocated=new ArrayList<Memory>();
        try{
            java.util.function.IntFunction<Memory> alloc=size->{var m=new Memory(size);m.clear();allocated.add(m);return m;};
            var admin=alloc.apply(0x230);var adminAddress=alloc.apply(8);var model=alloc.apply(0x98);
            var controller=alloc.apply(0x98);var reference=alloc.apply(0x98);var info=alloc.apply(0xa0);
            var components=alloc.apply(16);var component=alloc.apply(0x1c0);var scripts=alloc.apply(8);
            var script=alloc.apply(0x168);var graph=alloc.apply(0x70);var storage=alloc.apply(16);
            var defs=alloc.apply(16);var def0=alloc.apply(8);var def1=alloc.apply(8);var states=alloc.apply(24);
            var state0=alloc.apply(0x158);var state1=alloc.apply(0x158);var unrelated=alloc.apply(0x158);
            var ownerLink=alloc.apply(0x458);var ownerComponent=alloc.apply(16);
            var creation=alloc.apply(8);var exit=alloc.apply(8);var system=alloc.apply(8);var user=alloc.apply(8);
            require(kernel.GetProcessTimes(process,creation,exit,system,user),"own process creation");
            adminAddress.setLong(0,Pointer.nativeValue(admin));admin.setInt(0x220,17);
            controller.setLong(0x28,Pointer.nativeValue(admin));controller.setInt(0x94,17);
            reference.setLong(8,Pointer.nativeValue(controller));reference.setInt(0x94,19);
            info.setLong(8,Pointer.nativeValue(controller));info.setLong(0x98,hero);
            model.setLong(0x28,Pointer.nativeValue(admin));model.setInt(0x94,19);
            model.setLong(0x50,Pointer.nativeValue(components));model.setInt(0x58,2);model.setInt(0x5c,2);
            components.setLong(0,Pointer.nativeValue(component));component.setLong(8,Pointer.nativeValue(model));component.setByte(0x10,(byte)0x23);
            component.setLong(0x1b0,Pointer.nativeValue(scripts));component.setInt(0x1b8,1);component.setInt(0x1bc,1);scripts.setLong(0,Pointer.nativeValue(script));
            script.setLong(0x10,Pointer.nativeValue(ownerLink));ownerLink.setLong(0x450,Pointer.nativeValue(ownerComponent));ownerComponent.setLong(8,Pointer.nativeValue(model));
            script.setLong(0x150,0x0580000000000027L);script.setLong(0x160,Pointer.nativeValue(graph));
            graph.setLong(0x60,Pointer.nativeValue(storage));graph.setLong(0x68,1);storage.setLong(0,Pointer.nativeValue(defs));storage.setLong(8,2);
            defs.setLong(0,Pointer.nativeValue(def0));defs.setLong(8,Pointer.nativeValue(def1));
            script.setLong(0xa0,Pointer.nativeValue(states));script.setInt(0xa8,3);script.setInt(0xac,3);
            states.setLong(0,Pointer.nativeValue(state0));states.setLong(8,Pointer.nativeValue(state1));states.setLong(16,Pointer.nativeValue(unrelated));
            long vtable=Pointer.nativeValue(adminAddress)-0x17b7f90L+0x15d7c98L;
            for(var state:List.of(state0,state1)){state.setLong(0,vtable);state.setLong(0x78,Pointer.nativeValue(script));state.setFloat(0x150,8);state.setInt(0x154,0x12345678);}
            state1.setInt(0x70,1);unrelated.setLong(0,Pointer.nativeValue(def0));unrelated.setFloat(0x150,42);
            var binding=new JsonObject();binding.addProperty("version",2);binding.addProperty("pid",pid);binding.addProperty("creation",creation.getLong(0));
            binding.addProperty("modelId",19);binding.addProperty("localId",17);binding.addProperty("hero",hero);
            String[] names={"admin","adminAddress","model","reference","heroInfo"};Memory[] data={admin,adminAddress,model,reference,info};
            for(int i=0;i<names.length;i++)binding.addProperty(names[i],Pointer.nativeValue(data[i]));
            Files.writeString(path,binding.toString());System.setProperty("owmc.nativeEventsDirectory",dir.toString());
            var pose=new HostPoseReader.Pose(42,1,pid,1,70,new float[]{1,0,0,0,1,0,0,0,1},new float[]{0,0,0},0,false);
            var reader=new NativeCooldownRefill();
            require(reader.restore(pose,19,hero,()->true)==2,"two original ability slots");
            require(state0.getFloat(0x150)==0&&state1.getFloat(0x150)==0,"both cooldowns restored");
            require(state0.getByte(0x144)==1&&state0.getByte(0x146)==1&&state0.getInt(0x154)==0x12345678&&unrelated.getFloat(0x150)==42,"mirrors refreshed; neighboring data/other state untouched");
            state0.setFloat(0x150,7);state1.setFloat(0x150,Float.NaN);
            denied(()->reader.restore(pose,19,hero,()->true),"invalid second slot must reject all writes");require(state0.getFloat(0x150)==7,"preflight prevents partial writes");
            state1.setFloat(0x150,8);state1.setLong(0x78,0);
            denied(()->reader.restore(pose,19,hero,()->true),"foreign state must reject");require(state0.getFloat(0x150)==7,"foreign state leaves first unchanged");state1.setLong(0x78,Pointer.nativeValue(script));
            reference.setInt(0x94,20);denied(()->reader.restore(pose,19,hero,()->true),"retired model must reject");reference.setInt(0x94,19);
            denied(()->reader.restore(pose,19,hero,()->false),"cancelled admission must reject");
            binding.addProperty("creation",creation.getLong(0)+1);Files.writeString(path,binding.toString());denied(()->reader.restore(pose,19,hero,()->true),"PID reuse must reject");
            require(state0.getFloat(0x150)==7&&state1.getFloat(0x150)==8,"all rejected cases leave timers unchanged");
        }finally{
            kernel.CloseHandle(process);for(var memory:allocated)memory.close();
            if(old==null)System.clearProperty("owmc.nativeEventsDirectory");else System.setProperty("owmc.nativeEventsDirectory",old);
            Files.deleteIfExists(path);Files.deleteIfExists(dir);
        }
        System.out.println("PASS: cooldown slots/mirrors, exact owners, preflight, cancellation, PID creation, unrelated memory");
    }
}
