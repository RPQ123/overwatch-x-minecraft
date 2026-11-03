package lab.owmcguest;

import com.google.gson.JsonArray;
import com.google.gson.JsonObject;
import java.util.*;
import java.util.function.Supplier;
import java.util.function.BooleanSupplier;
import net.fabricmc.loader.api.FabricLoader;
import net.minecraft.block.Blocks;
import net.minecraft.block.BlockState;
import net.minecraft.registry.Registries;
import net.minecraft.registry.RegistryKey;
import net.minecraft.registry.RegistryKeys;
import net.minecraft.registry.entry.RegistryEntryList;
import net.minecraft.server.MinecraftServer;
import net.minecraft.server.network.ServerPlayerEntity;
import net.minecraft.server.world.ServerWorld;
import net.minecraft.server.world.ChunkTicketType;
import net.minecraft.structure.StructurePiece;
import net.minecraft.structure.StructureStart;
import net.minecraft.structure.StructureContext;
import net.minecraft.structure.SimpleStructurePiece;
import net.minecraft.util.Identifier;
import net.minecraft.util.math.*;
import net.minecraft.world.GameRules;
import net.minecraft.world.World;
import net.minecraft.world.BlockView;
import net.minecraft.world.RaycastContext;
import net.minecraft.util.hit.HitResult;
import net.minecraft.util.shape.VoxelShape;
import net.minecraft.util.shape.VoxelShapes;
import net.minecraft.world.gen.structure.Structure;

