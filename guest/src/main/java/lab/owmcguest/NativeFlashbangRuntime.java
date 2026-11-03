package lab.owmcguest;

import java.util.*;
import com.google.gson.JsonObject;
import net.minecraft.entity.LivingEntity;
import net.minecraft.entity.effect.StatusEffectInstance;
import net.minecraft.entity.effect.StatusEffects;
import net.minecraft.particle.ParticleTypes;
import net.minecraft.particle.DustParticleEffect;
import net.minecraft.sound.SoundEvents;
import net.minecraft.sound.SoundCategory;
import net.minecraft.entity.attribute.*;
import net.minecraft.server.MinecraftServer;
import net.minecraft.server.network.ServerPlayerEntity;
import net.minecraft.server.world.ServerWorld;
import net.minecraft.util.Identifier;
import net.minecraft.util.hit.HitResult;
import net.minecraft.util.math.*;
import net.minecraft.world.RaycastContext;

/** Real native grenade; user-requested two-second potion slow and local burst. */
public final class NativeFlashbangRuntime {
    private static final Identifier SLOW=Identifier.of("owmcguest","flashbang_slow");
    private record Slowed(LivingEntity target,int expires){}
    private static final Map<UUID,Slowed> slowed=new HashMap<>();
    public static long detonations,affected,restored;
    private static double healthLost;
    public static volatile String status="{}";
    public static double detonate(ServerWorld world,ServerPlayerEntity player,NativeShotProtocol.Shot shot,NativeShotSimulation.Hit hit){
        if(shot.effect()==null||shot.effect().kind()!=2||!hit.loaded())return 0;
        var center=new Vec3d(hit.point().x(),hit.point().y(),hit.point().z());double loss=0;detonations++;
        world.spawnParticles(ParticleTypes.FLASH,center.x,center.y+.08,center.z,1,0,0,0,0);
        world.spawnParticles(ParticleTypes.POOF,center.x,center.y+.08,center.z,24,.25,.18,.25,.09);
        world.spawnParticles(ParticleTypes.ELECTRIC_SPARK,center.x,center.y+.08,center.z,36,.16,.12,.16,.23);
        var gold=new DustParticleEffect(new org.joml.Vector3f(1f,.72f,.18f),1.15f);
        world.spawnParticles(gold,center.x,center.y+.08,center.z,22,.48,.22,.48,.06);
        // One actual detonation, two short radial bands. No per-tick replay and
        // no extra flashbang damage/status application from cosmetic particles.
        for(int i=0;i<24;i++){
            double a=i*Math.PI/12,dx=Math.cos(a),dz=Math.sin(a);
            world.spawnParticles(ParticleTypes.ELECTRIC_SPARK,center.x+dx*.16,center.y+.08,center.z+dz*.16,0,dx*.33,.035,dz*.33,1);
        }
        world.playSound(null,center.x,center.y,center.z,SoundEvents.ENTITY_GENERIC_EXPLODE,SoundCategory.PLAYERS,.4f,1.8f);
        var owners=new HashSet<UUID>();
        // Pull a block impact slightly back along its incoming ray, so a ray
        // beginning exactly on a wall does not leak the blast through that wall.
        var incoming=new Vec3d(shot.velocity().x(),shot.velocity().y(),shot.velocity().z()).normalize();
        var normal=hit.normal();var origin=hit.block()&&normal!=null?center.add(normal.x()*.02,normal.y()*.02,normal.z()*.02):center.subtract(incoming.multiply(.02));
        for(var entity:NativeDamageTargets.in(world,player,new Box(center,center).expand(3))){
            var victim=NativeDamageTargets.owner(entity);
            if(!(victim instanceof LivingEntity living)||!owners.add(victim.getUuid())||!world.isChunkLoaded(entity.getBlockPos()))continue;
            var target=entity.getBoundingBox().getCenter();if(target.squaredDistanceTo(center)>9)continue;
            var cover=world.raycast(new RaycastContext(origin,target,RaycastContext.ShapeType.COLLIDER,RaycastContext.FluidHandling.NONE,player));
            if(cover.getType()!=HitResult.Type.MISS&&origin.squaredDistanceTo(cover.getPos())+1e-5<origin.squaredDistanceTo(target))continue;
            // The receipt remains the beta's measured25. Gameplay deliberately
            // uses the requested modern75, documented separately from that proof.
            var result=NativeDamageTargets.explosionDamage(world,entity,player,75*NativeShotSimulation.HP_SCALE);loss+=result.healthLost();
            var speed=living.getAttributeInstance(EntityAttributes.GENERIC_MOVEMENT_SPEED);
            if(speed!=null&&living.isAlive()){
                speed.removeModifier(SLOW);double before=speed.getValue();
                // A real vanilla potion supplies the requested visible particles.
                // Compensate its45% SlownessIII to the existing50% movement result.
                // Stronger/longer effects are left to vanilla's merge rules.
                living.addStatusEffect(new StatusEffectInstance(StatusEffects.SLOWNESS,40,2,false,true,true),player);
                double after=speed.getValue();double multiplier=after>0?Math.min(1,before*.5/after)-1:0;
                speed.addTemporaryModifier(new EntityAttributeModifier(SLOW,multiplier,EntityAttributeModifier.Operation.ADD_MULTIPLIED_TOTAL));
                slowed.put(living.getUuid(),new Slowed(living,world.getServer().getTicks()+40));affected++;
            }
        }
        // Latest explicit user exception: retain flash/slow/damage, no added
        // terrain explosion. Ordinary explosive projectiles keep their policy.
        healthLost+=loss;return loss;
    }
    public static void tick(MinecraftServer server){
        var it=slowed.values().iterator();while(it.hasNext()){
            var s=it.next();if(s.target().isRemoved()||!s.target().isAlive()||server.getTicks()>=s.expires()){
                remove(s);it.remove();
            }
        }
        var out=new JsonObject();out.addProperty("detonations",detonations);out.addProperty("affected",affected);out.addProperty("active",slowed.size());out.addProperty("restored",restored);out.addProperty("durationTicks",40);out.addProperty("speedMultiplier",.5);out.addProperty("potion","minecraft:slowness");out.addProperty("healthLost",healthLost);out.addProperty("terrainBursts",0);out.addProperty("terrainBlocks",0);out.addProperty("terrainStrength",NativeExplosionTerrain.FLASHBANG);out.addProperty("terrainError","");out.addProperty("terrainPolicy","explicit-user-exception");status=out.toString();
    }
    private static void remove(Slowed s){var speed=s.target().getAttributeInstance(EntityAttributes.GENERIC_MOVEMENT_SPEED);if(speed!=null)speed.removeModifier(SLOW);restored++;}
    public static void resetSession(){for(var s:slowed.values())remove(s);slowed.clear();}
}
