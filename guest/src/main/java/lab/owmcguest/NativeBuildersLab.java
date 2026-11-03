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
    private record Respawn(UUID owner,long world,int after,net.minecraft.server.world.ServerWorld fixtureWorld,boolean keepInventory){}
    private static Respawn pendingRespawn;
    static{net.fabricmc.fabric.api.event.lifecycle.v1.ServerTickEvents.END_SERVER_TICK.register(server->{
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
            case "torb-scrap-lab"->{
                cleanup();NativeCombatScene.groundLab(server,owner);var at=p.getPos().add(forward.multiply(1,0,1).normalize().multiply(1.1));
                for(int i=0;i<2;i++){var mob=EntityType.HUSK.create(p.getServerWorld());if(mob==null)throw new IllegalStateException("fixture entity unavailable");
                    mob.refreshPositionAndAngles(at.x,at.y,at.z,0,0);if(!p.getServerWorld().isSpaceEmpty(mob,mob.getBoundingBox()))throw new IllegalStateException("occupied fixture");
                    mob.setAiDisabled(true);mob.setNoGravity(true);mob.setSilent(true);mob.setPersistent();mob.setHealth(1);mob.addCommandTag("owmc-builders-fixture");
                    if(!p.getServerWorld().spawnEntity(mob))throw new IllegalStateException("fixture spawn failed");mobs.add(mob);}
            }
            case "torb-repair-lab"->NativeTorbjornRuntime.injureForTest(server,owner);
            case "torb-core-target"->{
                cleanup();var at=p.getPos().add(forward.multiply(1,0,1).normalize().multiply(6));var mob=EntityType.HUSK.create(p.getServerWorld());
                if(mob==null)throw new IllegalStateException("fixture entity unavailable");mob.refreshPositionAndAngles(at.x,at.y,at.z,0,0);
                if(!p.getServerWorld().isSpaceEmpty(mob,mob.getBoundingBox()))throw new IllegalStateException("occupied Core target");
                mob.setAiDisabled(true);mob.setNoGravity(true);mob.setSilent(true);mob.setPersistent();mob.getAttributeInstance(net.minecraft.entity.attribute.EntityAttributes.GENERIC_MAX_HEALTH).setBaseValue(100);mob.setHealth(100);
                mob.addCommandTag("owmc-builders-fixture");if(!p.getServerWorld().spawnEntity(mob))throw new IllegalStateException("fixture spawn failed");mobs.add(mob);
            }
            case "torb-approach-lab"->NativeTorbjornRuntime.approachForTest(server,owner,forward);
            case "torb-pack-lab"->NativeTorbjornRuntime.packForTest(server,owner);
            case "torb-pack-recipient-lab"->{
                var at=NativeTorbjornRuntime.packPositionForTest(server,owner);var ally=EntityType.VILLAGER.create(p.getServerWorld());
                if(ally==null)throw new IllegalStateException("pack recipient unavailable");boolean placed=false;
                for(var offset:List.of(new Vec3d(.8,.05,0),new Vec3d(-.8,.05,0),new Vec3d(0,.05,.8),new Vec3d(0,.05,-.8))){
                    var pos=at.add(offset);ally.refreshPositionAndAngles(pos.x,pos.y,pos.z,0,0);
                    if(p.getServerWorld().isSpaceEmpty(ally,ally.getBoundingBox())){placed=true;break;}
                }
                if(!placed){ally.discard();throw new IllegalStateException("occupied pack recipient fixture");}
                ally.setAiDisabled(true);ally.setNoGravity(true);ally.setSilent(true);ally.setPersistent();ally.addCommandTag("owmc-builders-fixture");
                if(!p.getServerWorld().spawnEntity(ally))throw new IllegalStateException("pack recipient spawn failed");mobs.add(ally);
                NativeTorbjornRuntime.packTestRecipient=ally.getUuidAsString();
            }
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
        var pending=pendingRespawn;
        if(pending!=null){var server=pending.fixtureWorld().getServer();var p=server.getPlayerManager().getPlayer(pending.owner());
            try{if(p!=null&&allowed(p)&&!p.isAlive()&&NativeWorldIdentity.of(server,p.getWorld().getRegistryKey())==pending.world())
                server.getPlayerManager().respawnPlayer(p,false,net.minecraft.entity.Entity.RemovalReason.KILLED);}
            finally{finishRespawn(pending);}
        }
        for(var mob:mobs)if(!mob.isRemoved())mob.discard();mobs.clear();NativeTorbjornRuntime.packTestRecipient="";
    }
}
