package lab.owmcguest;

import java.util.concurrent.ArrayBlockingQueue;
import java.util.concurrent.CountDownLatch;

/** Reproduce an old producer offering work after the client cleared its queue. */
public final class NativeUltimateEventGateCheck {
    private static void require(boolean ok){if(!ok)throw new AssertionError("ultimate event crossed its session");}
    public static void main(String[] args)throws Exception{
        var old=new NativeUltimateEventGate.Scope(1,10,20,30);
        var next=new NativeUltimateEventGate.Scope(2,11,20,30);
        var queue=new ArrayBlockingQueue<NativeUltimateEventGate.Scope>(4);
        var sampled=new CountDownLatch(1);var release=new CountDownLatch(1);
        var producer=new Thread(()->{try{sampled.countDown();release.await();queue.put(old);}catch(InterruptedException e){Thread.currentThread().interrupt();}});
        producer.start();sampled.await();queue.clear();release.countDown();producer.join();
        require(!NativeUltimateEventGate.accepts(queue.take(),next,1000,1050));
        require(NativeUltimateEventGate.accepts(next,next,1000,1050));
        require(!NativeUltimateEventGate.accepts(next,new NativeUltimateEventGate.Scope(3,11,20,31),1000,1050));
        require(!NativeUltimateEventGate.accepts(next,new NativeUltimateEventGate.Scope(2,11,21,30),1000,1050));
        require(!NativeUltimateEventGate.accepts(next,next,1000,1201));
        require(!NativeUltimateEventGate.accepts(next,next,1101,1050));
        var invalid=new NativeUltimateEventGate.Scope(0,0,0,0);require(!NativeUltimateEventGate.accepts(invalid,invalid,1000,1050));
        System.out.println("Ultimate delayed-producer race, dimension/model/source identity and freshness checks passed");
    }
}
