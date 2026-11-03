package lab.owmcguest;

import java.util.UUID;
import com.google.gson.JsonObject;
import net.minecraft.entity.LivingEntity;
import net.minecraft.server.MinecraftServer;

/** MC adaptation: declared self-heal amount/interval during real native phases.
 * Cryo damage rejection and fire cleansing share exactly the same scoped phase.
 */
public final class NativeSustainRuntime {
    private static final NativeSustainPhase phase=new NativeSustainPhase();
    private static long activation,lastServerTick=-1;
    private static double healed;
    private static long extinguished,casts,protectedDamageEvents,rejected;
    public static volatile String status="{\"active\":false,\"healed\":0}";
    public static boolean supported(long hero){return hero==0x02e0000000000015L||hero==0x02e00000000000ddL;}
    public static void refresh(UUID owner,long world,long source,long model,long hero,long tick,boolean active,double amount,double interval,long wall){
        long now=System.currentTimeMillis();
        if(owner==null||!supported(hero)||!NativeEliminationRuntime.sessionMatches(owner,world,hero,model,source)||now-wall>150||wall>now+50){rejected++;return;}
        var scope=new NativeSustainPhase.Scope(owner,world,source,model,hero);
        boolean changed=!scope.equals(phase.scope())||phase.tick()!=tick;
        if(!phase.refresh(scope,tick,active,amount,interval,wall)){rejected++;return;}
        if(changed){activation=tick;lastServerTick=-1;if(active&&tick>0)casts++;}
    }
    private static boolean valid(MinecraftServer server,NativeSustainPhase.Scope s){
        if(s==null||!phase.active(System.currentTimeMillis()))return false;
        var p=server.getPlayerManager().getPlayer(s.owner());
        return p!=null&&p.isAlive()&&NativeWorldIdentity.of(server,p.getWorld().getRegistryKey())==s.world()
            &&NativeEliminationRuntime.sessionMatches(s.owner(),s.world(),s.hero(),s.model(),s.source());
    }
    public static boolean protects(LivingEntity entity){
        var s=phase.scope();boolean protectedNow=s!=null&&s.hero()==NativeSustainPhase.MEI&&entity.getUuid().equals(s.owner())
            &&entity.getServer()!=null&&valid(entity.getServer(),s);
        if(protectedNow)protectedDamageEvents++;
        return protectedNow;
    }
    public static void tick(MinecraftServer server){
        var s=phase.scope();boolean active=valid(server,s);double rate=0;
        if(active){
            if(s.hero()==0x02e00000000000ddL){
                var p=server.getPlayerManager().getPlayer(s.owner());
                if(p.getFireTicks()>0){p.extinguish();extinguished++;}
            }
            rate=phase.rate();
            long current=Integer.toUnsignedLong(server.getTicks());
            if(lastServerTick>=0&&current==lastServerTick+1){
                var p=server.getPlayerManager().getPlayer(s.owner());float before=p.getHealth();
                float amount=(float)phase.consume();
                if(amount>0){p.heal(amount);double actual=Math.max(0,p.getHealth()-before);healed+=actual;}
            }
            lastServerTick=current;
        }else lastServerTick=-1;
        var out=new JsonObject();out.addProperty("active",active);out.addProperty("hero",s==null?0:s.hero());out.addProperty("nativeTick",activation);out.addProperty("rateMcHp",rate);out.addProperty("healed",healed);out.addProperty("remaining",Double.isFinite(phase.remaining())?phase.remaining():-1);out.addProperty("extinguished",extinguished);
        out.addProperty("casts",casts);out.addProperty("protectedDamageEvents",protectedDamageEvents);out.addProperty("rejected",rejected);
        out.addProperty("source",s==null?0:s.source());out.addProperty("model",s==null?0:s.model());out.addProperty("world",s==null?0:s.world());
        out.addProperty("adapter","declared-amount-over-interval");status=out.toString();
    }
    public static void resetSession(){phase.clear();activation=0;lastServerTick=-1;healed=0;extinguished=casts=protectedDamageEvents=rejected=0;status="{\"active\":false,\"healed\":0,\"extinguished\":0,\"casts\":0,\"protectedDamageEvents\":0,\"rejected\":0}";}
}
