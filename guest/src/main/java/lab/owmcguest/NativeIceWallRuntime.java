package lab.owmcguest;

import java.util.*;
import net.minecraft.block.BlockState;
import net.minecraft.entity.LivingEntity;
import net.minecraft.server.MinecraftServer;
import net.minecraft.server.network.ServerPlayerEntity;
import net.minecraft.server.world.ServerWorld;
import net.minecraft.server.world.ChunkTicketType;
import net.minecraft.sound.*;
import net.minecraft.util.hit.*;
import net.minecraft.util.math.*;
import net.minecraft.world.RaycastContext;

/** MC owns one terrain plan, used by the native-authorized preview, meshes and
 * fractional collision. Original0622 node29 starts the real10-second cooldown. */
public final class NativeIceWallRuntime {
    public record Scope(UUID owner,long world,long source,long model){}
    public record Support(BlockPos at,BlockState state){}
    public record View(Scope scope,IceWallGeometry.Plan plan,List<IceWallGeometry.Cell> cells,List<IceWallGeometry.Pillar> pillars,List<Support> supports,float yaw,float rise,long wall){public long world(){return scope.world();}}
    public record Preview(Scope scope,IceWallGeometry.Plan plan,boolean valid,String reason,long token,long wall){}
    private record Planned(IceWallGeometry.Plan geometry,Map<BlockPos,BlockState> baseline,List<Support> supports){}
    private static final ChunkTicketType<Long> TICKET=ChunkTicketType.create("owmc_ice_wall",Comparator.<Long>naturalOrder(),140);
    private static final class Wall {ServerWorld world;Planned plan;int age;long ticket;final Set<ChunkPos> chunks=new HashSet<>();final Map<BlockPos,BlockState> original=new LinkedHashMap<>(),expected=new LinkedHashMap<>();}
    private static final int LIFETIME=100,RISE_TICKS=8;
    private static Scope scope;private static Wall wall;private static Planned previewPlan;
    public static volatile View view;public static volatile Preview previewView;
    private static long previews,builds,refused,blocksPlaced;private static String reason="";
    public static volatile String status="{}";
    public static PlacementCooldowns.Scope cooldown(Scope s){return new PlacementCooldowns.Scope(s.owner(),s.world(),s.source(),s.model(),1);}
    private static ServerPlayerEntity owner(MinecraftServer server,Scope s){
        var p=s==null?null:server.getPlayerManager().getPlayer(s.owner());
        return p!=null&&p.isAlive()&&s.equals(scope)&&NativeWorldIdentity.of(server,p.getWorld().getRegistryKey())==s.world()?p:null;
    }
    private static Planned plan(ServerPlayerEntity p){
        var w=p.getServerWorld();var eye=p.getEyePos();var look=p.getRotationVec(1);
        var hit=w.raycast(new RaycastContext(eye,eye.add(look.multiply(35)),RaycastContext.ShapeType.COLLIDER,RaycastContext.FluidHandling.NONE,p));
        if(!(hit instanceof BlockHitResult bh)||hit.getType()!=HitResult.Type.BLOCK)throw new IllegalArgumentException("no ground in35m");
        var point=bh.getPos().add(Vec3d.of(bh.getSide().getVector()).multiply(.01));int cx=(int)Math.floor(point.x),cz=(int)Math.floor(point.z);boolean x=Math.abs(look.z)>=Math.abs(look.x);
        var ground=new ArrayList<IceWallGeometry.Ground>();var supportMap=new HashMap<BlockPos,BlockState>();
        for(int i=0;i<IceWallGeometry.WIDTH;i++)for(int depth=0;depth<IceWallGeometry.THICKNESS;depth++){
            int k=i-IceWallGeometry.WIDTH/2,d=depth-IceWallGeometry.THICKNESS/2;
            int px=cx+(x?k:d),pz=cz+(x?d:k);var from=new Vec3d(px+.5,point.y+2,pz+.5);var to=new Vec3d(px+.5,point.y-3,pz+.5);
            if(!w.isChunkLoaded(BlockPos.ofFloored(from))||!w.isChunkLoaded(BlockPos.ofFloored(to)))throw new IllegalArgumentException("unloaded wall footprint");
            var floor=w.raycast(new RaycastContext(from,to,RaycastContext.ShapeType.COLLIDER,RaycastContext.FluidHandling.NONE,p));
            if(floor.getType()!=HitResult.Type.BLOCK||floor.getSide()!=Direction.UP)throw new IllegalArgumentException("unsupported column");
            double y=Math.rint(floor.getPos().y*16)/16;ground.add(new IceWallGeometry.Ground(px,pz,y));supportMap.put(floor.getBlockPos(),w.getBlockState(floor.getBlockPos()));
        }
        var geometry=new IceWallGeometry.Plan(x,ground);var baseline=new LinkedHashMap<BlockPos,BlockState>();var supports=new ArrayList<Support>();
        for(var cell:geometry.cells(1)){
            var at=new BlockPos(cell.x(),cell.y(),cell.z());if(at.getY()<w.getBottomY()||at.getY()>=w.getTopY()||!w.isChunkLoaded(at)||!w.getWorldBorder().contains(at))throw new IllegalArgumentException("wall world bounds");
            var old=w.getBlockState(at);boolean partialSupport=cell.lower()>0&&supportMap.containsKey(at);
            if(!old.getFluidState().isEmpty()||w.getBlockEntity(at)!=null||!old.getCollisionShape(w,at).isEmpty()&&!partialSupport)throw new IllegalArgumentException("wall footprint occupied");
            baseline.put(at,old);if(partialSupport)supports.add(new Support(at,old));
        }
        var result=new Planned(geometry,Map.copyOf(baseline),List.copyOf(supports));
        if(!lift(w,result.geometry().cells(1),false))throw new IllegalArgumentException("no safe space above wall occupants");return result;
    }
    public static void preview(MinecraftServer server,Scope next,long token,boolean active){
        if(scope!=null&&!scope.equals(next))resetSession();scope=next;
        if(!active){previewView=null;previewPlan=null;publish();return;}
        var p=owner(server,next);if(p==null)return;if(previewView==null)previews++;
        try{previewPlan=plan(p);previewView=new Preview(next,previewPlan.geometry(),PlacementCooldowns.available(cooldown(next)),"",token,System.currentTimeMillis());}
        catch(IllegalArgumentException invalid){reason=invalid.getMessage();previewPlan=null;previewView=new Preview(next,null,false,reason,token,System.currentTimeMillis());}
        publish();
    }
    public static boolean request(MinecraftServer server,Scope next,long token){
        var p=owner(server,next);var v=previewView;var selected=previewPlan;
        if(p==null||v==null||!v.valid()||v.token()!=token||selected==null||System.currentTimeMillis()-v.wall()>250){refused++;publish();return false;}
        boolean accepted=PlacementCooldowns.request(cooldown(next),token,()->commit(server,next,selected));if(accepted){previewView=null;previewPlan=null;}publish();return accepted;
    }
    private static void commit(MinecraftServer server,Scope next,Planned selected){
        var p=owner(server,next);if(p==null)return;var w=p.getServerWorld();
        for(var e:selected.baseline().entrySet())if(!w.isChunkLoaded(e.getKey())||!w.getBlockState(e.getKey()).equals(e.getValue())){refused++;reason="terrain changed before native cooldown receipt";publish();return;}
        clear();wall=new Wall();wall.world=w;wall.plan=selected;wall.ticket=++builds;reason="";
        for(var cell:selected.geometry().cells(1)){var cp=new ChunkPos(new BlockPos(cell.x(),cell.y(),cell.z()));if(wall.chunks.add(cp))w.getChunkManager().addTicket(TICKET,cp,0,wall.ticket);}
        w.playSound(null,BlockPos.ofFloored(p.getPos()),SoundEvents.BLOCK_GLASS_PLACE,SoundCategory.PLAYERS,1.2f,.6f);publish();
    }
    private static boolean lift(ServerWorld w,List<IceWallGeometry.Cell> cells,boolean apply){
        var moves=new LinkedHashMap<LivingEntity,Double>();
        for(var cell:cells){var box=new Box(cell.x(),cell.y()+cell.lower(),cell.z(),cell.x()+1,cell.y()+cell.top()/16.,cell.z()+1);
            for(var e:w.getEntitiesByClass(LivingEntity.class,box,LivingEntity::isAlive)){
                double up=box.maxY-e.getBoundingBox().minY+.01;if(up>0)moves.merge(e,up,Math::max);
            }}
        for(var e:moves.entrySet())if(e.getKey().hasVehicle()||e.getKey().getY()+e.getValue()+e.getKey().getHeight()>=w.getTopY()||!w.isSpaceEmpty(e.getKey(),e.getKey().getBoundingBox().offset(0,e.getValue(),0)))return false;
        if(apply)for(var e:moves.entrySet()){var actor=e.getKey();actor.requestTeleport(actor.getX(),actor.getY()+e.getValue(),actor.getZ());actor.fallDistance=0;}
        return true;
    }
    public static void tick(MinecraftServer server){
        if(previewView!=null&&System.currentTimeMillis()-previewView.wall()>250){previewView=null;previewPlan=null;}
        if(wall==null)return;if(owner(server,scope)==null||++wall.age>LIFETIME){clear();return;}
        var w=wall.world;for(var e:wall.expected.entrySet())if(!w.isChunkLoaded(e.getKey())||!w.getBlockState(e.getKey()).equals(e.getValue())){reason="wall collision changed/unloaded";clear();return;}
        double rise=Math.min(1,wall.age/(double)RISE_TICKS);var cells=wall.plan.geometry().cells(rise);
        if(wall.age<=RISE_TICKS){
            if(!lift(w,cells,true)){refused++;reason="unsafe occupant lift";clear();return;}
            for(var cell:cells){var at=new BlockPos(cell.x(),cell.y(),cell.z());var expected=TemporaryIceWallBlock.BLOCK.getDefaultState().with(TemporaryIceWallBlock.HEIGHT,cell.top());
                wall.original.putIfAbsent(at,w.getBlockState(at));if(!w.getBlockState(at).equals(expected)){w.setBlockState(at,expected);blocksPlaced++;}wall.expected.put(at,expected);}
        }
        view=new View(scope,wall.plan.geometry(),cells,wall.plan.geometry().pillars(rise),wall.plan.supports(),wall.plan.geometry().yaw(),(float)rise,System.currentTimeMillis());publish();
    }
    public static void cancel(Scope old){if(old!=null&&old.equals(scope)){PlacementCooldowns.cancel(cooldown(old));resetSession();}}
    public static void clear(){
        if(wall!=null)for(var e:wall.original.entrySet()){var w=wall.world;var expected=wall.expected.get(e.getKey());if(w.isChunkLoaded(e.getKey())&&w.getBlockState(e.getKey()).equals(expected))w.setBlockState(e.getKey(),e.getValue());}
        if(wall!=null)for(var cp:wall.chunks)wall.world.getChunkManager().removeTicket(TICKET,cp,0,wall.ticket);
        wall=null;view=null;publish();
    }
    public static void resetSession(){if(scope!=null)PlacementCooldowns.cancel(cooldown(scope));clear();scope=null;previewView=null;previewPlan=null;publish();}
    private static void publish(){var o=new com.google.gson.JsonObject();o.addProperty("wall",wall!=null);o.addProperty("previewing",previewView!=null);o.addProperty("previewValid",previewView!=null&&previewView.valid());o.addProperty("previews",previews);o.addProperty("builds",builds);o.addProperty("refused",refused);o.addProperty("blocksPlaced",blocksPlaced);o.addProperty("blocksActive",wall==null?0:wall.expected.size());o.addProperty("lastRejection",reason);o.addProperty("cooldownSeconds",10);o.addProperty("terrainQuantization",1/16.);if(wall!=null)o.addProperty("age",wall.age);status=o.toString();}
}
