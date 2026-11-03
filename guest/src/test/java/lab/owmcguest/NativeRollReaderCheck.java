package lab.owmcguest;

import com.google.gson.JsonObject;
import com.sun.jna.*;
import java.nio.file.Files;

/** Actual Win64 reads of owned memory: no game, injection or synthetic input. */
public final class NativeRollReaderCheck {
    private static void require(boolean ok,String message){if(!ok)throw new AssertionError(message);}
    public static void main(String[] args)throws Exception{
        var dir=Files.createTempDirectory("owmc-roll-reader-");String previous=System.getProperty("owmc.nativeEventsDirectory");
        int pid=(int)ProcessHandle.current().pid();var file=dir.resolve("native-roll-request-"+pid+".json");
        var kernel=Native.load("kernel32",NativeAbilityReader.Kernel.class);var handle=kernel.OpenProcess(0x400,false,pid);
        try(var admin=new Memory(0x230);var adminAddress=new Memory(8);var reference=new Memory(0x98);
            var model=new Memory(0x98);var heroInfo=new Memory(0xa0);var script=new Memory(0x168);
            var inner=new Memory(0x458);var component=new Memory(16);var graph=new Memory(8);var bag=new Memory(8);
            var speed=new Memory(0xb0);var timeout=new Memory(24);var vtable=new Memory(8);
            var logger=new Memory(16);var sentinel=new Memory(40);var outerNode=new Memory(64);
            var stateHead=new Memory(40);var timerNode=new Memory(64);var actionNode=new Memory(64);
            var creation=new Memory(8);var exit=new Memory(8);var system=new Memory(8);var user=new Memory(8);
            var reader=new NativeRollReader()){
            for(var m:new Memory[]{admin,adminAddress,reference,model,heroInfo,script,inner,component,graph,bag,speed,timeout,vtable,logger,sentinel,outerNode,stateHead,timerNode,actionNode})m.clear();
            require(kernel.GetProcessTimes(handle,creation,exit,system,user),"Fixture creation identity");
            adminAddress.setLong(0,Pointer.nativeValue(admin));admin.setInt(0x220,17);
            reference.setInt(0x94,19);model.setInt(0x94,19);model.setLong(0x28,Pointer.nativeValue(admin));
            heroInfo.setLong(0x98,0x02e0000000000042L);script.setLong(0x150,0x05800000000001f0L);
            script.setLong(0x98,Pointer.nativeValue(bag));script.setLong(0x160,Pointer.nativeValue(graph));
            script.setLong(0x10,Pointer.nativeValue(inner));inner.setLong(0x450,Pointer.nativeValue(component));component.setLong(8,Pointer.nativeValue(model));
            speed.setLong(0,Pointer.nativeValue(vtable));speed.setInt(0xa0,15);speed.setInt(0xac,2);
            timeout.setLong(0,Pointer.nativeValue(vtable));timeout.setFloat(16,.4f);
            logger.setLong(0,Pointer.nativeValue(sentinel));sentinel.setLong(8,Pointer.nativeValue(sentinel));sentinel.setByte(25,(byte)1);
            var b=new JsonObject();b.addProperty("version",1);b.addProperty("pid",pid);b.addProperty("creation",creation.getLong(0));
            b.addProperty("resource",0x05800000000001f0L);b.addProperty("hero",0x02e0000000000042L);b.addProperty("node",4);
            b.addProperty("localId",17);b.addProperty("modelId",19);
            String[] names={"admin","adminAddress","reference","model","heroInfo","script","graph","bag","speed","timeout","numericVtable","timeoutVtable","logger"};
            Memory[] values={admin,adminAddress,reference,model,heroInfo,script,graph,bag,speed,timeout,vtable,vtable,logger};
            for(int j=0;j<names.length;j++)b.addProperty(names[j],Pointer.nativeValue(values[j]));
            Files.writeString(file,b.toString());System.setProperty("owmc.nativeEventsDirectory",dir.toString());
            var pose=new HostPoseReader.Pose(42,1,pid,1,70,new float[]{1,0,0,0,1,0,0,0,1},new float[]{0,0,0},0,false);
            var idle=reader.poll(pose);require(idle!=null&&!idle.active()&&idle.tick()==0&&idle.speed()==15,"Typed idle baseline, resource IDs are not addresses");
            logger.setLong(8,1);sentinel.setLong(8,Pointer.nativeValue(outerNode));
            outerNode.setLong(0,Pointer.nativeValue(sentinel));outerNode.setLong(8,Pointer.nativeValue(sentinel));outerNode.setLong(16,Pointer.nativeValue(sentinel));outerNode.setLong(32,Pointer.nativeValue(script));
            outerNode.setLong(40,Pointer.nativeValue(stateHead));outerNode.setLong(48,2);stateHead.setByte(25,(byte)1);stateHead.setLong(8,Pointer.nativeValue(timerNode));
            timerNode.setLong(0,Pointer.nativeValue(stateHead));timerNode.setLong(8,Pointer.nativeValue(stateHead));timerNode.setLong(16,Pointer.nativeValue(actionNode));timerNode.setInt(32,4);timerNode.setLong(40,100);
            actionNode.setLong(0,Pointer.nativeValue(stateHead));actionNode.setLong(8,Pointer.nativeValue(timerNode));actionNode.setLong(16,Pointer.nativeValue(stateHead));actionNode.setInt(32,11);actionNode.setLong(40,100);actionNode.setByte(48,(byte)1);
            var active=reader.poll(pose);require(active!=null&&active.active()&&!active.directional(),"Matching native forward action");
            actionNode.setInt(32,8);require(reader.poll(pose).directional(),"Matching original directional action");
            actionNode.setLong(40,99);require(reader.poll(pose)==null,"Earlier action cannot supply direction for a new roll");
            actionNode.setLong(40,100);timerNode.setLong(40,500);timerNode.setByte(48,(byte)1);
            require(!reader.poll(pose).active(),"Original End ends roll");
            reference.setInt(0x94,20);require(reader.poll(pose)==null,"Hero replacement must invalidate the old reader");reference.setInt(0x94,19);
            speed.setFloat(0xa0,Float.NaN);speed.setInt(0xac,3);require(reader.poll(pose)==null,"NaN native speed refused");speed.setInt(0xa0,15);speed.setInt(0xac,2);
            require(reader.poll(pose)!=null,"Same valid owner reconnects");reader.close();
            b.addProperty("creation",creation.getLong(0)-1);Files.writeString(file,b.toString());require(reader.poll(pose)==null,"Reused PID identity refused");
        }finally{
            kernel.CloseHandle(handle);if(previous==null)System.clearProperty("owmc.nativeEventsDirectory");else System.setProperty("owmc.nativeEventsDirectory",previous);
            Files.deleteIfExists(file);Files.deleteIfExists(dir);
        }
        System.out.println("PASS: actual Win64 roll reads, native action correlation, owner/creation/type guards and reconnect");
    }
}
