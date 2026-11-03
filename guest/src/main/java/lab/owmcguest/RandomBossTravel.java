package lab.owmcguest;
import com.google.gson.*;
import java.util.*;
import java.util.function.BooleanSupplier;
import net.fabricmc.loader.api.FabricLoader;
import net.minecraft.entity.LivingEntity;
import net.minecraft.registry.*;
import net.minecraft.registry.entry.RegistryEntryList;
import net.minecraft.server.MinecraftServer;
import net.minecraft.server.network.ServerPlayerEntity;
import net.minecraft.server.world.*;
import net.minecraft.structure.*;
import net.minecraft.util.Identifier;
import net.minecraft.util.math.*;
import net.minecraft.world.World;
import net.minecraft.world.chunk.ChunkStatus;

/** Original loaded bosses across dimensions, or a real generated dungeon. Never spawns a boss. */
public final class RandomBossTravel {
    private static final Set<String> ROOTS=Set.of("minecraft:ender_dragon","minecraft:wither","twilightforest:naga","twilightforest:lich","twilightforest:minoshroom","twilightforest:hydra","twilightforest:knight_phantom","twilightforest:ur_ghast","twilightforest:alpha_yeti","twilightforest:snow_queen","aether:slider","aether:valkyrie_queen","aether:sun_spirit");
    private static final String[] TF={"naga","lich","minoshroom","hydra","knight_phantom","ur_ghast","alpha_yeti","snow_queen"};
    private static final String[] DUNGEONS={"bronze_dungeon","silver_dungeon","gold_dungeon"},PIECES={"BronzeBossRoom","SilverBossRoom","GoldBossRoom"};
    private static final ChunkTicketType<Long> TICKET=ChunkTicketType.create("owmc_random_boss",Comparator.<Long>naturalOrder(),2600);
    private static long requestId,completed,tfBase,aoaBase,busyRequests;private static volatile Job job;private static String phase="idle",error="",boss="";private static JsonObject destination,evidence;
    public static volatile String status="{}";
    public static boolean busy(){return job!=null;}
    private static final class Job {
        UUID owner;ServerWorld origin,world;BooleanSupplier admitted;int deadline,index,chunkIndex,entityStart;BlockPos query,located;net.minecraft.world.gen.structure.Structure structure;BlockBox box;List<ChunkPos> chunks=List.of();Set<ChunkPos> tickets=new LinkedHashSet<>();boolean delegate,strictBoss,aoa;
    }
    public static void request(MinecraftServer server,UUID owner,boolean aetherOnly,BooleanSupplier admitted){
        request(server,owner,aetherOnly,admitted,admitted);
    }
    public static void request(MinecraftServer server,UUID owner,boolean aetherOnly,BooleanSupplier admitted,BooleanSupplier current){
        request(server,owner,aetherOnly,admitted,current,-1);
    }
    public static void requestAether(MinecraftServer server,UUID owner,int index,BooleanSupplier admitted){
        if(index<0||index>2)throw new IllegalArgumentException("Unknown original Aether dungeon");
        request(server,owner,true,admitted,admitted,index);
    }
    private static void request(MinecraftServer server,UUID owner,boolean aetherOnly,BooleanSupplier admitted,BooleanSupplier current,int selectedDungeon){
        if(job!=null){busyRequests++;report();return;}requestId++;error="";destination=null;evidence=new JsonObject();
        try{
            var p=server.getPlayerManager().getPlayer(owner);
            if(!server.isSingleplayer()||!Boolean.getBoolean("owmc.twilightTrial")||!System.getProperty("owmc.worldName","").startsWith("Overwatch Twilight ")||p==null||!p.isAlive()||!SurvivalRuntime.permitted(p)||!admitted.getAsBoolean())throw new IllegalStateException("Random boss travel needs the current offline creative admission");
            var j=new Job();j.owner=owner;j.origin=p.getServerWorld();j.admitted=admitted;j.deadline=server.getTicks()+2400;job=j;
            if(!aetherOnly){
                var loaded=new ArrayList<LivingEntity>();
                for(var w:server.getWorlds())for(var e:w.iterateEntities())if(e instanceof LivingEntity living&&living.isAlive()&&isBoss(living)&&!e.getCommandTags().contains("owmc-multipart-probe")&&(w!=p.getServerWorld()||e.squaredDistanceTo(p)>192*192))loaded.add(living);
                Collections.shuffle(loaded);evidence.addProperty("loadedBossCandidates",loaded.size());
                for(var e:loaded){var w=(ServerWorld)e.getWorld();var at=safeNear(w,p,e.getBlockPos(),null);if(at!=null){boss=Registries.ENTITY_TYPE.getId(e.getType()).toString();evidence.addProperty("entityId",e.getId());evidence.addProperty("entityUuid",e.getUuidAsString());evidence.addProperty("resolution","existing-live-boss");arrive(p,w,at,e.getPos());return;}}
            }
            if(!aetherOnly&&Registries.ENTITY_TYPE.containsId(Identifier.of("aoa3:smash"))&&p.getRandom().nextInt(11)<8){
                j.aoa=true;boss="aoa3:"+AoABossTravel.IDS[p.getRandom().nextInt(8)];
                var old=JsonParser.parseString(AoABossTravel.status).getAsJsonObject();aoaBase=old.has("requestId")?old.get("requestId").getAsLong():0;
                AoABossTravel.request(server,owner,boss.substring(5),admitted,current);phase="aoa-original-arena";report();return;
            }
            // NeoForge's original bronze dungeon Boss was actually observed.
            // Without Twilight, global travel may locate that original room,
            // but must still observe the living Boss before claiming success.
            boolean aether=FabricLoader.getInstance().isModLoaded("aether")&&(aetherOnly||!FabricLoader.getInstance().isModLoaded("twilightforest"));
            j.strictBoss=true;
            if(!aether){
                if(!FabricLoader.getInstance().isModLoaded("twilightforest"))throw new IllegalStateException("No loaded boss or supported dungeon provider");
                boss="twilightforest:"+TF[p.getRandom().nextInt(TF.length)];j.delegate=true;tfBase=JsonParser.parseString(TwilightBossTravel.status).getAsJsonObject().get("requestId").getAsLong();
                var query=p.getBlockPos().add((p.getRandom().nextInt(17)-8)*512,0,(p.getRandom().nextInt(17)-8)*512);
                TwilightBossTravel.requestAt(server,owner,boss.substring(15),admitted,query);phase="twilight-dungeon";report();return;
            }
            j.world=server.getWorld(RegistryKey.of(RegistryKeys.WORLD,Identifier.of("aether","the_aether")));
            if(j.world==null)throw new IllegalStateException("Actual Aether dimension unavailable");
            j.index=selectedDungeon>=0?selectedDungeon:p.getRandom().nextInt(3);boss="aether:"+DUNGEONS[j.index];
            j.structure=j.world.getRegistryManager().get(RegistryKeys.STRUCTURE).getOrEmpty(Identifier.of("aether",DUNGEONS[j.index])).orElseThrow();
            j.query=p.getBlockPos().add((p.getRandom().nextInt(9)-4)*512,0,(p.getRandom().nextInt(9)-4)*512);phase="locating";
        }catch(Exception e){fail(e);}report();
    }
    public static void tick(MinecraftServer server){
        if(job==null)return;
        try{
            var j=job;var p=server.getPlayerManager().getPlayer(j.owner);
            if(j.aoa){
                var d=JsonParser.parseString(AoABossTravel.status).getAsJsonObject();
                if(d.has("requestId")&&d.get("requestId").getAsLong()>aoaBase&&!d.get("busy").getAsBoolean()){
                    if(!d.get("error").getAsString().isEmpty())throw new IllegalStateException(d.get("error").getAsString());
                    destination=d.getAsJsonObject("destination").deepCopy();evidence.add("aoa",d);completed++;job=null;phase="complete";
                }else if(server.getTicks()>j.deadline)throw new IllegalStateException("Original AoA arena deadline reached");
                report();return;
            }
            if(phase.equals("arrived-awaiting-boss")){
                if(p==null||!p.isAlive()||p.getServerWorld()!=j.world)throw new IllegalStateException("Destination owner changed while original boss loads");
                var actual=j.world.getEntitiesByClass(LivingEntity.class,Box.from(j.box).expand(24),e->e.isAlive()&&isBoss(e));
                if(!actual.isEmpty()){var target=actual.getFirst();evidence.addProperty("entityUuid",target.getUuidAsString());evidence.addProperty("entityId",target.getId());evidence.addProperty("resolution","original-room-player-ticket-boss");completed++;release();job=null;phase="complete";}
                else if(server.getTicks()-j.entityStart>200){
                    evidence.addProperty("bossPresent",false);evidence.addProperty("resolution","original-dungeon-entry-only");
                    if(j.strictBoss)throw new IllegalStateException("Original dungeon loaded but no living Boss was observed; random Boss travel is not complete");
                    evidence.addProperty("notice","Original boss not observed; dungeon entry is not a completed boss encounter");completed++;release();job=null;phase="complete";
                }
                report();return;
            }
            if(j.delegate){
                var d=JsonParser.parseString(TwilightBossTravel.status).getAsJsonObject();
                if(d.get("requestId").getAsLong()>tfBase&&!d.get("busy").getAsBoolean()){
                    if(!d.get("error").getAsString().isEmpty())throw new IllegalStateException(d.get("error").getAsString());
                    destination=d.getAsJsonObject("destination").deepCopy();evidence.add("twilight",d);completed++;job=null;phase="complete";
                }else if(p==null||!p.isAlive()||!SurvivalRuntime.permitted(p)||p.getServerWorld()!=j.origin||!j.admitted.getAsBoolean()||server.getTicks()>j.deadline)throw new IllegalStateException("Delegated search admission expired");
                report();return;
            }
            if(p==null||!p.isAlive()||!SurvivalRuntime.permitted(p)||p.getServerWorld()!=j.origin||!j.admitted.getAsBoolean()||server.getTicks()>j.deadline)throw new IllegalStateException("Boss search cancelled or bounded deadline reached");
            switch(phase){
                case "locating"->{
                    var registry=j.world.getRegistryManager().get(RegistryKeys.STRUCTURE);
                    var found=j.world.getChunkManager().getChunkGenerator().locateStructure(j.world,RegistryEntryList.of(registry.getEntry(j.structure)),j.query,64,false);
                    if(found==null)throw new IllegalStateException("No original Aether dungeon found within bounded search");
                    j.located=found.getFirst();j.chunks=List.of(new ChunkPos(j.located));j.chunkIndex=0;phase="loading-start";
                }
                case "loading-start"->{
                    if(!load(j))break;var cp=j.chunks.getFirst();var chunk=j.world.getChunkManager().getWorldChunk(cp.x,cp.z);var start=chunk.getStructureStart(j.structure);
                    if(start==null||!start.hasChildren())start=j.world.getStructureAccessor().getStructureStarts(cp,s->s==j.structure).stream().filter(StructureStart::hasChildren).findFirst().orElseThrow();
                    var piece=start.getChildren().stream().filter(s->s.getClass().getSimpleName().equals(PIECES[j.index])).findFirst().orElseThrow(()->new IllegalStateException("Original Aether boss room piece missing"));
                    j.box=piece.getBoundingBox();evidence.addProperty("piece",piece.getClass().getName());
                    var list=new ArrayList<ChunkPos>();for(int x=(j.box.getMinX()-4)>>4;x<=(j.box.getMaxX()+4)>>4;x++)for(int z=(j.box.getMinZ()-4)>>4;z<=(j.box.getMaxZ()+4)>>4;z++)list.add(new ChunkPos(x,z));
                    if(list.size()>100)throw new IllegalStateException("Aether room exceeds chunk budget");j.chunks=list;j.chunkIndex=0;phase="loading-room";
                }
                case "loading-room"->{if(load(j)){j.entityStart=server.getTicks();phase="waiting-original-entities";}}
                case "waiting-original-entities"->{
                    if(j.chunks.stream().anyMatch(cp->!j.world.isChunkLoaded(cp.toLong()))){if(server.getTicks()-j.entityStart>200)throw new IllegalStateException("Original dungeon entities not loaded");break;}
                    var entities=j.world.getEntitiesByClass(LivingEntity.class,Box.from(j.box).expand(4),e->e.isAlive()&&isBoss(e));
                    if(entities.isEmpty()){
                        if(server.getTicks()-j.entityStart<20)break;
                        var at=safeNear(j.world,p,j.box.getCenter(),j.box);
                        if(at==null)throw new IllegalStateException("Original room has no safe connected floor");
                        var position=Vec3d.ofBottomCenter(at);j.world.getChunkManager().addTicket(ChunkTicketType.POST_TELEPORT,new ChunkPos(at),1,p.getId());
                        p.teleport(j.world,position.x,position.y,position.z,0,0);p.setVelocity(Vec3d.ZERO);p.fallDistance=0;
                        destination=new JsonObject();destination.addProperty("dimension",j.world.getRegistryKey().getValue().toString());destination.addProperty("x",position.x);destination.addProperty("y",position.y);destination.addProperty("z",position.z);
                        evidence.addProperty("resolution","original-room-awaiting-player-entity-tickets");phase="arrived-awaiting-boss";j.entityStart=server.getTicks();break;
                    }
                    var target=entities.getFirst();var at=safeNear(j.world,p,target.getBlockPos(),j.box);
                    if(at==null)throw new IllegalStateException("No actual safe floor near the original boss; terrain preserved");
                    evidence.addProperty("entityUuid",target.getUuidAsString());evidence.addProperty("entityId",target.getId());evidence.addProperty("resolution","generated-room-original-boss");arrive(p,j.world,at,target.getPos());
                }
                default->throw new IllegalStateException("Unknown random travel phase");
            }
        }catch(Exception e){fail(e);}report();
    }
    private static boolean load(Job j){
        for(int i=0;i<2&&j.chunkIndex<j.chunks.size();i++){var cp=j.chunks.get(j.chunkIndex++);if(j.tickets.add(cp))j.world.getChunkManager().addTicket(TICKET,cp,0,requestId);}
        return j.chunkIndex==j.chunks.size()&&j.chunks.stream().allMatch(cp->j.world.getChunkManager().getWorldChunk(cp.x,cp.z)!=null);
    }
    private static BlockPos safeNear(ServerWorld w,ServerPlayerEntity p,BlockPos target,BlockBox box){
        for(int radius:new int[]{6,9,12,16})for(int direction=0;direction<16;direction++){
            double angle=direction*Math.PI/8;int x=target.getX()+(int)Math.round(Math.cos(angle)*radius),z=target.getZ()+(int)Math.round(Math.sin(angle)*radius);
            int top=box==null?Math.min(w.getTopY()-3,target.getY()+4):Math.min(w.getTopY()-3,box.getMaxY()-2),bottom=box==null?Math.max(w.getBottomY()+1,target.getY()-64):Math.max(w.getBottomY()+1,box.getMinY());
            for(int y=top;y>=bottom;y--){var at=new BlockPos(x,y,z);if(box!=null&&!box.contains(at))continue;if(!w.isChunkLoaded(at)||!w.getWorldBorder().contains(at)||!w.getBlockState(at).isAir()||!w.getBlockState(at.up()).isAir()||!w.getFluidState(at.down()).isEmpty())continue;
                var floor=w.getBlockState(at.down());if(!floor.isSideSolidFullSquare(w,at.down(),Direction.UP)||floor.isOf(net.minecraft.block.Blocks.MAGMA_BLOCK)||floor.isOf(net.minecraft.block.Blocks.CAMPFIRE)||floor.isOf(net.minecraft.block.Blocks.CACTUS))continue;
                if(w.isSpaceEmpty(p,p.getBoundingBox().offset(Vec3d.ofBottomCenter(at).subtract(p.getPos()))))return at;
            }
        }return null;
    }
    private static void arrive(ServerPlayerEntity p,ServerWorld w,BlockPos at,Vec3d center){
        var position=Vec3d.ofBottomCenter(at);float yaw=(float)Math.toDegrees(Math.atan2(-(center.x-position.x),center.z-position.z));
        w.getChunkManager().addTicket(ChunkTicketType.POST_TELEPORT,new ChunkPos(at),1,p.getId());p.teleport(w,position.x,position.y,position.z,yaw,0);p.setVelocity(Vec3d.ZERO);p.fallDistance=0;
        destination=new JsonObject();destination.addProperty("dimension",w.getRegistryKey().getValue().toString());destination.addProperty("x",position.x);destination.addProperty("y",position.y);destination.addProperty("z",position.z);destination.addProperty("yaw",yaw);completed++;release();job=null;phase="complete";report();
    }
    static boolean isBoss(LivingEntity entity){
        if(ROOTS.contains(Registries.ENTITY_TYPE.getId(entity.getType()).toString())||entity.getType().isIn(net.minecraft.registry.tag.TagKey.of(RegistryKeys.ENTITY_TYPE,Identifier.of("c","bosses"))))return true;
        for(Class<?> type=entity.getClass();type!=null;type=type.getSuperclass())if(type.getName().startsWith("net.tslat.aoa3.content.entity.boss."))return true;
        return false;
    }
    private static void release(){if(job!=null&&job.world!=null){int n=job.tickets.size();for(var cp:job.tickets)job.world.getChunkManager().removeTicket(TICKET,cp,0,requestId);job.tickets.clear();if(evidence!=null)evidence.addProperty("releasedTickets",n);}}
    private static void fail(Exception e){release();job=null;phase="failed";error=e.getClass().getSimpleName()+": "+e.getMessage();}
    public static void close(){release();job=null;phase="idle";report();}
    private static void report(){var o=new JsonObject();o.addProperty("requestId",requestId);o.addProperty("completed",completed);o.addProperty("busy",job!=null);o.addProperty("busyRequests",busyRequests);o.addProperty("phase",phase);o.addProperty("boss",boss);o.addProperty("error",error);o.addProperty("noReplacementBosses",true);if(destination!=null)o.add("destination",destination);if(evidence!=null)o.add("evidence",evidence);status=o.toString();}
}
