package lab.owmcguest;

import com.google.gson.*;
import java.util.*;
import java.util.function.*;
import java.lang.reflect.Proxy;
import net.minecraft.entity.*;
import net.minecraft.item.*;
import net.minecraft.registry.*;
import net.minecraft.server.MinecraftServer;
import net.minecraft.server.world.*;
import net.minecraft.server.network.ServerPlayerEntity;
import net.minecraft.util.Identifier;
import net.minecraft.util.math.*;
import net.minecraft.world.*;

/** Creative entry to the installed mod's actual registered arena and summoning lifecycle. */
public final class AoABossTravel {
    public static final String[] IDS={"smash","nethengeic_wither","king_bambambam","tyrosaur","elite_smash","elite_nethengeic_wither","elite_king_bambambam","elite_tyrosaur"};
    public static final String[] NAMES={"粉碎","纳德吉克凋灵","爆裂之王","地域领主","精英粉碎","精英纳德吉克凋灵","精英爆裂之王","精英地域领主"};
    private static final String API="net.tslat.aoa3.content.world.nowhere.NowhereBossArena";
    private static final String TOKEN="net.tslat.aoa3.content.item.misc.summoning.BossTokenItem";
    private static final ChunkTicketType<Long> TICKET=ChunkTicketType.create("owmc_aoa_boss",Comparator.<Long>naturalOrder(),1600);
    private static long requestId,completed,busyRequests;private static volatile Job job;private static String error="",phase="idle",boss="";private static JsonObject evidence=new JsonObject(),destination;
    public static volatile String status="{}";
    private static final class Job {
        long id;UUID owner;ServerWorld world,origin;BooleanSupplier initial,current;int deadline,entryTick,arenaIndex,chunkIndex;Object arena;List<Object> arenas;EntityType<?> type;ItemStack stack;Object token;Box bounds;
        List<ChunkPos> chunks=List.of();Set<ChunkPos> tickets=new LinkedHashSet<>();Entity spawned;boolean committed;
    }
    public static boolean busy(){return job!=null;}
    public static void request(MinecraftServer server,UUID owner,String selected,BooleanSupplier admitted,BooleanSupplier current){
        if(job!=null){busyRequests++;report();return;}requestId++;error="";boss=selected;destination=null;evidence=new JsonObject();
        try{
            var p=server.getPlayerManager().getPlayer(owner);
            if(!server.isSingleplayer()||!Boolean.getBoolean("owmc.twilightTrial")||!System.getProperty("owmc.worldName","").startsWith("Overwatch Twilight ")||p==null||!p.isAlive()||!SurvivalRuntime.permitted(p)||!admitted.getAsBoolean())throw new IllegalStateException("Current offline creative admission required");
            if(!Arrays.asList(IDS).contains(selected))throw new IllegalStateException("Not a registered supported AoA Boss");
            var j=new Job();j.id=requestId;j.owner=owner;j.origin=p.getServerWorld();j.initial=admitted;j.current=current;j.deadline=server.getTicks()+1400;
            j.world=server.getWorld(RegistryKey.of(RegistryKeys.WORLD,Identifier.of("aoa3:nowhere")));if(j.world==null)throw new IllegalStateException("Original Nowhere dimension missing");
            j.type=Registries.ENTITY_TYPE.getOrEmpty(Identifier.of("aoa3",selected)).orElseThrow();
            // Obtain original arena instances from the actual dynamic registry.
            var key=Class.forName("net.tslat.aoa3.common.registration.AoARegistries").getField("NOWHERE_BOSS_ARENAS_REGISTRY_KEY").get(null);
            @SuppressWarnings("unchecked") var registry=server.getRegistryManager().get((RegistryKey<Registry<Object>>)key);
            j.arenas=new ArrayList<>();registry.forEach(j.arenas::add);Collections.shuffle(j.arenas);
            if(j.arenas.isEmpty())throw new IllegalStateException("No original arena definitions registered");
            String normal=selected.replace("elite_","");
            for(var item:Registries.ITEM)if(ModApi.implementsType(item,TOKEN))try{
                var stack=item.getDefaultStack();var type=ModApi.call(item,"getEntityType",stack);
                if(type instanceof EntityType<?> t&&Registries.ENTITY_TYPE.getId(t).toString().equals("aoa3:"+normal)){j.token=item;j.stack=stack;break;}
            }catch(Exception ignored){}
            if(j.token==null)throw new IllegalStateException("Original normal Boss token unavailable");
            job=j;nextArena(j);phase="loading-anchor";
            evidence.addProperty("registeredBoss",Registries.ENTITY_TYPE.getId(j.type).toString());evidence.addProperty("token",Registries.ITEM.getId(j.stack.getItem()).toString());evidence.addProperty("elite",selected.startsWith("elite_"));
        }catch(Exception e){fail(e);}report();
    }
    private static void nextArena(Job j)throws Exception{
        if(j.arenaIndex>=j.arenas.size())throw new IllegalStateException("No unoccupied original arena within this request");
        release(j);j.arena=j.arenas.get(j.arenaIndex++);
        var field=j.arena.getClass().getDeclaredField("structurePos");field.setAccessible(true);var pos=(BlockPos)field.get(j.arena);
        j.chunks=List.of(new ChunkPos(pos));j.chunkIndex=0;evidence.addProperty("arena",j.arena.getClass().getField("structureId").get(j.arena).toString());
    }
    public static void tick(MinecraftServer server){
        var j=job;if(j==null)return;
        try{
            var p=server.getPlayerManager().getPlayer(j.owner);
            if(p==null||!p.isAlive()||!SurvivalRuntime.permitted(p)||server.getTicks()>j.deadline)throw new IllegalStateException("Boss travel cancelled or bounded deadline reached");
            if(!j.committed&&(p.getServerWorld()!=j.origin||!j.initial.getAsBoolean()))throw new IllegalStateException("Original travel admission expired");
            if(j.committed&&p.getServerWorld()!=j.world)throw new IllegalStateException("Player left the requested Boss dimension");
            switch(phase){
                case "loading-anchor"->{if(load(j)){
                    j.bounds=(Box)ModApi.call(j.arena,"getStructureBounds",j.world);
                    if(j.bounds==null||j.bounds.getLengthX()>240||j.bounds.getLengthZ()>240)throw new IllegalStateException("Original arena structure not generated or outside budget");
                    var chunks=new ArrayList<ChunkPos>();for(int x=MathHelper.floor(j.bounds.minX)>>4;x<=MathHelper.floor(j.bounds.maxX)>>4;x++)for(int z=MathHelper.floor(j.bounds.minZ)>>4;z<=MathHelper.floor(j.bounds.maxZ)>>4;z++)chunks.add(new ChunkPos(x,z));
                    if(chunks.size()>256)throw new IllegalStateException("Original arena chunk budget exceeded");j.chunks=chunks;j.chunkIndex=0;phase="loading-arena";
                }}
                case "loading-arena"->{if(load(j)){
                    if(!Boolean.TRUE.equals(ModApi.call(j.arena,"checkAndClear",j.world))){nextArena(j);phase="loading-anchor";break;}
                    // Original arena entry points and delayed Boss spawning remain author-owned.
                    // The F12 creative shortcut moves to that real world before the author's
                    // same-world player teleport. It does not construct an imitation arena.
                    var spawn=(Vec3d)ModApi.call(j.arena,"getRandomBossSpawn");
                    var at=new Vec3d(j.bounds.getCenter().x,j.bounds.minY+52,j.bounds.getCenter().z);
                    // Author player positions are read from the registered definition, not guessed.
                    var field=j.arena.getClass().getDeclaredField("playerSpawnPoints");field.setAccessible(true);
                    var points=(List<?>)field.get(j.arena);if(points.isEmpty())throw new IllegalStateException("Original player spawn absent");at=(Vec3d)points.getFirst();
                    p.teleport(j.world,at.x,at.y,at.z,0,0);p.setVelocity(Vec3d.ZERO);p.fallDistance=0;j.committed=true;j.entryTick=server.getTicks();
                    var function=Class.forName(TOKEN+"$SpawningFunction");
                    Object proxy=Proxy.newProxyInstance(function.getClassLoader(),new Class<?>[]{function},(self,method,args)->{
                        if(method.getDeclaringClass()==Object.class)return method.getName().equals("toString")?"OWMC original Boss spawning bridge":method.getName().equals("hashCode")?System.identityHashCode(self):self==args[0];
                        if(job!=j||!current(server,j))return null;
                        Object result;
                        if(boss.startsWith("elite_"))result=ModApi.call(Class.forName("net.tslat.aoa3.util.EntitySpawningUtil"),"spawnEntity",j.world,j.type,args[1],SpawnReason.TRIGGERED);
                        else result=ModApi.call(j.token,"spawnBoss",j.world,args[1],j.stack,args[3]);
                        if(result instanceof Entity entity)j.spawned=entity;return result;
                    });
                    Predicate<Object> valid=player->player==p&&current(server,j);
                    ModApi.call(j.arena,"placePlayersAndBoss",j.world,List.of(p),valid,j.stack,j.type,proxy);
                    destination=new JsonObject();destination.addProperty("dimension",j.world.getRegistryKey().getValue().toString());destination.addProperty("x",at.x);destination.addProperty("y",at.y);destination.addProperty("z",at.z);
                    evidence.addProperty("originalArenaLifecycle",true);evidence.addProperty("originalSpawnX",spawn.x);evidence.addProperty("originalSpawnY",spawn.y);evidence.addProperty("originalSpawnZ",spawn.z);phase="original-summoning";
                }}
                case "original-summoning"->{
                    if(server.getTicks()-j.entryTick>60&&!j.current.getAsBoolean())throw new IllegalStateException("Native owner/menu changed during original summoning");
                    if(j.spawned!=null&&j.spawned.isAlive()&&j.spawned.getWorld()==j.world&&j.world.getEntity(j.spawned.getUuid())==j.spawned){
                        destination.addProperty("x",p.getX());destination.addProperty("y",p.getY());destination.addProperty("z",p.getZ());
                        evidence.addProperty("entityUuid",j.spawned.getUuidAsString());evidence.addProperty("entityId",j.spawned.getId());evidence.addProperty("actualEntity",Registries.ENTITY_TYPE.getId(j.spawned.getType()).toString());evidence.addProperty("health",j.spawned instanceof LivingEntity l?l.getHealth():0);evidence.addProperty("resolution","original-arena-and-original-mod-spawn");completed++;release(j);job=null;phase="complete";
                    }else if(server.getTicks()-j.entryTick>400)throw new IllegalStateException("Original arena did not produce a living Boss");
                }
                default->throw new IllegalStateException("Unexpected original arena phase");
            }
        }catch(Exception e){fail(e);}report();
    }
    private static boolean current(MinecraftServer s,Job j){var p=s.getPlayerManager().getPlayer(j.owner);return job==j&&p!=null&&p.isAlive()&&SurvivalRuntime.permitted(p)&&p.getServerWorld()==j.world&&j.current.getAsBoolean();}
    private static boolean load(Job j){for(int i=0;i<4&&j.chunkIndex<j.chunks.size();i++){var cp=j.chunks.get(j.chunkIndex++);if(j.tickets.add(cp))j.world.getChunkManager().addTicket(TICKET,cp,0,j.id);}return j.chunkIndex==j.chunks.size()&&j.chunks.stream().allMatch(cp->j.world.getChunkManager().getWorldChunk(cp.x,cp.z)!=null&&j.world.isChunkLoaded(cp.toLong()));}
    private static void release(Job j){for(var cp:j.tickets)j.world.getChunkManager().removeTicket(TICKET,cp,0,j.id);evidence.addProperty("releasedTickets",j.tickets.size());j.tickets.clear();}
    private static void fail(Exception e){if(job!=null)release(job);job=null;phase="failed";error=e.getClass().getSimpleName()+": "+e.getMessage();}
    public static void close(){if(job!=null)release(job);job=null;phase="idle";report();}
    private static void report(){var o=new JsonObject();o.addProperty("requestId",requestId);o.addProperty("completed",completed);o.addProperty("busyRequests",busyRequests);o.addProperty("busy",job!=null);o.addProperty("phase",phase);o.addProperty("boss",boss);o.addProperty("error",error);o.add("evidence",evidence.deepCopy());if(destination!=null)o.add("destination",destination.deepCopy());status=o.toString();}
}
