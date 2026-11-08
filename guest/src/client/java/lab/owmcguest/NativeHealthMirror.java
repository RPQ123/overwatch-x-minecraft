package lab.owmcguest;

import java.util.UUID;
import java.util.function.Supplier;

/** Same guarded HP reader/writer, owned exclusively by a daemon, never render/tick.
 * Only absolute MC health coalesces; vanilla damage and voice events stay intact. */
final class NativeHealthMirror implements AutoCloseable {
    record Target(boolean enabled,float health,long wall){}
    record Context(HostPoseReader.Pose host,UUID owner,long world,long model,long hero,long wall,Target target){
        boolean same(Context b){return b!=null&&owner.equals(b.owner)&&world==b.world&&model==b.model&&hero==b.hero
            &&host.pid()==b.host.pid()&&host.generation()==b.host.generation();}
        boolean fresh(long now){return now>=wall&&now-wall<=250;}
    }
    record Result(Context context,NativeHealthReader.State state,long wall){}
    interface Port extends AutoCloseable{
        NativeHealthReader.State poll(HostPoseReader.Pose h,long model,long hero);
        boolean write(NativeHealthReader.State state,double target,java.util.function.BooleanSupplier admitted);
        String error();
        void close();
    }
    private static final class ReaderPort implements Port{
        private NativeHealthReader reader;
        public NativeHealthReader.State poll(HostPoseReader.Pose h,long m,long hero){if(reader==null)reader=new NativeHealthReader();return reader.poll(h,m,hero);}
        public boolean write(NativeHealthReader.State s,double target,java.util.function.BooleanSupplier admitted){return reader!=null&&reader.write(s,target,admitted);}
        public String error(){return reader==null?"waiting for native health binding":reader.error;}
        public void close(){if(reader!=null){reader.close();reader=null;}}
    }
    private final Port port;private final LatestSnapshotWorker<Context,Result> worker;
    volatile long writes,readNanos,writeNanos,stale;volatile String error="waiting for native health binding";
    NativeHealthMirror(){this(new ReaderPort());}
    NativeHealthMirror(Port port){this.port=port;worker=new LatestSnapshotWorker<>("OWMC guarded HP mirror",20,this::process,port::close);}
    private Result process(Context started,Supplier<Context> latest){
        long now=System.currentTimeMillis();if(!started.fresh(now)){stale++;return null;}
        long stamp=System.nanoTime();var state=port.poll(started.host(),started.model(),started.hero());readNanos=System.nanoTime()-stamp;
        var current=latest.get();now=System.currentTimeMillis();
        if(current==null||!started.same(current)||!current.fresh(now)){stale++;return null;}
        if(state==null){error=port.error();return null;}
        var target=current.target();
        if(target!=null&&now>=target.wall()&&now-target.wall()<=250){
            double wanted=target.enabled()?Math.clamp(target.health()/SurvivalHealthPlan.SCALE,0,state.maximum()):state.maximum();
            stamp=System.nanoTime();
            // Re-check admission after polling, then NativeHealthReader verifies
            // native owner/config/current pool bytes immediately before writing.
            var admitted=latest.get();
            if(admitted!=current){stale++;return new Result(current,state,now);}
            if(port.write(state,wanted,()->latest.get()==current&&current.fresh(System.currentTimeMillis()))){writes++;error="";}else error=port.error();writeNanos=System.nanoTime()-stamp;
        }else error="";
        return new Result(current,state,System.currentTimeMillis());
    }
    void submit(Context context){worker.submit(context);}
    void clear(){worker.clear();}
    boolean stopped(){return worker.stopped();}
    Result latest(Context current,long now){var r=worker.latest();return r!=null&&current.same(r.context())&&now>=r.wall()&&now-r.wall()<=250?r:null;}
    com.google.gson.JsonObject diagnostics(){var o=new com.google.gson.JsonObject();o.addProperty("owner","single-background-thread");o.addProperty("writes",writes);o.addProperty("calls",worker.calls);o.addProperty("lastWorkerMs",worker.lastNanos/1_000_000.);o.addProperty("maxWorkerMs",worker.maxNanos/1_000_000.);o.addProperty("lastReadMs",readNanos/1_000_000.);o.addProperty("lastWriteMs",writeNanos/1_000_000.);o.addProperty("stale",stale);o.addProperty("error",worker.error.isEmpty()?error:worker.error);return o;}
    @Override public void close(){worker.close();}
}
