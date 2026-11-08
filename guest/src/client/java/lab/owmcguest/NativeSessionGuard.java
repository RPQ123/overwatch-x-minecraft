package lab.owmcguest;

import java.util.UUID;
import net.minecraft.client.MinecraftClient;

/**
 * Prevents native ability state from crossing a real MC dimension or hero
 * recreation.  A new native model is a new session even when the player and
 * host process stay alive.
 */
final class NativeSessionGuard {
    private static boolean initialized,inputConfirmed;
    private static UUID player;
    private static long world, hero, model, hostGeneration;
    private static final NativeSpawnHealthGate spawnHealth=new NativeSpawnHealthGate();
    private record SpawnHealth(UUID player,long world,long hero,long model,long source){}
    private static volatile SpawnHealth pendingSpawn;

    private NativeSessionGuard() {}

    static boolean observe(MinecraftClient client, long nextWorld, long nextHero,
                           long nextModel, long nextHostGeneration,boolean confirmed) {
        UUID nextPlayer=client.player==null?null:client.player.getUuid();
        boolean initializeHealth=spawnHealth.claim(nextPlayer,nextHostGeneration,nextHero,nextModel,confirmed);
        if(initializeHealth)pendingSpawn=new SpawnHealth(nextPlayer,nextWorld,nextHero,nextModel,nextHostGeneration);
        boolean changed=!initialized||!java.util.Objects.equals(player,nextPlayer)
            ||world!=nextWorld||hero!=nextHero||model!=nextModel
            ||hostGeneration!=nextHostGeneration||inputConfirmed!=confirmed||initializeHealth;
        if(!changed)return false;
        initialized=true;player=nextPlayer;world=nextWorld;hero=nextHero;
        model=nextModel;hostGeneration=nextHostGeneration;inputConfirmed=confirmed;
        // Same-pawn picker/focus/ability-camera transitions revoke queued
        // client/server leases too. Input confirmation is not a new pawn:
        // NativeSpawnHealthGate still prevents a reconnect from healing it.
        resetClientState();return true;
    }
    private static void resetClientState(){
        NativeLocomotionController.INSTANCE.resetSession();
        NativeFlightController.INSTANCE.resetSession();
        NativeConcussiveController.INSTANCE.reset();
        NativeBlinkController.INSTANCE.resetSession();
        NativeMotorController.INSTANCE.resetSession();
        NativeDashController.INSTANCE.resetSession();
        NativeRollController.INSTANCE.resetSession();
        NativeUltimateController.INSTANCE.resetSession();
        EarlyChineseVoices.INSTANCE.resetSession();
        HeroVoiceEvents.INSTANCE.resetSession(); // 语音挂接：身份/世界变化清除排队，保留累计诊断。
        PharahBarrageSound.INSTANCE.reset();
        BioticFieldSound.INSTANCE.reset();
        CombatFeedbackSound.INSTANCE.reset();
        NativeChargeController.INSTANCE.resetSession();
        NativeMeleeController.INSTANCE.resetSession();
        NativeDeflectController.INSTANCE.resetSession();
        NativeSustainController.INSTANCE.resetSession();
        NativeInfraSightController.INSTANCE.reset();
        NativeBioticController.INSTANCE.resetSession();
        NativePulseController.INSTANCE.resetSession();
        NativeRecallController.INSTANCE.resetSession();
        NativeReaperController.INSTANCE.resetSession();
        NativeWraithController.INSTANCE.resetSession();
        NativeShadowController.INSTANCE.resetSession();
        NativeGrappleController.INSTANCE.revalidateSession(player,world,hero,model,hostGeneration);
        NativeMeiSkillController.INSTANCE.resetSession();
        NativeJunkratController.INSTANCE.resetSession();
        NativeHanzoSkillController.INSTANCE.resetSession();
        NativeTorbjornController.INSTANCE.resetSession();
        HeroClientModules.revalidateSession(player,world,hero,model,hostGeneration);
        NativePortalController.INSTANCE.resetSession();
        NativeUtilityController.INSTANCE.resetSession();
        TwilightBossMenu.reset();
        PortalMenu.reset();
        NativeDeadeyeController.INSTANCE.resetSession();
        WallClimbController.INSTANCE.resetSession();
    }
    static void disconnected(){resetForTests();resetClientState();}

    /** Must run on the integrated server thread. */
    static void resetServerState() {
        var health=pendingSpawn;pendingSpawn=null;
        if(health!=null&&health.player().equals(player)&&health.world()==world&&health.hero()==hero&&health.model()==model&&health.source()==hostGeneration){
            var server=MinecraftClient.getInstance().getServer();var p=server==null?null:server.getPlayerManager().getPlayer(health.player());
            // Match the existing full-health creative initialization contract.
            // No respawn, survival heal, same-pawn reader reconnect or Q credit.
            if(p!=null&&p.isAlive()&&p.isCreative()&&NativeWorldIdentity.of(server,p.getWorld().getRegistryKey())==health.world())p.setHealth(p.getMaxHealth());
        }
        // An admitted potion belongs to its actual MC victim, not the caster's
        // current native model. Keep the remaining two-second slow on hero/world
        // changes; server ticks expire it and server stopping clears it in close().
        NativeDeadeyeRuntime.resetSession();
        HanzoSonicArrowRuntime.resetSession();
        NativeCombatRuntime.resetSession();
        NativeConcussiveRuntime.resetSession();
        NativeDashRuntime.resetSession();
        NativeUltimateRuntime.resetSession();
        NativeVisorRuntime.resetSession();
        NativeMeleeRuntime.resetSession();
        NativeDeflectRuntime.resetSession();
        NativeSustainRuntime.resetSession();
        NativeBioticRuntime.resetSession();
        // integrator: same-pawn transitions preserve Pulse; revalidate after configure below.
        NativeReaperRuntime.resetSession();
        NativeWraithRuntime.resetSession();
        NativeShadowRuntime.resetSession();
        NativeVenomRuntime.resetSession();
        NativeBlizzardRuntime.resetSession();
        NativeIceWallRuntime.resetSession();
        NativeJunkratRuntime.resetSession();
        NativeHanzoSkillRuntime.resetSession();
        NativeTorbjornRuntime.revalidateSession(player,world,hero,model,hostGeneration);
        HeroServerModules.revalidateSession(player,world,hero,model,hostGeneration);
        NativePortalRuntime.resetSession();
        NativeEliminationRuntime.configure(player,world,hero,model,hostGeneration);
        NativePulseRuntime.revalidateSession(player,world,hero,model,hostGeneration);
        NativeRecallRuntime.configure(player,world,hero,model,hostGeneration);
        NativeCombatFeedback.configure(player,world,hero,model,hostGeneration);
        NativeSoulRuntime.configure(player,world,hero,model,hostGeneration);
    }

    static void resetForTests() {
        initialized=inputConfirmed=false;player=null;world=hero=model=hostGeneration=0;
        spawnHealth.reset();pendingSpawn=null;
    }
}
