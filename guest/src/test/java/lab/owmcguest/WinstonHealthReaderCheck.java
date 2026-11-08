package lab.owmcguest;

import com.google.gson.*;
import com.sun.jna.*;
import java.nio.file.*;
import java.util.*;

/** Actual Win64 self-memory fixture, never a game process. Tests the complete
 * temporary pool reader/writer, not only the pure conversion planner. */
public final class WinstonHealthReaderCheck {
    private static int checks;
    private static void require(boolean value,String message){checks++;if(!value)throw new AssertionError(message);}
    public static void main(String[] args)throws Exception{
        var dir=Files.createTempDirectory("owmc-winston-hp-");String old=System.getProperty("owmc.nativeEventsDirectory");
        var kernel=Native.load("kernel32",NativeAbilityReader.Kernel.class);int pid=(int)ProcessHandle.current().pid();var handle=kernel.OpenProcess(0x400,false,pid);
        var lease=WinstonClient.class.getDeclaredField("primalUntil");lease.setAccessible(true);
        try(var admin=new Memory(0x230);var adminAddress=new Memory(8);var reference=new Memory(0x98);var model=new Memory(0x98);
            var info=new Memory(0xa0);var health=new Memory(0x480);var vtable=new Memory(8);var numeric=new Memory(8);var components=new Memory(16);
            var base=new Memory(0xb0);var armor=new Memory(0xb0);var shield=new Memory(0xb0);var creation=new Memory(8);var exit=new Memory(8);var system=new Memory(8);var user=new Memory(8);var reader=new NativeHealthReader()){
            for(var m:new Memory[]{admin,adminAddress,reference,model,info,health,vtable,numeric,components,base,armor,shield})m.clear();
            require(kernel.GetProcessTimes(handle,creation,exit,system,user),"self-process creation");
            adminAddress.setLong(0,Pointer.nativeValue(admin));admin.setInt(0x220,17);reference.setInt(0x94,19);model.setInt(0x94,19);info.setLong(0x98,WinstonRules.HERO);
            health.setLong(0,Pointer.nativeValue(vtable));health.setLong(8,Pointer.nativeValue(model));health.setByte(0x10,(byte)0x28);
            model.setLong(0x50,Pointer.nativeValue(components));model.setInt(0x58,2);model.setInt(0x5c,2);components.setLong(0,Pointer.nativeValue(health));
            var b=new JsonObject();b.addProperty("version",1);b.addProperty("pid",pid);b.addProperty("creation",creation.getLong(0));b.addProperty("localId",17);b.addProperty("modelId",19);b.addProperty("hero",WinstonRules.HERO);
            b.addProperty("executableSha256","f73a747b7d63a07402958b2b2c4587125a46ef8e181281669da009d352308e9f");
            String[] names={"admin","adminAddress","reference","model","heroInfo","health","healthVtable","numericVtable"};Memory[] values={admin,adminAddress,reference,model,info,health,vtable,numeric};
            for(int j=0;j<names.length;j++)b.addProperty(names[j],Pointer.nativeValue(values[j]));
            int[] offsets={0x98,0x1d8,0x318},amounts={400,100,0};Memory[] variables={base,armor,shield};var pools=new JsonArray();
            for(int j=0;j<3;j++){
                var variable=variables[j];variable.setLong(0,Pointer.nativeValue(numeric));variable.setInt(0xa0,amounts[j]);variable.setInt(0xac,2);
                health.setInt(offsets[j],amounts[j]>0?1:0);health.setFloat(offsets[j]+4,amounts[j]);health.setFloat(offsets[j]+8,amounts[j]);health.setInt(offsets[j]+12,0x12345678);
                var p=new JsonObject();p.addProperty("offset",offsets[j]);p.addProperty("amount",amounts[j]);p.addProperty("variable",Pointer.nativeValue(variable));p.addProperty("amountRaw",HexFormat.of().formatHex(variable.getByteArray(0xa0,16)));pools.add(p);
            }
            b.add("pools",pools);var file=dir.resolve("native-health-request-"+pid+".json");Files.writeString(file,b.toString());System.setProperty("owmc.nativeEventsDirectory",dir.toString());
            var pose=new HostPoseReader.Pose(42,1,pid,1,70,new float[]{1,0,0,0,1,0,0,0,1},new float[]{0,0,0},0,false);
            lease.setLong(null,0);var state=reader.poll(pose,19,WinstonRules.HERO);require(state!=null&&state.maximum()==500,"base native maximum");require(reader.write(state,450),"ordinary Winston HP write");
            int bonus=0x98+20;health.setInt(bonus,1);health.setFloat(bonus+4,500);health.setFloat(bonus+8,500);health.setLong(bonus+12,0x132435465768798aL);
            require(reader.poll(pose,19,WinstonRules.HERO)==null,"extra pool requires fresh native Primal lease");
            lease.setLong(null,System.currentTimeMillis()+10000);state=reader.poll(pose,19,WinstonRules.HERO);
            require(state!=null&&state.maximum()==1000&&state.current()==950,"Primal extra actual pool read");require(reader.write(state,875),"Primal HP written across actual slots");
            require(health.getFloat(0x98+8)+health.getFloat(bonus+8)+health.getFloat(0x1d8+8)==875,"exact total health875");
            require(health.getLong(bonus+12)==0x132435465768798aL,"extra pool owner metadata intact");require(!reader.write(state,800),"old before-image refused");
            state=reader.poll(pose,19,WinstonRules.HERO);reference.setInt(0x94,20);require(!reader.write(state,700),"recreated native pawn never written");reference.setInt(0x94,19);
            health.setFloat(bonus+4,501);require(reader.poll(pose,19,WinstonRules.HERO)==null,"unrecognized live bonus refused");
            health.setInt(bonus,0);health.setFloat(bonus+4,0);health.setFloat(bonus+8,0);lease.setLong(null,0);
            state=reader.poll(pose,19,WinstonRules.HERO);require(state!=null&&state.maximum()==500,"native End restores base without creating extra pool");
        }finally{lease.setLong(null,0);kernel.CloseHandle(handle);if(old==null)System.clearProperty("owmc.nativeEventsDirectory");else System.setProperty("owmc.nativeEventsDirectory",old);}
        System.out.println("PASS WinstonHealthReader "+checks+" self-memory assertions; original game layout remains user-test pending");
    }
}
