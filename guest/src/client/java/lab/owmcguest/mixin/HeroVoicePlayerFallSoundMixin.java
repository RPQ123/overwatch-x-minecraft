package lab.owmcguest.mixin;

import lab.owmcguest.HeroVoiceMovementSounds;
import net.minecraft.entity.Entity;
import net.minecraft.entity.damage.DamageSource;
import net.minecraft.entity.player.PlayerEntity;
import net.minecraft.registry.tag.DamageTypeTags;
import net.minecraft.sound.SoundEvent;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Inject;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfoReturnable;

/** 语音挂接：坠落伤害额外的玩家hurt语气声也删除，伤害本身不变。 */
@Mixin(PlayerEntity.class)
public abstract class HeroVoicePlayerFallSoundMixin {
    @Inject(method="getHurtSound",at=@At("HEAD"),cancellable=true)
    private void owmc$removeFallHurtVoice(DamageSource source,CallbackInfoReturnable<SoundEvent> cir){
        if(source.isIn(DamageTypeTags.IS_FALL)&&HeroVoiceMovementSounds.activePlayer((Entity)(Object)this)){
            HeroVoiceMovementSounds.fallHurtSuppressed();cir.setReturnValue(null);
        }
    }
}
