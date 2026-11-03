package lab.owmcguest;

import net.fabricmc.api.ModInitializer;
import net.fabricmc.fabric.api.networking.v1.ServerPlayConnectionEvents;
import net.fabricmc.fabric.api.event.lifecycle.v1.ServerLifecycleEvents;
import net.fabricmc.fabric.api.event.lifecycle.v1.ServerTickEvents;
import net.minecraft.block.Blocks;
import net.minecraft.util.math.BlockPos;

public final class GuestMod implements ModInitializer {
    public static volatile BlockPos proofBlock;
    @Override public void onInitialize() {
        CombatParticles.register();
        WidowSpiderEntity.register();
        SummonedMobLifecycle.register();
        if(Boolean.getBoolean("owmc.dayNightCycle") && !Boolean.getBoolean("owmc.frameExport")) {
            ServerLifecycleEvents.SERVER_STARTED.register(NativeWorldSettings::apply);
            net.fabricmc.fabric.api.event.lifecycle.v1.ServerTickEvents.END_SERVER_TICK.register(NativeWorldSettings::tick);
        }
        if(Boolean.getBoolean("owmc.frameExport")) {
            HeroVoiceRuntime.register(); // 语音挂接：独立MC权威事件，不消费源氏击杀重置队列。
            ServerLifecycleEvents.SERVER_STARTED.register(PortalCatalog::refresh);
            ServerTickEvents.END_SERVER_TICK.register(TwilightForestTrial::tick);
            ServerTickEvents.END_SERVER_TICK.register(TwilightBossTravel::tick);
            ServerTickEvents.END_SERVER_TICK.register(RandomBossTravel::tick);
            ServerTickEvents.END_SERVER_TICK.register(AoABossTravel::tick);
            ServerTickEvents.END_SERVER_TICK.register(BossObservations::tick);
            ServerLifecycleEvents.SERVER_STOPPING.register(server->AoABossTravel.close());
            ServerLifecycleEvents.SERVER_STOPPING.register(server->RandomBossTravel.close());
            ServerLifecycleEvents.SERVER_STOPPING.register(server->TwilightBossTravel.close());
            ServerLifecycleEvents.SERVER_STOPPING.register(server->TwilightForestTrial.close());
            ServerLifecycleEvents.SERVER_STARTED.register(server->NativeCombatScene.beginSession());
            net.fabricmc.fabric.api.event.lifecycle.v1.ServerTickEvents.END_SERVER_TICK.register(NativeCombatScene::recoverOrphans);
            ServerLifecycleEvents.SERVER_STARTED.register(NativeWorldSettings::apply);
            net.fabricmc.fabric.api.event.lifecycle.v1.ServerTickEvents.END_SERVER_TICK.register(NativeWorldSettings::tick);
            net.fabricmc.fabric.api.event.lifecycle.v1.ServerTickEvents.END_SERVER_TICK.register(NativeCombatRuntime::tick);
            ServerTickEvents.END_SERVER_TICK.register(HanzoSonicArrowRuntime::tick);
            ServerTickEvents.END_SERVER_TICK.register(NativeMeiFreezeRuntime::tick);
            ServerLifecycleEvents.SERVER_STOPPING.register(server->NativeMeiFreezeRuntime.close());
            ServerLifecycleEvents.SERVER_STOPPING.register(server->HanzoSonicArrowRuntime.resetSession());
            net.fabricmc.fabric.api.event.lifecycle.v1.ServerTickEvents.END_SERVER_TICK.register(NativeDashRuntime::tick);
            net.fabricmc.fabric.api.event.lifecycle.v1.ServerTickEvents.END_SERVER_TICK.register(NativeEliminationRuntime::tick);
            net.fabricmc.fabric.api.event.lifecycle.v1.ServerTickEvents.END_SERVER_TICK.register(NativeCombatFeedback::tick);
            net.fabricmc.fabric.api.event.lifecycle.v1.ServerTickEvents.END_SERVER_TICK.register(NativeBossRuntime::tick);
            net.fabricmc.fabric.api.event.lifecycle.v1.ServerTickEvents.START_SERVER_TICK.register(NativeDeflectRuntime::tick);
            net.fabricmc.fabric.api.event.lifecycle.v1.ServerTickEvents.END_SERVER_TICK.register(NativeSustainRuntime::tick);
            ServerTickEvents.END_SERVER_TICK.register(NativeBioticRuntime::tick);
            ServerTickEvents.END_SERVER_TICK.register(NativePulseRuntime::tick);
            ServerTickEvents.END_SERVER_TICK.register(NativeRecallRuntime::tick);
            ServerTickEvents.END_SERVER_TICK.register(NativeReaperRuntime::tick);
            ServerTickEvents.END_SERVER_TICK.register(NativeWraithRuntime::tick);
            ServerTickEvents.END_SERVER_TICK.register(NativeShadowRuntime::tick);
            ServerTickEvents.END_SERVER_TICK.register(NativeVenomRuntime::tick);
            ServerTickEvents.END_SERVER_TICK.register(NativeBlizzardRuntime::tick);
            ServerTickEvents.END_SERVER_TICK.register(NativeIceWallRuntime::tick);
            ServerTickEvents.END_SERVER_TICK.register(NativeJunkratRuntime::tick);
            ServerTickEvents.END_SERVER_TICK.register(NativeHanzoSkillRuntime::tick);
            ServerTickEvents.END_SERVER_TICK.register(NativeTorbjornRuntime::tick);
            ServerTickEvents.END_SERVER_TICK.register(HeroServerModules::tick);
            ServerTickEvents.END_SERVER_TICK.register(NativeSoulRuntime::tick);
            net.fabricmc.fabric.api.entity.event.v1.ServerLivingEntityEvents.ALLOW_DAMAGE.register((entity,source,amount)->{NativeDeflectRuntime.beforeDamage(entity,source);return !NativeSustainRuntime.protects(entity)&&!NativeRecallRuntime.protects(entity)&&!NativeWraithRuntime.protects(entity);});
            net.fabricmc.fabric.api.entity.event.v1.ServerLivingEntityEvents.AFTER_DAMAGE.register((entity,source,base,damage,blocked)->NativeDeflectRuntime.afterDamage(entity,source));
            net.fabricmc.fabric.api.entity.event.v1.ServerLivingEntityEvents.AFTER_DEATH.register(NativeDeflectRuntime::afterDamage);
            net.fabricmc.fabric.api.event.lifecycle.v1.ServerTickEvents.END_SERVER_TICK.register(VillageWorldSetup::tick);
            ServerLifecycleEvents.SERVER_STOPPED.register(server->NativeDashRuntime.close());
            ServerLifecycleEvents.SERVER_STOPPING.register(server->NativeCombatRuntime.close());
            ServerLifecycleEvents.SERVER_STOPPING.register(server->NativeCombatFeedback.resetSession());
            ServerLifecycleEvents.SERVER_STOPPED.register(server->NativeMeleeRuntime.close());
            ServerLifecycleEvents.SERVER_STOPPED.register(server->NativePortalRuntime.close());
            ServerLifecycleEvents.SERVER_STOPPED.register(server->NativeDeflectRuntime.resetSession());
            ServerLifecycleEvents.SERVER_STOPPED.register(server->NativeSustainRuntime.resetSession());
            ServerLifecycleEvents.SERVER_STOPPED.register(server->NativeBioticRuntime.resetSession());
            ServerLifecycleEvents.SERVER_STOPPED.register(server->NativePulseRuntime.resetSession());
            ServerLifecycleEvents.SERVER_STOPPED.register(server->NativeRecallRuntime.resetSession());
            ServerLifecycleEvents.SERVER_STOPPED.register(server->NativeReaperRuntime.resetSession());
            ServerLifecycleEvents.SERVER_STOPPED.register(server->NativeWraithRuntime.resetSession());
            ServerLifecycleEvents.SERVER_STOPPED.register(server->NativeShadowRuntime.clear());
            ServerLifecycleEvents.SERVER_STOPPED.register(server->NativeVenomRuntime.clear());
            ServerLifecycleEvents.SERVER_STOPPED.register(server->NativeBlizzardRuntime.clear());
            ServerLifecycleEvents.SERVER_STOPPING.register(server->NativeIceWallRuntime.clear());  // 世界保存前移除屏障，避免残留进存档
            ServerLifecycleEvents.SERVER_STOPPED.register(server->NativeIceWallRuntime.clear());
            ServerLifecycleEvents.SERVER_STOPPED.register(server->NativeJunkratRuntime.clear());
            ServerLifecycleEvents.SERVER_STOPPED.register(server->NativeHanzoSkillRuntime.clear());
            ServerLifecycleEvents.SERVER_STOPPED.register(server->NativeTorbjornRuntime.clear());
            ServerLifecycleEvents.SERVER_STOPPING.register(server->{HanzoArrowVisualLab.cleanup();NativeCombatScene.cleanup();HeroServerModules.clear();});
            ServerLifecycleEvents.SERVER_STOPPED.register(server->NativeSoulRuntime.resetSession());
        }
        if(Boolean.getBoolean("owmc.exportPatch")) {
            ServerPlayConnectionEvents.JOIN.register((handler,sender,server)->PatchWorld.start(server,handler.player));
            ServerLifecycleEvents.SERVER_STOPPED.register(server->PatchWorld.close());
        }
        if (!Boolean.getBoolean("owmc.exportProof")) return;
        ServerPlayConnectionEvents.JOIN.register((handler, sender, server) -> {
            if (!server.isSingleplayer()) return;
            proofBlock = handler.player.getBlockPos().add(2, 0, 0);
            handler.player.getServerWorld().setBlockState(proofBlock, Blocks.STONE.getDefaultState());
            System.out.println("[OWMCGuest] Proof block placed in independent world: " + proofBlock);
        });
    }
}
