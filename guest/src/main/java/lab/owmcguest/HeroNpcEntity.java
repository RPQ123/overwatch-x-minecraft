package lab.owmcguest;

import net.fabricmc.fabric.api.object.builder.v1.entity.FabricDefaultAttributeRegistry;
import net.minecraft.entity.*;
import net.minecraft.entity.mob.PathAwareEntity;
import net.minecraft.entity.ai.goal.LookAtEntityGoal;
import net.minecraft.entity.ai.goal.LookAroundGoal;
import net.minecraft.entity.player.PlayerEntity;
import net.minecraft.entity.attribute.EntityAttributes;
import net.minecraft.entity.data.*;
import net.minecraft.entity.damage.DamageSource;
import net.minecraft.nbt.NbtCompound;
import net.minecraft.registry.*;
import net.minecraft.text.Text;
import net.minecraft.util.Identifier;
import net.minecraft.world.World;

/** A real damageable MC training target. Original OW body is supplied by its renderer. */
public final class HeroNpcEntity extends PathAwareEntity {
    public static final EntityType<HeroNpcEntity> TYPE=Registry.register(Registries.ENTITY_TYPE,Identifier.of("owmcguest","hero_npc"),
        EntityType.Builder.<HeroNpcEntity>create(HeroNpcEntity::new,SpawnGroup.CREATURE).dimensions(.7f,1.9f).maxTrackingRange(12).trackingTickInterval(2).disableSaving().disableSummon().build("owmcguest:hero_npc"));
    private static final TrackedData<Integer> HERO=DataTracker.registerData(HeroNpcEntity.class,TrackedDataHandlerRegistry.INTEGER);
    java.util.UUID summonedBy;
    private boolean deathRecorded;
    public HeroNpcEntity(EntityType<? extends HeroNpcEntity> type,World world){super(type,world);setPersistent();setCanPickUpLoot(false);experiencePoints=0;}
    public static void register(){FabricDefaultAttributeRegistry.register(TYPE,createMobAttributes().add(EntityAttributes.GENERIC_MAX_HEALTH,20).add(EntityAttributes.GENERIC_MOVEMENT_SPEED,0).add(EntityAttributes.GENERIC_KNOCKBACK_RESISTANCE,.5));}
    @Override protected void initDataTracker(DataTracker.Builder builder){super.initDataTracker(builder);builder.add(HERO,0);}
    @Override protected void initGoals(){goalSelector.add(1,new LookAtEntityGoal(this,PlayerEntity.class,12));goalSelector.add(2,new LookAroundGoal(this));}
    public int heroIndex(){return dataTracker.get(HERO);}
    void configure(int index,java.util.UUID owner){
        var entry=HeroNpcCatalog.entry(index);dataTracker.set(HERO,index);summonedBy=owner;
        getAttributeInstance(EntityAttributes.GENERIC_MAX_HEALTH).setBaseValue(entry.health()*SurvivalHealthPlan.SCALE);setHealth(getMaxHealth());
        setCustomName(Text.literal(entry.name()));setCustomNameVisible(true);addCommandTag("owmc-hero-summon");
    }
    @Override public void onDeath(DamageSource source){if(deathRecorded)return;deathRecorded=true;super.onDeath(source);if(!getWorld().isClient)HeroSummonRuntime.killed(this);}
    @Override protected void dropLoot(DamageSource source,boolean causedByPlayer){}
    @Override public boolean saveNbt(NbtCompound nbt){return false;}
}
