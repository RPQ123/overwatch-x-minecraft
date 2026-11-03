package lab.owmcguest;

import com.google.gson.*;
import com.sun.jna.*;
import java.nio.*;
import java.nio.file.*;
import java.util.*;

/** Real self-process memory oracle: damage, healing, zero and stale-owner refusal. */
public final class SurvivalHealthCheck {
    private static void require(boolean ok,String label){if(!ok)throw new AssertionError(label);}
    public static void main(String[] args)throws Exception{
        var dir=Files.createTempDirectory("owmc-survival-health-");String old=System.getProperty("owmc.nativeEventsDirectory");
        int pid=(int)ProcessHandle.current().pid();var kernel=Native.load("kernel32",NativeAbilityReader.Kernel.class);var handle=kernel.OpenProcess(0x400,false,pid);
        try(var admin=new Memory(0x230);var adminAddress=new Memory(8);var reference=new Memory(0x98);var model=new Memory(0x98);
            var info=new Memory(0xa0);var health=new Memory(0x480);var vtable=new Memory(8);var numericVtable=new Memory(8);var components=new Memory(16);
            var base=new Memory(0xb0);var armor=new Memory(0xb0);var shield=new Memory(0xb0);
            var creation=new Memory(8);var exit=new Memory(8);var system=new Memory(8);var user=new Memory(8);var reader=new NativeHealthReader()){
            for(var m:new Memory[]{admin,adminAddress,reference,model,info,health,vtable,numericVtable,components,base,armor,shield})m.clear();
            require(kernel.GetProcessTimes(handle,creation,exit,system,user),"self-process creation");
            adminAddress.setLong(0,Pointer.nativeValue(admin));admin.setInt(0x220,17);reference.setInt(0x94,19);model.setInt(0x94,19);
            info.setLong(0x98,0x02e0000000000029L);health.setLong(0,Pointer.nativeValue(vtable));health.setLong(8,Pointer.nativeValue(model));health.setByte(0x10,(byte)0x28);
            model.setLong(0x50,Pointer.nativeValue(components));model.setInt(0x58,2);model.setInt(0x5c,2);components.setLong(0,Pointer.nativeValue(health));
            int[] offsets={0x98,0x1d8,0x318};double[] amounts={200,50,25};Memory[] variables={base,armor,shield};var pools=new JsonArray();
            for(int j=0;j<3;j++){
                variables[j].setLong(0,Pointer.nativeValue(numericVtable));variables[j].setInt(0xa0,(int)amounts[j]);variables[j].setInt(0xac,2);
                health.setInt(offsets[j],1);health.setFloat(offsets[j]+4,(float)amounts[j]);health.setFloat(offsets[j]+8,(float)amounts[j]);health.setInt(offsets[j]+12,0x12345678);
                var p=new JsonObject();p.addProperty("offset",offsets[j]);p.addProperty("amount",amounts[j]);p.addProperty("variable",Pointer.nativeValue(variables[j]));p.addProperty("amountRaw",HexFormat.of().formatHex(variables[j].getByteArray(0xa0,16)));pools.add(p);
            }
            var b=new JsonObject();b.addProperty("version",1);b.addProperty("pid",pid);b.addProperty("creation",creation.getLong(0));b.addProperty("localId",17);b.addProperty("modelId",19);b.addProperty("hero",0x02e0000000000029L);
            b.addProperty("executableSha256","f73a747b7d63a07402958b2b2c4587125a46ef8e181281669da009d352308e9f");b.add("pools",pools);
            String[] names={"admin","adminAddress","reference","model","heroInfo","health","healthVtable","numericVtable"};Memory[] values={admin,adminAddress,reference,model,info,health,vtable,numericVtable};
            for(int j=0;j<names.length;j++)b.addProperty(names[j],Pointer.nativeValue(values[j]));
            var file=dir.resolve("native-health-request-"+pid+".json");Files.writeString(file,b.toString());System.setProperty("owmc.nativeEventsDirectory",dir.toString());
            var pose=new HostPoseReader.Pose(42,1,pid,1,70,new float[]{1,0,0,0,1,0,0,0,1},new float[]{0,0,0},0,false);
            var state=reader.poll(pose,19,0x02e0000000000029L);require(state!=null&&state.maximum()==275&&state.current()==275,"original pools");
            require(reader.write(state,225)&&health.getFloat(0x98+8)==200&&health.getFloat(0x1d8+8)==25&&health.getFloat(0x318+8)==0,"damage consumes shield then armor");
            for(int offset:offsets)require(health.getInt(offset+12)==0x12345678,"native pool metadata preserved");
            require(!reader.write(state,100),"stale snapshot refused");
            state=reader.poll(pose,19,0x02e0000000000029L);require(reader.write(state,260),"healing replenishes actual pools");
            state=reader.poll(pose,19,0x02e0000000000029L);require(reader.write(state,0),"real zero health");
            state=reader.poll(pose,19,0x02e0000000000029L);reference.setInt(0x94,20);require(!reader.write(state,275)&&health.getFloat(0x98+8)==0,"departed hero never written");reference.setInt(0x94,19);
            require(reader.poll(pose,19,0x02e0000000000029L)!=null,"reader reconnect does not heal");
            health.setInt(0x98+20,1);require(reader.poll(pose,19,0x02e0000000000029L)==null,"additional native pools retained");health.setInt(0x98+20,0);
            base.setInt(0xa0,201);require(reader.poll(pose,19,0x02e0000000000029L)==null,"changed typed config rejected");base.setInt(0xa0,200);
            reader.close();b.addProperty("creation",creation.getLong(0)-1);Files.writeString(file,b.toString());require(reader.poll(pose,19,0x02e0000000000029L)==null,"PID reuse rejected");
            require(HeroNpcCatalog.ENTRIES.size()==12&&HeroNpcCatalog.ENTRIES.stream().map(HeroNpcCatalog.Entry::id).distinct().count()==12,"all twelve heroes unique");
        }finally{kernel.CloseHandle(handle);if(old==null)System.clearProperty("owmc.nativeEventsDirectory");else System.setProperty("owmc.nativeEventsDirectory",old);}
        System.out.println("PASS: survival native pools, metadata, damage/heal/zero, stale owner/config/creation, twelve-hero catalog");
    }
}
