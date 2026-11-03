package lab.owmcguest;

import com.google.gson.JsonObject;
import java.util.Map;

/** 语音挂接：原版Q消息入口的真实新tick；不等龙生成，也不读取Q按键。 */
final class HeroVoiceHanzoBegin implements AutoCloseable {
    static {
        NativeSkillReader.register("heroVoiceHanzoBegin",new NativeSkillReader.Spec(0x02e0000000000005L,
            0x05800000000000b9L,Map.of("castBegin",79,"release",76)));
    }
    private final NativeSkillReader reader=new NativeSkillReader("heroVoiceHanzoBegin");
    private final HeroVoicePolicy.Edges edges=new HeroVoicePolicy.Edges();
    private JsonObject status=new JsonObject();
    private long offered,lastOffered,releaseAtOffer,offeredWall;
    long observe(HostPoseReader.Pose host,HeroVoiceRuntime.Binding binding){
        var sample=reader.poll(host,binding.model(),binding.hero());
        var out=new JsonObject();out.addProperty("beginNode",79);out.addProperty("releaseWitnessNode",76);
        out.addProperty("source",binding.source());out.addProperty("model",binding.model());out.addProperty("world",binding.world());
        if(sample==null){edges.clear();out.addProperty("ready",false);out.addProperty("error",reader.error);status=out;return 0;}
        var begin=sample.entries().get("castBegin");var release=sample.entries().get("release");
        // EntryGameMessage通常同tick已经finished；新时间戳才是事件，不能要求active持续一帧。
        boolean newer=edges.newer("castBegin",begin.tick());
        out.addProperty("ready",true);out.addProperty("beginTick",begin.tick());out.addProperty("entryActive",begin.active());
        out.addProperty("releaseTick",release.tick());out.addProperty("newEdge",newer);
        if(newer){offered++;lastOffered=begin.tick();releaseAtOffer=release.tick();offeredWall=System.currentTimeMillis();}
        out.addProperty("releaseTickAtOffer",releaseAtOffer);out.addProperty("offeredWall",offeredWall);
        out.addProperty("offered",offered);out.addProperty("lastOffered",lastOffered);out.addProperty("error","");status=out;
        return newer?begin.tick():0;
    }
    String status(){return status.toString();}
    void rebaseline(){edges.clear();}
    @Override public void close(){reader.close();edges.clear();status=new JsonObject();offered=lastOffered=releaseAtOffer=offeredWall=0;}
}
