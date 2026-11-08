package lab.owmcguest;

import java.util.*;
import net.minecraft.entity.EntityType;
import net.minecraft.entity.LivingEntity;
import net.minecraft.server.MinecraftServer;
import net.minecraft.server.network.ServerPlayerEntity;
import net.minecraft.util.math.Vec3d;

/** 隔离存档的普通 MC 场景；不调用任何 cast/hammer/Core/资源入账接口。 */
public final class NativeBuildersLab {
    private static final List<LivingEntity> mobs=new ArrayList<>();
    private static final Map<net.minecraft.util.math.BlockPos,net.minecraft.block.BlockState> growthRoof=new LinkedHashMap<>();
    private static net.minecraft.server.world.ServerWorld roofWorld;
    public static volatile String packRecipientStatus="{}";
    private record Respawn(UUID owner,long world,int after,net.minecraft.server.world.ServerWorld fixtureWorld,boolean keepInventory){}
    private static Respawn pendingRespawn;
    static{net.fabricmc.fabric.api.event.lifecycle.v1.ServerTickEvents.END_SERVER_TICK.register(server->{
        publishRecipient();
        var pending=pendingRespawn;if(pending==null)return;var p=server.getPlayerManager().getPlayer(pending.owner());
        if(p==null||!allowed(p)||NativeWorldIdentity.of(server,p.getWorld().getRegistryKey())!=pending.world()){finishRespawn(pending);return;}
        if(p.isAlive()){finishRespawn(pending);return;}
        if(server.getTicks()>=pending.after()){
            try{server.getPlayerManager().respawnPlayer(p,false,net.minecraft.entity.Entity.RemovalReason.KILLED);}finally{finishRespawn(pending);}
        }
    });}
    private static void finishRespawn(Respawn pending){
        pending.fixtureWorld().getGameRules().get(net.minecraft.world.GameRules.KEEP_INVENTORY).set(pending.keepInventory(),pending.fixtureWorld().getServer());
        if(pendingRespawn==pending)pendingRespawn=null;
    }
    public static boolean allowed(ServerPlayerEntity p){return p!=null&&p.isCreative()&&Boolean.getBoolean("owmc.twilightTrial")
        &&System.getProperty("owmc.worldName","").startsWith("Overwatch Twilight Switch ");}
    public static void action(MinecraftServer server,UUID owner,Vec3d forward,String name){
        var p=server.getPlayerManager().getPlayer(owner);if(!allowed(p))throw new IllegalStateException("builders fixture requires isolated creative Switch lab");
        switch(name){
            case "muzzle-native-reference"->MuzzlePresentation.nativeReferenceOnly=true;
            case "muzzle-visual-restore"->MuzzlePresentation.nativeReferenceOnly=false;
            case "torb-scrap-lab"->{
                cleanup();NativeCombatScene.groundLab(server,owner);var at=p.getPos().add(forward.multiply(1,0,1).normalize().multiply(1.1));
                for(int i=0;i<2;i++){var mob=EntityType.HUSK.create(p.getServerWorld());if(mob==null)throw new IllegalStateException("fixture entity unavailable");
                    mob.refreshPositionAndAngles(at.x,at.y,at.z,0,0);if(!p.getServerWorld().isSpaceEmpty(mob,mob.getBoundingBox()))throw new IllegalStateException("occupied fixture");
                    mob.setAiDisabled(true);mob.setNoGravity(true);mob.setSilent(true);mob.setPersistent();mob.setHealth(1);mob.addCommandTag("owmc-builders-fixture");
                    if(!p.getServerWorld().spawnEntity(mob))throw new IllegalStateException("fixture spawn failed");mobs.add(mob);}
            }
            case "torb-repair-lab"->NativeTorbjornRuntime.injureForTest(server,owner);
            case "torb-tracking-lab"->{
                cleanup();var direction=forward.multiply(1,0,1).normalize();var side=new Vec3d(-direction.z,0,direction.x);
                for(int i=0;i<2;i++){var at=p.getPos().add(direction.multiply(6+i*3)).add(side.multiply(i==0?-1:2));
                    var mob=EntityType.HUSK.create(p.getServerWorld());if(mob==null)throw new IllegalStateException("tracking mob unavailable");
                    mob.refreshPositionAndAngles(at.x,at.y,at.z,0,0);if(!p.getServerWorld().isSpaceEmpty(mob,mob.getBoundingBox()))throw new IllegalStateException("tracking volume occupied");
                    mob.setAiDisabled(true);mob.setNoGravity(true);mob.setSilent(true);mob.setPersistent();
                    mob.getAttributeInstance(net.minecraft.entity.attribute.EntityAttributes.GENERIC_MAX_HEALTH).setBaseValue(20);mob.setHealth(20);
                    mob.addCommandTag("owmc-builders-fixture");if(!p.getServerWorld().spawnEntity(mob))throw new IllegalStateException("tracking spawn failed");mobs.add(mob);}
            }
            case "torb-targets-cleanup"->cleanup();
            case "torb-core-target"->{
                cleanup();var at=p.getPos().add(forward.multiply(1,0,1).normalize().multiply(6));var mob=EntityType.HUSK.create(p.getServerWorld());
                if(mob==null)throw new IllegalStateException("fixture entity unavailable");mob.refreshPositionAndAngles(at.x,at.y,at.z,0,0);
                if(!p.getServerWorld().isSpaceEmpty(mob,mob.getBoundingBox()))throw new IllegalStateException("occupied Core target");
                mob.setAiDisabled(true);mob.setNoGravity(true);mob.setSilent(true);mob.setPersistent();mob.getAttributeInstance(net.minecraft.entity.attribute.EntityAttributes.GENERIC_MAX_HEALTH).setBaseValue(100);mob.setHealth(100);
                mob.addCommandTag("owmc-builders-fixture");if(!p.getServerWorld().spawnEntity(mob))throw new IllegalStateException("fixture spawn failed");mobs.add(mob);
            }
            case "torb-approach-lab"->NativeTorbjornRuntime.approachForTest(server,owner,forward);
            case "torb-pack-lab"->NativeTorbjornRuntime.packForTest(server,owner);
            case "torb-pack-recipient-lab","torb-pack-monster-lab","torb-pack-animal-lab","torb-pack-hero-lab","torb-pack-cage-lab"->{
                var at=NativeTorbjornRuntime.packPositionForTest(server,owner);LivingEntity ally=switch(name){
                    case "torb-pack-monster-lab","torb-pack-cage-lab"->EntityType.HUSK.create(p.getServerWorld());
                    case "torb-pack-animal-lab"->EntityType.COW.create(p.getServerWorld());
                    case "torb-pack-hero-lab"->{var npc=HeroNpcEntity.TYPE.create(p.getServerWorld());if(npc!=null)npc.configure(0,owner);yield npc;}
                    default->EntityType.VILLAGER.create(p.getServerWorld());
                };
                if(ally==null)throw new IllegalStateException("pack recipient unavailable");boolean placed=false;
                for(var offset:List.of(new Vec3d(.8,.05,0),new Vec3d(-.8,.05,0),new Vec3d(0,.05,.8),new Vec3d(0,.05,-.8))){
                    var pos=at.add(offset);ally.refreshPositionAndAngles(pos.x,pos.y,pos.z,0,0);
                    if(p.getServerWorld().isSpaceEmpty(ally,ally.getBoundingBox())){placed=true;break;}
                }
                if(!placed){ally.discard();throw new IllegalStateException("occupied pack recipient fixture");}
                if(ally instanceof net.minecraft.entity.mob.MobEntity mob){mob.setAiDisabled(true);mob.setPersistent();}
                ally.setNoGravity(true);ally.setSilent(true);ally.addCommandTag("owmc-builders-fixture");
                if(!p.getServerWorld().spawnEntity(ally))throw new IllegalStateException("pack recipient spawn failed");mobs.add(ally);
                NativeTorbjornRuntime.packTestRecipient=ally.getUuidAsString();
                if(name.equals("torb-pack-cage-lab"))makeGrowthRoof(p.getServerWorld(),at);
            }
            case "torb-growth-clearance"->restoreGrowthRoof();
            case "junk-death-lab"->{
                if(!p.isAlive()||pendingRespawn!=null)throw new IllegalStateException("death fixture already active");
                var rule=p.getServerWorld().getGameRules().get(net.minecraft.world.GameRules.KEEP_INVENTORY);boolean before=rule.get();
                // 不依赖死亡后仍存在的原版相机/HTTP pose：80tick兜底晚于炸弹50tick引信。
                var pending=new Respawn(owner,NativeWorldIdentity.of(server,p.getWorld().getRegistryKey()),server.getTicks()+80,p.getServerWorld(),before);pendingRespawn=pending;
                // respawnPlayer.copyFrom 同样读取 keepInventory，必须保留到复制背包完成才恢复规则。
                try{rule.set(true,server);p.damage(p.getDamageSources().genericKill(),Float.MAX_VALUE);if(p.isAlive())finishRespawn(pending);}
                catch(RuntimeException error){finishRespawn(pending);throw error;}
            }
            case "junk-respawn-lab"->{
                var pending=pendingRespawn;
                try{if(!p.isAlive())server.getPlayerManager().respawnPlayer(p,false,net.minecraft.entity.Entity.RemovalReason.KILLED);}
                finally{if(pending!=null)finishRespawn(pending);}
            }
            default->throw new IllegalArgumentException(name);
        }
    }
    public static void cleanup(){
        restoreGrowthRoof();
        var pending=pendingRespawn;
        if(pending!=null){var server=pending.fixtureWorld().getServer();var p=server.getPlayerManager().getPlayer(pending.owner());
            try{if(p!=null&&allowed(p)&&!p.isAlive()&&NativeWorldIdentity.of(server,p.getWorld().getRegistryKey())==pending.world())
                server.getPlayerManager().respawnPlayer(p,false,net.minecraft.entity.Entity.RemovalReason.KILLED);}
            finally{finishRespawn(pending);}
        }
        for(var mob:mobs)if(!mob.isRemoved())mob.discard();mobs.clear();NativeTorbjornRuntime.packTestRecipient="";
    }
    private static void makeGrowthRoof(net.minecraft.server.world.ServerWorld world,Vec3d at){
        restoreGrowthRoof();var centre=net.minecraft.util.math.BlockPos.ofFloored(at).up(3);
        for(int x=-4;x<=4;x++)for(int z=-4;z<=4;z++)if(!world.getBlockState(centre.add(x,0,z)).isAir())throw new IllegalStateException("occupied growth safety room");
        roofWorld=world;for(int x=-4;x<=4;x++)for(int z=-4;z<=4;z++){var pos=centre.add(x,0,z);growthRoof.put(pos,world.getBlockState(pos));world.setBlockState(pos,net.minecraft.block.Blocks.GLASS.getDefaultState());}
    }
    private static void restoreGrowthRoof(){
        if(roofWorld!=null)for(var entry:growthRoof.entrySet())if(roofWorld.getBlockState(entry.getKey()).isOf(net.minecraft.block.Blocks.GLASS))roofWorld.setBlockState(entry.getKey(),entry.getValue());
        growthRoof.clear();roofWorld=null;
    }
    private static void publishRecipient(){
        var out=new com.google.gson.JsonObject();
        for(var e:mobs)if(!e.isRemoved()&&e.getUuidAsString().equals(NativeTorbjornRuntime.packTestRecipient)){
            out.addProperty("id",e.getUuidAsString());out.addProperty("entityId",e.getId());out.addProperty("type",net.minecraft.registry.Registries.ENTITY_TYPE.getId(e.getType()).toString());
            out.addProperty("scale",e.getAttributeValue(net.minecraft.entity.attribute.EntityAttributes.GENERIC_SCALE));out.addProperty("width",e.getBoundingBox().getLengthX());out.addProperty("height",e.getBoundingBox().getLengthY());out.addProperty("absorption",e.getAbsorptionAmount());
            out.addProperty("inBlocks",e.getWorld().getBlockCollisions(e,e.getBoundingBox()).iterator().hasNext());
        }packRecipientStatus=out.toString();
    }
}
