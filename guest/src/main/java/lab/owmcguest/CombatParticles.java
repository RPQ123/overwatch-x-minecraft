package lab.owmcguest;

import net.fabricmc.fabric.api.particle.v1.FabricParticleTypes;
import net.minecraft.particle.SimpleParticleType;
import net.minecraft.registry.*;
import net.minecraft.util.Identifier;

public final class CombatParticles {
    public static final SimpleParticleType DEADEYE_BLOOD=FabricParticleTypes.simple(true);
    public static void register(){Registry.register(Registries.PARTICLE_TYPE,Identifier.of("owmcguest","deadeye_blood"),DEADEYE_BLOOD);}
}
