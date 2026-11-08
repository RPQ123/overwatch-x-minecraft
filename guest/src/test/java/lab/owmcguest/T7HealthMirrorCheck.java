package lab.owmcguest;

import com.google.gson.*;
import com.sun.jna.*;
import java.nio.*;
import java.nio.file.*;
import java.util.*;

/** Real self-process memory oracle: damage, healing, zero and stale-owner refusal. */
public final class T7HealthMirrorCheck {
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
            final var mainThread=Thread.currentThread();
            var delay=new java.util.concurrent.atomic.AtomicBoolean(true);
            var nativeWrites=new java.util.concurrent.atomic.AtomicLong();var nativeReads=new java.util.concurrent.atomic.AtomicLong();
            var closes=new java.util.concurrent.atomic.AtomicInteger();
            var entered=new java.util.concurrent.CountDownLatch(1);
            var originalKernel=NativeHealthReader.class.getDeclaredField("kernel");originalKernel.setAccessible(true);
            var delayed=(NativeAbilityReader.Kernel)java.lang.reflect.Proxy.newProxyInstance(NativeAbilityReader.Kernel.class.getClassLoader(),new Class[]{NativeAbilityReader.Kernel.class},(proxy,method,a)->{
                if(method.getName().equals("ReadProcessMemory")){nativeReads.incrementAndGet();if(delay.get())java.util.concurrent.locks.LockSupport.parkNanos(2_000_000L);}
                if(method.getName().equals("WriteProcessMemory"))nativeWrites.incrementAndGet();
                try{return method.invoke(kernel,a);}catch(java.lang.reflect.InvocationTargetException e){throw e.getCause();}
            });originalKernel.set(reader,delayed);
            long legacyStarted=System.nanoTime();state=reader.poll(pose,19,0x02e0000000000029L);require(state!=null&&reader.write(state,225),"retained synchronous path comparison");
            double synchronousMs=(System.nanoTime()-legacyStarted)/1_000_000.;long synchronousReads=nativeReads.get(),synchronousWrites=nativeWrites.get();
            for(int j=0;j<3;j++)health.setFloat(offsets[j]+8,(float)amounts[j]);nativeReads.set(0);nativeWrites.set(0);
            var port=new NativeHealthMirror.Port(){
                public NativeHealthReader.State poll(HostPoseReader.Pose h,long modelId,long hero){require(Thread.currentThread()!=mainThread,"native polling must not run on main");entered.countDown();return reader.poll(h,modelId,hero);}
                public boolean write(NativeHealthReader.State s,double target,java.util.function.BooleanSupplier admitted){require(Thread.currentThread()!=mainThread,"native writing must not run on main");return reader.write(s,target,admitted);}
                public String error(){return reader.error;}
                public void close(){reader.close();closes.incrementAndGet();}
            };
            var owner=UUID.randomUUID();var mirror=new NativeHealthMirror(port);long maximum=0;int mainExchanges=0;long[] costs=new long[40];
            java.util.function.Function<Float,NativeHealthMirror.Context> request=hp->{long wall=System.currentTimeMillis();return new NativeHealthMirror.Context(pose,owner,1,19,0x02e0000000000029L,wall,new NativeHealthMirror.Target(true,hp,wall));};
            try{
                mirror.submit(request.apply(22.5f));require(entered.await(1,java.util.concurrent.TimeUnit.SECONDS),"worker begins real self-process polling");
                for(int step=0;step<40;step++){
                    var next=request.apply(10f);long start=System.nanoTime();mirror.submit(next);mirror.latest(next,System.currentTimeMillis());long cost=System.nanoTime()-start;
                    costs[step]=cost;maximum=Math.max(maximum,cost);mainExchanges++;Thread.sleep(2);
                }
                long start=System.nanoTime();mirror.clear();maximum=Math.max(maximum,System.nanoTime()-start);
                await(()->closes.get()>0,5000,"clear closes in-flight reader on its owner");
                require(nativeWrites.get()==0&&health.getFloat(0x98+8)==200&&health.getFloat(0x1d8+8)==50&&health.getFloat(0x318+8)==25,"cancelled in-flight HP cannot reach native memory");
                require(maximum<50_000_000L,"main never waits for the injected native I/O");delay.set(false);
                mirror.submit(request.apply(22.5f));mirror.submit(request.apply(10f));
                await(()->health.getFloat(0x98+8)==100&&health.getFloat(0x1d8+8)==0&&health.getFloat(0x318+8)==0,3000,"latest MC HP reaches native pools after I/O resumes");
                var wrong=new NativeHealthMirror.Context(pose,owner,2,19,0x02e0000000000029L,System.currentTimeMillis(),null);
                require(mirror.latest(wrong,System.currentTimeMillis())==null,"old-world result never admitted");
                var result=new JsonObject();result.addProperty("fixtureOnly",true);result.addProperty("injectedRequestedDelayPerReadMs",2);result.addProperty("retainedSynchronousPathMs",synchronousMs);result.addProperty("retainedSynchronousReads",synchronousReads);result.addProperty("retainedSynchronousWrites",synchronousWrites);result.addProperty("mainExchanges",mainExchanges);result.addProperty("maxMainExchangeMs",maximum/1_000_000.);Arrays.sort(costs);result.addProperty("mainP95Ms",costs[37]/1_000_000.);result.addProperty("canceledNativeWrites",0);result.addProperty("eventualNativeHp",100);result.add("mirror",mirror.diagnostics());Files.writeString(Path.of(args[0]),result.toString());System.out.println("PASS T7 guarded asynchronous HP mirror "+result);
            }finally{mirror.close();await(mirror::stopped,5000,"worker release is bounded in fixture");}
            state=reader.poll(pose,19,0x02e0000000000029L);require(state!=null,"handoff complete");long prior=nativeWrites.get();
            var gate=new java.util.concurrent.atomic.AtomicInteger();require(!reader.write(state,50,()->gate.getAndIncrement()==0),"admission rechecked immediately before native write");
            require(nativeWrites.get()==prior&&health.getFloat(0x98+8)==100,"late scope cancellation never writes HP");
            for(int offset:offsets)require(health.getInt(offset+12)==0x12345678,"native metadata retained");
        }finally{kernel.CloseHandle(handle);if(old==null)System.clearProperty("owmc.nativeEventsDirectory");else System.setProperty("owmc.nativeEventsDirectory",old);}
    }
    private static void await(java.util.function.BooleanSupplier condition,long timeout,String why)throws Exception{
        long deadline=System.nanoTime()+timeout*1_000_000;while(!condition.getAsBoolean()&&System.nanoTime()<deadline)Thread.sleep(2);require(condition.getAsBoolean(),why);
    }
}
