package lab.owmcguest;

import com.google.gson.JsonObject;
import java.util.*;
import net.minecraft.block.Blocks;
import net.minecraft.entity.Entity;
import net.minecraft.entity.player.PlayerEntity;
import net.minecraft.server.MinecraftServer;
import net.minecraft.server.network.ServerPlayerEntity;
import net.minecraft.server.world.ServerWorld;
import net.minecraft.util.hit.HitResult;
import net.minecraft.util.math.*;
import net.minecraft.world.RaycastContext;

/** Offline24919, HERO-BRIEFS-NEW8-20261025 §2. Only ModifyHealth9/10 Begin
 * opens hammer damage, Pet58 Begin/End opens/closes the MC barrier. First samples
 * and End-only hammer samples never create attacks. Shift110 is an ATTEMPT;
 * movement requires a subsequent fresh TrackMovement6 Begin (not observed yet).
 * FireStrike e2:3 and Earthshatter be:1 have declarations only: diagnostic-only,
 * no projectiles/shockwave/damage. Passive has no evidence and is not invented.
 * MC 适配值: hammer75, reach4.5, cone110deg, knockback.35; cardinal 5x3 barrier
 * three blocks ahead, no native durability/regen/team filtering. Only AIR may be
 * replaced, only still-owned BARRIER removed. Lease200ms, hammer cap650ms.
 * Barrier entity GUID is unknown. Asset-chain01ea completed but has NO LOD0 mesh;
 * future command: tools/build_mesh_pack.py reinhardt-fire 04000000000001ea.
 * No native attack/collision/durability fidelity or real play acceptance claimed. */
public final class ReinhardtServer implements HeroServerModule {
    private static final com.google.gson.Gson EVIDENCE_JSON=new com.google.gson.Gson();
    public static final ReinhardtServer INSTANCE=new ReinhardtServer();
    public static final long HERO=0x02e0000000000007L;
    public record Scope(UUID owner,long world,long source,long model){}
    static final double HAMMER=75,REACH=4.5,CONE=Math.cos(Math.toRadians(55)),PUSH=.35;
    static final long LEASE_MS=200,SWING_MS=650;
    private Map<String,TanksNodeEvidence.Node> candidateEvidence=Map.of();
    /** Read-only candidate counters. No observed candidate authorizes an effect. */
    public void observeCandidates(Scope expected,long wall,Map<String,TanksNodeEvidence.Node> nodes){
        long age=System.currentTimeMillis()-wall;
        if(expected!=null&&expected.equals(scope)&&age>=-50&&age<=150){candidateEvidence=Map.copyOf(nodes);publish();}
    }
    private Scope scope;
    private ServerWorld shieldWorld;
    private Vec3d shieldNormal;
    private final Set<BlockPos> shield=new HashSet<>();
    private final Set<Integer> hitTargets=new HashSet<>();
    private final long[] seen=new long[6];
    private long heartbeat,swingWall;
    private int swingSlot=-1;
    private boolean barrier,charging;
    private long casts,hammerCasts,hammerHits,barrierCasts,barrierPlacements,barrierRemovals;
    private long chargeAttempts,chargeStarts,fireCandidates,shatterCandidates,rejected,windowEnds;
    private double damageApplied;
    private volatile boolean resetRequested;
    private volatile String json="{\"active\":false}";

