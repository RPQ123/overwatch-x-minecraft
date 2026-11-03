package lab.owmcguest;

import com.google.gson.JsonObject;
import com.sun.jna.Memory;
import com.sun.jna.Native;
import com.sun.jna.Pointer;
import java.nio.file.Files;

/** Real read-only Win64 reads of this test's owned memory. No game or server is started.
 * Winston and Widow get the same authenticated melee graph without any Infra-Sight fields. */
public final class WidowMeleeReaderCheck {
    private static void require(boolean value,String message){if(!value)throw new AssertionError(message);}

    public static void main(String[] args)throws Exception{
        boolean expectBroken=args.length==1&&args[0].equals("--expect-broken");
        var directory=Files.createTempDirectory("owmc-widow-melee-");
        String previous=System.getProperty("owmc.nativeEventsDirectory");
        int pid=(int)ProcessHandle.current().pid();
        var file=directory.resolve("native-melee-request-"+pid+".json");
        var kernel=Native.load("kernel32",NativeAbilityReader.Kernel.class);
        var handle=kernel.OpenProcess(0x400,false,pid);
        try(var admin=new Memory(0x230);var adminAddress=new Memory(8);var reference=new Memory(0x98);
            var model=new Memory(0x98);var heroInfo=new Memory(0xa0);var script=new Memory(0x168);
            var inner=new Memory(0x458);var component=new Memory(16);var graph=new Memory(0x60);
            var bag=new Memory(0x3a0);var storage=new Memory(16);var nodes=new Memory(14*8);
            var modify=new Memory(0x110);var strike=new Memory(0x148);var vtable=new Memory(8);
            var damage=new Memory(0xb0);var health=new Memory(0x40);var config=new Memory(8);
            var radius=new Memory(24);var offset=new Memory(32);var pairs=new Memory(16);
            var logger=new Memory(16);var sentinel=new Memory(40);var outer=new Memory(64);
            var stateHead=new Memory(40);var strikeRow=new Memory(64);
            var creation=new Memory(8);var exit=new Memory(8);var system=new Memory(8);var user=new Memory(8);
            var reader=new NativeSkillReader(true)){
            for(var memory:new Memory[]{admin,adminAddress,reference,model,heroInfo,script,inner,component,
                graph,bag,storage,nodes,modify,strike,vtable,damage,health,config,radius,offset,pairs,
                logger,sentinel,outer,stateHead,strikeRow})memory.clear();
            require(kernel.GetProcessTimes(handle,creation,exit,system,user),"fixture process identity");
            adminAddress.setLong(0,Pointer.nativeValue(admin));admin.setInt(0x220,17);
            reference.setInt(0x94,19);model.setInt(0x94,19);model.setLong(0x28,Pointer.nativeValue(admin));
            script.setLong(0x150,0x0580000000000043L);script.setLong(0x98,Pointer.nativeValue(bag));
            script.setLong(0x160,Pointer.nativeValue(graph));script.setLong(0x10,Pointer.nativeValue(inner));
            inner.setLong(0x450,Pointer.nativeValue(component));component.setLong(8,Pointer.nativeValue(model));
            graph.setLong(0x50,Pointer.nativeValue(storage));graph.setLong(0x58,1);
            storage.setLong(0,Pointer.nativeValue(nodes));storage.setLong(8,14);
            nodes.setLong(12*8,Pointer.nativeValue(modify));nodes.setLong(13*8,Pointer.nativeValue(strike));
            modify.setLong(0,Pointer.nativeValue(vtable));strike.setLong(0,Pointer.nativeValue(vtable));
            damage.setLong(0,Pointer.nativeValue(vtable));damage.setInt(0xa0,30);damage.setInt(0xac,2);
            radius.setLong(0,Pointer.nativeValue(vtable));radius.setInt(16,1);
            offset.setLong(0,Pointer.nativeValue(vtable));offset.setFloat(16,0);
            offset.setFloat(20,1.5f);offset.setFloat(24,1.5f);
            bag.setLong(0xa0,Pointer.nativeValue(pairs));bag.setInt(0xa8,1);bag.setInt(0xac,1);
            pairs.setLong(0,0x0d800000000001dcL);pairs.setLong(8,Pointer.nativeValue(damage));
            modify.setLong(0x108,Pointer.nativeValue(health));health.setLong(0x38,Pointer.nativeValue(config));
            strike.setLong(0x130,Pointer.nativeValue(offset));strike.setLong(0x140,Pointer.nativeValue(radius));
            logger.setLong(0,Pointer.nativeValue(sentinel));logger.setLong(8,1);
            sentinel.setLong(8,Pointer.nativeValue(outer));sentinel.setByte(25,(byte)1);
            outer.setLong(0,Pointer.nativeValue(sentinel));outer.setLong(8,Pointer.nativeValue(sentinel));
            outer.setLong(16,Pointer.nativeValue(sentinel));outer.setLong(32,Pointer.nativeValue(script));
            outer.setLong(40,Pointer.nativeValue(stateHead));outer.setLong(48,1);
            stateHead.setByte(25,(byte)1);stateHead.setLong(8,Pointer.nativeValue(strikeRow));
            strikeRow.setLong(0,Pointer.nativeValue(stateHead));strikeRow.setLong(8,Pointer.nativeValue(stateHead));
            strikeRow.setLong(16,Pointer.nativeValue(stateHead));strikeRow.setInt(32,13);
            strikeRow.setLong(40,100); // flag 0 is a genuine TrackTargets Begin.
            var binding=new JsonObject();binding.addProperty("version",1);binding.addProperty("pid",pid);
            binding.addProperty("creation",creation.getLong(0));binding.addProperty("localId",17);
            binding.addProperty("modelId",19);binding.addProperty("resource",0x0580000000000043L);
            String[] fields={"admin","adminAddress","reference","model","heroInfo","script","graph","bag","logger",
                "damage","health","damageConfig","radius","radiusVtable","offset","offsetVtable","numericVtable"};
            Memory[] addresses={admin,adminAddress,reference,model,heroInfo,script,graph,bag,logger,
                damage,health,config,radius,vtable,offset,vtable,vtable};
            for(int i=0;i<fields.length;i++)binding.addProperty(fields[i],Pointer.nativeValue(addresses[i]));
            binding.addProperty("damageBucket",0);binding.addProperty("eye",1.5);
            var states=new JsonObject();
            for(int i=0;i<2;i++){
                var node=new JsonObject();node.addProperty("index",12+i);
                node.addProperty("address",Pointer.nativeValue(i==0?modify:strike));
                node.addProperty("vtable",Pointer.nativeValue(vtable));states.add(i==0?"modify":"strike",node);
            }
            binding.add("states",states);System.setProperty("owmc.nativeEventsDirectory",directory.toString());
            var pose=new HostPoseReader.Pose(42,1,pid,1,70,
                new float[]{1,0,0,0,1,0,0,0,1},new float[]{0,0,0},0,false);
            long winston=0x02e0000000000009L,widow=0x02e000000000000aL;
            binding.addProperty("hero",winston);heroInfo.setLong(0x98,winston);Files.writeString(file,binding.toString());
            require(reader.poll(pose,19,winston)!=null,"Winston reference melee fixture must authenticate");
            reader.close();binding.addProperty("hero",widow);heroInfo.setLong(0x98,widow);
            Files.writeString(file,binding.toString());
            require(!binding.has("infraDuration"),"melee graph must not contain ultimate geometry");
            var state=reader.poll(pose,19,widow);
            if(expectBroken){
                require(state==null&&!reader.error.isBlank(),"baseline reproduces Widow-only reader rejection");
                System.out.println("PASS baseline: Winston accepted; Widow melee rejected: "+reader.error);
                return;
            }
            require(state!=null,"Widow melee must authenticate without Infra-Sight: "+reader.error);
            require(state.active("strike")&&state.geometry().damage()==30&&state.geometry().radius()==1,
                "real native strike and live geometry must survive the fix");
            var phase=new NativeDashPhase();
            require(!phase.observe(state.source(),state.model(),100,true,0),"first sample stays a baseline");
            strikeRow.setLong(40,101);state=reader.poll(pose,19,widow);
            require(phase.observe(state.source(),state.model(),state.entries().get("strike").tick(),true,1),
                "fresh original strike admits one swing");
            require(!phase.observe(state.source(),state.model(),101,true,2),"replay must not admit another swing");
            damage.setInt(0xa0,35);
            require(reader.poll(pose,19,widow).geometry().damage()==35,"live damage stays authoritative");
            pairs.setLong(0,123);
            require(reader.poll(pose,19,widow)==null,"altered native damage membership stays rejected");
            pairs.setLong(0,0x0d800000000001dcL);offset.setFloat(24,15);
            require(reader.poll(pose,19,widow)==null,"altered native geometry stays rejected");
            offset.setFloat(24,1.5f);heroInfo.setLong(0x98,winston);
            require(reader.poll(pose,19,widow)==null,"changed native hero owner stays rejected");
            System.out.println("PASS candidate: Widow native melee/geometry, baseline, replay and tamper gates");
        }finally{
            kernel.CloseHandle(handle);Files.deleteIfExists(file);Files.deleteIfExists(directory);
            if(previous==null)System.clearProperty("owmc.nativeEventsDirectory");
            else System.setProperty("owmc.nativeEventsDirectory",previous);
        }
    }
}
