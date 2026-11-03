package lab.owmcguest.mixin;

import lab.owmcguest.HeroVoiceMovementSounds;
import net.minecraft.client.sound.SoundInstance;
import net.minecraft.client.sound.SoundSystem;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Inject;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfo;

/** 语音挂接：播放之前直接删除起落语气声，不用冷却补救。 */
@Mixin(SoundSystem.class)
public abstract class HeroVoiceMovementSoundMixin {
    @Inject(method="play(Lnet/minecraft/client/sound/SoundInstance;)V",at=@At("HEAD"),cancellable=true)
    private void owmc$removeMovementVoices(SoundInstance sound,CallbackInfo ci){
        if(HeroVoiceMovementSounds.suppress(sound))ci.cancel();
    }
}
