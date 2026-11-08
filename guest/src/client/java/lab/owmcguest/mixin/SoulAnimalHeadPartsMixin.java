package lab.owmcguest.mixin;
import lab.owmcguest.SoulAnimalHeadParts;
import net.minecraft.client.model.ModelPart;
import net.minecraft.client.render.entity.model.AnimalModel;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.gen.Invoker;
/** Use mapped virtual dispatch, not Yarn-only reflection strings in production. */
@Mixin(AnimalModel.class)
public abstract class SoulAnimalHeadPartsMixin implements SoulAnimalHeadParts {
    @Invoker("getHeadParts") public abstract Iterable<ModelPart> owmc$soulHeadParts();
}
