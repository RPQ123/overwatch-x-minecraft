package lab.owmcguest;

import java.util.*;
import java.util.concurrent.CompletableFuture;
import java.util.stream.Stream;
import net.minecraft.entity.Entity;
import net.minecraft.server.world.ChunkLevelType;
import net.minecraft.server.world.ServerEntityManager;
import net.minecraft.util.math.BlockBox;
import net.minecraft.util.math.BlockPos;
import net.minecraft.util.math.Box;
import net.minecraft.util.math.ChunkPos;
import net.minecraft.world.entity.EntityChangeListener;
import net.minecraft.world.entity.EntityHandler;
import net.minecraft.world.entity.EntityLike;
import net.minecraft.world.storage.ChunkDataAccess;
import net.minecraft.world.storage.ChunkDataList;

/** Geometry and actual vanilla entity-manager fixtures; neither is in-game travel acceptance. */
public final class TwilightBossTravelCheck {
    public static void main(String[] args){
        var room=new BlockBox(100,30,-200,115,35,-185);
        var anchor=new BlockPos(107,32,-193);
        var first=TwilightBossTravel.floorCandidates(room,anchor,"minoshroom");
        check(!first.isEmpty(),"real room perimeter has candidates");
        check(first.size()==new HashSet<>(first).size(),"candidate positions deduplicated");
        check(first.stream().allMatch(p->p.getY()==31),"Minoshroom stays on original local1 walking layer");
        check(first.stream().allMatch(p->p.getX()>=97&&p.getX()<=118&&p.getZ()>=-203&&p.getZ()<=-182),"no unrelated coordinate guess");
        check(room.contains(first.getFirst()),"actual interior floor edge considered before exterior cornices");
        var shifted=new BlockBox(1100,50,1800,1115,55,1815);
        var moved=TwilightBossTravel.floorCandidates(shifted,anchor.add(1000,20,2000),"minoshroom");
        check(moved.size()==first.size(),"translation keeps count");
        for(int i=0;i<first.size();i++)check(moved.get(i).equals(first.get(i).add(1000,20,2000)),"all candidates follow actual translated room");
        var high=new BlockBox(0,70,0,18,170,18);
        var top=TwilightBossTravel.floorCandidates(high,new BlockPos(9,169,9),"ur_ghast");
        check(top.stream().allMatch(p->p.getY()==166),"Ur-Ghast visits exact original top floor, not lower floor");
        var naga=TwilightBossTravel.floorCandidates(new BlockBox(-270,2,-14,-226,12,30),new BlockPos(-248,5,8),"naga");
        check(naga.stream().allMatch(p->p.getY()==4),"actual failed Naga underground y0 never considered");
        check(TwilightBossTravel.floorFeetY(new BlockBox(-268,76,-264,-238,87,-234),"lich")==80,"actual Lich template local3 support means feet80, not75");
        check(TwilightBossTravel.floorFeetY(new BlockBox(-538,0,-522,-470,17,-454),"hydra")==0,"actual Hydra floor0, not underground-2");
        check(TwilightBossTravel.floorFeetY(new BlockBox(-314,1,246,-246,19,314),"alpha_yeti")==1,"actual Yeti cave layer1, not underground-1");
        check(TwilightBossTravel.floorFeetY(new BlockBox(-466,140,290,-452,180,304),"snow_queen")==171,"actual Snow Queen top room floor171, not packed-ice pocket168");
        check(TwilightBossTravel.templateSpawnerCandidates("twilightforest:courtyard/spawner",new BlockBox(-248,4,8,-248,5,8)).equals(List.of(new BlockPos(-248,5,8))),"actual first-failed saved Naga template resolves original block");
        check(TwilightBossTravel.templateSpawnerCandidates("twilightforest:courtyard/pathway",new BlockBox(-248,4,8,-248,5,8)).isEmpty(),"unrelated template never becomes spawner");
        check(TwilightBossTravel.templateSpawnerCandidates("twilightforest:courtyard/spawner",new BlockBox(-248,4,8,-247,5,8)).isEmpty(),"changed original template dimensions rejected");
        check(TwilightBossTravel.templateSpawnerCandidates("twilightforest:lich_tower/tower_boss_room",new BlockBox(100,80,200,130,91,230)).equals(List.of(new BlockPos(115,85,215))),"actual Lich template centered marker rotates invariantly");
        var origins=new HashSet<BlockPos>();for(int i=0;i<17;i++)origins.add(TwilightBossTravel.queryOrigin(new BlockPos(14,3,-9),i));
        check(origins.size()==17,"all bounded locate query centers are unique");
        check(origins.stream().allMatch(p->p.getY()==3&&Math.abs(p.getX()-14)<=1024&&Math.abs(p.getZ()+9)<=1024),"query centers preserve actual starting height and bounds; not destinations");
        checkOriginalEntityReadiness();
        System.out.println("TwilightBossTravel geometry and vanilla asynchronous entity readiness passed");
    }
    private static void checkOriginalEntityReadiness(){
        var access=new DeferredEntities();var handler=new TrackedEntities();
        var manager=new ServerEntityManager<>(StoredEntity.class,handler,access);
        var chunk=new ChunkPos(-16,0);var entity=new StoredEntity(7301,UUID.randomUUID(),new BlockPos(-248,4,8));
        manager.updateTrackingStatus(chunk,ChunkLevelType.FULL);
        check(access.reads==1,"FULL33 already requests original entity data without an entity-ticking lease");
        check(!manager.isLoaded(chunk.toLong()),"terrain FULL must not be mistaken for completed entity I/O");
        check(manager.getLookup().get(entity.getUuid())==null,"pending original entity is not queryable yet");
        access.pending.complete(new ChunkDataList<>(chunk,List.of(entity)));
        check(!manager.isLoaded(chunk.toLong()),"completed I/O still waits for vanilla entityManagement tick");
        manager.tick();
        check(manager.isLoaded(chunk.toLong()),"actual LOADED acknowledgement follows queue consumption");
        check(manager.getLookup().get(entity.getUuid())==entity,"the original stored identity is now queryable");
        check(handler.tracked==1&&handler.ticking==0,"FULL tracks original entities without forcing their AI to tick");
        manager.updateTrackingStatus(chunk,ChunkLevelType.INACCESSIBLE);manager.tick();
        check(!manager.isLoaded(chunk.toLong()),"released/unloaded entity chunk loses its LOADED acknowledgement");
        check(manager.getLookup().get(entity.getUuid())==null,"unloaded original identity is absent from live query");
        manager.updateTrackingStatus(chunk,ChunkLevelType.FULL);
        check(access.reads==2&&!manager.isLoaded(chunk.toLong()),"revisit must await a new asynchronous entity read");
        var restored=new StoredEntity(entity.getId(),entity.getUuid(),entity.getBlockPos());
        access.pending.complete(new ChunkDataList<>(chunk,List.of(restored)));manager.tick();
        check(manager.isLoaded(chunk.toLong())&&manager.getLookup().get(entity.getUuid())==restored,"revisit resolves the persisted original identity without spawning a replacement");
    }
    private static final class DeferredEntities implements ChunkDataAccess<StoredEntity>{
        int reads;CompletableFuture<ChunkDataList<StoredEntity>> pending;
        public CompletableFuture<ChunkDataList<StoredEntity>> readChunkData(ChunkPos pos){reads++;pending=new CompletableFuture<>();return pending;}
        public void writeChunkData(ChunkDataList<StoredEntity> data){}
        public void awaitAll(boolean sync){}
    }
    private static final class TrackedEntities implements EntityHandler<StoredEntity>{
        int tracked,ticking;
        public void create(StoredEntity entity){}
        public void destroy(StoredEntity entity){}
        public void startTicking(StoredEntity entity){ticking++;}
        public void stopTicking(StoredEntity entity){ticking--;}
        public void startTracking(StoredEntity entity){tracked++;}
        public void stopTracking(StoredEntity entity){tracked--;}
        public void updateLoadStatus(StoredEntity entity){}
    }
    private static final class StoredEntity implements EntityLike{
        final int id;final UUID uuid;final BlockPos pos;EntityChangeListener listener=EntityChangeListener.NONE;
        StoredEntity(int id,UUID uuid,BlockPos pos){this.id=id;this.uuid=uuid;this.pos=pos;}
        public int getId(){return id;}
        public UUID getUuid(){return uuid;}
        public BlockPos getBlockPos(){return pos;}
        public Box getBoundingBox(){return new Box(pos);}
        public void setChangeListener(EntityChangeListener listener){this.listener=listener;}
        public Stream<StoredEntity> streamSelfAndPassengers(){return Stream.of(this);}
        public Stream<StoredEntity> streamPassengersAndSelf(){return Stream.of(this);}
        public void setRemoved(Entity.RemovalReason reason){listener.remove(reason);}
        public boolean shouldSave(){return true;}
        public boolean isPlayer(){return false;}
    }
    private static void check(boolean value,String message){if(!value)throw new AssertionError(message);}
}
