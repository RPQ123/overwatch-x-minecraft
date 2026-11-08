package lab.owmcguest;

import java.util.concurrent.atomic.AtomicReference;
import java.util.concurrent.locks.LockSupport;
import java.util.function.*;

/** One resource owner, one latest input, no caller-thread I/O or waits.
 * Absolute snapshots may coalesce; incremental damage/events must not use this.
 * clear/close never join an OS call. The owner closes resources when it returns. */
public final class LatestSnapshotWorker<I,O> implements AutoCloseable {
    @FunctionalInterface public interface Work<I,O>{O run(I started,Supplier<I> latest)throws Exception;}
    private final AtomicReference<I> input=new AtomicReference<>();
    private final Work<I,O> work;private final Runnable release;private final long period;
    private final Thread thread;private volatile O output;private volatile boolean closed,stopped;
    public volatile String error="";public volatile long calls,lastNanos,maxNanos;
    public LatestSnapshotWorker(String name,long periodMillis,Work<I,O> work,Runnable release){
        if(periodMillis<10||periodMillis>1000)throw new IllegalArgumentException("worker period");
        this.period=periodMillis*1_000_000;this.work=work;this.release=release;
        thread=new Thread(this::loop,name);thread.setDaemon(true);thread.setPriority(Thread.MIN_PRIORITY);thread.start();
    }
    public void submit(I next){if(next==null){clear();return;}if(!closed){input.set(next);LockSupport.unpark(thread);}}
    public void clear(){input.set(null);output=null;LockSupport.unpark(thread);}
    public O latest(){return output;}
    public boolean stopped(){return stopped;}
    private void loop(){
        boolean owned=false;long next=0;
        try{while(!closed){
            I item=input.get();
            if(item==null){if(owned){release.run();owned=false;}next=0;LockSupport.park();continue;}
            long remaining=next-System.nanoTime();if(remaining>0){LockSupport.parkNanos(remaining);continue;}
            long started=System.nanoTime();owned=true;
            try{O result=work.run(item,input::get);if(!closed&&input.get()!=null)output=result;error="";}
            catch(Exception failure){output=null;error=failure.toString();release.run();owned=false;}
            finally{calls++;lastNanos=System.nanoTime()-started;maxNanos=Math.max(maxNanos,lastNanos);next=System.nanoTime()+period;}
        }}finally{output=null;try{release.run();}finally{stopped=true;}}
    }
    @Override public void close(){closed=true;clear();thread.interrupt();LockSupport.unpark(thread);}
}
