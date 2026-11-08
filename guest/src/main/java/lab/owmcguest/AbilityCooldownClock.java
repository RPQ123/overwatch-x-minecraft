package lab.owmcguest;

import java.util.*;

/** Offline server adaptation. Never advances an available ability, a newer native
 * cooldown, a stale lease or an already faster native counter. */
public final class AbilityCooldownClock {
    private record Sample(long wall,float seconds){}
    private final Map<Long,Sample> samples=new HashMap<>();
    public void clear(){samples.clear();}
    public float sample(long state,long now,float nativeSeconds,boolean available){
        if(state==0||now<=0||!Float.isFinite(nativeSeconds)||nativeSeconds<0||nativeSeconds>120)throw new IllegalArgumentException("ability clock bounds");
        if(available||nativeSeconds==0){samples.remove(state);return nativeSeconds;}
        var old=samples.get(state);float next=nativeSeconds;
        if(old!=null&&now>=old.wall()&&now-old.wall()<=1000&&nativeSeconds<=old.seconds()+.05f)
            next=Math.min(nativeSeconds,Math.max(0,old.seconds()-(now-old.wall())/1000.f));
        if(samples.size()>=128&&!samples.containsKey(state))samples.clear();
        samples.put(state,new Sample(now,next));return next;
    }
}
