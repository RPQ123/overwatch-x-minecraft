package lab.owmcguest;

import net.minecraft.server.MinecraftServer;

/** Actual server dragon health, scoped to the player's current dimension. */
public final class NativeBossRuntime {
    public record State(long world,float health,float maximum) {}
    public static volatile State latest;
    public static void tick(MinecraftServer server){
        State next=null;
        for(var player:server.getPlayerManager().getPlayerList()){
            var world=player.getServerWorld();double nearest=192*192;
            for(var dragon:world.getAliveEnderDragons()){
                double distance=dragon.squaredDistanceTo(player);
                if(distance<=nearest){nearest=distance;next=new State(NativeWorldIdentity.of(server,world.getRegistryKey()),dragon.getHealth(),dragon.getMaxHealth());}
            }
            if(next!=null)break;
        }
        latest=next;
    }
    public static String status(){var value=latest;return value==null?"{\"visible\":false}":"{\"visible\":true,\"health\":"+value.health()+",\"maximum\":"+value.maximum()+"}";}
}
