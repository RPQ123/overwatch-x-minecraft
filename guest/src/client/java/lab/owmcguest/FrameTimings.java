package lab.owmcguest;

import java.util.Arrays;

/** Bounded recent timings in nanoseconds; snapshots are taken on the status thread. */
final class FrameTimings {
    private final long[] samples=new long[1024];private int at,count;
    synchronized void add(long ns){samples[at]=ns;at=(at+1)%samples.length;count=Math.min(samples.length,count+1);}
    synchronized String json(){
        if(count==0)return "null";long[] sorted=Arrays.copyOf(samples,count);Arrays.sort(sorted);double sum=0;for(long v:sorted)sum+=v;
        return "{\"samples\":"+count+",\"meanMs\":"+(sum/count/1e6)+",\"p50Ms\":"+(sorted[(count-1)/2]/1e6)+",\"p95Ms\":"+(sorted[(int)((count-1)*.95)]/1e6)+",\"p99Ms\":"+(sorted[(int)((count-1)*.99)]/1e6)+",\"maxMs\":"+(sorted[count-1]/1e6)+"}";
    }
}
