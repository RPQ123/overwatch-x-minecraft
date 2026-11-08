package lab.owmcguest;

import com.google.gson.JsonObject;
import java.util.*;
import java.util.concurrent.ArrayBlockingQueue;
import net.minecraft.client.MinecraftClient;
import net.minecraft.client.sound.PositionedSoundInstance;
import net.minecraft.client.sound.SoundInstance;
import net.minecraft.entity.LivingEntity;
import net.minecraft.sound.SoundCategory;

/** 语音挂接：私有清单与真实事件，不读取按键或增加原生回调。 */
public final class HeroVoiceEvents implements AutoCloseable {
    public static final HeroVoiceEvents INSTANCE=new HeroVoiceEvents();
    private static final org.slf4j.Logger LOG=org.slf4j.LoggerFactory.getLogger("owmc-hero-voice");
    private record Key(String hero,String event) {}
    private record Event(HeroVoiceRuntime.Binding binding,String event,long token,long ns,String signal,String variant) {}
    private final HeroVoiceAssets assets=new HeroVoiceAssets();
    private final HeroVoiceEffects effects=new HeroVoiceEffects(); // 语音挂接：位置音效不占人声。
    private List<HeroVoiceAssets.Clip> effectClips=List.of();
    private final HeroVoiceSignals signals=new HeroVoiceSignals(this);
    private final HeroVoiceKillGate killGate=new HeroVoiceKillGate(); // 语音挂接：单杀概率与连杀保底。
    private final ArrayBlockingQueue<Event> queue=new ArrayBlockingQueue<>(64);
    private final Map<Key,List<HeroVoiceAssets.Clip>> bank=new HashMap<>();
    private final Map<Key,String> lastVariant=new HashMap<>();
    private final Map<Key,Long> lastPlayed=new HashMap<>();
    private final Map<String,Long> seen=new HashMap<>(),counts=new LinkedHashMap<>(),heroCounts=new LinkedHashMap<>(),admitted=new LinkedHashMap<>();
    private final Random random=new Random();
    private HeroVoiceRuntime.Binding binding;
    private long epoch,frame,frameWall,expired,duplicates,rejected,missingClips,observedPlaying;
    private int loadedClips,manifestEntries,missingFiles;
    private String error="等待私有语音清单",lastHash="",lastEvent="",lastHero="",lastOrigin="",lastAsset="";
    private boolean reloading,closed,packReady;
    private String assetError="";
    private String lastResolvedSound="",lastSignal="";
    private HeroVoiceAssets.Loaded pendingPack;
    private long lastPlayedNanos,lastPlayedWallMs;
    private long resourceReloadsRequested,resourceReloadsSkipped;
    private String resourceReuseReason="not-checked";
    private final Set<String> nativeOwned=Set.copyOf(Arrays.stream(System.getProperty("owmc.heroVoiceNativeOwned","").split(",")).map(String::trim).filter(s->!s.isEmpty()).toList());
    private final boolean enabled=Boolean.parseBoolean(System.getProperty("owmc.heroVoices","true"));
    static volatile String status="{}";

