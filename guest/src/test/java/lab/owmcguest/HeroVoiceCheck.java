package lab.owmcguest;

import java.nio.file.*;
import java.util.concurrent.TimeUnit;
import com.google.gson.*;

/** 语音挂接：无游戏实例的策略/真实MP3转换/修改缓存拒绝测试。 */
public final class HeroVoiceCheck {
    private static void check(boolean value,String message){if(!value)throw new AssertionError(message);}
    private static HeroVoiceAssets.Loaded load(Path profile)throws Exception{
        try(var loader=new HeroVoiceAssets()){
            loader.request(profile);long until=System.nanoTime()+TimeUnit.SECONDS.toNanos(30);
            HeroVoiceAssets.Loaded result;
            while((result=loader.take())==null){check(System.nanoTime()<until,"asset worker deadline");Thread.sleep(10);}
            check(!loader.pending()&&loader.current()==(result.missing()==0&&result.error().isEmpty()),"asset readiness includes failed/incomplete loads");
            return result;
        }
    }
    public static void main(String[] args)throws Exception{
        System.clearProperty("owmc.heroVoiceFfmpeg"); // 验证本机LOCALAPPDATA默认解析，不依赖测试显式路径。
        String[] order={"ult_cast","ult_ready","select","ability:deflect","kill","death","respawn","pain","healing_request","jump"};
        for(int i=1;i<order.length;i++)check(HeroVoicePolicy.priority(order[i-1])>HeroVoicePolicy.priority(order[i]),"priority "+order[i]);
        check(HeroVoicePolicy.legacyOwned(0x29,"ult_cast")&&!HeroVoicePolicy.legacyOwned(5,"ult_cast"),"legacy Q owner");
        check(HeroVoicePolicy.legacyOwned(8,"select")&&HeroVoicePolicy.legacyOwned(0x42,"ability:flashbang"),"legacy select/E");
        check(HeroVoicePolicy.priority("sfx:dragon_roar")==0,"spatial SFX must not occupy voice channel");
        var random=new java.util.Random(17);String previous="a";
        for(int i=0;i<100;i++){String next=HeroVoicePolicy.nextHash(java.util.List.of("a","b","c"),previous,random);check(!next.equals(previous),"no consecutive variant repeat");previous=next;}
        check(HeroVoicePolicy.nextHash(java.util.List.of("a"),"a",random).equals("a"),"single available recording");
        var meter=new HeroVoicePolicy.Meter();
        check(!meter.observe(100,100)&&!meter.observe(100,100),"initial full must baseline");
        check(!meter.observe(20,100)&&meter.observe(100,100)&&!meter.observe(100,100),"one edge per charge cycle");
        check(!meter.observe(99.99999,100)&&!meter.observe(100,100),"full jitter must not rearm");
        check(!meter.observe(Double.NaN,100)&&!meter.observe(100,100),"invalid/reconnect baselines");
        var edges=new HeroVoicePolicy.Edges();
        check(!edges.newer("a",15)&&!edges.newer("a",15)&&edges.newer("a",16)&&!edges.newer("a",0)&&edges.newer("a",1),"counter baseline/regression");
        var wall=new HeroVoicePolicy.IceWall();
        check(wall.observe(0,0,false,true)==0&&wall.observe(1,1,true,true)==0,"no wall voice during selection");
        check(wall.observe(1,1,true,false)==0,"selection wall must not replay later");
        check(wall.observe(1,2,false,false)==0,"preview does not speak");
        check(wall.observe(2,2,false,false)==0,"confirmation alone does not speak");
        check(wall.observe(2,2,true,false)==2,"one actual MC build speaks");
        for(int i=0;i<50;i++)check(wall.observe(2,2,true,false)==0,"growing wall never repeats");
        check(wall.observe(3,2,true,false)==0&&wall.observe(4,2,true,false)==0,"repeated confirms in one preview cycle stay silent");
        check(wall.observe(4,3,true,false)==0&&wall.observe(5,3,true,false)==5,"new preview needs a new actual wall");
        wall.reset();check(wall.observe(5,3,true,false)==0,"rebind does not replay existing wall");
        wall.reset();check(wall.observe(0,0,false,false)==0&&wall.observe(0,1,false,false)==0,"new preview arms without speech");
        check(wall.observe(1,1,false,false)==0&&wall.pendingBuild()==1,"early build stays pending until placement");
        check(wall.observe(1,2,false,false)==0&&wall.pendingBuild()==1,"preview change must not swallow pending build");
        for(int i=0;i<30;i++)check(wall.observe(1,2,false,false)==0,"temporarily stale or absent view must wait");
        check(wall.observe(1,2,true,false)==1&&wall.lastOfferedBuild()==1,"late actual blocks offer exactly once");
        check(wall.observe(1,2,true,false)==0&&!wall.armed(),"late placement does not repeat");
        Path root=Path.of(System.getProperty("owmc.heroVoiceDirectory")),profile=root.resolve("profile");
        var first=load(profile);check(first.clips().size()==1,"verified MP3 conversion: "+first.error());
        check(first.missing()>=23&&first.error().contains("ult_ready"),"single-clip fixture must report incomplete restored roster: "+first.error()); // 语音挂接：转换成功不等于21人就绪素材已齐。
        var clip=first.clips().getFirst();check(clip.durationMs()>100&&clip.durationMs()<30000,"actual OGG duration");
        check(first.resourcesChanged(),"first conversion requires resources to load");
        var definitions=profile.resolve("resourcepacks/"+HeroVoiceAssets.PACK+"/assets/owmcguest/sounds.json");
        var before=Files.getLastModifiedTime(definitions);
        var second=load(profile);check(second.clips().size()==1&&second.clips().getFirst().equals(clip),"stable receipt cache");
        check(!second.resourcesChanged()&&Files.getLastModifiedTime(definitions).equals(before),"unchanged cache must not rewrite definitions");
        check(!second.reusable(true,true,c->true),"incomplete asset report cannot certify a loaded pack");
        var ready=new HeroVoiceAssets.Loaded(second.clips(),second.manifestCount(),0,"",second.stamp(),second.resourcesChanged());
        check(ready.reusable(true,true,c->c.equals(clip)),"enabled, active, registered unchanged pack can skip reload");
        check(!first.reusable(true,true,c->true),"changed resources still reload even with registered IDs");
        check(!ready.reusable(false,true,c->true)&&!ready.reusable(true,false,c->true),"disabled or inactive pack must reload");
        check(!ready.reusable(true,true,c->false),"missing or wrong registered sound must reload");
        Files.writeString(definitions,new GsonBuilder().setPrettyPrinting().create().toJson(JsonParser.parseString(Files.readString(definitions))));
        check(!load(profile).resourcesChanged(),"equivalent prebuilt JSON whitespace does not require reload");
        Files.writeString(definitions,"{}");
        check(load(profile).resourcesChanged(),"changed sound definitions require reload");
        Path ogg=profile.resolve("resourcepacks/"+HeroVoiceAssets.PACK+"/assets/owmcguest/sounds/private/full/"+clip.hash()+".ogg");
        byte[] original=Files.readAllBytes(ogg);byte[] changed=original.clone();changed[changed.length-1]^=1;Files.write(ogg,changed);
        var corrupt=load(profile);check(corrupt.clips().isEmpty()&&corrupt.error().contains("modified OGG"),"modified cache must fail closed");
        check(java.util.Arrays.equals(changed,Files.readAllBytes(ogg)),"modified cache must be preserved");
        Files.write(ogg,original);
        String savedManifest=Files.readString(root.resolve("manifest.json"));
        var manifest=JsonParser.parseString(savedManifest).getAsJsonObject();
        manifest.getAsJsonObject(clip.hash()).addProperty("sha256","0".repeat(64));Files.writeString(root.resolve("manifest.json"),manifest.toString());
        try{var bad=load(profile);check(bad.clips().isEmpty()&&bad.error().contains("MP3 SHA256 mismatch"),"source hash guard");}
        finally{Files.writeString(root.resolve("manifest.json"),savedManifest);}
        System.out.println("HeroVoiceCheck passed: priority, ownership, nonrepeat random, meter, duplicate edges, MP3/OGG, cache integrity, source hash, default ffmpeg path");
    }
}
