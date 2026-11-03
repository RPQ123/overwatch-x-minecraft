package lab.owmcguest.mixin;

import lab.owmcguest.SummonSpawnScope;
import lab.owmcguest.F9SummonAccess;
import net.minecraft.entity.Entity;
import net.minecraft.server.world.ServerWorld;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Inject;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfoReturnable;

/** Captures actual new spawns in F9 batches/fixtures, not entities loaded by a chunk. */
@Mixin(ServerWorld.class)
public abstract class F9SummonSpawnMixin implements F9SummonAccess {
    @Inject(method="spawnEntity",at=@At("HEAD"),cancellable=true)
    private void owmc$f9Spawn(Entity entity,CallbackInfoReturnable<Boolean> result){
        if(!SummonSpawnScope.beforeSpawn((ServerWorld)(Object)this,entity))result.setReturnValue(false);
    }
}
