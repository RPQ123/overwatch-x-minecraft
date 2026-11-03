package lab.owmcguest;

import java.util.LinkedHashMap;
import java.util.UUID;
import com.google.gson.JsonArray;
import com.google.gson.JsonObject;
import net.minecraft.entity.Entity;
import net.minecraft.entity.mob.MobEntity;
import net.minecraft.entity.attribute.EntityAttributes;
import net.minecraft.entity.attribute.EntityAttributeModifier;
import net.minecraft.registry.Registries;
import net.minecraft.registry.RegistryKeys;
import net.minecraft.registry.tag.TagKey;
import net.minecraft.server.MinecraftServer;
import net.minecraft.server.world.ServerWorld;
import net.minecraft.server.network.ServerPlayerEntity;
import net.minecraft.particle.ParticleTypes;
import net.minecraft.sound.SoundCategory;
import net.minecraft.sound.SoundEvents;
import net.minecraft.util.Identifier;
import lab.owmcguest.NativeShotProtocol.Shot;

/** Already-hit mob effects use MC ticks; no key-driven casts or persistent NoAI. */
public final class NativeMeiFreezeRuntime {
    public static final long HERO=0x02e00000000000ddL;
    private static final Identifier MODIFIER=Identifier.of("owmcguest","mei_frost");
    private static final TagKey<net.minecraft.entity.EntityType<?>> IMMUNE=TagKey.of(RegistryKeys.ENTITY_TYPE,Identifier.of("minecraft","freeze_immune_entity_types"));
    private record Entry(MobEntity mob,ServerWorld world,MeiFreezeProgress progress){}
    private static final LinkedHashMap<UUID,Entry> targets=new LinkedHashMap<>();
    public static volatile String status="{}";
    private static long accepted,freezes,expired,aiBlocked,travelBlocked;
    private NativeMeiFreezeRuntime(){}
    static boolean spray(Shot s){
        var e=s.effect();return e!=null&&e.hero()==HERO&&e.resource()==0x04000000000008beL&&e.kind()==0
            &&!s.hitscan()&&!s.beam()&&!s.rocket()&&s.nativeDamage()==2.25&&s.lifetime()==5&&s.range()==10
            &&Math.abs(s.velocity().lengthSquared()-1600)<.1&&e.gravity()==0&&e.splash()==0&&e.radius()==0&&e.bounces()==0&&e.fuse()==0;
    }
    public static void contact(ServerPlayerEntity owner,long worldId,long model,long generation,Shot shot,Entity entity){
        if(!spray(shot))return;
        hit(owner,worldId,model,generation,generation+":"+model+":"+shot.identity(),entity);
    }
    /** Shared freeze contact: the spray (per original shot) and Blizzard (per MC area tick) both feed it. */
    public static void hit(ServerPlayerEntity owner,long worldId,long model,long generation,String identity,Entity entity){
        if(!(entity instanceof MobEntity mob)||!mob.isAlive()||!(mob.getWorld() instanceof ServerWorld world)
            ||owner.getServerWorld()!=world||!NativeEliminationRuntime.sessionMatches(owner.getUuid(),worldId,HERO,model,generation)
            ||!Registries.ENTITY_TYPE.getId(mob.getType()).getNamespace().equals("minecraft")
            ||mob instanceof net.minecraft.entity.boss.WitherEntity||mob.getType()==net.minecraft.entity.EntityType.ENDER_DRAGON||mob.getType().isIn(IMMUNE))return;
        var entry=targets.get(mob.getUuid());
        if(entry==null){if(targets.size()>=256)return;entry=new Entry(mob,world,new MeiFreezeProgress());targets.put(mob.getUuid(),entry);}
        long tick=world.getTime();boolean was=entry.progress.frozen(tick);
        if(entry.progress.hit(identity,tick))accepted++;
        if(!was&&entry.progress.frozen(tick)){
            freezes++;world.spawnParticles(ParticleTypes.SNOWFLAKE,mob.getX(),mob.getBodyY(.5),mob.getZ(),24,.35,.6,.35,.03);
            world.playSound(null,mob.getBlockPos(),SoundEvents.BLOCK_GLASS_BREAK,SoundCategory.PLAYERS,.65f,1.5f);
            mob.getNavigation().stop();
        }
        apply(entry,tick);
    }
    private static void apply(Entry entry,long tick){
        var speed=entry.mob.getAttributeInstance(EntityAttributes.GENERIC_MOVEMENT_SPEED);if(speed==null)return;
        double slow=entry.progress.slow(tick);var old=speed.getModifier(MODIFIER);
        if(old!=null&&Math.abs(old.value()+slow)<1e-9)return;
        speed.removeModifier(MODIFIER);
        if(slow>0)speed.addTemporaryModifier(new EntityAttributeModifier(MODIFIER,-slow,EntityAttributeModifier.Operation.ADD_MULTIPLIED_TOTAL));
    }
    /** Server-thread queries only; client interpolation remains vanilla. */
    public static boolean frozen(Entity entity){
        if(!(entity.getWorld() instanceof ServerWorld world))return false;
        var entry=targets.get(entity.getUuid());return entry!=null&&entry.mob==entity&&entry.world==world&&entity.isAlive()&&entry.progress.frozen(world.getTime());
    }
    public static void blockedAi(){aiBlocked++;}
    public static void blockedTravel(){travelBlocked++;}
    public static void tick(MinecraftServer server){
        var rows=new JsonArray();
        var iterator=targets.values().iterator();while(iterator.hasNext()){
            var entry=iterator.next();var mob=entry.mob;long tick=entry.world.getTime();entry.progress.advance(tick);
            if(!mob.isAlive()||mob.isRemoved()||mob.getWorld()!=entry.world||entry.world.getEntity(mob.getUuid())!=mob||entry.progress.empty()){
                var attr=mob.getAttributeInstance(EntityAttributes.GENERIC_MOVEMENT_SPEED);if(attr!=null)attr.removeModifier(MODIFIER);iterator.remove();expired++;continue;
            }
            apply(entry,tick);
            if(tick%4==0)entry.world.spawnParticles(ParticleTypes.SNOWFLAKE,mob.getX(),mob.getBodyY(.5),mob.getZ(),entry.progress.frozen(tick)?4:2,.25,.45,.25,.005);
            var row=new JsonObject();row.addProperty("target",mob.getId());row.addProperty("stacks",entry.progress.stacks());row.addProperty("frozen",entry.progress.frozen(tick));row.addProperty("remainingTicks",entry.progress.remaining(tick));row.addProperty("slow",entry.progress.slow(tick));row.addProperty("aiDisabled",mob.isAiDisabled());rows.add(row);
        }
        var out=new JsonObject();out.addProperty("acceptedContacts",accepted);out.addProperty("freezes",freezes);out.addProperty("expired",expired);out.addProperty("aiBlocked",aiBlocked);out.addProperty("travelBlocked",travelBlocked);out.add("targets",rows);out.addProperty("policy","minewatch2018-30contacts-10tick-decay-90tick-freeze-vanilla-mobs");status=out.toString();
    }
    public static void close(){for(var e:targets.values()){var a=e.mob.getAttributeInstance(EntityAttributes.GENERIC_MOVEMENT_SPEED);if(a!=null)a.removeModifier(MODIFIER);}targets.clear();accepted=freezes=expired=aiBlocked=travelBlocked=0;status="{}";}
}
