package lab.owmcguest;

import net.minecraft.client.MinecraftClient;
import net.minecraft.client.sound.PositionedSoundInstance;
import net.minecraft.sound.SoundEvents;

/** MC sound adaptation: play locally on the observed native Begin, before the
 * server task/rewind/End receipt. This is playback submission, not measured DAC latency. */
final class RecallStartSound {
    private static final RecallSoundGate gate=new RecallSoundGate();
    private static long starts,lastBegin,lastObservedWall,lastPlayWall;
    static volatile String status="{\"starts\":0}";
    static void begin(MinecraftClient client,NativeRecallRuntime.Scope scope,long begin,long observed){
        var key=new RecallSoundGate.Scope(scope.owner(),scope.world(),scope.source(),scope.model());
        if(!gate.claim(key,begin))return;
        client.getSoundManager().play(PositionedSoundInstance.master(SoundEvents.ENTITY_ENDERMAN_TELEPORT,1.8f,.5f));
        starts++;lastBegin=begin;lastObservedWall=observed;lastPlayWall=System.currentTimeMillis();
        var o=new com.google.gson.JsonObject();o.addProperty("starts",starts);o.addProperty("nativeBegin",lastBegin);
        o.addProperty("observedWall",lastObservedWall);o.addProperty("playWall",lastPlayWall);o.addProperty("submitDelayMs",lastPlayWall-lastObservedWall);
        o.addProperty("source",scope.source());o.addProperty("world",scope.world());o.addProperty("model",scope.model());o.addProperty("trigger","native-recall-Begin-client");
        status=o.toString();
    }
}
