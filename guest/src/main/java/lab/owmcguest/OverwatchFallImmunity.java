package lab.owmcguest;

import net.minecraft.entity.LivingEntity;
import net.minecraft.entity.damage.DamageSource;
import net.minecraft.entity.player.PlayerEntity;
import net.minecraft.registry.tag.DamageTypeTags;

/** Overwatch heroes take no fall damage: the hero player and summoned hero NPCs. */
public final class OverwatchFallImmunity {
    private OverwatchFallImmunity() {}

    public static boolean immune(LivingEntity entity, DamageSource source) {
        if (!source.isIn(DamageTypeTags.IS_FALL)) return false;
        boolean hero = entity instanceof PlayerEntity || entity instanceof HeroNpcEntity;
        if (hero) entity.fallDistance = 0;
        return hero;
    }
}