    private ServerPlayerEntity player(MinecraftServer server,Scope s){
        var p=s==null?null:server.getPlayerManager().getPlayer(s.owner());
        return p!=null&&p.isAlive()&&!p.hasVehicle()&&s.source()!=0&&s.model()!=0
            &&NativeWorldIdentity.of(server,p.getWorld().getRegistryKey())==s.world()?p:null;
    }
    /** One immutable client snapshot, executed on the server thread. Event tokens
     * are native logger ticks, never MC/input ticks; slots9/10 are independent. */
    public void sample(MinecraftServer server,Scope next,long wall,long[] events,
                       boolean left,boolean right,boolean raised,boolean charge){
        long now=System.currentTimeMillis();
        if(wall>now+50||now-wall>150||player(server,next)==null){rejected++;return;}
        if(resetRequested){clearOwned();resetRequested=false;}
        if(!next.equals(scope)){clearOwned();scope=next;Arrays.fill(seen,0);}
        heartbeat=now;
        for(int i=0;i<events.length;i++)if(events[i]>seen[i]){
            seen[i]=events[i];
            switch(i){
                case 0,1->{if((i==0&&left)||(i==1&&right)){
                    swingSlot=i;swingWall=now;hitTargets.clear();casts++;hammerCasts++;}}
                case 2->chargeAttempts++;
                case 3->fireCandidates++;
                case 4->shatterCandidates++;
                case 5->{if(charge)chargeStarts++;}
                default->throw new IllegalArgumentException("Reinhardt event slot");
            }
        }
        if(swingSlot==0&&!left||swingSlot==1&&!right){swingSlot=-1;windowEnds++;}
        if(raised&&!barrier){barrierCasts++;casts++;}
        barrier=raised;charging=charge;
        if(!barrier)removeShield();
        publish();
    }
    public void invalidate(MinecraftServer server,Scope expected){
        if(expected!=null&&expected.equals(scope)){clearOwned();publish();}
    }
    @Override public void tick(MinecraftServer server){
        if(resetRequested){clearOwned();resetRequested=false;}
        var p=player(server,scope);
        if(p==null||System.currentTimeMillis()-heartbeat>LEASE_MS){clearOwned();publish();return;}
        if(barrier)moveShield(p);else removeShield();
        if(swingSlot>=0){
            if(System.currentTimeMillis()-swingWall>SWING_MS)swingSlot=-1;
            else hammer(p);
        }
        publish();
    }
    private void hammer(ServerPlayerEntity p){
        var w=p.getServerWorld();var eye=p.getEyePos();var look=p.getRotationVec(1).normalize();
        for(var e:NativeDamageTargets.in(w,p,p.getBoundingBox().expand(REACH))){
            var victim=NativeDamageTargets.owner(e);
            if(hitTargets.contains(victim.getId())||p.isTeammate(victim)||e instanceof PlayerEntity)continue;
            var box=e.getBoundingBox();
            var at=new Vec3d(MathHelper.clamp(eye.x,box.minX,box.maxX),MathHelper.clamp(eye.y,box.minY,box.maxY),MathHelper.clamp(eye.z,box.minZ,box.maxZ));
            var offset=at.subtract(eye);
            if(offset.lengthSquared()>REACH*REACH||offset.lengthSquared()>1e-6&&look.dotProduct(offset.normalize())<CONE)continue;
            var wall=w.raycast(new RaycastContext(eye,at,RaycastContext.ShapeType.COLLIDER,RaycastContext.FluidHandling.NONE,p));
            if(wall.getType()==HitResult.Type.BLOCK&&wall.getPos().squaredDistanceTo(eye)<at.squaredDistanceTo(eye)-.001)continue;
            hitTargets.add(victim.getId());
            var r=NativeDamageTargets.meleeDamage(w,e,p,HAMMER*NativeShotSimulation.HP_SCALE);
            if(r.applied()){hammerHits++;damageApplied+=r.healthLost();
                var push=victim.getPos().subtract(p.getPos()).multiply(1,0,1).normalize().multiply(PUSH);
                victim.addVelocity(push.x,.1,push.z);victim.velocityModified=true;}
        }
    }
    private void moveShield(ServerPlayerEntity p){
        var w=p.getServerWorld();
        if(shieldWorld!=w){removeShield();shieldWorld=w;}
        var forward=Direction.fromRotation(p.getYaw());var side=forward.rotateYClockwise();
        shieldNormal=Vec3d.of(forward.getVector());
        var center=p.getBlockPos().offset(forward,3);var wanted=new HashSet<BlockPos>();
        for(int x=-2;x<=2;x++)for(int y=0;y<3;y++){
            var at=center.offset(side,x).up(y);
            if(w.isChunkLoaded(at)&&w.isInBuildLimit(at)&&w.getWorldBorder().contains(at))wanted.add(at.toImmutable());
        }
        for(var it=shield.iterator();it.hasNext();){var at=it.next();
            if(!wanted.contains(at)){erase(at);it.remove();}}
        for(var at:wanted){
            if(shield.contains(at))continue;
            if(!w.getBlockState(at).isAir()||!w.getOtherEntities(null,new Box(at),Entity::isAlive).isEmpty())continue;
            if(w.setBlockState(at,Blocks.BARRIER.getDefaultState(),3)){shield.add(at);barrierPlacements++;}
        }
    }
    private void erase(BlockPos at){
        // Cleanup may load the old chunk: no owned barrier is abandoned on travel.
        if(shieldWorld!=null&&shieldWorld.getBlockState(at).isOf(Blocks.BARRIER)){
            shieldWorld.setBlockState(at,Blocks.AIR.getDefaultState(),3);barrierRemovals++;}
    }
    private void removeShield(){for(var at:shield)erase(at);shield.clear();shieldWorld=null;shieldNormal=null;}
    private void clearOwned(){candidateEvidence=Map.of();removeShield();scope=null;swingSlot=-1;hitTargets.clear();barrier=charging=false;heartbeat=0;}
    private void publish(){
        var o=new JsonObject();o.add("nativeCandidates",EVIDENCE_JSON.toJsonTree(candidateEvidence));
        o.addProperty("candidateEffectsEnabled",false);
        o.addProperty("active",scope!=null);o.addProperty("casts",casts);
        o.addProperty("hammerCasts",hammerCasts);o.addProperty("hammerHits",hammerHits);o.addProperty("hits",hammerHits);
        o.addProperty("damageApplied",damageApplied);o.addProperty("hammerWindow",swingSlot>=0);o.addProperty("windowEnds",windowEnds);
        o.addProperty("barrierActive",barrier);o.addProperty("barrierCasts",barrierCasts);o.addProperty("barrierBlocks",shield.size());
        o.addProperty("barrierPlacements",barrierPlacements);o.addProperty("barrierRemovals",barrierRemovals);
        o.addProperty("chargeAttempts",chargeAttempts);o.addProperty("chargeStarts",chargeStarts);o.addProperty("charging",charging);
        o.addProperty("fireCandidates",fireCandidates);o.addProperty("shatterCandidates",shatterCandidates);o.addProperty("rejected",rejected);
        o.addProperty("chargeDamageEnabled",false);o.addProperty("fireEnabled",false);o.addProperty("shatterEnabled",false);
        o.addProperty("pending","Shift movement6/slam11/damage not calibrated; E/Q declarations only; passive unknown; shield entity GUID unknown");
        o.addProperty("mcAdaptation","hammer cone/damage/knockback; invisible cardinal barrier blocks/all projectiles, no durability; charge travel only on fresh movement6 B");
        
        // integrator/models: only real state/geometry, never input-derived effects.
if(scope!=null&&barrier&&shieldWorld!=null&&shieldNormal!=null){
            var placed=shield.stream().filter(at->shieldWorld.isChunkLoaded(at)&&shieldWorld.getBlockState(at).isOf(Blocks.BARRIER)).toList();
            if(!placed.isEmpty()){
                int minX=placed.stream().mapToInt(BlockPos::getX).min().orElseThrow(),maxX=placed.stream().mapToInt(BlockPos::getX).max().orElseThrow();
                int minY=placed.stream().mapToInt(BlockPos::getY).min().orElseThrow(),maxY=placed.stream().mapToInt(BlockPos::getY).max().orElseThrow();
                int minZ=placed.stream().mapToInt(BlockPos::getZ).min().orElseThrow(),maxZ=placed.stream().mapToInt(BlockPos::getZ).max().orElseThrow();
                var center=new Vec3d((minX+maxX+1)*.5,(minY+maxY+1)*.5,(minZ+maxZ+1)*.5);
                double width=shieldNormal.x==0?maxX-minX+1:maxZ-minZ+1;
                var f=OriginalEffectFrames.frame(scope.owner(),scope.world(),scope.source(),scope.model(),heartbeat);
                var e=OriginalEffectFrames.body(f,"reinhardt-barrier",center,new Vec3d(width/6.78943348,(maxY-minY+1)/4.252882,1),.25f,false);
                e.add("direction",OriginalEffectFrames.vec(shieldNormal));e.addProperty("axis","z");o.add("models",f);
            }
        }
        json=o.toString();
    }
    /** May be called by the client session guard: defer all world mutations. */
    @Override public void resetSession(){resetRequested=true;}
    /** Existing registry calls clear on SERVER_STOPPING, before world saving. */
    @Override public void clear(){clearOwned();resetRequested=false;publish();}
    @Override public String statusKey(){return "reinhardt";}
    @Override public String status(){return json;}
}
