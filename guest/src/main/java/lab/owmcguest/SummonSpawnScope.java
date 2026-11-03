package lab.owmcguest;

import net.minecraft.entity.Entity;
import net.minecraft.entity.LivingEntity;
import net.minecraft.server.MinecraftServer;
import net.minecraft.server.network.ServerPlayerEntity;
import net.minecraft.server.world.ServerWorld;

/** Only synchronous F9 requests own this scope; natural/chunk-loaded mobs never inherit it. */
public final class SummonSpawnScope implements AutoCloseable {
    static {
        BossBarEvidence.registerBarType(net.minecraft.entity.boss.BossBar.class);
        BossBarEvidence.registerSharedBase(Entity.class);
        BossBarEvidence.registerSharedBase(LivingEntity.class);
        BossBarEvidence.registerSharedBase(net.minecraft.entity.mob.MobEntity.class);
    }
    private static final ThreadLocal<SummonSpawnScope> active=new ThreadLocal<>();
    private final SummonSpawnScope previous;private final MinecraftServer server;private final boolean random;
    private int probes;
    public SummonSpawnScope(MinecraftServer server,boolean random){
        if(!server.isOnThread())throw new IllegalStateException("F9 scope requires server thread");
        SummonedMobLifecycle.register();this.server=server;this.random=random;previous=active.get();active.set(this);
    }
    public static final class Probe implements AutoCloseable {
        private final SummonSpawnScope scope;private boolean closed;
        private Probe(SummonSpawnScope scope){this.scope=scope;if(scope!=null)scope.probes++;}
        @Override public void close(){if(!closed){closed=true;if(scope!=null)scope.probes--;}}
    }
    public static Probe probe(){return new Probe(active.get());}
    public static void discardSilently(Entity entity,ServerWorld world){
        try(var scope=new SummonSpawnScope(world.getServer(),false);var ignored=probe()){
            entity.discard(); // DISCARD, not kill/damage; also block custom removal spawns.
        }
    }
    public static boolean hasBossBar(LivingEntity entity){
        return RandomSummonPolicy.blacklisted(net.minecraft.registry.Registries.ENTITY_TYPE.getId(entity.getType()).toString())
            ||entity.getType().getRegistryEntry().streamTags().anyMatch(tag->BossBarEvidence.bossTag(tag.id().toString()))
            ||BossBarEvidence.inspect(entity)!=BossBarEvidence.Verdict.CLEAR;
    }
    public static boolean beforeSpawn(ServerWorld world,Entity entity){
        var scope=active.get();if(scope==null||scope.server!=world.getServer())return true;
        if(scope.probes>0)return false;
        if(!(entity instanceof LivingEntity living)||entity instanceof ServerPlayerEntity)return true;
        if(scope.random&&hasBossBar(living))return false;
        SummonedMobLifecycle.mark(entity,world);return true;
    }
    @Override public void close(){active.set(previous);}
}