/** Optional, server-thread-only travel to original TF boss rooms; never summons replacement bosses. */
public final class TwilightBossTravel {
    public static volatile String status="{}";
    private record Boss(String id,String structure,String piece,String spawner,String entity) {}
    private static final List<Boss> BOSSES=List.of(
        new Boss("naga","naga_courtyard","CourtyardMain","naga_boss_spawner","naga"),
        new Boss("lich","lich_tower","LichBossRoom","lich_boss_spawner","lich"),
        new Boss("minoshroom","labyrinth","MazeRoomBossComponent","minoshroom_boss_spawner","minoshroom"),
        new Boss("hydra","hydra_lair","HydraLairComponent","hydra_boss_spawner","hydra"),
        new Boss("knight_phantom","knight_stronghold","StrongholdBossRoomComponent","knight_phantom_boss_spawner","knight_phantom"),
        new Boss("ur_ghast","dark_tower","DarkTowerMainComponent","ur_ghast_boss_spawner","ur_ghast"),
        new Boss("alpha_yeti","yeti_cave","YetiCaveComponent","alpha_yeti_boss_spawner","alpha_yeti"),
        new Boss("snow_queen","aurora_palace","IceTowerBossWingComponent","snow_queen_boss_spawner","snow_queen")
    );
    private static final int[] RADII={8,16,32,64,96,128};
    private static final int MAX_CANDIDATES=8,MAX_QUERY_CENTERS=17;
    private static final int ENTITY_LOAD_BUDGET_TICKS=200;
    // Public addTicket radius 0 means FULL level 33 in this exact Yarn runtime.
    // Explicit release is authoritative; expiry is a final safety bound if an owner disappears.
    private static final ChunkTicketType<Long> TICKET=ChunkTicketType.create("owmc_twilight_boss_travel",Comparator.<Long>naturalOrder(),2600);
    private static final RegistryKey<World> DIMENSION=RegistryKey.of(RegistryKeys.WORLD,Identifier.of("twilightforest","twilight_forest"));
    private static long requestId,completed,busyRequests;
    private static String bossId="",error="",phase="idle",destinationKind="";
    private static boolean progressionDisabled;
    private static Job job;
    private static JsonObject destination,activation;
    private static JsonObject evidence;
    private static JsonArray rejectedCandidates=new JsonArray();
    private static MinecraftServer serverIdentity;
    private static final class Job {
        UUID owner; Boss boss; ServerWorld world,originWorld; BlockPos origin,located,anchor,originalMarker; Structure structure; BooleanSupplier stillAdmitted;
        StructureStart start; StructurePiece piece; int radiusIndex,deadline,chunkIndex,missingChunks,queryIndex,candidateCount;
        Set<Long> seenLocated=new HashSet<>();
        long ticketId; Set<ChunkPos> tickets=new LinkedHashSet<>(); List<ChunkPos> chunks=List.of();
        List<BlockPos> candidates=List.of(); int candidateIndex;
        Iterator<BlockPos> spawnerScan; int spawnerScanned;
        int entityWaitStarted=-1,missingEntityChunks,entityWaitPolls,bossQueryCount;
        boolean markerScanCompleted;
        Set<Long> connectedFloor=new HashSet<>(); ArrayDeque<BlockPos> floorFrontier=new ArrayDeque<>();
    }
    private static boolean allowed(MinecraftServer server){
        return server.isSingleplayer()&&Boolean.getBoolean("owmc.twilightTrial")
            &&System.getProperty("owmc.worldName","").startsWith("Overwatch Twilight ")
            &&FabricLoader.getInstance().isModLoaded("twilightforest")
            &&FabricLoader.getInstance().getModContainer("twilightforest").orElseThrow().getMetadata().getVersion().getFriendlyString().equals("4.8.754");
    }
    private static boolean eligible(ServerPlayerEntity player){return player!=null&&player.isAlive()&&SurvivalRuntime.permitted(player);}
    /** Caller requires release before re-arming; every new idle attempt gets an immediate request ID. */
    public static void request(MinecraftServer server,UUID owner,String id){
        request(server,owner,id,()->true);
    }
    /** The predicate reads a client-published admission token only, never client/JNA state on this thread. */
    public static void request(MinecraftServer server,UUID owner,String id,BooleanSupplier stillAdmitted){
        requestAt(server,owner,id,stillAdmitted,null);
    }
    public static void requestAt(MinecraftServer server,UUID owner,String id,BooleanSupplier stillAdmitted,BlockPos searchOrigin){
        if(!server.isOnThread())throw new IllegalStateException("Boss travel must be requested on the server thread");
        if(serverIdentity!=server)reset(server);
        if(job!=null){busyRequests++;report();return;}
        requestId++;bossId=id==null?"":id;error="";destination=null;activation=null;evidence=null;rejectedCandidates=new JsonArray();destinationKind="";
        try{
            if(!allowed(server))throw new IllegalStateException("Boss travel requires the pinned mod in the separate singleplayer Twilight trial");
            var player=server.getPlayerManager().getPlayer(owner);
            if(!eligible(player))throw new IllegalStateException("Boss travel requires a living creative player");
            if(stillAdmitted==null||!stillAdmitted.getAsBoolean())throw new IllegalStateException("Boss travel admission expired; finish the current skill and reopen F12");
            var boss=BOSSES.stream().filter(b->b.id.equals(bossId)).findFirst().orElseThrow(()->new IllegalArgumentException("Unknown or unimplemented boss"));
            var world=server.getWorld(DIMENSION);
            if(world==null)throw new IllegalStateException("The real Twilight dimension is unavailable");
            disableProgression(server);
            var structure=world.getRegistryManager().get(RegistryKeys.STRUCTURE).getOrEmpty(Identifier.of("twilightforest",boss.structure)).orElseThrow(()->new IllegalStateException("Original structure is not registered"));
            var next=new Job();next.owner=owner;next.boss=boss;next.world=world;next.structure=structure;
            next.origin=searchOrigin==null?player.getBlockPos():searchOrigin;next.originWorld=player.getServerWorld();next.stillAdmitted=stillAdmitted;next.ticketId=requestId;next.deadline=server.getTicks()+2400;job=next;phase="locating";
        }catch(Exception failure){fail(failure);}
        report();
    }
    @SuppressWarnings("unchecked")
    private static void disableProgression(MinecraftServer server)throws ReflectiveOperationException{
        // Public upstream Supplier; its BooleanRule callback sends the mod's original client packet.
        var field=Class.forName("twilightforest.init.TFGameRules").getField("ENFORCED_PROGRESSION_RULE");
        var supplier=(Supplier<?>)field.get(null);
        var key=(GameRules.Key<GameRules.BooleanRule>)supplier.get();
        for(var world:server.getWorlds())if(world.getGameRules().getBoolean(key))world.getGameRules().get(key).set(false,server);
        progressionDisabled=true;for(var world:server.getWorlds())progressionDisabled&=!world.getGameRules().getBoolean(key);
    }
    public static void tick(MinecraftServer server){
        if(serverIdentity!=server)reset(server);
        if(!allowed(server)){if(job!=null)fail(new IllegalStateException("Twilight trial authorization changed"));report();return;}
        try{
            if(server.getTicks()%100==0)disableProgression(server);
            if(job==null){if(server.getTicks()%20==0)report();return;}
            var player=server.getPlayerManager().getPlayer(job.owner);
            if(!eligible(player))throw new IllegalStateException("Travel owner disconnected, died or left creative mode");
            if(!job.stillAdmitted.getAsBoolean())throw new IllegalStateException("Travel cancelled: skill, hero, focus or native admission changed; reopen F12 when idle");
            if(player.getServerWorld()!=job.originWorld)throw new IllegalStateException("Travel owner changed dimension during pending travel");
            if(server.getTicks()>job.deadline)throw new IllegalStateException("Bounded boss travel timed out; no terrain was excavated");
            switch(phase){
                case "locating" -> locate();
                case "loading-start" -> loadStart();
                case "loading-room" -> loadRoom();
                case "waiting-original-entities" -> waitOriginalEntities();
                case "finding-spawner" -> scanSpawner();
                case "checking-floor-connectivity" -> connectFloor();
                case "finding-floor" -> findFloor(player);
                default -> throw new IllegalStateException("Unknown boss travel phase");
            }
        }catch(Exception failure){fail(failure);}
        report();
    }
    private static void locate(){
        if(job.queryIndex>=MAX_QUERY_CENTERS||job.candidateCount>=MAX_CANDIDATES)throw new IllegalStateException("Bounded original boss search exhausted: "+job.candidateCount+" real structures, "+job.queryIndex+" search centers");
        var registry=job.world.getRegistryManager().get(RegistryKeys.STRUCTURE);
        var entry=registry.getEntry(job.structure);
        // One bounded vanilla locate call per server tick. Never access a world from a worker thread.
        int radius=RADII[job.radiusIndex++];
        var found=job.world.getChunkManager().getChunkGenerator().locateStructure(job.world,RegistryEntryList.of(entry),queryOrigin(job.origin,job.queryIndex),radius,false);
        if(found==null){if(job.radiusIndex>=RADII.length){job.queryIndex++;job.radiusIndex=0;}return;}
        job.located=found.getFirst().toImmutable();
        if(!job.seenLocated.add(job.located.asLong())){job.queryIndex++;job.radiusIndex=0;return;}
        job.candidateCount++;
        if(!job.world.getWorldBorder().contains(job.located)){retryCandidate("Original structure lies outside the world border");return;}
        var chunk=new ChunkPos(job.located);job.chunks=List.of(chunk);job.chunkIndex=0;phase="loading-start";
    }
    private static boolean loadChunks(){
        // Do not call getChunkFutureSyncOnMainThread: it pumps tasks until done
        // on the server thread, despite returning a future. Our tickets let the
        // ordinary chunk pipeline progress between ticks; getWorldChunk is get-now.
        int issued=0;
        while(job.chunkIndex<job.chunks.size()&&issued++<2){
            var p=job.chunks.get(job.chunkIndex++);
            if(job.tickets.add(p))job.world.getChunkManager().addTicket(TICKET,p,0,job.ticketId);
        }
        job.missingChunks=0;
        for(var p:job.chunks)if(job.world.getChunkManager().getWorldChunk(p.x,p.z)==null)job.missingChunks++;
        return job.chunkIndex>=job.chunks.size()&&job.missingChunks==0;
    }
    private static void loadStart(){
        if(!loadChunks())return;
        var cp=job.chunks.getFirst();var chunk=job.world.getChunkManager().getWorldChunk(cp.x,cp.z);
        var start=chunk==null?null:chunk.getStructureStart(job.structure);
        if(start==null||!start.hasChildren()){
            // A locate point may be an offset from the start; use real generated references only.
            var candidates=job.world.getStructureAccessor().getStructureStarts(cp,s->s==job.structure);
            start=candidates.stream().filter(StructureStart::hasChildren).findFirst().orElse(null);
        }
        if(start==null||!start.hasChildren()){retryCandidate("Located structure has no generated original start");return;}
        job.start=start;
        evidence=new JsonObject();evidence.add("startBox",boxJson(start.getBoundingBox()));evidence.addProperty("startPieces",start.getChildren().size());
        var classCounts=new TreeMap<String,Integer>();for(var p:start.getChildren())classCounts.merge(p.getClass().getSimpleName(),1,Integer::sum);
        var classesJson=new JsonObject();classCounts.forEach(classesJson::addProperty);evidence.add("pieceClasses",classesJson);
        var pieces=start.getChildren().stream().filter(p->p.getClass().getSimpleName().equals(job.boss.piece)).toList();
        if(pieces.isEmpty()){retryCandidate("The expected original boss room piece is missing");return;}
        // The Dark Tower has several mains; only the highest original main contains Ur-Ghast's spawner.
        job.piece=pieces.stream().max(Comparator.comparingInt(p->p.getBoundingBox().getMaxY())).orElseThrow();
        var box=job.piece.getBoundingBox();
        evidence.addProperty("piece",job.piece.getClass().getName());evidence.add("roomBox",boxJson(box));
        if(box.getBlockCountX()>128||box.getBlockCountZ()>128)throw new IllegalStateException("Unexpected boss room extent");
        var chunks=new ArrayList<ChunkPos>();
        for(int x=(box.getMinX()-4)>>4;x<=(box.getMaxX()+4)>>4;x++)for(int z=(box.getMinZ()-4)>>4;z<=(box.getMaxZ()+4)>>4;z++)chunks.add(new ChunkPos(x,z));
        if(chunks.size()>100)throw new IllegalStateException("Boss room exceeds bounded chunk budget");
        if(chunks.stream().filter(p->!job.tickets.contains(p)).count()+job.tickets.size()>100)throw new IllegalStateException("Boss room plus original start exceeds ticket budget");
        job.chunks=chunks;job.chunkIndex=0;phase="loading-room";
    }
    private static void loadRoom(){
        if(!loadChunks())return;
        var expected=Identifier.of("twilightforest",job.boss.spawner);var box=job.piece.getBoundingBox();
        int indexed=0;var seen=new JsonArray();var classes=new HashSet<String>();
        for(var cp:job.chunks){
            var chunk=job.world.getChunkManager().getWorldChunk(cp.x,cp.z);
            if(chunk==null)throw new IllegalStateException("An owned FULL room chunk became unavailable before its spawner scan");
            classes.add(chunk.getClass().getSimpleName());
            for(var at:chunk.getBlockEntityPositions()){
                indexed++;var blockId=Registries.BLOCK.getId(job.world.getBlockState(at).getBlock());
                if(blockId.getPath().contains("boss_spawner")&&seen.size()<32){var row=posJson(at);row.addProperty("block",blockId.toString());row.addProperty("inRoom",box.contains(at));seen.add(row);}
                if(box.contains(at)&&blockId.equals(expected)){job.anchor=at.toImmutable();break;}
            }
            if(job.anchor!=null)break;
        }
        evidence.addProperty("indexedBlockEntityPositions",indexed);evidence.addProperty("chunkClasses",String.join(",",classes));evidence.add("indexedBossBlocks",seen);
        if(job.anchor!=null)evidence.addProperty("resolutionMethod","block-entity-index");
        // Fresh structure templates can have actual spawner blocks before their BE index
        // is materialized. Validate the original template's exact tiny marker region.
        // No guessed world coordinate, fabricated anchor or whole-dungeon scan is used.
        if(job.anchor==null&&(job.boss.id.equals("naga")||job.boss.id.equals("lich"))){
            String expectedTemplate=job.boss.id.equals("naga")?"twilightforest:courtyard/spawner":"twilightforest:lich_tower/tower_boss_room";
            var checked=new JsonArray();
            for(var piece:job.start.getChildren()){
                if(!(piece instanceof SimpleStructurePiece))continue;
                if(job.boss.id.equals("naga")&&piece.getBoundingBox().getBlockCountX()*piece.getBoundingBox().getBlockCountY()*piece.getBoundingBox().getBlockCountZ()>2)continue;
                if(job.boss.id.equals("lich")&&piece!=job.piece)continue;
                var tag=piece.toNbt(StructureContext.from(job.world));
                if(!tag.getString("Template").equals(expectedTemplate))continue;
                for(var at:templateSpawnerCandidates(expectedTemplate,piece.getBoundingBox())){
                    if(!box.contains(at)||!job.world.isChunkLoaded(at))continue;
                    job.originalMarker=at.toImmutable();
                    var actual=Registries.BLOCK.getId(job.world.getBlockState(at).getBlock());var row=posJson(at);row.addProperty("block",actual.toString());checked.add(row);
                    if(actual.equals(expected)){job.anchor=at.toImmutable();evidence.addProperty("resolutionMethod","original-template-block");break;}
                }
                if(job.anchor!=null)break;
            }
            evidence.add("templateBlockChecks",checked);
        }
        if(job.anchor==null){
            var at=sourceSpawnerAnchor(job.piece,job.boss.id);
            if(at!=null&&box.contains(at)&&job.world.isChunkLoaded(at)){
                job.originalMarker=at.toImmutable();
                var actual=Registries.BLOCK.getId(job.world.getBlockState(at).getBlock());var row=posJson(at);row.addProperty("block",actual.toString());evidence.add("sourceTransformBlockCheck",row);
                if(actual.equals(expected)){job.anchor=at.toImmutable();evidence.addProperty("resolutionMethod","original-piece-transform-block");}
            }
        }
        if(job.anchor==null){
            // A FULL WorldChunk does not imply that its separate asynchronous
            // entity file has reached ServerEntityManager.Status.LOADED yet.
            // Keep the existing FULL33 lease; no ticking-level upgrade is needed.
            job.entityWaitStarted=job.world.getServer().getTicks();phase="waiting-original-entities";
            waitOriginalEntities();return;
        }
        prepareFloor();
    }
    private static void waitOriginalEntities(){
        job.entityWaitPolls++;job.missingEntityChunks=0;
        // This exact ServerWorld long overload reads entityManager.isLoaded,
        // unlike getWorldChunk (terrain readiness) or the BlockPos overload.
        for(var cp:job.chunks)if(!job.world.isChunkLoaded(cp.toLong()))job.missingEntityChunks++;
        int elapsed=job.world.getServer().getTicks()-job.entityWaitStarted;
        evidence.addProperty("entityChunksTotal",job.chunks.size());
        evidence.addProperty("missingEntityChunks",job.missingEntityChunks);
        evidence.addProperty("entityLoaded",job.missingEntityChunks==0);
        evidence.addProperty("entityWaitTicks",elapsed);evidence.addProperty("entityWaitPolls",job.entityWaitPolls);
        evidence.addProperty("entityLoadBudgetTicks",ENTITY_LOAD_BUDGET_TICKS);
        if(job.missingEntityChunks>0){
            if(elapsed>=ENTITY_LOAD_BUDGET_TICKS)throw new IllegalStateException("Original boss entity loading timed out; room was not declared conquered");
            return;
        }
        if(resolveExistingBoss()){prepareFloor();return;}
        if(job.markerScanCompleted){retryCandidate("Entity-loaded original room contains no real boss spawner or living boss; it may already be conquered");return;}
        // A last read-only check of this real, narrow boss room; no whole
        // dungeon/world scan and no fabricated coordinate or replacement boss.
        var box=job.piece.getBoundingBox();
        long volume=(long)box.getBlockCountX()*box.getBlockCountY()*box.getBlockCountZ();
        if(volume>50000){retryCandidate("Original boss marker absent after entity-loaded/indexed/template/transform checks; room exceeds bounded fallback scan");return;}
        job.spawnerScan=BlockPos.iterate(box.getMinX(),box.getMinY(),box.getMinZ(),box.getMaxX(),box.getMaxY(),box.getMaxZ()).iterator();
        job.spawnerScanned=0;evidence.addProperty("fallbackScanVolume",volume);phase="finding-spawner";
    }
    /** Queries only real living original bosses, after entity data readiness. Never creates one. */
    private static boolean resolveExistingBoss(){
        var box=job.piece.getBoundingBox();
        var bounds=new Box(box.getMinX(),box.getMinY(),box.getMinZ(),box.getMaxX()+1,box.getMaxY()+1,box.getMaxZ()+1).expand(24);
        var bosses=job.world.getEntitiesByClass(net.minecraft.entity.LivingEntity.class,bounds,e->e.isAlive()&&Registries.ENTITY_TYPE.getId(e.getType()).equals(Identifier.of("twilightforest",job.boss.entity)));
        evidence.addProperty("originalBossQueryCount",++job.bossQueryCount);evidence.addProperty("originalBossCount",bosses.size());
        if(bosses.isEmpty())return false;
        evidence.add("existingBossPosition",posJson(bosses.getFirst().getBlockPos()));
        job.anchor=job.originalMarker!=null?job.originalMarker:bosses.getFirst().getBlockPos();
        evidence.addProperty("resolutionMethod",job.originalMarker!=null?"existing-original-boss-and-original-marker":"existing-original-boss");
        return true;
    }
    private static void prepareFloor(){
        evidence.add("anchor",posJson(job.anchor));
        evidence.addProperty("floorFeetY",floorFeetY(job.piece.getBoundingBox(),job.boss.id));
        evidence.addProperty("floorRule","pinned-original-boss-room-floor-v1");
        var box=job.piece.getBoundingBox();
        job.candidates=floorCandidates(box,job.anchor,job.boss.id);job.candidateIndex=0;
        if(!openArena(job.boss.id)){
            var player=job.world.getServer().getPlayerManager().getPlayer(job.owner);
            int y=floorFeetY(box,job.boss.id);
            for(int x=-5;x<=5;x++)for(int z=-5;z<=5;z++){
                var at=new BlockPos(job.anchor.getX()+x,y,job.anchor.getZ()+z);
                if(box.contains(at)&&floorCell(job.world,at)&&viewsOriginalRoom(job.world,player,at,job.anchor)&&job.connectedFloor.add(at.asLong()))job.floorFrontier.add(at);
            }
            evidence.addProperty("floorConnectivitySeeds",job.floorFrontier.size());phase="checking-floor-connectivity";
        }else phase="finding-floor";
    }
    private static void connectFloor(){
        var box=job.piece.getBoundingBox();
        for(int count=0;count<256&&!job.floorFrontier.isEmpty();count++){
            var at=job.floorFrontier.removeFirst();
            for(var direction:Direction.Type.HORIZONTAL){
                var next=at.offset(direction);
                if(box.contains(next)&&!job.connectedFloor.contains(next.asLong())&&floorCell(job.world,next)){
                    job.connectedFloor.add(next.asLong());job.floorFrontier.addLast(next);
                    if(job.connectedFloor.size()>4096)throw new IllegalStateException("Original boss floor exceeds bounded connectivity budget");
                }
            }
        }
        evidence.addProperty("connectedFloorCells",job.connectedFloor.size());
        if(job.floorFrontier.isEmpty()){
            if(job.connectedFloor.isEmpty()){retryCandidate("No actual walkable boss-floor component has a view into the original room");return;}
            // A template's true walking area can end well inside its decorative
            // bbox (Lich's central smooth-stone floor is surrounded by stairs).
            // Its actual connected boundary is a valid room-side edge too.
            var boundary=new ArrayList<BlockPos>();
            for(long packed:job.connectedFloor){
                var at=BlockPos.fromLong(packed);boolean edge=false;
                for(var direction:Direction.Type.HORIZONTAL)if(!job.connectedFloor.contains(at.offset(direction).asLong())){edge=true;break;}
                if(edge)boundary.add(at);
            }
            boundary.sort(Comparator.comparingLong((BlockPos at)->{
                long x=(long)at.getX()-job.anchor.getX(),z=(long)at.getZ()-job.anchor.getZ();return -(x*x+z*z);
            }).thenComparingInt(BlockPos::getX).thenComparingInt(BlockPos::getZ));
            evidence.addProperty("connectedFloorBoundaryCells",boundary.size());
            var ordered=new LinkedHashSet<BlockPos>(boundary);ordered.addAll(job.candidates);job.candidates=List.copyOf(ordered);
            phase="finding-floor";
        }
    }
    private static void scanSpawner(){
        var expected=Identifier.of("twilightforest",job.boss.spawner);
        for(int count=0;count<512&&job.spawnerScan.hasNext();count++){
            var at=job.spawnerScan.next();job.spawnerScanned++;
            if(!job.world.isChunkLoaded(at))throw new IllegalStateException("An owned room chunk became unavailable during bounded marker scan");
            if(Registries.BLOCK.getId(job.world.getBlockState(at).getBlock()).equals(expected)){
                job.anchor=at.toImmutable();evidence.addProperty("resolutionMethod","bounded-original-room-block-scan");evidence.addProperty("fallbackBlocksScanned",job.spawnerScanned);prepareFloor();return;
            }
        }
        evidence.addProperty("fallbackBlocksScanned",job.spawnerScanned);
        if(!job.spawnerScan.hasNext()){
            // A real boss may have loaded while the bounded block scan advanced.
            // Recheck the entity readiness and live entity query before rejecting.
            job.markerScanCompleted=true;phase="waiting-original-entities";waitOriginalEntities();
        }
    }
    private static BlockPos sourceSpawnerAnchor(StructurePiece piece,String boss){
        try{
            int x,y,z;
            switch(boss){
                case "minoshroom" -> {x=7;y=2;z=7;}
                case "hydra" -> {x=27;y=3;z=27;}
                case "knight_phantom" -> {x=13;y=2;z=13;}
                case "ur_ghast" -> {x=9;y=originalInt(piece,"height")-2;z=9;}
                case "alpha_yeti" -> {x=originalInt(piece,"radius");y=1;z=x;}
                case "snow_queen" -> {x=7;y=(originalInt(piece,"height")/10)*10-6;z=7;}
                default -> {return null;}
            }
            // Existing public original helper calls the piece's actual virtual
            // world transforms, including Yeti's special vertical adjustment.
            return (BlockPos)piece.getClass().getMethod("getBlockPosWithOffset",int.class,int.class,int.class).invoke(piece,x,y,z);
        }catch(ReflectiveOperationException failure){evidence.addProperty("originalTransformUnavailable",failure.getClass().getSimpleName());return null;}
    }
    private static int originalInt(Object piece,String name)throws ReflectiveOperationException{
        for(Class<?> type=piece.getClass();type!=null;type=type.getSuperclass())try{
            var field=type.getDeclaredField(name);field.setAccessible(true);return field.getInt(piece);
        }catch(NoSuchFieldException missing){/* inspect the next original superclass */}
        throw new NoSuchFieldException(name);
    }
    /** Positions from the actual pinned templates; centered Lich position is rotation invariant. */
    static List<BlockPos> templateSpawnerCandidates(String template,BlockBox box){
        if(template.equals("twilightforest:courtyard/spawner")&&box.getBlockCountX()==1&&box.getBlockCountY()==2&&box.getBlockCountZ()==1)
            return List.of(new BlockPos(box.getMinX(),box.getMinY()+1,box.getMinZ()));
        if(template.equals("twilightforest:lich_tower/tower_boss_room")&&box.getBlockCountX()==31&&box.getBlockCountY()==12&&box.getBlockCountZ()==31)
            return List.of(new BlockPos(box.getMinX()+15,box.getMinY()+5,box.getMinZ()+15));
        return List.of();
    }
    /** Candidate geometry is derived from the actual room box and spawner, not world-seed coordinates. */
    static List<BlockPos> floorCandidates(BlockBox box,BlockPos anchor,String boss){
        var result=new ArrayList<BlockPos>();
        boolean open=openArena(boss);
        int lower=floorFeetY(box,boss),upper=lower;
        // Actual room-side floor wins over exterior decorative cornices. Open
        // arenas may also use an outside strip on their verified floor layer.
        int[] depths=open?new int[]{-3,-2,-1,0,1,2,3,4,5}:new int[]{2,3,4,5,1,0};
        for(int depth:depths)for(int y=lower;y<=upper;y++){
            int minX=box.getMinX()+depth,maxX=box.getMaxX()-depth,minZ=box.getMinZ()+depth,maxZ=box.getMaxZ()-depth;
            if(minX>maxX||minZ>maxZ)continue;
            for(int x=minX;x<=maxX;x++){result.add(new BlockPos(x,y,minZ));result.add(new BlockPos(x,y,maxZ));}
            for(int z=minZ+1;z<maxZ;z++){result.add(new BlockPos(minX,y,z));result.add(new BlockPos(maxX,y,z));}
        }
        // Open lairs' actual walkable entrance can lie inside their broad terrain bounding box.
        if(open)for(int radius=24;radius>=10;radius--)for(int y=lower;y<=upper;y++)for(int d=-radius;d<=radius;d++){
            result.add(anchor.add(d,y-anchor.getY(),-radius));result.add(anchor.add(d,y-anchor.getY(),radius));
            result.add(anchor.add(-radius,y-anchor.getY(),d));result.add(anchor.add(radius,y-anchor.getY(),d));
        }
        return List.copyOf(new LinkedHashSet<>(result));
    }
    private static boolean openArena(String boss){return Set.of("naga","hydra","alpha_yeti").contains(boss);}
    /** Exact original floor layers, not a downward search from the floating boss marker. */
    static int floorFeetY(BlockBox box,String boss){
        return switch(boss){
            case "naga" -> box.getMinY()+2; // Courtyard y=3 floor, marker y=5 in first actual save.
            case "lich" -> box.getMinY()+4; // actual template smooth-stone floor local3, spawner local5.
            case "minoshroom","knight_phantom" -> box.getMinY()+1; // original room floor local0.
            case "hydra","alpha_yeti" -> box.getMinY(); // original lair/cave density floor, not a sub-floor pocket.
            case "ur_ghast" -> box.getMaxY()-4; // last 5-block floor at height-6; feet at height-5.
            case "snow_queen" -> box.getMinY()+(box.getBlockCountY()/10-1)*10+1; // original IceTowerWing floorHeight=10.
            default -> throw new IllegalArgumentException("No verified original floor rule for "+boss);
        };
    }
    private static void findFloor(ServerPlayerEntity player){
        for(int count=0;count<384&&job.candidateIndex<job.candidates.size();count++){
            var at=job.candidates.get(job.candidateIndex++);
            if(!safe(job.world,player,at))continue;
            var box=job.piece.getBoundingBox();
            if(job.boss.id.equals("naga")&&!job.world.isSkyVisible(at.up(2)))continue;
            if(!openArena(job.boss.id)&&!job.connectedFloor.contains(at.asLong()))continue;
            if(!viewsOriginalRoom(job.world,player,at,job.anchor))continue;
            if(!job.stillAdmitted.getAsBoolean())throw new IllegalStateException("Travel admission expired immediately before teleport");
            destinationKind=box.contains(at)?"boss-room-edge":"boss-room-door-exterior";
            // Keep an actual solid floor, two air blocks and the full current player collision box.
            var target=Vec3d.ofBottomCenter(at);float yaw=(float)Math.toDegrees(Math.atan2(job.anchor.getZ()+.5-target.z,job.anchor.getX()+.5-target.x))-90;
            // Native short arrival lease bridges player ticket establishment.
            job.world.getChunkManager().addTicket(ChunkTicketType.POST_TELEPORT,new ChunkPos(at),1,player.getId());
            player.teleport(job.world,target.x,target.y,target.z,yaw,0);player.setVelocity(Vec3d.ZERO);player.fallDistance=0;
            destination=new JsonObject();destination.addProperty("x",target.x);destination.addProperty("y",target.y);destination.addProperty("z",target.z);destination.addProperty("yaw",yaw);
            destination.addProperty("dimension",DIMENSION.getValue().toString());destination.addProperty("destinationKind",destinationKind);
            destination.addProperty("piece",job.piece.getClass().getSimpleName());destination.add("anchor",posJson(job.anchor));
            completed++;releaseTickets();job=null;phase="complete";return;
        }
        if(job.candidateIndex>=job.candidates.size())retryCandidate("No verified connected original-floor room edge; no blocks were removed");
    }
    /** Reject enclosed cavities and wrong-side cave walls, retaining original arena bars. */
    private static boolean viewsOriginalRoom(ServerWorld world,ServerPlayerEntity player,BlockPos at,BlockPos anchor){
        var eye=Vec3d.ofBottomCenter(at).add(0,1.6,0);var target=Vec3d.ofCenter(anchor);
        var context=new RaycastContext(eye,target,RaycastContext.ShapeType.COLLIDER,RaycastContext.FluidHandling.NONE,player){
            @Override public VoxelShape getBlockShape(BlockState state,BlockView view,BlockPos pos){
                // Merely a visibility/door classification; no block or player collision is modified.
                if(state.isOf(Blocks.IRON_BARS)||state.isOf(Blocks.OAK_FENCE))return VoxelShapes.empty();
                return super.getBlockShape(state,view,pos);
            }
        };
        var hit=world.raycast(context);
        return hit.getType()==HitResult.Type.MISS||hit.getBlockPos().equals(anchor);
    }
    /** A safe exterior block beside a solid wall is not a verified doorway. */
    private static boolean doorwayConnects(ServerWorld world,BlockBox box,BlockPos outside){
        int x=MathHelper.clamp(outside.getX(),box.getMinX(),box.getMaxX());
        int z=MathHelper.clamp(outside.getZ(),box.getMinZ(),box.getMaxZ());
        // Corner diagonals cannot identify a doorway; use the actual room's flat side.
        if(x!=outside.getX()&&z!=outside.getZ())return false;
        var threshold=new BlockPos(x,outside.getY(),z);
        for(int y=0;y<2;y++){
            var state=world.getBlockState(threshold.up(y));
            // Minoshroom and Knight Phantom intentionally retain their original arena bars.
            if(!state.isAir()&&!state.isOf(Blocks.IRON_BARS)&&!state.isOf(Blocks.OAK_FENCE))return false;
        }
        int steps=outside.getManhattanDistance(threshold);
        if(steps>4)return false;
        var direction=new BlockPos(Integer.signum(x-outside.getX()),0,Integer.signum(z-outside.getZ()));
        for(int n=1;n<steps;n++){
            var step=outside.add(direction.getX()*n,0,direction.getZ()*n);
            if(!world.getBlockState(step).isAir()||!world.getBlockState(step.up()).isAir())return false;
        }
        return true;
    }
    private static boolean safe(ServerWorld world,ServerPlayerEntity player,BlockPos at){
        if(at.getY()<=world.getBottomY()||at.getY()+2>=world.getTopY()||!world.getWorldBorder().contains(at)||!world.isChunkLoaded(at))return false;
        if(!world.getBlockState(at).isAir()||!world.getBlockState(at.up()).isAir()||!world.getBlockState(at.down()).isSideSolidFullSquare(world,at.down(),Direction.UP))return false;
        if(!world.getFluidState(at.down()).isEmpty())return false;
        var floor=world.getBlockState(at.down());
        if(floor.isOf(Blocks.MAGMA_BLOCK)||floor.isOf(Blocks.CAMPFIRE)||floor.isOf(Blocks.SOUL_CAMPFIRE)||floor.isOf(Blocks.CACTUS))return false;
        var target=Vec3d.ofBottomCenter(at);var moved=player.getBoundingBox().offset(target.subtract(player.getPos()));
        return world.getWorldBorder().contains(moved)&&world.isSpaceEmpty(player,moved);
    }
    private static boolean floorCell(ServerWorld world,BlockPos at){
        if(!world.getWorldBorder().contains(at)||!world.isChunkLoaded(at))return false;
        return world.getBlockState(at).isAir()&&world.getBlockState(at.up()).isAir()
            &&world.getBlockState(at.down()).isSideSolidFullSquare(world,at.down(),Direction.UP)
            &&world.getFluidState(at.down()).isEmpty();
    }
    private static JsonObject posJson(BlockPos p){var out=new JsonObject();out.addProperty("x",p.getX());out.addProperty("y",p.getY());out.addProperty("z",p.getZ());return out;}
    /** Only changes a locate query center; never supplies guessed teleport coordinates. */
    static BlockPos queryOrigin(BlockPos origin,int index){
        if(index==0)return origin;
        if(index<0||index>=MAX_QUERY_CENTERS)throw new IllegalArgumentException("Search center exceeds bounded catalog");
        int[][] directions={{1,0},{-1,0},{0,1},{0,-1},{1,1},{-1,1},{1,-1},{-1,-1}};
        int scale=512*((index-1)/8+1);var direction=directions[(index-1)%8];
        return origin.add(direction[0]*scale,0,direction[1]*scale);
    }
    private static void retryCandidate(String reason){
        releaseTickets();
        var rejected=new JsonObject();rejected.addProperty("reason",reason);rejected.addProperty("candidate",job.candidateCount);
        if(job.located!=null)rejected.add("located",posJson(job.located));if(evidence!=null)rejected.add("evidence",evidence.deepCopy());rejectedCandidates.add(rejected);
        job.queryIndex++;job.radiusIndex=0;job.chunkIndex=0;job.missingChunks=0;
        job.located=null;job.anchor=null;job.originalMarker=null;job.start=null;job.piece=null;job.chunks=List.of();job.candidates=List.of();job.candidateIndex=0;job.spawnerScan=null;job.spawnerScanned=0;
        job.entityWaitStarted=-1;job.missingEntityChunks=0;job.entityWaitPolls=0;job.bossQueryCount=0;job.markerScanCompleted=false;
        job.connectedFloor.clear();job.floorFrontier.clear();evidence=null;phase="locating";
    }
    private static JsonObject boxJson(BlockBox b){var out=new JsonObject();out.addProperty("minX",b.getMinX());out.addProperty("minY",b.getMinY());out.addProperty("minZ",b.getMinZ());out.addProperty("maxX",b.getMaxX());out.addProperty("maxY",b.getMaxY());out.addProperty("maxZ",b.getMaxZ());return out;}
    private static void releaseTickets(){
        if(job==null)return;
        int count=job.tickets.size();
        for(var p:job.tickets)job.world.getChunkManager().removeTicket(TICKET,p,0,job.ticketId);
        job.tickets.clear();if(evidence!=null&&count>0)evidence.addProperty("releasedTickets",count);
    }
    private static void fail(Exception failure){error=failure.getClass().getSimpleName()+": "+failure.getMessage();releaseTickets();job=null;phase="failed";}
    private static void reset(MinecraftServer server){releaseTickets();serverIdentity=server;job=null;phase="idle";progressionDisabled=false;error="";destination=null;activation=null;evidence=null;rejectedCandidates=new JsonArray();}
    public static void close(){releaseTickets();job=null;serverIdentity=null;phase="idle";progressionDisabled=false;error="";destination=null;activation=null;evidence=null;rejectedCandidates=new JsonArray();report();}
    private static void report(){
        var out=new JsonObject();out.addProperty("busy",job!=null);out.addProperty("requestId",requestId);out.addProperty("completed",completed);out.addProperty("busyRequests",busyRequests);out.addProperty("boss",bossId);out.addProperty("phase",phase);out.addProperty("error",error);
        out.addProperty("progressionDisabled",progressionDisabled);out.addProperty("gamerule","tfEnforcedProgression");out.addProperty("version","4.8.754");
        out.addProperty("maxSearchRadiusChunks",128);out.addProperty("maxChunks",100);out.addProperty("timeoutTicks",2400);
        var boss=BOSSES.stream().filter(b->b.id.equals(bossId)).findFirst().orElse(null);
        if(boss!=null)out.addProperty("structureId","twilightforest:"+boss.structure);
        if(destination!=null)out.add("destination",destination.deepCopy());if(activation!=null)out.add("pedestalActivation",activation.deepCopy());
        if(evidence!=null)out.add("evidence",evidence.deepCopy());
        out.add("rejectedCandidates",rejectedCandidates.deepCopy());out.addProperty("maxCandidateStructures",MAX_CANDIDATES);out.addProperty("maxQueryCenters",MAX_QUERY_CENTERS);
        if(job!=null){out.addProperty("chunksScheduled",job.chunkIndex);out.addProperty("chunksTotal",job.chunks.size());out.addProperty("missingChunks",job.missingChunks);out.addProperty("ownedTickets",job.tickets.size());out.addProperty("candidateStructures",job.candidateCount);out.addProperty("queryIndex",job.queryIndex);if(job.queryIndex<MAX_QUERY_CENTERS)out.add("queryOrigin",posJson(queryOrigin(job.origin,job.queryIndex)));if(job.located!=null)out.add("located",posJson(job.located));if(job.anchor!=null)out.add("anchor",posJson(job.anchor));}
        var catalog=new JsonArray();for(var b:BOSSES){var item=new JsonObject();item.addProperty("id",b.id);item.addProperty("structureId","twilightforest:"+b.structure);item.addProperty("implemented",true);catalog.add(item);}out.add("catalog",catalog);
        out.addProperty("finalCastleBossImplemented",false);status=out.toString();
    }
    private TwilightBossTravel(){}
}
