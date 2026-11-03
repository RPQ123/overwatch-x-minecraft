package lab.owmcguest;

import java.util.UUID;
import net.minecraft.registry.*;
import net.minecraft.server.MinecraftServer;
import net.minecraft.util.Identifier;
import net.minecraft.util.math.BlockPos;
import net.minecraft.world.World;

/** Explicit isolated regression travel, using real server/client world transfer. */
public final class NativeSwitchTrial {
    public static volatile String error="";
    public static void travel(MinecraftServer server,UUID owner,String name){
        error="";var p=server.getPlayerManager().getPlayer(owner);
        if(!Boolean.getBoolean("owmc.twilightTrial")||!System.getProperty("owmc.worldName","").startsWith("Overwatch Twilight Switch ")||p==null||!p.isCreative()){
            error="Switch test requires the separate creative regression save";return;
        }
        var key=switch(name){case "overworld"->World.OVERWORLD;case "nether"->World.NETHER;case "end"->World.END;case "twilight"->RegistryKey.of(RegistryKeys.WORLD,Identifier.of("twilightforest","twilight_forest"));default->null;};
        var w=key==null?null:server.getWorld(key);if(w==null){error="Requested real dimension unavailable";return;}
        NativeCombatScene.cleanup();TwilightForestTrial.stopNativeProbe(server);
        int x=57,z=12;w.getChunk(new BlockPos(x,0,z));
        double y=name.equals("nether")?140:name.equals("end")?160:w.getTopY(net.minecraft.world.Heightmap.Type.WORLD_SURFACE,x,z)+12;
        p.teleport(w,x+.5,y,z+.5,p.getYaw(),p.getPitch());p.getAbilities().flying=true;p.sendAbilitiesUpdate();
    }
}
