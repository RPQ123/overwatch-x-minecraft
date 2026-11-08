package lab.owmcguest;

import com.google.gson.JsonObject;
import java.util.HashMap;
import java.util.Map;

/** 语音挂接：仅消费原版最早已知施法节点；不依赖MC弹体、伤害或服务器建造计数。 */
final class HeroVoiceUltimateSignals implements AutoCloseable {
    static {
        NativeSkillReader.register("heroVoiceBastionBegin",new NativeSkillReader.Spec(0x02e0000000000015L,0x058000000000012fL,Map.of("transform",123,"tank",105)));
        NativeSkillReader.register("junkTire",new NativeSkillReader.Spec(0x02e0000000000065L,0x0580000000000232L,Map.of("create",32,"control",10,"view",11,"windup",7)));
        NativeSkillReader.register("roadhogWeapon",new NativeSkillReader.Spec(0x02e0000000000040L,0x05800000000001c6L,Map.of("primary",30,"secondary",34,"wholeHog",37)));
        NativeSkillReader.register("winstonPrimal",new NativeSkillReader.Spec(WinstonRules.HERO,0x0580000000000109L,Map.of("rage",10,"pool",7)));
        NativeSkillReader.register("zaryaGraviton",new NativeSkillReader.Spec(0x02e0000000000068L,0x058000000000025fL,Map.of("volley",2)));
        NativeSkillReader.register("heroVoiceLucioBegin",new NativeSkillReader.Spec(0x02e0000000000079L,0x058000000000073aL,Map.of("castBegin",9,"barrier",0)));
        NativeSkillReader.register("zenTranscendence",new NativeSkillReader.Spec(0x02e0000000000020L,0x058000000000017bL,Map.of("windup",19,"heal",17,"aura",30)));
        NativeSkillReader.register("symmetraPortal",new NativeSkillReader.Spec(0x02e0000000000016L,0x0580000000000169L,Map.of("portalPreview",42,"portalGhost",74,"portalPlace",2,"portalCommit",66)));
    }
    private final Map<String,NativeSkillReader> readers=new HashMap<>();
    private final HeroVoicePolicy.Edges edges=new HeroVoicePolicy.Edges();
    private final NativeAbilityReader genjiMeter=new NativeAbilityReader(true);
    private JsonObject status=new JsonObject();
    private long offered,lastTick,offeredWall;
    record Sample(long tick,String signal) {}
    private record Profile(String purpose,String state,String signal,boolean instant) {}
    private static Profile profile(String hero){return switch(hero){
        case "bastion"->new Profile("heroVoiceBastionBegin","transform","native:bastion-012f:123-transform-begin",false);
        case "torbjorn"->new Profile("skills","ultimate","native:torbjorn-01c2:21-begin",false);
        case "widowmaker"->new Profile("skills","ultimate","native:widowmaker-0067:18-begin",false);
        case "mei"->new Profile("blizzard","windup","native:mei-064a:1-begin",false);
        case "junkrat"->new Profile("junkTire","windup","native:junkrat-0232:7-begin",false);
        case "roadhog"->new Profile("roadhogWeapon","wholeHog","native:roadhog-01c6:37-begin",false);
        case "winston"->new Profile("winstonPrimal","rage","native:winston-0109:10-primal-begin",false);
        case "zarya"->new Profile("zaryaGraviton","volley","native:zarya-025f:2-tick",true);
        case "lucio"->new Profile("heroVoiceLucioBegin","castBegin","native:lucio-073a:9-begin",false);
        case "zenyatta"->new Profile("zenTranscendence","windup","native:zenyatta-017b:19-begin",false);
        // 语音挂接：放置型大招不能在42预览就喊“已上线”；只认原版66提交，不等MC建造。
        case "symmetra"->new Profile("symmetraPortal","portalCommit","native:symmetra-0169:66-commit",true);
        default->null;
    };}
    Sample observe(HostPoseReader.Pose host,HeroVoiceRuntime.Binding binding){
        String hero=HeroVoicePolicy.heroName(binding.hero());var p=profile(hero);var out=new JsonObject();
        out.addProperty("hero",hero);out.addProperty("model",binding.model());out.addProperty("source",binding.source());out.addProperty("world",binding.world());
        if(p==null){out.addProperty("ready",false);out.addProperty("error","legacy owner, Hanzo independent Begin, or no certified cast Begin");status=out;return null;}
        var reader=readers.computeIfAbsent(p.purpose(),key->key.equals("skills")?new NativeSkillReader():new NativeSkillReader(key));
        var sample=reader.poll(host,binding.model(),binding.hero());out.addProperty("signal",p.signal());out.addProperty("state",p.state());
        if(sample==null){edges.clear();out.addProperty("ready",false);out.addProperty("error",reader.error);status=out;return null;}
        var e=sample.entries().get(p.state());
        if(e==null){edges.clear();out.addProperty("ready",false);out.addProperty("error","missing native state "+p.state()+"; refresh original binding");status=out;return null;} // 语音挂接：旧绑定缺起手节点时拒绝发声，不能崩主线程。
        boolean fresh=edges.newer(p.signal(),e.tick());
        boolean begin=fresh&&(p.instant()||e.active());
        out.addProperty("ready",true);out.addProperty("tick",e.tick());out.addProperty("active",e.active());out.addProperty("newBegin",begin);
        if(hero.equals("bastion")){var tank=sample.entries().get("tank");out.addProperty("tankTick",tank.tick());out.addProperty("tankActive",tank.active());} // 语音挂接：105仅为晚到的形态见证，绝不触发。
        if(begin){offered++;lastTick=e.tick();offeredWall=System.currentTimeMillis();}
        out.addProperty("offered",offered);out.addProperty("lastOffered",lastTick);out.addProperty("offeredWall",offeredWall);out.addProperty("error","");status=out;
        return begin?new Sample(e.tick(),p.signal()):null;
    }
    /** 语音挂接：源氏沿用其原版变量/归属校验，只读；绝不创建第二个充能写入者。 */
    NativeAbilityReader.Ultimate genjiCharge(HostPoseReader.Pose host,HeroVoiceRuntime.Binding binding){
        var u=genjiMeter.ultimate(host);return u!=null&&u.source()==binding.source()&&u.model()==binding.model()?u:null;
    }
    JsonObject status(){return status.deepCopy();}
    void rebaseline(){edges.clear();status=new JsonObject();}
    @Override public void close(){readers.values().forEach(NativeSkillReader::close);genjiMeter.close();rebaseline();offered=lastTick=offeredWall=0;}
}
