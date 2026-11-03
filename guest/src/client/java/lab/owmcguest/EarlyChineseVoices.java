package lab.owmcguest;

import com.google.gson.JsonObject;
import net.minecraft.client.MinecraftClient;
import net.minecraft.client.sound.PositionedSoundInstance;
import net.minecraft.client.sound.SoundInstance;
import net.minecraft.sound.SoundCategory;
import net.minecraft.util.Identifier;

/** Private OW1 roster selection/Barrage recordings. Existing Q/E admission stays intact. */
final class EarlyChineseVoices implements AutoCloseable {
    static final EarlyChineseVoices INSTANCE=new EarlyChineseVoices();
    private final HeroSelectCalloutGate selections=new HeroSelectCalloutGate();
    private final UltimateCalloutGate barrage=new UltimateCalloutGate();
    private final UltimateCalloutGate biotic=new UltimateCalloutGate(),visor=new UltimateCalloutGate();
    private final UltimateCalloutGate pulse=new UltimateCalloutGate(),blossom=new UltimateCalloutGate(),shadowVoice=new UltimateCalloutGate();
    private final UltimateCalloutGate blossomFallback=new UltimateCalloutGate(); // 语音挂接：原已实测runtime的同源Begin作为读失败回退，不看Q按键。
    private final NativeSkillReader skills=new NativeSkillReader();
    private final NativeSkillReader pulseSkills=new NativeSkillReader("pulse"); // 语音挂接：直接消费投掷动画Begin，不等MC炸弹生成。
    private final java.util.Map<String,PositionedSoundInstance> sounds=new java.util.HashMap<>();
    private final java.util.Map<String,Long> counts=new java.util.LinkedHashMap<>();
    private static final java.util.List<String> ROSTER=java.util.List.of("genji","mccree","pharah","reaper","soldier76","tracer","bastion","hanzo","junkrat","mei","torbjorn","widowmaker","dva","reinhardt","roadhog","winston","zarya","lucio","mercy","symmetra","zenyatta");
    private long session;private String error="",lastEvent="";
    private long reaperSource,reaperModel,reaperWorld,reaperBegin,reaperWall;
    private String reaperSignal="";private JsonObject reaperStatus=new JsonObject();
    static volatile String status="{}";
    boolean selectionPending(){return selections.pending();} // 语音挂接：供建墙语音排除选人前置阶段。
    boolean barrageSpeaking(MinecraftClient client){var sound=sounds.get("pharah.barrage");return sound!=null&&client.getSoundManager().isPlaying(sound);}
    boolean bioticSpeaking(MinecraftClient client){var sound=sounds.get("soldier76.bioticfield");return sound!=null&&client.getSoundManager().isPlaying(sound);}
    boolean reaperCasting(long source,long model,long world,long now){return reaperBegin>0&&reaperSource==source&&reaperModel==model&&reaperWorld==world&&now>=reaperWall&&now-reaperWall<=150;}
    String reaperSignal(){return reaperSignal;}
    JsonObject reaperStatus(){return reaperStatus.deepCopy();}
    private void play(MinecraftClient client,String event){
        // 语音挂接：猎空按用户要求静音选人；堡垒无字幕电子音也退出默认人声。
        if(event.startsWith("hero.")&&!HeroVoicePolicy.selectionAllowed(event.split("\\.")[1]))return;
        // 用户要求（2026-10-27）：死神不要大招语音。
        if(event.equals("reaper.blossom"))return;
        var id=Identifier.of("owmcguest",event);
        if(client.getSoundManager().get(id)==null){error=event.equals("reaper.blossom")?"死神中文大招资源未注册；刷新four_dps_voice_assets":"private recording unavailable: "+event;return;}
        var sound=new PositionedSoundInstance(id,SoundCategory.VOICE,1f,1f,SoundInstance.createRandom(),false,0,SoundInstance.AttenuationType.NONE,0,0,0,true);
        // 语音挂接：保留原素材和门控，只把播放所有权交给统一人声声道。
        String canonical=event.startsWith("hero.")?"select":event.equals("soldier76.bioticfield")?"ability:biotic_field":event.equals("reaper.shadow")?"ability:shadow_step":"ult_cast";
        if(!HeroVoiceChannel.play(client,sound,"legacy-early",canonical,30000))return;
        for(var old:sounds.values())client.getSoundManager().stop(old);sounds.clear();
        sounds.put(event,sound);HeroVoiceEvents.INSTANCE.legacyPlayed(client,event,sound);counts.merge(event,1L,Long::sum);lastEvent=event;error="";
    }
    void tick(MinecraftClient client){
        var host=HostPoseReader.INSTANCE.latest();long hero=NativeLocomotionController.INSTANCE.hero(),model=NativeLocomotionController.INSTANCE.modelId();
        if(hero!=NativePulseRuntime.HERO)pulseSkills.close();
        // flags==1 only means a real scene pose, including the picker. The
        // existing host inputActive additionally proves native first person
        // (viewMode==1) and foreground ownership; hover must never speak.
        boolean confirmed=host!=null&&host.flags()==1&&host.inputActive()&&client.player!=null&&client.player.isAlive()&&client.world!=null&&client.getServer()!=null&&model!=0;
        if(selections.observe(host==null?0:host.generation(),hero,confirmed,System.nanoTime()/1_000_000)){
            String name=switch((int)(hero&0xffff)){
                case 0x29->"genji";case 0x42->"mccree";case 8->"pharah";case 2->"reaper";
                case 0x6e->"soldier76";case 3->"tracer";case 0x15->"bastion";case 5->"hanzo";
                case 0x65->"junkrat";case 0xdd->"mei";case 6->"torbjorn";case 10->"widowmaker";
                case 0x7a->"dva";case 7->"reinhardt";case 0x40->"roadhog";case 9->"winston";
                case 0x68->"zarya";case 0x79->"lucio";case 4->"mercy";case 0x16->"symmetra";
                case 0x20->"zenyatta";default->null;
            };
            if(name!=null)play(client,"hero."+name+".select");
        }
        if(confirmed&&hero==0x02e0000000000008L){
            var state=skills.poll(host,model,hero);
            if(state!=null){
                var phase=state.entries().get("barrage");long world=NativeWorldIdentity.of(client.getServer(),client.world.getRegistryKey());
                if(phase!=null&&barrage.observe(session,host.generation(),model,world,phase.active()?phase.tick():0))play(client,"pharah.barrage");
            }else error=skills.error;
        }else if(confirmed&&hero==NativeBioticRuntime.HERO){
            var state=skills.poll(host,model,hero);long world=NativeWorldIdentity.of(client.getServer(),client.world.getRegistryKey());
            if(state!=null){var phase=state.entries().get("ultimate");if(visor.observe(session,host.generation(),model,world,phase.active()?phase.tick():0))play(client,"soldier76.visor");} // 语音挂接：0259:15 Begin，不等12瞄准阶段。
            var field=NativeBioticRuntime.view;
            long begin=field!=null&&field.source()==host.generation()&&field.world()==world&&field.model()==model&&System.currentTimeMillis()-field.wall()<250?field.nativeTick():0;
            if(biotic.observe(session,host.generation(),model,world,begin))play(client,"soldier76.bioticfield");
        }else if(confirmed&&hero==NativePulseRuntime.HERO){
            skills.close();var state=pulseSkills.poll(host,model,hero);long world=NativeWorldIdentity.of(client.getServer(),client.world.getRegistryKey());
            if(state!=null){var cast=state.entries().get("cast");if(pulse.observe(session,host.generation(),model,world,cast.active()?cast.tick():0))play(client,"tracer.pulse");}
        }else if(host!=null&&host.flags()==1&&host.generation()!=0&&hero==NativeReaperRuntime.HERO&&client.player!=null&&client.player.isAlive()&&client.world!=null&&client.getServer()!=null&&model!=0){
            // 语音挂接：Q动画9是真实施法信号；49独立采样曾静默失效，保留可见诊断及原认证回执回退。
            var state=skills.poll(host,model,hero);long world=NativeWorldIdentity.of(client.getServer(),client.world.getRegistryKey()),now=System.currentTimeMillis();
            var root=state==null?null:state.entries().get("ultimate");var animation=state==null?null:state.entries().get("animation");
            boolean direct=animation!=null&&blossom.observe(session,host.generation(),model,world,animation.active()?animation.tick():0);
            if(animation!=null&&animation.active()){reaperSource=host.generation();reaperModel=model;reaperWorld=world;reaperBegin=animation.tick();reaperWall=now;}
            var phase=NativeReaperRuntime.view;
            boolean runtimeScope=phase!=null&&phase.scope().owner().equals(client.player.getUuid())
                &&phase.scope().source()==host.generation()&&phase.scope().model()==model&&phase.scope().world()==world&&now>=phase.wall()&&now-phase.wall()<=150;
            boolean phaseFresh=runtimeScope&&phase.begin()>0; // 语音挂接：Runtime只在实际活动期发布View，结束即清空。
            boolean fallback=blossomFallback.observe(session,host.generation(),model,world,phaseFresh?phase.begin():0);
            var detail=new JsonObject();detail.addProperty("rawReady",state!=null&&animation!=null);detail.addProperty("rawError",state==null?skills.error:animation==null?"missing animation node9":"");
            detail.addProperty("rootTick",root==null?0:root.tick());detail.addProperty("rootActive",root!=null&&root.active());detail.addProperty("animationTick",animation==null?0:animation.tick());detail.addProperty("animationActive",animation!=null&&animation.active());
            detail.addProperty("directEdge",direct);detail.addProperty("runtimeFreshScope",runtimeScope);detail.addProperty("runtimeFreshActive",phaseFresh);detail.addProperty("runtimeBegin",phase==null?0:phase.begin());detail.addProperty("fallbackEdge",fallback);
            detail.addProperty("source",host.generation());detail.addProperty("model",model);detail.addProperty("world",world);detail.addProperty("fixedUltHash",HeroVoicePolicy.REAPER_ULT_HASH);detail.addProperty("voiceLanguage","zh-CN");
            detail.addProperty("clipReady",client.getSoundManager().get(Identifier.of("owmcguest","reaper.blossom"))!=null);reaperStatus=detail;
            if(direct){reaperSignal="native:reaper-0044:9-animation-begin";play(client,"reaper.blossom");}
            else if(fallback&&HeroVoiceChannel.skillCooldowns.remaining("reaper","ult_cast",System.nanoTime()/1_000_000)==0){reaperSignal="native:reaper-runtime-cast-begin";play(client,"reaper.blossom");}
            var step=NativeShadowRuntime.receipt;
            long arrival=step!=null&&step.phase()==2&&step.scope().source()==host.generation()&&step.scope().world()==world&&step.scope().model()==model&&System.currentTimeMillis()-step.wall()<250?step.confirm():0;
            if(shadowVoice.observe(session,host.generation(),model,world,arrival))play(client,"reaper.shadow");
        }else skills.close();
        var out=new JsonObject();out.addProperty("lastEvent",lastEvent);out.addProperty("error",error);
        out.add("reaperBegin",reaperStatus); // 语音挂接：失败时也保留原版节点/读取错误/固定素材可用性。
        out.addProperty("selectionDelayMs",HeroSelectCalloutGate.DELAY_MS);
        out.addProperty("lastSelectionDelayMs",selections.lastDelayMs());
        var events=new JsonObject();counts.forEach(events::addProperty);out.add("events",events);
        out.addProperty("playing",sounds.values().stream().anyMatch(s->client.getSoundManager().isPlaying(s)));
        long expected=ROSTER.stream().filter(HeroVoicePolicy::selectionAllowed).count();
        long ready=ROSTER.stream().filter(HeroVoicePolicy::selectionAllowed).filter(s->client.getSoundManager().get(Identifier.of("owmcguest","hero."+s+".select"))!=null).count();
        out.addProperty("selectionClipsReady",ready);out.addProperty("selectionRosterSize",expected);out.addProperty("mutedSelections","tracer,bastion");
        out.addProperty("ready",ready==expected&&client.getSoundManager().get(Identifier.of("owmcguest","pharah.barrage"))!=null);
        status=out.toString();
    }
    void resetSession(){
        session++;barrage.reset();biotic.reset();visor.reset();pulse.reset();blossom.reset();blossomFallback.reset();shadowVoice.reset();skills.close();pulseSkills.close();selections.cancelPending();
        reaperSource=reaperModel=reaperWorld=reaperBegin=reaperWall=0;reaperSignal="";reaperStatus=new JsonObject();
        var client=MinecraftClient.getInstance();for(var sound:sounds.values())client.getSoundManager().stop(sound);sounds.clear();
        // Keep last confirmed hero across dimensions/death/model recreation.
    }
    @Override public void close(){resetSession();}
}
