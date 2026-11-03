package lab.owmcguest;

import net.minecraft.client.MinecraftClient;
import net.minecraft.entity.Entity;

/** Local MC Glowing outline from an actual Venom Mine poison interval.
 * The shared isGlowing hook ORs this contribution with its existing result. Ending
 * venom never removes another source's effect/flag, nor changes scoreboard colors. */
public final class NativeVenomReveal {
    private NativeVenomReveal(){}

    public static boolean reveals(Entity entity){
        var client=MinecraftClient.getInstance();var view=NativeVenomRuntime.poisonReveal;
        if(view==null||entity==null||!entity.isAlive()||entity.isSpectator()||client.world==null
            ||entity.getWorld()!=client.world||client.player==null||!client.player.isAlive()
            ||client.getServer()==null||!client.player.getUuid().equals(view.scope().owner()))return false;
        var target=view.entities().get(entity.getId());
        if(target==null||!entity.getUuid().equals(target.uuid())||target.ticksRemaining()<=0)return false;
        var locomotion=NativeLocomotionController.INSTANCE;var host=HostPoseReader.INSTANCE.latest();
        if(locomotion.hero()!=0x02e000000000000aL||locomotion.modelId()!=view.scope().model()
            ||host==null||!host.inputActive()||host.generation()!=view.scope().source())return false;
        long now=System.currentTimeMillis();
        return now-view.wall()<=150&&view.wall()<=now+50
            &&client.world.getRegistryKey().getValue().toString().equals(view.dimension())
            &&NativeWorldIdentity.of(client.getServer(),client.world.getRegistryKey())==view.scope().world();
    }
}
