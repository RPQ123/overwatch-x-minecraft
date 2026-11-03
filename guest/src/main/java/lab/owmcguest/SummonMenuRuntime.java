package lab.owmcguest;

import com.google.gson.JsonObject;
import java.util.*;
import java.util.function.BooleanSupplier;
import net.minecraft.entity.*;
import net.minecraft.entity.mob.MobEntity;
import net.minecraft.entity.mob.Monster;
import net.minecraft.entity.mob.Angerable;
import net.minecraft.entity.ai.RangedAttackMob;
import net.minecraft.entity.attribute.EntityAttributes;
import net.minecraft.registry.Registries;
import net.minecraft.server.MinecraftServer;
import net.minecraft.server.network.ServerPlayerEntity;
import net.minecraft.util.Identifier;
import net.minecraft.util.math.*;

/** Explicit MC creative adaptation. No command strings, NBT or new network packet. */
public final class SummonMenuRuntime {
    public record Entry(String id,String translationKey){}
    public record Result(long request,boolean success,int spawned,String error){}
    private static long requests,completed,spawned,randomRequests,randomSpawned;
    public static volatile String status="{}";
    private SummonMenuRuntime(){}
    private static ServerPlayerEntity player(MinecraftServer server,UUID owner,long world,BooleanSupplier fresh){
        var p=server.getPlayerManager().getPlayer(owner);
        if(!server.isOnThread()||!server.isSingleplayer()||p==null||!p.isAlive()||!SurvivalRuntime.permitted(p)
            ||NativeWorldIdentity.of(server,p.getWorld().getRegistryKey())!=world||!fresh.getAsBoolean())
            throw new IllegalStateException("menu.owmcguest.summon.denied");
        return p;
    }
    /** Snapshot from the server registry, including mod entities; constructors run only on the server. */
    public static List<Entry> catalog(MinecraftServer server,UUID owner,long world,BooleanSupplier fresh){
        var p=player(server,owner,world,fresh);var entries=new ArrayList<Entry>();
        for(var type:Registries.ENTITY_TYPE){
            if(!type.isSummonable())continue;
            try(var ignored=SummonSpawnScope.probe()){
                // SpawnGroup.MISC also contains real mobs (golems, bosses). Do not use it as a filter.
                var probe=type.create(p.getServerWorld());
                if(probe instanceof LivingEntity)entries.add(new Entry(Registries.ENTITY_TYPE.getId(type).toString(),type.getTranslationKey()));
                if(probe!=null)probe.discard();
            }catch(RuntimeException ignored){/* This installed type cannot be constructed here. */}
        }
        player(server,owner,world,fresh);
        entries.sort(Comparator.comparing(Entry::id));return List.copyOf(entries);
    }
    private record RandomPool(List<String> ids,int bossRejected){}
    private static RandomPool randomPool(MinecraftServer server,UUID owner,long world,BooleanSupplier fresh){
        var p=player(server,owner,world,fresh);var candidates=new ArrayList<String>();int rejected=0;
        for(var type:Registries.ENTITY_TYPE){
            String id=Registries.ENTITY_TYPE.getId(type).toString();
            if(!type.isSummonable())continue;
            if(RandomSummonPolicy.blacklisted(id)){rejected++;continue;}
            if(!RandomSummonPolicy.fits(type.getWidth(),type.getHeight(),type.getWidth()))continue;
            Entity probe=null;
            try(var ignored=SummonSpawnScope.probe()){
                probe=type.create(p.getServerWorld());if(!(probe instanceof MobEntity mob))continue;
                if(SummonSpawnScope.hasBossBar(mob)){rejected++;continue;}
                var damage=mob.getAttributeInstance(EntityAttributes.GENERIC_ATTACK_DAMAGE);var box=mob.getBoundingBox();
                if(RandomSummonPolicy.combatant(id,type.getSpawnGroup()==SpawnGroup.MONSTER,mob instanceof Monster,mob instanceof Angerable,mob instanceof RangedAttackMob,damage==null?0:damage.getValue())
                    &&RandomSummonPolicy.fits(box.getLengthX(),box.getLengthY(),box.getLengthZ()))candidates.add(id);
            }catch(RuntimeException|LinkageError ignored){/* Uninspectable/unconstructable types fail closed. */}
            finally{if(probe!=null)SummonSpawnScope.discardSilently(probe,p.getServerWorld());}
        }
        player(server,owner,world,fresh);return new RandomPool(List.copyOf(candidates),rejected);
    }
    /** Shared single/random placement. No entity enters the world until every check passes. */
    private static String spawnOne(MinecraftServer server,UUID owner,long world,String selected,boolean random,BooleanSupplier fresh){
        return spawnOne(server,owner,world,selected,random,fresh,null);
    }
    private static String spawnOne(MinecraftServer server,UUID owner,long world,String selected,boolean random,BooleanSupplier fresh,
                                   java.util.function.Consumer<Entity> customize){
        var p=player(server,owner,world,fresh);var w=p.getServerWorld();Identifier id=Identifier.tryParse(selected);
        if(id==null||!Registries.ENTITY_TYPE.containsId(id))throw new IllegalStateException("menu.owmcguest.summon.unknown");
        var type=Registries.ENTITY_TYPE.get(id);
        if(!type.isSummonable())throw new IllegalStateException("menu.owmcguest.summon.unknown");
        Entity entity;try(var ignored=SummonSpawnScope.probe()){entity=type.create(w);}
        if(!(entity instanceof LivingEntity living)){if(entity!=null)entity.discard();throw new IllegalStateException("menu.owmcguest.summon.unknown");}
        boolean placed=false;
        try{
            if(random&&SummonSpawnScope.hasBossBar(living))throw new IllegalStateException("menu.owmcguest.summon.random_boss");
            try(var ignored=SummonSpawnScope.probe()){
                if(entity instanceof MobEntity mob)mob.initialize(w,w.getLocalDifficulty(p.getBlockPos()),SpawnReason.COMMAND,null);
            }
            if(customize!=null)customize.accept(entity);
            // A lazy custom bar or a larger variant may be created during initialization.
            if(random&&SummonSpawnScope.hasBossBar(living))throw new IllegalStateException("menu.owmcguest.summon.random_boss");
            var forward=p.getRotationVec(1f);forward=new Vec3d(forward.x,0,forward.z).normalize();
            if(forward.lengthSquared()<.5)forward=new Vec3d(0,0,1);
            var side=new Vec3d(-forward.z,0,forward.x);
            for(int distance=6;distance<=14;distance+=2)for(int offset:new int[]{0,-3,3}){
                var center=p.getPos().add(forward.multiply(distance)).add(side.multiply(offset));
                for(int dy=3;dy>=-6;dy--){
                    var at=BlockPos.ofFloored(center).up(dy);
                    entity.refreshPositionAndAngles(at.getX()+.5,at.getY(),at.getZ()+.5,p.getYaw()+180,0);
                    var box=entity.getBoundingBox();
                    if(random&&!RandomSummonPolicy.fits(box.getLengthX(),box.getLengthY(),box.getLengthZ()))throw new IllegalStateException("menu.owmcguest.summon.random_large");
                    if(!Double.isFinite(box.getAverageSideLength())||box.getLengthX()>128||box.getLengthZ()>128||box.getLengthY()>256)throw new IllegalStateException("menu.owmcguest.summon.no_space");
                    if(box.minY<w.getBottomY()||box.maxY>=w.getTopY()||!w.getWorldBorder().contains(box)||box.intersects(p.getBoundingBox()))continue;
                    boolean loaded=true;
                    for(int x=MathHelper.floor(box.minX)>>4;x<=MathHelper.floor(box.maxX)>>4;x++)for(int z=MathHelper.floor(box.minZ)>>4;z<=MathHelper.floor(box.maxZ)>>4;z++)
                        if(!w.isChunkLoaded(new BlockPos(x<<4,at.getY(),z<<4)))loaded=false;
                    if(!loaded||!w.isSpaceEmpty(entity,box)||!w.canPlayerModifyAt(p,at))continue;
                    if(!w.getOtherEntities(entity,box,e->e instanceof LivingEntity&&!e.isRemoved()).isEmpty())continue;
                    if(!w.getBlockState(at.down()).isSolidBlock(w,at.down())&&w.getFluidState(at).isEmpty()&&dy!=0)continue;
                    player(server,owner,world,fresh);
                    if(entity instanceof MobEntity mob)mob.setPersistent();
                    // Direct path is also guarded when the common batch/fixture Mixin awaits integration.
                    if(!SummonSpawnScope.beforeSpawn(w,entity))throw new IllegalStateException("menu.owmcguest.summon.random_boss");
                    if(!w.spawnEntity(entity))throw new IllegalStateException("menu.owmcguest.summon.rejected");
                    placed=true;return id.toString();
                }
            }
            throw new IllegalStateException("menu.owmcguest.summon.no_space");
        }finally{if(!placed)SummonSpawnScope.discardSilently(entity,w);}
    }
    public static Result summon(MinecraftServer server,UUID owner,long world,String selection,BooleanSupplier fresh){
        long request=++requests;int count=0,candidates=0,bossRejected=0,rejectedSlots=0,attempts=0;String error="";boolean success=false;
        var resolved=new ArrayList<String>();boolean random=RandomSummonPolicy.SELECTION.equals(selection);if(random)randomRequests++;
        try(var scope=new SummonSpawnScope(server,random)){
            var p=player(server,owner,world,fresh);
            if(!selection.equals("test:cleanup")&&!(p.getServerWorld() instanceof F9SummonAccess))throw new IllegalStateException("menu.owmcguest.summon.integration_required");
            if(selection.equals("batch:cats")){
                // 用户要求：一批所有不同颜色的猫；第一只命名“老吴”以触发老吴模组效果。
                var variants=Registries.CAT_VARIANT.streamEntries().toList();boolean first=true;
                for(var variant:variants){
                    final boolean laowu=first;first=false;
                    try{resolved.add(spawnOne(server,owner,world,"minecraft:cat",false,fresh,e->{
                        if(e instanceof net.minecraft.entity.passive.CatEntity cat){cat.setVariant(variant);
                            if(laowu)cat.setCustomName(net.minecraft.text.Text.literal("老吴"));}}));count++;}
                    catch(RuntimeException failure){error=failure.getMessage()==null?"menu.owmcguest.summon.rejected":failure.getMessage();}
                }
                if(count==0)throw new IllegalStateException(error.isEmpty()?"menu.owmcguest.summon.no_space":error);
                error="";
            }else if(selection.equals("batch:animals8")){
                // 用户要求：随机原版动物 ×8。
                var pool=new ArrayList<String>();
                for(var type:Registries.ENTITY_TYPE){
                    var id=Registries.ENTITY_TYPE.getId(type);if(!id.getNamespace().equals("minecraft")||!type.isSummonable())continue;
                    Entity probe=null;
                    try(var ignored=SummonSpawnScope.probe()){probe=type.create(p.getServerWorld());
                        if(probe instanceof net.minecraft.entity.passive.AnimalEntity)pool.add(id.toString());}
                    catch(RuntimeException|LinkageError ignored){}
                    finally{if(probe!=null)SummonSpawnScope.discardSilently(probe,p.getServerWorld());}
                }
                if(pool.isEmpty())throw new IllegalStateException("menu.owmcguest.summon.random_empty");
                while(attempts<32&&count<8){
                    attempts++;String selected=pool.get(p.getRandom().nextInt(pool.size()));
                    try{resolved.add(spawnOne(server,owner,world,selected,false,fresh));count++;}catch(RuntimeException ignored){}
                }
                if(count==0)throw new IllegalStateException("menu.owmcguest.summon.no_space");
            }else if(selection.equals("batch:random8")){
                PlayerUtilities.spawnBatch(server,owner);
                var receipt=com.google.gson.JsonParser.parseString(PlayerUtilities.status).getAsJsonObject();
                count=receipt.get("lastBatch").getAsInt();
                if(count==0)throw new IllegalStateException("menu.owmcguest.summon.no_space");
            }else if(selection.startsWith("test:")){
                if(!Boolean.getBoolean("owmc.twilightTrial")||!System.getProperty("owmc.worldName","").startsWith("Overwatch Twilight Switch "))
                    throw new IllegalStateException("menu.owmcguest.summon.test_denied");
                var eye=p.getEyePos();var direction=p.getRotationVec(1f);
                switch(selection){
                    case "test:crowd"->NativeCombatScene.deadeyeCrowd(server,owner,eye,direction);
                    case "test:beam"->NativeCombatScene.beam(server,owner,eye,direction);
                    case "test:mei"->NativeCombatScene.meiLab(server,owner,direction);
                    case "test:enderman"->NativeCombatScene.enderman(server,owner,eye,direction,false);
                    case "test:far"->NativeCombatScene.start(server,owner,eye,direction,16);
                    case "test:cleanup"->NativeCombatScene.cleanup();
                    default->throw new IllegalStateException("menu.owmcguest.summon.unknown");
                }
                var receipt=new JsonObject();NativeCombatScene.addStatus(server,receipt);
                if(!selection.equals("test:cleanup")&&receipt.has("testError")&&!receipt.get("testError").getAsString().isBlank())throw new IllegalStateException(receipt.get("testError").getAsString());
                if(receipt.has("beamTargets"))count=receipt.getAsJsonObject("beamTargets").size();
                else if(receipt.has("targetAlive")&&receipt.get("targetAlive").getAsBoolean())count=1;
            }else if(random){
                var pool=randomPool(server,owner,world,fresh);candidates=pool.ids().size();bossRejected=pool.bossRejected();
                if(candidates==0)throw new IllegalStateException("menu.owmcguest.summon.random_empty");
                var remaining=new ArrayList<>(pool.ids());String lastError="menu.owmcguest.summon.no_space";
                while(attempts<RandomSummonPolicy.MAX_ATTEMPTS&&count<RandomSummonPolicy.BATCH_SIZE&&!remaining.isEmpty()){
                    player(server,owner,world,fresh);
                    attempts++;String selected=RandomSummonPolicy.choose(remaining,p.getRandom()::nextInt);
                    try{resolved.add(spawnOne(server,owner,world,selected,true,fresh));count++;}
                    catch(RuntimeException failure){
                        lastError=failure.getMessage()==null?"menu.owmcguest.summon.rejected":failure.getMessage();
                        if(lastError.equals("menu.owmcguest.summon.random_boss"))rejectedSlots++;
                        remaining.remove(selected); // Do not repeatedly initialize a rejected type.
                    }
                }
                if(count<RandomSummonPolicy.BATCH_SIZE)throw new IllegalStateException(count==0?lastError:"menu.owmcguest.summon.random_partial");
            }else{resolved.add(spawnOne(server,owner,world,selection,false,fresh));count=1;}
            success=true;completed++;
        }catch(RuntimeException failure){error=failure.getMessage()==null?failure.getClass().getSimpleName():failure.getMessage();}
        spawned+=count;if(random)randomSpawned+=count;
        var out=new JsonObject();out.addProperty("requests",requests);out.addProperty("completed",completed);out.addProperty("spawned",spawned);
        out.addProperty("lastCount",count);out.addProperty("selection",selection);out.addProperty("error",error);
        out.addProperty("randomRequests",randomRequests);out.addProperty("randomSpawned",randomSpawned);out.addProperty("randomCandidates",candidates);out.addProperty("bossBarRejectedTypes",bossRejected);
        out.addProperty("bossBarRejectedSlots",rejectedSlots);out.addProperty("randomAttempts",attempts);
        out.addProperty("requestedCount",random?RandomSummonPolicy.BATCH_SIZE:selection.equals("batch:random8")||selection.equals("batch:animals8")?8:selection.equals("batch:cats")?Registries.CAT_VARIANT.size():1);
        out.addProperty("resolvedEntity",resolved.isEmpty()?"":resolved.getLast());out.add("resolvedEntities",new com.google.gson.Gson().toJsonTree(resolved));
        out.add("lifecycle",SummonedMobLifecycle.diagnostics());status=out.toString();return new Result(request,success,count,error);
    }
}
