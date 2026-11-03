package lab.owmcguest;

import java.util.LinkedHashMap;
import net.minecraft.entity.Entity;
import net.minecraft.entity.LivingEntity;
import net.minecraft.entity.boss.dragon.EnderDragonEntity;
import net.minecraft.entity.boss.dragon.EnderDragonPart;
import net.minecraft.entity.decoration.EndCrystalEntity;
import net.minecraft.entity.damage.DamageSource;
import net.minecraft.registry.RegistryKey;
import net.minecraft.registry.RegistryKeys;
import net.minecraft.server.network.ServerPlayerEntity;
import net.minecraft.server.world.ServerWorld;
import net.minecraft.util.Identifier;
import net.minecraft.util.math.Box;

/** Original entity damage, including crystals, dragon parts and optional mod parts. */
public final class NativeDamageTargets {
    public record Result(boolean applied,double healthLost) {}
    private enum Kind {
        PROJECTILE("native_projectile"),MELEE("native_melee"),BEAM("native_beam"),EXPLOSION("native_explosion");
        final String id;Kind(String id){this.id=id;}
    }
    public static volatile long crystalsDestroyed;
    public static java.util.Collection<Entity> in(ServerWorld world,Entity source,Box bounds){
        var targets=new LinkedHashMap<Integer,Entity>();
        for(var entity:world.getOtherEntities(source,bounds,e->e.isAlive()&&!e.isSpectator()
                &&(e instanceof LivingEntity||e instanceof EndCrystalEntity||e instanceof EnderDragonPart))){
            // The dragon root's box is not a damageable body part.
            if(!(entity instanceof EnderDragonEntity)&&!OptionalMultipartTargets.hiddenRoot(entity))targets.put(entity.getId(),entity);
        }
        for(var dragon:world.getAliveEnderDragons())for(var part:dragon.getBodyParts())
            if(part.getBoundingBox().intersects(bounds))targets.put(part.getId(),part);
        for(var part:OptionalMultipartTargets.parts(world).values())
            if(part.getBoundingBox().intersects(bounds))targets.put(part.getId(),part);
        return targets.values();
    }
    public static Entity resolve(ServerWorld world,int id){
        var entity=world.getEntityById(id);
        if(entity!=null)return entity;
        var dragon=world.getDragonPart(id);return dragon!=null?dragon:OptionalMultipartTargets.parts(world).get(id);
    }
    public static Entity owner(Entity entity){return entity instanceof EnderDragonPart part?part.owner:OptionalMultipartTargets.owner(entity);}
    public static Result projectileDamage(ServerWorld world,Entity entity,ServerPlayerEntity player,double amount){
        return damage(world,entity,player,amount,Kind.PROJECTILE);
    }
    /** Read-only vanilla armor/potion/protection forecast for the lethal marker.
     * Never call damage here: charging must not hurt mobs or wear their armor. */
    public static double projectileHealthEstimate(ServerWorld world,Entity entity,ServerPlayerEntity player,double amount){
        var victim=owner(entity);if(!(victim instanceof LivingEntity living))return amount;
        var type=world.getRegistryManager().get(RegistryKeys.DAMAGE_TYPE).entryOf(RegistryKey.of(RegistryKeys.DAMAGE_TYPE,Identifier.of("owmcguest","native_projectile")));
        var source=new DamageSource(type,player);
        if(living.isInvulnerableTo(source))return 0;
        float value=(float)amount;
        if(entity instanceof EnderDragonPart part&&part!=part.owner.head)value=value/4+Math.min(value,1);
        value=net.minecraft.entity.DamageUtil.getDamageLeft(living,value,source,living.getArmor(),(float)living.getAttributeValue(net.minecraft.entity.attribute.EntityAttributes.GENERIC_ARMOR_TOUGHNESS));
        var resistance=living.getStatusEffect(net.minecraft.entity.effect.StatusEffects.RESISTANCE);
        if(resistance!=null)value=Math.max(0,value*(25-(resistance.getAmplifier()+1)*5)/25);
        value=net.minecraft.entity.DamageUtil.getInflictedDamage(value,net.minecraft.enchantment.EnchantmentHelper.getProtectionAmount(world,living,source));
        return Math.max(0,value-living.getAbsorptionAmount());
    }
    public static Result meleeDamage(ServerWorld world,Entity entity,ServerPlayerEntity player,double amount){
        return damage(world,entity,player,amount,Kind.MELEE);
    }
    public static Result beamDamage(ServerWorld world,Entity entity,ServerPlayerEntity player,double amount){
        return damage(world,entity,player,amount,Kind.BEAM);
    }
    public static Result explosionDamage(ServerWorld world,Entity entity,ServerPlayerEntity player,double amount){
        return damage(world,entity,player,amount,Kind.EXPLOSION);
    }
    private static Result damage(ServerWorld world,Entity entity,ServerPlayerEntity player,double amount,Kind kind){
        if(entity==null||!entity.isAlive()||!Double.isFinite(amount)||amount<=0)return new Result(false,0);
        var type=world.getRegistryManager().get(RegistryKeys.DAMAGE_TYPE).entryOf(
            RegistryKey.of(RegistryKeys.DAMAGE_TYPE,Identifier.of("owmcguest",kind.id)));
        var victim=owner(entity);float before=victim instanceof LivingEntity living?living.getHealth():0;
        float shield=victim instanceof LivingEntity living?living.getAbsorptionAmount():0;
        var source=new DamageSource(type,player);boolean applied=entity.damage(source,(float)amount);
        if(entity instanceof EndCrystalEntity&&applied&&entity.isRemoved())crystalsDestroyed++;
        double loss=victim instanceof LivingEntity living?Math.max(0,before-living.getHealth()):0;
        TwilightForestTrial.damageReceipt(world,entity,player,amount,source,applied,loss);
        NativeCombatScene.damageReceipt(entity,amount,source,applied,loss);
        if(loss>0)NativeEliminationRuntime.damage(player,victim,loss);
        double acceptedLoss=loss+(victim instanceof LivingEntity living?Math.max(0,shield-living.getAbsorptionAmount()):0);
        if(acceptedLoss>0)NativeCombatFeedback.damage(player,victim,acceptedLoss);
        else if(applied&&entity instanceof EndCrystalEntity&&entity.isRemoved())NativeCombatFeedback.contact(player);
        return new Result(applied,loss);
    }
}
