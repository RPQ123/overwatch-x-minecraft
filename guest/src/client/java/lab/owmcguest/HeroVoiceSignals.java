package lab.owmcguest;

import com.google.gson.*;
import java.util.HashMap;
import java.util.Map;
import net.minecraft.client.MinecraftClient;

/** 语音挂接：只消费现有适配器的已认证新 tick/成功计数；初样本仅基线。 */
final class HeroVoiceSignals {
    private final HeroVoiceEvents voice;
    private final HeroVoicePolicy.Edges edges=new HeroVoicePolicy.Edges();
    private final HeroVoicePolicy.Meter meter=new HeroVoicePolicy.Meter();
    private final HeroVoicePolicy.IceWall iceWall=new HeroVoicePolicy.IceWall();
    private final HeroVoiceHanzoBegin hanzoBegin=new HeroVoiceHanzoBegin();
    private final HeroVoiceUltimateSignals ultimates=new HeroVoiceUltimateSignals();
    private String iceWallStatus="{}";
    private JsonObject counterStatus=new JsonObject(); // 语音挂接：失败时也可核对生产者原始计数。
    private long iceWallViewSamples,iceWallFreshSamples;
    private final Map<String,Long> phases=new HashMap<>();
    private long sequence;
    HeroVoiceSignals(HeroVoiceEvents voice){this.voice=voice;}
    private static JsonObject json(String value){try{return JsonParser.parseString(value).getAsJsonObject();}catch(Exception e){return new JsonObject();}}
    private static boolean active(JsonObject o,String key){return o.has(key)&&!o.get(key).isJsonNull()&&o.get(key).getAsBoolean();}
    private static long number(JsonObject o,String key){return o.has(key)&&!o.get(key).isJsonNull()?o.get(key).getAsLong():0;}
    private void count(String event,String report,String field,String key){
        count(event,report,field,key,false);
    }
    private void count(String event,String report,String field,String key,boolean initiallyZero){
        var o=json(report);Long n=o.has(field)&&o.get(field).isJsonPrimitive()?number(o,field):null;
        boolean seed=initiallyZero&&report.trim().equals("{}");
        boolean offered=n==null?edges.newer(key,null,seed):n>=0&&edges.newer(key,n,false);
        var diagnostic=counterStatus.has(key)?counterStatus.getAsJsonObject(key):new JsonObject();
        diagnostic.addProperty("event",event);diagnostic.addProperty("field",field);diagnostic.addProperty("value",n);
        diagnostic.addProperty("initialZeroBaseline",seed);diagnostic.addProperty("newEdge",offered);
        if(offered){diagnostic.addProperty("lastOffered",n);voice.emit(event,n,"native:"+key,"");}
        counterStatus.add(key,diagnostic);
    }
    private void phase(String event,String key,long tick,boolean running){
        Long old=phases.get(key);
        if(old==null){phases.put(key,Math.max(0,tick));return;}
        if(running&&tick>old){phases.put(key,tick);voice.emit(event,tick,"native:"+key,"");}
    }
    private void toggle(String event,String report,String field,String key){
        var o=json(report);if(!o.has(field))return;
        boolean running=active(o,field);long token=running?1:0;
        if(edges.newer(key,token)&&running)voice.emit(event,++sequence,"native:"+key,"");
    }
    void tick(MinecraftClient client,HeroVoiceRuntime.Binding b){
        var host=HostPoseReader.INSTANCE.latest();
        if(host==null||!host.inputActive()||!client.player.isAlive())return;
        long hero=b.hero();String name=HeroVoicePolicy.heroName(hero);
        var charge=json(NativeChargeController.status);
        // 语音挂接：满值读数来自原版变量；源氏只读其专用绑定，其余20人消费ALL-HERO-CHARGE同身份回执。
        var readyStatus=new JsonObject();boolean valid=false;double value=0,cost=0;
        if(hero==0x02e0000000000029L){
            var u=ultimates.genjiCharge(host,b);if(u!=null){valid=true;value=u.charge();cost=u.cost();}
        }else if(active(charge,"ready")&&number(charge,"hero")==hero&&number(charge,"modelId")==b.model()&&number(charge,"worldId")==b.world()&&number(charge,"hostGeneration")==b.source()){
            if(charge.has("charge")&&charge.has("cost")){valid=true;value=charge.get("charge").getAsDouble();cost=charge.get("cost").getAsDouble();}
        }
        boolean crossed=valid&&meter.observe(value,cost);if(!valid)meter.reset();
        readyStatus.addProperty("ready",valid);readyStatus.addProperty("charge",value);readyStatus.addProperty("cost",cost);readyStatus.addProperty("crossedFull",crossed);
        readyStatus.addProperty("model",b.model());readyStatus.addProperty("world",b.world());readyStatus.addProperty("source",b.source());
        readyStatus.addProperty("hasClip",voice.hasClip(name,"ult_ready"));counterStatus.add("ultReady",readyStatus);
        if(crossed)voice.emit("ult_ready",++sequence,"native:charge-unfull-to-full","");
        var ultimate=ultimates.observe(host,b);counterStatus.add("ultBegin",ultimates.status());
        if(ultimate!=null)voice.emit("ult_cast",ultimate.tick(),ultimate.signal(),"");
        switch(name){
            // 语音挂接：该runtime仅爆炸后才首次发布detonations；初始{}确知是0，不能吞掉第一发。
            case "pharah" -> count("ability:concussive_blast",NativeConcussiveRuntime.status,"detonations","concussive",true);
            case "genji" -> {
                count("ability:swift_strike",NativeDashRuntime.status,"begins","dash");
                var d=json(NativeDeflectRuntime.status);phase("ability:deflect","deflect",number(d,"nativeTick"),active(d,"active"));
            }
            case "mccree" -> count("ability:combat_roll",NativeRollController.status,"starts","roll");
            case "tracer" -> {
                // 语音挂接：闪现/回溯不再叠加无字幕“呀”及位移语气声。
                var pulse=NativePulseRuntime.view;
                if(pulse!=null&&pulse.owner().equals(b.player())&&pulse.source()==b.source()&&pulse.model()==b.model()&&pulse.world()==b.world())
                    phase("ability:pulse_attach","pulse-attach",pulse.nativeTick(),pulse.attached()&&!pulse.blockAttached()&&pulse.remaining()>0);
                else phase("ability:pulse_attach","pulse-attach",0,false);
            }
            case "reaper" -> count("ability:wraith",NativeWraithRuntime.status,"starts","wraith");
            case "mei" -> {
                iceWall(b); // 语音挂接：仅MC实际建墙一次，预览/确认请求不直接播。
                sustain(hero,"ability:cryo_freeze"); // 语音挂接：Q已前移到064a:1，不再等MC投掷计数。
                var combat=json(NativeCombatRuntime.status);
                if(combat.has("meiFreeze"))count("ability:freeze_target",combat.get("meiFreeze").toString(),"freezes","mei-freeze");
            }
            case "bastion" -> sustain(hero,"ability:self_repair");
            case "hanzo" -> {
                count("ability:scatter_arrow",NativeHanzoSkillRuntime.status,"scatters","scatter");
                long begin=hanzoBegin.observe(host,b);
                counterStatus.add("hanzoBegin",JsonParser.parseString(hanzoBegin.status()));
                if(begin>0)voice.emit("ult_cast",begin,"native:hanzo-b9-entry79",""); // 语音挂接：旧dragonCasts晚触发删除，不双播。
                var combat=json(NativeCombatRuntime.status);
                if(combat.has("sonic"))count("ability:sonic_arrow",combat.get("sonic").toString(),"admitted","sonic");
            }
            case "junkrat" -> {
                count("ability:concussion_mine",NativeJunkratRuntime.status,"mines","mine");
                count("ability:steel_trap",NativeJunkratRuntime.status,"traps","trap");
                count("ability:steel_trap_trigger",NativeJunkratRuntime.status,"trapTriggers","trap-trigger");
            }
            case "torbjorn" -> {
                count("ability:turret_deploy",NativeTorbjornRuntime.status,"deploys","turret");
                count("ability:armor_pack",NativeTorbjornRuntime.status,"packsThrown","armor-pack");
            }
            case "widowmaker" -> {
                // 语音挂接：抓钩候选只有发射/滑行注释，停止不明人声。
                count("ability:venom_mine",NativeVenomRuntime.status,"throws","venom");
                count("ability:venom_trigger",NativeVenomRuntime.status,"detonations","venom-trigger");
            }
            case "mercy" -> {
                var m=json(MercyServer.INSTANCE.status());String channel=m.has("channel")?m.get("channel").getAsString():"";
                boolean target=m.has("target")&&!m.get("target").isJsonNull()&&!m.get("target").getAsString().isBlank();
                phase("ability:heal_beam","mercy-heal",number(m,"beginTick"),target&&channel.equals("HEAL"));
                phase("ability:damage_boost","mercy-boost",number(m,"beginTick"),target&&channel.equals("BOOST"));
            }
            case "reinhardt" -> {
                count("ability:barrier",ReinhardtServer.INSTANCE.status(),"barrierCasts","reinhardt-barrier");
                count("ability:charge",ReinhardtServer.INSTANCE.status(),"chargeStarts","reinhardt-charge");
            }
            case "zarya" -> {
                var z=json(ZaryaServer.INSTANCE.status());phase("ability:particle_barrier","zarya-self",number(z,"selfLastBeginTick"),active(z,"selfActive"));
            }
            case "roadhog" -> {
                count("ability:chain_hook",RoadhogServer.INSTANCE.status(),"hookCasts","hook");
                count("ability:chain_hook_hit",RoadhogServer.INSTANCE.status(),"hookHits","hook-hit");
                count("ability:take_a_breather",RoadhogServer.INSTANCE.status(),"healCasts","breather");
            }
            case "symmetra" -> {
                count("ability:sentry_turret",SymmetraServer.INSTANCE.status(),"turretBuilds","symmetra-turret");
            }
            case "lucio" -> {
                count("ability:amp_it_up",LucioServer.INSTANCE.status(),"ampCasts","amp");
                count("ability:crossfade_switch",LucioServer.INSTANCE.status(),"songCommits","song");
            }
            default -> { /* D.Va机甲/温斯顿/禅雅塔缺成功回执，不猜施法。 */ }
        }
    }
    private void sustain(long hero,String event){
        var s=json(NativeSustainRuntime.status);
        if(number(s,"hero")==hero)phase(event,"sustain",number(s,"nativeTick"),active(s,"active"));
    }
    private void iceWall(HeroVoiceRuntime.Binding binding){
        var wall=json(NativeIceWallRuntime.status);
        if(!wall.has("builds")||!wall.has("previews"))return;
        var view=NativeIceWallRuntime.view;long now=System.currentTimeMillis();
        long age=view==null?-1:now-view.wall();boolean worldMatches=view!=null&&view.world()==binding.world();
        boolean fresh=view!=null&&age>=0&&age<=150;
        if(view!=null){iceWallViewSamples++;if(fresh)iceWallFreshSamples++;}
        boolean placed=active(wall,"wall")&&number(wall,"blocksActive")>0&&worldMatches&&fresh;
        boolean selecting=EarlyChineseVoices.INSTANCE.selectionPending();
        long build=iceWall.observe(number(wall,"builds"),number(wall,"previews"),placed,selecting);
        wall.addProperty("placedInCurrentWorld",placed);wall.addProperty("selectionPending",selecting);wall.addProperty("offeredBuild",build);
        // 语音挂接：保留两个同源NativeWorldIdentity、采样年龄和锁存状态，超时也能定位。
        wall.addProperty("bindingWorld",binding.world());wall.addProperty("viewPresent",view!=null);wall.addProperty("viewWorld",view==null?0:view.world());
        wall.addProperty("worldMatches",worldMatches);wall.addProperty("viewAgeMs",age);wall.addProperty("viewFresh",fresh);
        wall.addProperty("viewSamples",iceWallViewSamples);wall.addProperty("freshViewSamples",iceWallFreshSamples);
        wall.addProperty("gateArmed",iceWall.armed());wall.addProperty("pendingBuild",iceWall.pendingBuild());wall.addProperty("lastOfferedBuild",iceWall.lastOfferedBuild());
        iceWallStatus=wall.toString();
        if(build>0)voice.emit("ability:ice_wall",build,"mc:ice-wall-built","");
    }
    String iceWallStatus(){return iceWallStatus;}
    String counterStatus(){return counterStatus.toString();}
    void rebaseline(){edges.clear();phases.clear();meter.reset();hanzoBegin.rebaseline();ultimates.rebaseline();counterStatus=new JsonObject();} // 语音挂接：同身份短暂卡顿不丢待建墙。
    void reset(){rebaseline();hanzoBegin.close();ultimates.close();iceWall.reset();iceWallStatus="{}";iceWallViewSamples=iceWallFreshSamples=0;}
}
