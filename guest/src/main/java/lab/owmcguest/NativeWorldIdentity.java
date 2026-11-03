package lab.owmcguest;

import java.nio.charset.StandardCharsets;
import java.util.UUID;
import net.minecraft.server.MinecraftServer;
import net.minecraft.registry.RegistryKey;
import net.minecraft.world.World;
import net.minecraft.util.WorldSavePath;

public final class NativeWorldIdentity {
    public static long of(MinecraftServer server,RegistryKey<World> dimension){
        String text=server.getSavePath(WorldSavePath.ROOT).toAbsolutePath().normalize()+"|"+dimension.getValue();
        long id=UUID.nameUUIDFromBytes(text.getBytes(StandardCharsets.UTF_8)).getMostSignificantBits();
        return id==0?1:id;
    }
}
