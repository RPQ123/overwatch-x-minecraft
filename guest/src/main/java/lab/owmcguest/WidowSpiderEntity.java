package lab.owmcguest;

import net.fabricmc.fabric.api.object.builder.v1.entity.FabricDefaultAttributeRegistry;
import net.minecraft.entity.Entity;
import net.minecraft.entity.EntityType;
import net.minecraft.entity.LivingEntity;
import net.minecraft.entity.SpawnGroup;
import net.minecraft.entity.ai.goal.LookAroundGoal;
import net.minecraft.entity.ai.goal.MeleeAttackGoal;
import net.minecraft.entity.ai.goal.SwimGoal;
import net.minecraft.entity.ai.goal.WanderAroundFarGoal;
import net.minecraft.entity.attribute.EntityAttributes;
import net.minecraft.entity.damage.DamageSource;
import net.minecraft.entity.mob.CaveSpiderEntity;
import net.minecraft.registry.Registries;
import net.minecraft.registry.Registry;
import net.minecraft.server.world.ServerWorld;
import net.minecraft.text.Text;
import net.minecraft.util.Identifier;
import net.minecraft.util.math.MathHelper;
import net.minecraft.world.World;

/** MC adaptation requested on 2026-10-27: 30% cave spider, rainbow name, all-species
 * targeting within 16 blocks, 1/10 max HP decay each second, death after 200 ticks.
 * Attack damage, difficulty scaling and poison are inherited unchanged from CaveSpiderEntity.
 * This entity is created only by the native-confirmed Venom Mine landing path. */
public final class WidowSpiderEntity extends CaveSpiderEntity {
    public static final float SCALE=.3f;
    public static final int LIFETIME_TICKS=200,DECAY_INTERVAL=20;
    private static final double HUNT_RANGE=16;
    public static final EntityType<WidowSpiderEntity> TYPE=Registry.register(Registries.ENTITY_TYPE,
        Identifier.of("owmcguest","widow_spider"),EntityType.Builder
            .<WidowSpiderEntity>create(WidowSpiderEntity::new,SpawnGroup.MONSTER)
            .dimensions(.7f,.5f).maxTrackingRange(8).trackingTickInterval(2)
            .disableSaving().build("owmcguest:widow_spider"));
    private NativeVenomRuntime.Scope scope;
    private int lifeTicks;

    /** Call once from GuestMod.onInitialize, before the entity registries freeze. */
    public static void register(){
        FabricDefaultAttributeRegistry.register(TYPE,createCaveSpiderAttributes()
            .add(EntityAttributes.GENERIC_SCALE,SCALE));
    }

    public WidowSpiderEntity(EntityType<? extends WidowSpiderEntity> type,World world){
        super(type,world);
        setCustomName(rainbowName());
        setCustomNameVisible(true);
        setCanPickUpLoot(false);
        experiencePoints=0;
    }

    public static Text rainbowName(){
        var name=Text.empty();String label="Spider Man";
        for(int i=0;i<label.length();i++){
            int rgb=MathHelper.hsvToRgb(i/(float)label.length(),.85f,1f);
            name.append(Text.literal(label.substring(i,i+1)).styled(style->style.withColor(rgb)));
        }
        return name;
    }

    void launchedBy(NativeVenomRuntime.Scope owner){scope=owner;}
    int lifeTicks(){return lifeTicks;}

    @Override protected void initGoals(){
        // Vanilla spider attack/target goals stop in daylight and only hunt players/golems.
        // Use its normal melee navigation/attack with an explicit all-species target scan.
        goalSelector.add(1,new SwimGoal(this));
        goalSelector.add(2,new MeleeAttackGoal(this,1.0,true));
        goalSelector.add(3,new WanderAroundFarGoal(this,.8));
        goalSelector.add(4,new LookAroundGoal(this));
    }

    private boolean canHunt(LivingEntity target){
        return target!=this&&target.isAlive()&&!target.isSpectator()
            &&scope!=null&&!target.getUuid().equals(scope.owner());
    }

    private boolean validOwner(ServerWorld world){
        if(scope==null)return false;
        var owner=world.getServer().getPlayerManager().getPlayer(scope.owner());
        return owner!=null&&owner.isAlive()
            &&NativeWorldIdentity.of(world.getServer(),world.getRegistryKey())==scope.world()
            &&owner.getServerWorld()==world
            &&NativeEliminationRuntime.sessionMatches(scope.owner(),scope.world(),
                0x02e000000000000aL,scope.model(),scope.source());
    }

    @Override public void tick(){
        if(getWorld() instanceof ServerWorld world&&isAlive()){
            if(!validOwner(world)){discard();return;}
            lifeTicks++;
            if(lifeTicks%DECAY_INTERVAL==0){
                float before=getHealth();
                damage(getDamageSources().starve(),getMaxHealth()/10f);
                NativeVenomRuntime.spiderDecay(Math.max(0,before-getHealth()));
            }
            if(lifeTicks>=LIFETIME_TICKS){
                NativeVenomRuntime.spiderTimedOut();
                if(isAlive())kill(); // Hard limit even if healing/resistance offsets the decay.
            }
            if(isAlive()&&lifeTicks%5==1){
                var target=world.getEntitiesByClass(LivingEntity.class,
                    getBoundingBox().expand(HUNT_RANGE),this::canHunt).stream()
                    .filter(e->squaredDistanceTo(e)<=HUNT_RANGE*HUNT_RANGE&&canSee(e))
                    .min(java.util.Comparator.comparingDouble(this::squaredDistanceTo)).orElse(null);
                setTarget(target);
            }
            if(getTarget()!=null&&!canHunt(getTarget()))setTarget(null);
        }
        super.tick();
    }

    @Override public boolean tryAttack(Entity target){
        // Guard the actual damage path as well as selection, including after owner/session changes.
        if(!(getWorld() instanceof ServerWorld world)||!validOwner(world)
            ||!(target instanceof LivingEntity living)||!canHunt(living))return false;
        float before=living.getHealth()+living.getAbsorptionAmount();
        boolean hit=super.tryAttack(target);
        if(hit)NativeVenomRuntime.spiderHit(Math.max(0,before-living.getHealth()-living.getAbsorptionAmount()));
        return hit;
    }

    @Override protected boolean isDisallowedInPeaceful(){return false;}
    @Override protected void dropLoot(DamageSource source,boolean causedByPlayer){}
}
