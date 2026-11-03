package lab.owmcguest;

import com.google.gson.*;
import java.util.*;
import net.minecraft.client.MinecraftClient;

/** 语音挂接：装弹完成与低频闲聊。前者必须有原版读数，后者只是MC适配策略。 */
final class HeroVoiceOptionalClient implements AutoCloseable {
    private final HeroVoiceEvents voice;
    private final HeroVoiceAmmoReader ammo=new HeroVoiceAmmoReader();
    private final Map<String,HeroVoicePolicy.Reload> magazines=new HashMap<>();
    private final Random random=new Random();
    private final boolean idleEnabled=Boolean.getBoolean("owmc.heroVoiceIdle");
    private HeroVoiceRuntime.Binding binding;
    private long lastSerial,lastTick,lastActivity,nextIdle,refillBlockedUntil,sequence,completions,idles,lastCompletion;
    private long combatRevision=-1,admitted=-1;
    private JsonObject reloadStatus=new JsonObject();
    HeroVoiceOptionalClient(HeroVoiceEvents voice){this.voice=voice;}
    private static JsonObject json(String source){try{return JsonParser.parseString(source).getAsJsonObject();}catch(Exception ignored){return new JsonObject();}}
    private static boolean active(String source){var o=json(source);for(String key:List.of("active","aiming","casting"))if(o.has(key)&&o.get(key).getAsBoolean())return true;return false;}
    void activity(String event){
        if(event.equals("idle"))return;
        long now=System.nanoTime();lastActivity=now;nextIdle=now+(90+random.nextInt(91))*1_000_000_000L;
        if(event.startsWith("ability:")||event.equals("ult_cast"))refillBlockedUntil=now+2_000_000_000L;
    }
    void tick(MinecraftClient client,HeroVoiceRuntime.Binding scope,boolean channelQuiet){
        long now=System.nanoTime();
        if(!scope.same(binding)){reset();binding=scope;activity("scope");}
        if(lastTick!=0&&now-lastTick>250_000_000L){magazines.clear();activity("client-gap");}
        lastTick=now;
        var host=HostPoseReader.INSTANCE.latest();if(host==null||!host.inputActive()||!client.player.isAlive())return;
        String hero=HeroVoicePolicy.heroName(scope.hero());
        var sample=ammo.poll(host,scope);
        if(sample.serial()!=lastSerial){
            lastSerial=sample.serial();boolean complete=false;
            if(!sample.error().isEmpty())magazines.clear();
            boolean blocked=now<refillBlockedUntil||hero.equals("tracer")&&active(NativeRecallRuntime.status)
                ||hero.equals("mccree")&&active(NativeRollController.status)||hero.equals("reaper")&&active(NativeShadowRuntime.status);
            var rows=new JsonArray();
            for(var slot:sample.samples()){
                var gate=magazines.computeIfAbsent(slot.slot(),key->new HeroVoicePolicy.Reload());
                if(gate.observe(slot.ammo(),slot.maximum(),slot.commitTick(),now,blocked))complete=true;
                var row=new JsonObject();row.addProperty("slot",slot.slot());row.addProperty("ammo",slot.ammo());row.addProperty("maximum",slot.maximum());
                row.addProperty("commitTick",slot.commitTick());row.addProperty("evidence",slot.evidence());rows.add(row);
            }
            if(complete&&(lastCompletion==0||now-lastCompletion>500_000_000L)){
                lastCompletion=now;completions++;voice.emit("reload",++sequence,"native-magazine","");
            }
            reloadStatus=new JsonObject();reloadStatus.addProperty("ready",sample.error().isEmpty());reloadStatus.addProperty("error",sample.error());
            reloadStatus.addProperty("completions",completions);reloadStatus.addProperty("abilityRefillBlocked",blocked);reloadStatus.add("slots",rows);
        }
        long revision=HeroVoiceRuntime.combatRevision();
        var combat=json(NativeCombatRuntime.status);long shots=combat.has("admitted")?combat.get("admitted").getAsLong():-1;
        if(combatRevision!=revision||admitted!=shots){combatRevision=revision;admitted=shots;activity("combat");}
        var p=client.player;
        var effects=json(HeroVoiceRuntime.statusReport);
        boolean affected=effects.has("active")&&effects.getAsJsonArray("active").size()>0;
        if(host.movementBits()!=0||p.getVelocity().horizontalLengthSquared()>.01||p.hurtTime>0
            ||p.getHealth()<p.getMaxHealth()*.5f||p.getAbilities().flying||client.currentScreen!=null||affected){activity("busy");return;}
        if(idleEnabled&&channelQuiet&&now>=nextIdle&&now-lastActivity>=90_000_000_000L&&voice.hasClip(hero,"idle")){
            idles++;voice.emit("idle",++sequence,"mc-idle-policy","");nextIdle=now+(120+random.nextInt(121))*1_000_000_000L;
        }
    }
    JsonObject status(){
        var out=new JsonObject();out.add("reload",reloadStatus);out.add("mcStatus",json(HeroVoiceRuntime.statusReport));out.add("statusLab",json(HeroVoiceStatusLab.status));
        var idle=new JsonObject();long now=System.nanoTime();idle.addProperty("enabled",idleEnabled);idle.addProperty("scheduled",idles);
        idle.addProperty("quietSeconds",lastActivity==0?0:Math.max(0,(now-lastActivity)/1_000_000_000L));idle.addProperty("nextInSeconds",Math.max(0,(nextIdle-now)/1_000_000_000L));
        idle.addProperty("policy","MC适配: 90-180秒无战斗且静止后才候选，之后至少120秒；默认关闭");out.add("idle",idle);return out;
    }
    void reset(){binding=null;magazines.clear();ammo.reset();reloadStatus=new JsonObject();lastSerial=lastTick=lastActivity=nextIdle=refillBlockedUntil=lastCompletion=0;combatRevision=admitted=-1;}
    @Override public void close(){reset();}
}
