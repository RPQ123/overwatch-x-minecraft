package lab.owmcguest;

import java.util.*;
import com.google.gson.JsonObject;
import net.minecraft.server.MinecraftServer;
import net.minecraft.server.network.ServerPlayerEntity;
import net.minecraft.server.world.ServerWorld;
import net.minecraft.util.math.*;
import net.minecraft.world.explosion.Explosion;
import lab.owmcguest.NativeShotProtocol.*;

/** Server-owned self-only MC impulse. Projectile entry is called from admitted
 * loaded impacts BEFORE terrain destruction; mine entry requires a native cast
 * or detonation tick. Both share scope/exposure/falloff/replay handling. */
public final class NativeRocketSelfImpulse implements HeroServerModule {
    public static final NativeRocketSelfImpulse INSTANCE=new NativeRocketSelfImpulse();
    public static final long JUNKRAT=0x02e0000000000065L;
    public record Cue(long sequence,UUID owner,long world,int nativePid,long hostGeneration,long model,long hero,long wall,Vec3d impulse){}
    private final LinkedHashSet<String> seen=new LinkedHashSet<>();
    public static volatile List<Cue> cues=List.of();
    private long sequence,impacts,pushes,duplicates,blocked,outOfRange,refused,minePushes;
    private Vec3d lastImpulse=Vec3d.ZERO;
    private volatile String status="{}";
    private NativeRocketSelfImpulse(){}
    public void impact(ServerWorld world,ServerPlayerEntity p,Shot shot,NativeShotSimulation.Hit hit,Source source,long model){
        long hero=RocketSelfImpulse.hero(shot);if(hero==0)return;
        if(source==null||!hit.loaded()){refused++;publish();return;}
        var h=hit.point();var at=new Vec3d(h.x(),h.y(),h.z());var normal=hit.normal();var v=shot.velocity();
        var origin=hit.block()&&normal!=null?at.add(normal.x()*.03,normal.y()*.03,normal.z()*.03)
            :at.subtract(new Vec3d(v.x(),v.y(),v.z()).normalize().multiply(.03));
        double radius=shot.effect()==null?2.5:shot.effect().radius();
        int reach=(int)Math.ceil(NativeExplosionTerrain.strength(shot)*2)+1;
        apply(world,p,hero,source.pid(),source.hostGeneration(),model,"projectile:"+source+":"+shot.identity(),origin,radius,BlockPos.ofFloored(at),reach);
    }
    /** Builders: pass the authenticated signal's PID/session/model/tick. No
     * ground/jump prerequisite, no key reads, no own damage or terrain work.
     * Call once per actual mine burst and remove the previous vanilla kick. */
    public boolean concussiveMine(ServerWorld world,ServerPlayerEntity shooter,int nativePid,long hostGeneration,long model,long nativeTick,Vec3d actualBlastOrigin,double radius){
        if(nativeTick<=0||nativeTick>0xffffffffL){refused++;publish();return false;}
        return apply(world,shooter,JUNKRAT,nativePid,hostGeneration,model,"mine:"+nativeTick,actualBlastOrigin,radius,BlockPos.ofFloored(actualBlastOrigin),0);
    }
    private boolean apply(ServerWorld world,ServerPlayerEntity p,long hero,int pid,long generation,long model,String receipt,Vec3d origin,double radius,BlockPos footprint,int reach){
        long worldId=NativeWorldIdentity.of(world.getServer(),world.getRegistryKey());
        if(pid<=0||generation<=0||model<=0||!p.isAlive()||p.isSpectator()||p.hasVehicle()||p.getServerWorld()!=world
            ||!Double.isFinite(radius)||radius<=0||radius>16||!Double.isFinite(origin.x)||!Double.isFinite(origin.y)||!Double.isFinite(origin.z)
            ||!NativeEliminationRuntime.sessionMatches(p.getUuid(),worldId,hero,model,generation)){refused++;publish();return false;}
        String key=worldId+":"+p.getUuid()+":"+pid+":"+generation+":"+model+":"+hero+":"+receipt;
        if(!seen.add(key)){duplicates++;publish();return false;}
        if(seen.size()>4096)seen.remove(seen.iterator().next());impacts++;
        var box=p.getBoundingBox();var center=box.getCenter();
        if(center.distanceTo(origin)>=radius){outOfRange++;publish();return false;}
        // Match a projectile's accepted explosion footprint; mines need only
        // their loaded exposure rays (they do not borrow terrain destruction).
        for(int x=(footprint.getX()-reach)>>4;x<=(footprint.getX()+reach)>>4;x++)
            for(int z=(footprint.getZ()-reach)>>4;z<=(footprint.getZ()+reach)>>4;z++)
                if(!world.isChunkLoaded(new BlockPos(x<<4,footprint.getY(),z<<4))){blocked++;publish();return false;}
        for(int x=(int)Math.floor(Math.min(origin.x,box.minX))>>4;x<=((int)Math.floor(Math.max(origin.x,box.maxX))>>4);x++)
            for(int z=(int)Math.floor(Math.min(origin.z,box.minZ))>>4;z<=((int)Math.floor(Math.max(origin.z,box.maxZ))>>4);z++)
                if(!world.isChunkLoaded(new BlockPos(x<<4,(int)origin.y,z<<4))){blocked++;publish();return false;}
        double exposure=Explosion.getExposure(origin,p);
        var impulse=RocketSelfImpulse.calculate(new Vec(origin.x,origin.y,origin.z),new Vec(center.x,center.y,center.z),radius,exposure);
        lastImpulse=new Vec3d(impulse.x(),impulse.y(),impulse.z());
        if(lastImpulse.lengthSquared()<1e-10){blocked++;publish();return false;}
        p.setVelocity(p.getVelocity().add(lastImpulse));p.fallDistance=0;
        // The local adapter mirrors the impulse once. Do not add a velocity
        // packet which would race native flight/directional movement.
        var next=new ArrayList<>(cues);long now=System.currentTimeMillis();next.removeIf(c->now-c.wall()>250);
        if(next.size()>=32)next.removeFirst();
        next.add(new Cue(++sequence,p.getUuid(),worldId,pid,generation,model,hero,now,lastImpulse));cues=List.copyOf(next);
        pushes++;if(hero==JUNKRAT)minePushes++;publish();return true;
    }
    @Override public void tick(MinecraftServer server){
        long now=System.currentTimeMillis();
        cues=cues.stream().filter(c->{var p=server.getPlayerManager().getPlayer(c.owner());
            return now-c.wall()<=250&&p!=null&&p.isAlive()&&NativeWorldIdentity.of(server,p.getWorld().getRegistryKey())==c.world()
                &&NativeEliminationRuntime.sessionMatches(c.owner(),c.world(),c.hero(),c.model(),c.hostGeneration());}).toList();
        publish();
    }
    private void publish(){var o=new JsonObject();o.addProperty("impacts",impacts);o.addProperty("pushes",pushes);o.addProperty("minePushes",minePushes);o.addProperty("duplicates",duplicates);
        o.addProperty("blocked",blocked);o.addProperty("outOfRange",outOfRange);o.addProperty("refused",refused);o.addProperty("pendingCues",cues.size());
        o.addProperty("impulseX",lastImpulse.x);o.addProperty("impulseY",lastImpulse.y);o.addProperty("impulseZ",lastImpulse.z);
        o.addProperty("boost",RocketSelfImpulse.BOOST);o.addProperty("maxImpulse",RocketSelfImpulse.MAX_IMPULSE);o.addProperty("selfDamageApplied",0);
        o.addProperty("adapter","MC radial self impulse; native authenticated impacts/mine casts only; additive native flight");status=o.toString();}
    @Override public void resetSession(){cues=List.of();seen.clear();lastImpulse=Vec3d.ZERO;publish();}
    @Override public String statusKey(){return "rocketSelfImpulse";}
    @Override public String status(){return status;}
}
