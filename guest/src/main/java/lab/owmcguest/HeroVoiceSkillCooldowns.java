package lab.owmcguest;

import java.util.LinkedHashMap;
import java.util.Map;

/** 语音挂接：新旧播放入口共享英雄+技能事件硬冷却，声道/世界/换人重置均不清除。 */
public final class HeroVoiceSkillCooldowns {
    public static final long COOLDOWN_MS=10000;
    private record Key(String hero,String event) {}
    private final Map<Key,Long> played=new LinkedHashMap<>();
    private final Map<String,Long> suppressed=new LinkedHashMap<>();
    public static boolean applies(String event){return event.equals("ult_cast")||event.startsWith("ability:");}
    public long remaining(String hero,String event,long now){
        if(!applies(event))return 0;
        Long previous=played.get(new Key(hero,event));
        return previous==null?0:Math.max(0,COOLDOWN_MS-Math.max(0,now-previous));
    }
    public boolean admit(String hero,String event,long now){
        if(remaining(hero,event,now)==0)return true;
        suppressed.merge(hero+":"+event,1L,Long::sum);return false;
    }
    public void played(String hero,String event,long now){if(applies(event))played.put(new Key(hero,event),now);}
    public Map<String,Long> active(long now){
        var out=new LinkedHashMap<String,Long>();
        played.forEach((key,value)->{long left=remaining(key.hero(),key.event(),now);if(left>0)out.put(key.hero()+":"+key.event(),left);});
        return Map.copyOf(out);
    }
    public Map<String,Long> suppressed(){return Map.copyOf(suppressed);}
}