    private interface User32 extends com.sun.jna.win32.StdCallLibrary {
        com.sun.jna.Pointer GetForegroundWindow();int GetWindowThreadProcessId(com.sun.jna.Pointer window,com.sun.jna.ptr.IntByReference pid);
    }
    private static final class Focus {static final User32 USER=com.sun.jna.Native.load("user32",User32.class);}
    private HeroVoiceRuntime.Binding current(MinecraftClient client){
        var h=HostPoseReader.INSTANCE.latest();long now=System.currentTimeMillis();
        if(h==null||h.flags()!=1||h.generation()==0||client.player==null||client.world==null||client.getServer()==null)return null;
        if(h.frame()!=frame){frame=h.frame();frameWall=now;}
        if(now<frameWall||now-frameWall>150)return null;
        long hero=NativeLocomotionController.INSTANCE.hero(),model=NativeLocomotionController.INSTANCE.modelId();
        var pid=new com.sun.jna.ptr.IntByReference();Focus.USER.GetWindowThreadProcessId(Focus.USER.GetForegroundWindow(),pid);
        if(model==0||HeroVoicePolicy.heroName(hero).isEmpty()||pid.getValue()!=h.pid())return null;
        // 语音挂接：悬停/菜单不准入；保留旧死神已认证Q电影锁与MC死亡界面例外。
        if(!h.inputActive()&&client.player.isAlive()){
            var phase=NativeReaperRuntime.view;
            boolean nativeCast=hero==NativeReaperRuntime.HERO&&EarlyChineseVoices.INSTANCE.reaperCasting(h.generation(),model,NativeWorldIdentity.of(client.getServer(),client.world.getRegistryKey()),now);
            if(!nativeCast&&(hero!=NativeReaperRuntime.HERO||phase==null||phase.scope().source()!=h.generation()||phase.scope().model()!=model
                ||phase.scope().world()!=NativeWorldIdentity.of(client.getServer(),client.world.getRegistryKey())||phase.begin()<=0
                ||now-phase.wall()<0||now-phase.wall()>150))return null; // 语音挂接：已认证动画Begin不能被电影锁清空声道。
        }
        return new HeroVoiceRuntime.Binding(epoch,h.generation(),model,NativeWorldIdentity.of(client.getServer(),client.world.getRegistryKey()),hero,client.player.getUuid(),now);
    }
    void emit(String event,long token,String signal,String variant){
        if(binding==null||token<=0||!HeroVoicePolicy.allowed(event)||HeroVoicePolicy.priority(event)==0)return;
        // 语音挂接：无明确台词的技能不进仲裁队列，避免吞掉同帧真实击杀语音。
        if(HeroVoicePolicy.legacyOwned(binding.hero(),event)||!hasClip(HeroVoicePolicy.heroName(binding.hero()),event))return;
        admitted.merge(event,1L,Long::sum);
        if(!queue.offer(new Event(binding,event,token,System.nanoTime(),signal,variant)))rejected++;
    }
    void tick(MinecraftClient client){
        if(closed)return;
        load(client);
        // 语音挂接：MC停顿/断流后重新建立边沿基线，不把旧成功计数当新施法。
        if(binding!=null&&System.currentTimeMillis()-binding.wall()>200){queue.clear();signals.rebaseline();seen.clear();} // 语音挂接：身份不变时保留MC待建墙确认。
        var next=enabled?current(client):null;
        HeroVoiceMovementSounds.bind(next); // 语音挂接：只匹配当前原版英雄对应的MC本玩家。
        // W3: only four explicitly approved Winston SFX, with native ownership dedupe.
        effects.tick(client,next,effectClips);
        if(next==null){
            if(binding!=null){queue.clear();signals.reset();killGate.reset();seen.clear();lastPlayed.clear();HeroVoiceChannel.reset(client);}
            binding=null;HeroVoiceRuntime.unbind();publish(client);return;
        }
        if(!next.same(binding)){queue.clear();seen.clear();lastPlayed.clear();signals.reset();killGate.reset();HeroVoiceChannel.reset(client);}
        binding=next;HeroVoiceRuntime.bind(next);
        if(!client.player.isAlive())killGate.reset();
        if(!reloading){
            signals.tick(client,next);
            HeroVoiceRuntime.Cue cue;
            while((cue=HeroVoiceRuntime.poll())!=null){
                if(!next.same(cue.binding())){rejected++;continue;}
                if(!HeroVoicePolicy.allowed(cue.event()))continue; // 语音挂接：旧生产者不得恢复已清退类别。
                long age=System.nanoTime()-cue.observedNs();if(age<0||age>300_000_000L){expired++;continue;}
                if(cue.event().equals("kill")){
                    String heroName=HeroVoicePolicy.heroName(next.hero());
                    if(!hasClip(heroName,"kill")&&!hasClip(heroName,"multikill"))continue;
                    if(!killGate.observe(System.nanoTime()/1_000_000,random))continue;
                }
                admitted.merge(cue.event(),1L,Long::sum);
                if(!queue.offer(new Event(cue.binding(),cue.event(),cue.sequence(),cue.observedNs(),"mc",cue.variant())))rejected++;
            }
            drain(client);
        }
        if(HeroVoiceChannel.playing(client))observedPlaying++;
        publish(client);
    }
    private void load(MinecraftClient client){
        if(!enabled||reloading)return;
        assets.request(client.runDirectory.toPath());var update=assets.take();if(update!=null)pendingPack=update;
        // Initial pack loading already owns a resource reload. Its sound bank
        // is not installed until the overlay completes; checking it earlier
        // would mistake the in-flight bank for a missing pack and reload twice.
        if(pendingPack==null||client.getOverlay()!=null||HeroVoiceChannel.busy(client)||effects.busy(client))return;
        var loaded=pendingPack;pendingPack=null;
        packReady=false;manifestEntries=loaded.manifestCount();missingFiles=loaded.missing();error=assetError=loaded.error();
        if(loaded.clips().isEmpty())return;
        HeroVoiceChannel.reset(client);queue.clear();
        var packs=client.getResourcePackManager();
        String packId="file/"+HeroVoiceAssets.PACK;
        boolean active=client.getResourceManager().getAllResources(net.minecraft.util.Identifier.of("owmcguest","sounds.json"))
            .stream().anyMatch(resource->resource.getPackId().equals(packId));
        resourceReuseReason=loaded.resourcesChanged()?"content-changed":loaded.missing()!=0?"missing-assets":!loaded.error().isEmpty()?"asset-error":
            !packs.getEnabledIds().contains(packId)?"pack-disabled":!active?"pack-not-active":
            loaded.clips().stream().filter(clip->!registered(client,packId,clip)).findFirst().map(clip->"unregistered:"+clip.id()).orElse("reusable");
        if(loaded.reusable(packs.getEnabledIds().contains(packId),active,clip->registered(client,packId,clip))){
            installPack(loaded);resourceReloadsSkipped++;return;
        }
        reloading=true;packs.scanPacks();
        if(!packs.getEnabledIds().contains(packId)&&!packs.enable(packId)){reloading=false;error=assetError="private voice resource pack registration failed";return;}
        resourceReloadsRequested++;
        client.reloadResources().whenComplete((ignored,failure)->client.execute(()->{
            reloading=false;
            if(failure!=null){error=assetError="private resource reload: "+failure;return;}
            installPack(loaded);
        }));
    }
    private static boolean registered(MinecraftClient client,String packId,HeroVoiceAssets.Clip clip){
        var set=client.getSoundManager().get(clip.id());
        if(set==null||set.getWeight()!=1)return false;
        var random=net.minecraft.util.math.random.Random.create(0);
        var sound=set.getSound(random);
        if(sound.getRegistrationType()!=net.minecraft.client.sound.Sound.RegistrationType.FILE
            ||!sound.getIdentifier().equals(net.minecraft.util.Identifier.of("owmcguest","private/full/"+clip.hash()))
            ||sound.isStreamed()||sound.isPreloaded()||sound.getAttenuation()!=16
            ||sound.getVolume().get(random)!=1f||sound.getPitch().get(random)!=1f)return false;
        return client.getResourceManager().getResource(sound.getLocation()).filter(resource->resource.getPackId().equals(packId)).isPresent();
    }
    private void installPack(HeroVoiceAssets.Loaded loaded){
        bank.clear();lastVariant.clear();
        effectClips=loaded.clips().stream().filter(c->WinstonAudioCatalog.allowed(c.hero(),c.event(),c.hash())).toList();
        for(var clip:loaded.clips())if(!WinstonAudioCatalog.allowed(clip.hero(),clip.event(),clip.hash()))bank.computeIfAbsent(new Key(clip.hero(),clip.event()),key->new ArrayList<>()).add(clip);
        loadedClips=loaded.clips().size();packReady=true;
    }
    private void drain(MinecraftClient client){
        long now=System.nanoTime();Event candidate=null,event;
        while((event=queue.poll())!=null){
            if(binding==null||!HeroVoicePolicy.allowed(event.event())||!binding.same(event.binding())||HeroVoicePolicy.legacyOwned(binding.hero(),event.event())
                ||nativeOwned.contains(event.event())||nativeOwned.contains(HeroVoicePolicy.heroName(binding.hero())+":"+event.event())){rejected++;continue;}
            if(now-event.ns()<0||now-event.ns()>300_000_000L){expired++;continue;}
            if(!client.player.isAlive()){rejected++;continue;}
            String token=event.signal()+":"+event.event();long old=seen.getOrDefault(token,0L);
            if(event.token()<=old){duplicates++;continue;}seen.put(token,event.token());
            Key key=new Key(HeroVoicePolicy.heroName(binding.hero()),event.event());
            if((event.event().equals("kill")||event.event().equals("multikill"))&&!killGate.canSpeak(now/1_000_000))continue;
            // 语音挂接：同一技能跨新旧入口/重绑共享冷却；先过滤，避免挡住可播的低优先级事件。
            if(HeroVoiceSkillCooldowns.applies(event.event())){
                if(!HeroVoiceChannel.skillCooldowns.admit(key.hero(),key.event(),now/1_000_000))continue;
            }else if(lastPlayed.containsKey(key)&&now-lastPlayed.get(key)<HeroVoicePolicy.cooldownMs(event.event())*1_000_000L)continue;
            if(candidate==null||HeroVoicePolicy.priority(event.event())>HeroVoicePolicy.priority(candidate.event()))candidate=event;
        }
        // 语音挂接：保底在冷却/高优先级语音结束后重试，只有真正播出才清零连杀。
        if(binding!=null&&client.player.isAlive()&&killGate.pending(now/1_000_000)){
            var killKey=new Key(HeroVoicePolicy.heroName(binding.hero()),"kill");
            String guaranteed=hasClip(killKey.hero(),"multikill")?"multikill":"kill";
            if(!nativeOwned.contains("kill")&&!nativeOwned.contains(killKey.hero()+":kill")
                &&!nativeOwned.contains(guaranteed)&&!nativeOwned.contains(killKey.hero()+":"+guaranteed)&&hasClip(killKey.hero(),guaranteed)
                &&(!lastPlayed.containsKey(killKey)||now-lastPlayed.get(killKey)>=HeroVoicePolicy.cooldownMs("kill")*1_000_000L)
                &&(candidate==null||HeroVoicePolicy.priority(candidate.event())<=HeroVoicePolicy.priority("kill")))
                candidate=new Event(binding,guaranteed,0,now,"mc-kill-guarantee","");
        }
        if(candidate==null)return;
        if((candidate.event().equals("kill")||candidate.event().equals("multikill"))&&!killGate.canSpeak(now/1_000_000))return;
        Key key=new Key(HeroVoicePolicy.heroName(binding.hero()),candidate.event());var clips=bank.get(key);
        if(clips==null||clips.isEmpty()){missingClips++;return;}
        // 语音挂接：固定半藏自己的大招原声；缺失时报错，绝不随机回退到另一语言。
        String fixed=HeroVoicePolicy.fixedHash(key.hero(),key.event());
        String chosen=fixed.isEmpty()?HeroVoicePolicy.nextHash(clips.stream().map(HeroVoiceAssets.Clip::hash).toList(),lastVariant.get(key),random):fixed;
        var clip=clips.stream().filter(c->c.hash().equals(chosen)).findFirst().orElse(null);
        if(clip==null){missingClips++;error="missing fixed voice: "+chosen;return;}
        if(client.getSoundManager().get(clip.id())==null){error="private sound unavailable: "+clip.hash();missingClips++;return;}
        var sound=new PositionedSoundInstance(clip.id(),SoundCategory.VOICE,1f,1f,SoundInstance.createRandom(),false,0,SoundInstance.AttenuationType.NONE,0,0,0,true);
        if(!HeroVoiceChannel.play(client,sound,"thnu-full",candidate.event(),clip.durationMs()))return;
        lastResolvedSound=sound.getSound()==null?"unresolved":sound.getSound().getIdentifier().toString();
        lastVariant.put(key,clip.hash());lastPlayed.put(key,now);
        if(candidate.event().equals("kill")||candidate.event().equals("multikill")){
            // 语音挂接：多杀与普通击杀共用全英雄10秒硬冷却，不能换事件或切人绕过。
            lastPlayed.put(new Key(clip.hero(),"kill"),now);lastPlayed.put(new Key(clip.hero(),"multikill"),now);killGate.played(now/1_000_000);
        }
        lastSignal=candidate.signal(); // 语音挂接：日志可区分半藏Begin与旧的放龙成功计数。
        played(clip.hero(),candidate.event(),clip.hash(),clip.id().toString(),"thnu-full");
    }
    private void played(String hero,String event,String hash,String asset,String origin){
        lastPlayedNanos=System.nanoTime();lastPlayedWallMs=System.currentTimeMillis(); // 语音挂接：核验音频起点。
        counts.merge(event,1L,Long::sum);heroCounts.merge(hero+":"+event,1L,Long::sum);
        lastHero=hero;lastEvent=event;lastHash=hash;lastAsset=asset;lastOrigin=origin;
        LOG.info("heroVoice played hero={} event={} hash={} origin={} asset={} resolved={} signal={}",hero,event,hash,origin,asset,lastResolvedSound,lastSignal);
    }
    /** 语音挂接：旧入口只上报成功取得声道的播放，绝不再播放一份。 */
    void legacyPlayed(MinecraftClient client,String raw,PositionedSoundInstance sound){
        String name=HeroVoicePolicy.heroName(NativeLocomotionController.INSTANCE.hero());
        String event=raw.startsWith("hero.")?"select":raw.equals("mccree.flashbang")?"ability:flashbang":raw.equals("soldier76.bioticfield")?"ability:biotic_field":raw.equals("reaper.shadow")?"ability:shadow_step":"ult_cast";
        String stem=event.equals("select")?name+"-select":raw.equals("mccree.flashbang")?"mccree-e1":name+"-q";
        String hash=assets.legacyHash(stem),id=sound.getSound()==null?raw:sound.getSound().getIdentifier().toString();
        if(raw.equals("reaper.blossom"))hash=HeroVoicePolicy.REAPER_ULT_HASH; // 语音挂接：固定已验证中文素材，补齐过去未记录的旧入口hash。
        if(id.endsWith("genji_dragonblade"))hash="1dcda15f9f4a10451be06679c1b32be73f72b8b7e6983648a3638e02fa2723d5";
        lastResolvedSound=id;
        lastSignal=switch(raw){ // 语音挂接：旧素材播放也记录实际最早原版信号，便于逐英雄核验。
            case "genji.dragonblade"->"native:genji-0317:17-begin";
            case "mccree.deadeye"->"native:mccree-022f:18-begin";
            case "pharah.barrage"->"native:pharah-002b:12-begin";
            case "soldier76.visor"->"native:soldier76-0259:15-begin";
            case "tracer.pulse"->"native:tracer-0034:3-begin";
            case "reaper.blossom"->EarlyChineseVoices.INSTANCE.reaperSignal();
            default->"legacy:"+raw;
        };
        played(name,event,hash,id,"legacy");
    }
    /** 语音挂接：旧共享mixin的兼容空入口；不再产生任何跳跃语音。 */
    public static void onJump(LivingEntity entity){
        // 语音挂接：保留共享mixin ABI；全英雄停止跳跃语气声。
    }
    private void publish(MinecraftClient client){
        // 语音挂接：明确区分后台转换、待安装、资源重载和旧选人延迟，供录音前等待。
        boolean manifestCurrent=assets.current(),pendingResource=assets.pending()||pendingPack!=null;
        var out=new JsonObject();out.addProperty("enabled",enabled);out.addProperty("loadedClips",loadedClips);out.addProperty("manifestEntries",manifestEntries);out.addProperty("missingFiles",missingFiles);out.addProperty("loading",reloading||pendingResource);out.addProperty("resourceReloading",reloading);out.addProperty("error",error);
        out.addProperty("resourceReloadsRequested",resourceReloadsRequested);out.addProperty("resourceReloadsSkipped",resourceReloadsSkipped);
        out.addProperty("resourceReuseReason",resourceReuseReason);
        out.addProperty("assetsReady",enabled&&!closed&&packReady&&loadedClips>0&&missingFiles==0&&!reloading&&!pendingResource&&manifestCurrent);
        out.addProperty("pendingResourceReload",enabled&&(!packReady||pendingResource||reloading||!manifestCurrent));out.addProperty("assetError",assetError);
        out.addProperty("selectionPending",EarlyChineseVoices.INSTANCE.selectionPending());
        out.addProperty("hero",binding==null?"":HeroVoicePolicy.heroName(binding.hero()));out.addProperty("lastHero",lastHero);out.addProperty("lastEvent",lastEvent);out.addProperty("lastHash",lastHash);out.addProperty("lastAsset",lastAsset);out.addProperty("lastOrigin",lastOrigin);
        out.addProperty("lastPlayedNanos",lastPlayedNanos);out.addProperty("sampledNanos",System.nanoTime());out.addProperty("lastPlayedWallMs",lastPlayedWallMs);out.addProperty("lastResolvedSound",lastResolvedSound);out.add("sfx",effects.status(client));
        var skillCooldowns=new JsonObject();skillCooldowns.addProperty("cooldownMs",HeroVoiceSkillCooldowns.COOLDOWN_MS);
        var activeSkills=new JsonObject();HeroVoiceChannel.skillCooldowns.active(System.nanoTime()/1_000_000).forEach(activeSkills::addProperty);skillCooldowns.add("remainingMs",activeSkills);
        var suppressedSkills=new JsonObject();HeroVoiceChannel.skillCooldowns.suppressed().forEach(suppressedSkills::addProperty);skillCooldowns.add("suppressed",suppressedSkills);out.add("skillCooldowns",skillCooldowns);
        out.add("iceWall",com.google.gson.JsonParser.parseString(signals.iceWallStatus())); // 语音挂接：核对建墙成功与语音次数。
        out.add("signals",com.google.gson.JsonParser.parseString(signals.counterStatus())); // 语音挂接：区分未施放、首发门控与素材缺失。
        out.add("movementMute",HeroVoiceMovementSounds.status());
        out.addProperty("lastSignal",lastSignal);
        out.add("reaperBegin",EarlyChineseVoices.INSTANCE.reaperStatus()); // 语音挂接：失败时从统一诊断读取节点/回退/固定素材状态。
        out.addProperty("optionalDisabled",true); // 语音挂接：闲聊/状态/装弹均退出默认播放。
        var excluded=new JsonObject();assets.excludedEvents.forEach(excluded::addProperty);out.add("excludedEvents",excluded);
        var killPolicy=new JsonObject();killPolicy.addProperty("singleChance",HeroVoiceKillGate.SINGLE_KILL_CHANCE);killPolicy.addProperty("guaranteeKills",HeroVoiceKillGate.GUARANTEE_KILLS);killPolicy.addProperty("streakGapMs",HeroVoiceKillGate.STREAK_GAP_MS);
        killPolicy.addProperty("available",binding!=null&&(hasClip(HeroVoicePolicy.heroName(binding.hero()),"kill")||hasClip(HeroVoicePolicy.heroName(binding.hero()),"multikill")));
        killPolicy.addProperty("cooldownMs",HeroVoiceKillGate.COOLDOWN_MS);killPolicy.addProperty("cooldownRemainingMs",killGate.cooldownRemainingMs(System.nanoTime()/1_000_000));killPolicy.addProperty("cooldownSuppressed",killGate.cooldownSuppressed);
        killPolicy.addProperty("pending",killGate.pending(System.nanoTime()/1_000_000));killPolicy.addProperty("streak",killGate.streak());killPolicy.addProperty("rolls",killGate.rolls);killPolicy.addProperty("randomAccepted",killGate.randomAccepted);killPolicy.addProperty("randomSkipped",killGate.randomSkipped);killPolicy.addProperty("guarantees",killGate.guarantees);killPolicy.addProperty("played",killGate.played);killPolicy.addProperty("expired",killGate.expired);out.add("killSpeech",killPolicy);
        var events=new JsonObject();counts.forEach(events::addProperty);out.add("events",events);var perHero=new JsonObject();heroCounts.forEach(perHero::addProperty);out.add("heroEvents",perHero);var received=new JsonObject();admitted.forEach(received::addProperty);out.add("admitted",received);
        var available=new JsonObject();bank.forEach((key,clips)->available.addProperty(key.hero()+":"+key.event(),clips.size()));out.add("available",available);
        out.addProperty("playing",HeroVoiceChannel.playing(client));out.addProperty("observedPlayingTicks",observedPlaying);out.addProperty("channelOwner",HeroVoiceChannel.owner);out.addProperty("channelEvent",HeroVoiceChannel.event);out.addProperty("preempted",HeroVoiceChannel.preempted);out.addProperty("channelRefused",HeroVoiceChannel.refused);
        out.addProperty("channelBusy",HeroVoiceChannel.busy(client));
        out.addProperty("nativeOwned",String.join(",",nativeOwned));
        out.addProperty("expired",expired);out.addProperty("duplicates",duplicates);out.addProperty("rejected",rejected);out.addProperty("missingClips",missingClips);out.addProperty("mcKills",HeroVoiceRuntime.kills);out.addProperty("mcPains",HeroVoiceRuntime.pains);
        out.addProperty("killPolicy","MC 适配: 服务端 LivingEntity 真死亡且 DamageSource 攻击者是本玩家");out.addProperty("nativeOverlapVerified",false);status=out.toString();
    }
    boolean hasClip(String hero,String event){var clips=bank.get(new Key(hero,event));return clips!=null&&!clips.isEmpty();}
    void resetSession(){epoch++;binding=null;HeroVoiceMovementSounds.bind(null);queue.clear();seen.clear();lastPlayed.clear();signals.reset();killGate.reset();HeroVoiceRuntime.unbind();HeroVoiceChannel.reset(MinecraftClient.getInstance());effects.reset(MinecraftClient.getInstance());}
    @Override public void close(){closed=true;resetSession();assets.close();}
}
