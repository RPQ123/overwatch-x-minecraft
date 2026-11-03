package lab.owmcguest;

import java.util.UUID;
import java.util.List;
import com.google.gson.JsonObject;
import net.minecraft.server.MinecraftServer;
import net.minecraft.server.network.ServerPlayerEntity;
import net.minecraft.util.math.*;
import net.minecraft.particle.ParticleTypes;

/** Real MC history/health rewind, completed only by the original cast End. */
public final class NativeRecallRuntime {
    public static final long HERO=0x02e0000000000003L;
    public record Scope(UUID owner,long world,long source,long model){}
    public record Completion(Scope scope,long begin,long wall,boolean moved){}
    private record Pending(long begin,long wall,List<NativeRecallHistory.Point> candidates){}
    private static final NativeRecallHistory history=new NativeRecallHistory();
    private static Scope scope;private static Pending active;private static long lastBegin,starts,completed,refused,timeouts;
    private static double lastDistance,healed;
    private static long emptyHistoryCancellations,lastBeginWall;
    private static Scope historyTestScope;private static long historyTestUntilNanos,historyTestUntilWall;
    private static String historyTestError="";
    public static volatile String status="{\"active\":false}";
    public static volatile Completion completion;
    public static void configure(UUID owner,long world,long hero,long model,long source){
        resetSession();
        if(hero==HERO&&owner!=null&&world!=0&&model!=0&&source!=0){
            scope=new Scope(owner,world,source,model);
            if(completion!=null&&!completion.scope().equals(scope))completion=null;
        }else if(hero!=0&&hero!=HERO)completion=null;
        // Unknown identity can suspend/cancel gameplay, but cannot erase the
        // exact old cast's cleanup disposition before that pawn is observed
        // again. A definite different world/model/source drops it above.
    }
    private static boolean matches(ServerPlayerEntity p,Scope s){return s!=null&&p!=null&&p.isAlive()&&p.getUuid().equals(s.owner())
        &&NativeWorldIdentity.of(p.getServer(),p.getWorld().getRegistryKey())==s.world()
        &&NativeEliminationRuntime.sessionMatches(s.owner(),s.world(),HERO,s.model(),s.source());}
    public static void begin(MinecraftServer server,Scope s,long tick,long wall){
        var p=server.getPlayerManager().getPlayer(s.owner());long now=System.currentTimeMillis();
        if(!s.equals(scope)||!matches(p,s)||tick<=lastBegin||now-wall>150||wall>now+50||active!=null){refused++;return;}
        lastBegin=tick;lastBeginWall=wall;var points=history.candidates(wall);
        if(points.isEmpty()){
            // A verified original cast still needs a terminal disposition when
            // MC has no pre-Begin history. The client sends this cancellation
            // only after the actual native End; phase3 grants no heal or ammo.
            refused++;emptyHistoryCancellations++;completion=new Completion(s,tick,now,false);publish();return;
        }
        completion=null;active=new Pending(tick,wall,points);starts++;
        p.getServerWorld().spawnParticles(ParticleTypes.REVERSE_PORTAL,p.getX(),p.getY()+1,p.getZ(),30,.25,.5,.25,.02);publish();
    }
    public static void finish(MinecraftServer server,Scope s,long begin,long end,long wall){
        var p=server.getPlayerManager().getPlayer(s.owner());long now=System.currentTimeMillis();var pending=active;
        if(!s.equals(scope)||!matches(p,s)||pending==null||pending.begin()!=begin||end<begin||now-wall>150||wall>now+50){refused++;return;}
        active=null;var w=p.getServerWorld();NativeRecallHistory.Point chosen=null;
        for(var old:pending.candidates()){
            var dest=new Vec3d(old.x(),old.y(),old.z());if(dest.squaredDistanceTo(p.getPos())>128*128)continue;
            var box=p.getBoundingBox().offset(dest.subtract(p.getPos()));boolean loaded=true;
            for(int x=(int)Math.floor(box.minX)>>4;x<=((int)Math.floor(box.maxX)>>4);x++)for(int z=(int)Math.floor(box.minZ)>>4;z<=((int)Math.floor(box.maxZ)>>4);z++)if(!w.isChunkLoaded(new BlockPos(x<<4,(int)dest.y,z<<4)))loaded=false;
            if(loaded&&w.getWorldBorder().contains(box)&&dest.y>=w.getBottomY()&&w.isSpaceEmpty(p,box)){chosen=old;break;}
        }
        if(chosen==null){refused++;completion=new Completion(s,begin,now,false);publish();return;}
        var old=p.getPos();var dest=new Vec3d(chosen.x(),chosen.y(),chosen.z());lastDistance=old.distanceTo(dest);
        p.requestTeleport(dest.x,dest.y,dest.z);p.setVelocity(Vec3d.ZERO);p.fallDistance=0;
        float before=p.getHealth();p.heal(Math.max(0,chosen.health()-before));healed+=p.getHealth()-before;
        for(int i=0;i<=12;i++){var at=old.lerp(dest,i/12.);w.spawnParticles(ParticleTypes.ELECTRIC_SPARK,at.x,at.y+.8,at.z,2,.12,.2,.12,0);}
        w.spawnParticles(ParticleTypes.END_ROD,dest.x,dest.y+1,dest.z,20,.2,.5,.2,.03);
        // Start audio is submitted by RecallStartSound at the native Begin;
        // native End/MC arrival must not produce a second, delayed cue.
        completed++;completion=new Completion(s,begin,now,true);history.clear();publish();
    }
    public static boolean protects(net.minecraft.entity.Entity e){return e instanceof ServerPlayerEntity p&&active!=null&&matches(p,scope)&&System.currentTimeMillis()-active.wall()<=1500;}
    public static void tick(MinecraftServer server){
        if(scope==null)return;var p=server.getPlayerManager().getPlayer(scope.owner());
        if(!matches(p,scope)){resetSession();return;}
        long now=System.currentTimeMillis();if(active!=null&&now-active.wall()>1500){completion=new Completion(scope,active.begin(),now,false);active=null;timeouts++;}
        if(active==null&&!historySuppressedForTest())history.add(new NativeRecallHistory.Point(now,p.getX(),p.getY(),p.getZ(),p.getHealth()));publish();
    }
    /** Server-thread-only, fixed-duration fault fixture in the disposable Switch save. */
    public static boolean pauseHistoryForTest(MinecraftServer server,Scope expected){
        if(!server.isOnThread())throw new IllegalStateException("Recall history fixture requires the server thread");
        var p=expected==null||expected.owner()==null?null:server.getPlayerManager().getPlayer(expected.owner());
        if(!Boolean.getBoolean("owmc.twilightTrial")
            ||!System.getProperty("owmc.worldName","").startsWith("Overwatch Twilight Switch ")
            ||!server.isSingleplayer()||p==null||!p.isCreative()||!expected.equals(scope)||!matches(p,expected)||active!=null
            ||historySuppressedForTest()){
            historyTestError="Requires the current idle Tracer in the separate creative Switch save";publish();return false;
        }
        history.clear();historyTestScope=expected;historyTestUntilNanos=System.nanoTime()+500_000_000L;
        historyTestUntilWall=System.currentTimeMillis()+500;historyTestError="";publish();return true;
    }
    private static boolean historySuppressedForTest(){
        if(historyTestScope==null)return false;
        if(!historyTestScope.equals(scope)||System.nanoTime()>=historyTestUntilNanos){clearHistoryTest();return false;}
        return true;
    }
    private static void clearHistoryTest(){historyTestScope=null;historyTestUntilNanos=historyTestUntilWall=0;}
    private static void publish(){
        var o=new JsonObject();o.addProperty("active",active!=null);o.addProperty("historySamples",history.size());
        o.addProperty("starts",starts);o.addProperty("completed",completed);o.addProperty("refused",refused);o.addProperty("timeouts",timeouts);
        o.addProperty("emptyHistoryCancellations",emptyHistoryCancellations);o.addProperty("lastDistance",lastDistance);o.addProperty("healed",healed);
        o.addProperty("nativeBegin",active==null?0:active.begin());o.addProperty("completionPhase",completion==null?0:completion.moved()?2:3);
        o.addProperty("completionBegin",completion==null?0:completion.begin());o.addProperty("completionWall",completion==null?0:completion.wall());
        o.addProperty("lastBeginTick",lastBegin);o.addProperty("lastBeginWall",lastBeginWall);
        boolean paused=historySuppressedForTest();o.addProperty("historyTestPaused",paused);o.addProperty("historyTestUntil",historyTestUntilWall);
        o.addProperty("historyTestWorld",historyTestScope==null?0:historyTestScope.world());
        o.addProperty("historyTestSource",historyTestScope==null?0:historyTestScope.source());
        o.addProperty("historyTestModel",historyTestScope==null?0:historyTestScope.model());o.addProperty("historyTestError",historyTestError);
        status=o.toString();
    }
    public static void resetSession(){
        if(active!=null&&scope!=null)completion=new Completion(scope,active.begin(),System.currentTimeMillis(),false);
        scope=null;active=null;lastBegin=lastBeginWall=0;history.clear();clearHistoryTest();historyTestError="";publish();
    }
    public static void cancelForTests(){active=null;completion=null;history.clear();clearHistoryTest();historyTestError="";publish();}
}
