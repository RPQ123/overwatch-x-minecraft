package lab.owmcguest;

import java.util.HashMap;
import java.util.Map;
import java.util.UUID;

/** 已执行的原版 Begin 令牌。效果 cleanup 不得清除；MC 换世界也不是新的原版 Begin。 */
final class NativeTorbjornCoreAdmission {
    record Actor(UUID owner,long source,long model){}
    private final Map<Actor,Long> admitted=new HashMap<>();
    private final int capacity;
    NativeTorbjornCoreAdmission(){this(4096);}
    NativeTorbjornCoreAdmission(int capacity){if(capacity<1)throw new IllegalArgumentException();this.capacity=capacity;}
    boolean admit(Actor actor,long begin){
        if(actor==null||actor.owner()==null||actor.source()==0||actor.model()==0||begin<=0)return false;
        var previous=admitted.get(actor);
        if(previous!=null&&begin<=previous)return false;
        // 不驱逐旧令牌：容量耗尽时拒绝新 actor，不能为腾空间重新开放旧 Begin。
        if(previous==null&&admitted.size()>=capacity)return false;
        admitted.put(actor,begin);return true;
    }
}
