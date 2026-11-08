package lab.owmcguest;

import com.google.gson.*;
import java.nio.ByteBuffer;
import java.nio.ByteOrder;
import java.nio.file.*;
import java.security.MessageDigest;
import java.util.*;
import java.util.concurrent.*;
import net.minecraft.util.Identifier;

/** 语音挂接：后台校验私有 MP3，生成 MC 私有资源包；从不下载/打包进 JAR。 */
final class HeroVoiceAssets implements AutoCloseable {
    static final String PACK="owmc-private-full-voice";
    record Clip(String hero,String event,String hash,Identifier id,long durationMs,String variant) {}
    record Loaded(List<Clip> clips,int manifestCount,int missing,String error,long stamp,boolean resourcesChanged) {
        Loaded(List<Clip> clips,int manifestCount,int missing,String error,long stamp){this(clips,manifestCount,missing,error,stamp,true);}
        boolean reusable(boolean enabled,boolean active,java.util.function.Predicate<Clip> registered){
            return !resourcesChanged&&missing==0&&error.isEmpty()&&enabled&&active&&!clips.isEmpty()&&clips.stream().allMatch(registered);
        }
    }
    final Path root=PrivateAssetPaths.voices();
    private final ExecutorService worker=Executors.newSingleThreadExecutor(r->{var t=new Thread(r,"owmc-private-voice-assets");t.setDaemon(true);return t;});
    private Future<Loaded> pending;
    private long attemptedStamp=Long.MIN_VALUE,nextAttempt;
    private boolean incomplete=true;
    private volatile Map<String,String> legacyHashes=Map.of();
    volatile Map<String,Integer> excludedEvents=Map.of(); // 语音挂接：旧私有清单清退统计。
    private static final Set<String> HEROES=Set.of("bastion","dva","genji","hanzo","junkrat","lucio","mccree","mei","mercy","pharah","reaper","reinhardt","roadhog","soldier76","symmetra","torbjorn","tracer","widowmaker","winston","zarya","zenyatta");

    void request(Path profile){
        if(pending!=null||System.nanoTime()<nextAttempt)return;
        long stamp=-1;try{stamp=Files.getLastModifiedTime(root.resolve("manifest.json")).toMillis();}catch(Exception ignored){}
        if(!incomplete&&stamp==attemptedStamp)return;
        attemptedStamp=stamp;nextAttempt=System.nanoTime()+15_000_000_000L;
        final long value=stamp;pending=worker.submit(()->load(profile,value));
    }
    Loaded take(){
        if(pending==null||!pending.isDone())return null;
        try{var result=pending.get();incomplete=result.missing()>0||!result.error().isEmpty();return result;}
        catch(Exception e){incomplete=true;return new Loaded(List.of(),0,0,e.toString(),attemptedStamp);}
        finally{pending=null;}
    }
    String legacyHash(String stem){return legacyHashes.getOrDefault(stem,"");}
    boolean busy(){return pending!=null&&!pending.isDone();}
    boolean pending(){return pending!=null;} // 语音挂接：完成但尚未领取的结果也属于待安装。
    boolean current(){
        if(incomplete||pending!=null)return false;
        try{return attemptedStamp==Files.getLastModifiedTime(root.resolve("manifest.json")).toMillis();}
        catch(Exception ignored){return false;}
    }
    private void loadLegacy(){
        var out=new HashMap<String,String>();
        try{
            var p=root.resolveSibling("thnu-three").resolve("manifest.json");
            var data=JsonParser.parseString(Files.readString(p)).getAsJsonObject();
            for(var e:data.entrySet()){
                var o=e.getValue().getAsJsonObject();String h="";
                if(o.has("catalog")&&o.getAsJsonObject("catalog").has("filehash"))h=o.getAsJsonObject("catalog").get("filehash").getAsString();
                if(h.isBlank()&&o.has("sha256"))h=o.get("sha256").getAsString();
                out.put(e.getKey(),h);
            }
        }catch(Exception ignored){}
        legacyHashes=Map.copyOf(out);
    }
    private Loaded load(Path profile,long stamp){
        loadLegacy();var clips=new ArrayList<Clip>();int count=0,missing=0;boolean requireHanzo=false,changed=false;var errors=new ArrayList<String>();var excluded=new TreeMap<String,Integer>();
        try{
            Path manifest=root.resolve("manifest.json");
            if(!Files.isRegularFile(manifest))return new Loaded(List.of(),0,1,"等待 thnu-full/manifest.json",stamp);
            if(Files.size(manifest)>8_000_000)throw new IllegalArgumentException("voice manifest too large");
            var data=JsonParser.parseString(Files.readString(manifest)).getAsJsonObject();
            if(data.has("entries")&&data.get("entries").isJsonObject())data=data.getAsJsonObject("entries");
            Path pack=profile.toAbsolutePath().normalize().resolve("resourcepacks").resolve(PACK);
            Path marker=pack.resolve("owmc-owned-v1");
            if(Files.isDirectory(pack)&&!Files.isRegularFile(marker))throw new IllegalStateException("保留无所有权标记的私有资源包: "+pack);
            Files.createDirectories(pack);Files.writeString(marker,"OWMC private full voice v1\n");
            Path sounds=pack.resolve("assets/owmcguest/sounds/private/full");Files.createDirectories(sounds);
            var definitions=new JsonObject();Path ffmpeg=ffmpeg();
            for(var e:data.entrySet()){
                if(Thread.currentThread().isInterrupted())break;
                count++;
                try{
                    String hash=e.getKey();var o=e.getValue().getAsJsonObject();
                    String hero=o.get("hero").getAsString(),event=o.get("event").getAsString();
                    if(hero.equals("hanzo"))requireHanzo=true;
                    // 语音挂接：在读MP3/转换/注册前拒绝无字幕、旧可选与未知素材。
                    boolean certifiedSfx=WinstonAudioCatalog.allowed(hero,event,hash)||RoadhogSoundCatalog.allowed(hero,event,hash);
                    if(!certifiedSfx&&(!HeroVoicePolicy.clipAllowed(hero,event,hash)||!HeroVoiceDefaultCatalog.allowed(hero,event,hash))){excluded.merge(event,1,Integer::sum);continue;}
                    String pin=o.get("sha256").getAsString().toLowerCase(Locale.ROOT);
                    if(!hash.matches("[0-9a-f]{32}")||!HEROES.contains(hero)||!pin.matches("[0-9a-f]{64}")||!event.matches("[a-z_]+(?::[a-z_]+)?"))throw new IllegalArgumentException("invalid entry identity");
                    boolean directOgg=o.has("format")&&o.get("format").getAsString().equals("ogg");
                    Path input=directOgg?root.resolve(o.get("file").getAsString()).normalize():root.resolve(hero).resolve(hash+".mp3");
                    if(!Files.isRegularFile(input)){missing++;continue;}
                    if(!input.toRealPath().startsWith(root.toRealPath())||Files.size(input)>5_000_000)throw new IllegalArgumentException("private source bounds");
                    byte[] source=Files.readAllBytes(input);
                    if(!sha(source).equals(pin))throw new IllegalArgumentException("Voice source SHA256 mismatch");
                    if(directOgg&&(source.length<4||source[0]!='O'||source[1]!='g'||source[2]!='g'||source[3]!='S'))throw new IllegalArgumentException("OGG header");
                    String sourcePin=directOgg&&o.has("originalMp3Sha256")?o.get("originalMp3Sha256").getAsString():pin;
                    if(!sourcePin.matches("[0-9a-f]{64}"))throw new IllegalArgumentException("original source identity");
                    Path ogg=sounds.resolve(hash+".ogg"),receipt=sounds.resolve(hash+".json");
                    if(Files.exists(ogg)){
                        if(!Files.isRegularFile(receipt))throw new IllegalStateException("preserve unreceipted OGG cache");
                        var prior=JsonParser.parseString(Files.readString(receipt)).getAsJsonObject();
                        if(!sourcePin.equals(prior.get("sourceSha256").getAsString())||!sha(Files.readAllBytes(ogg)).equals(prior.get("oggSha256").getAsString())||(directOgg&&!pin.equals(prior.get("oggSha256").getAsString())))throw new IllegalStateException("preserve modified OGG cache");
                    }else{
                        changed=true;
                        if(directOgg)Files.write(ogg,source);
                        else{
                            if(ffmpeg==null)throw new IllegalStateException("本机 ffmpeg 不存在；可设置 -Dowmc.heroVoiceFfmpeg=<exe>");
                            convert(ffmpeg,source,ogg);
                        }
                        var proof=new JsonObject();proof.addProperty("sourceSha256",sourcePin);proof.addProperty("oggSha256",sha(Files.readAllBytes(ogg)));atomic(receipt,proof.toString());
                    }
                    long duration=durationMs(Files.readAllBytes(ogg));String id="hero_voice."+hash;
                    var sound=new JsonObject();sound.addProperty("replace",true);var list=new JsonArray();var item=new JsonObject();
                    item.addProperty("name","owmcguest:private/full/"+hash);item.addProperty("preload",false);list.add(item);sound.add("sounds",list);definitions.add(id,sound);
                    String variant=o.has("variant")?o.get("variant").getAsString():HeroVoiceDeathVariants.FALL.contains(hash)?"fall":"";
                    clips.add(new Clip(hero,event,hash,Identifier.of("owmcguest",id),duration,variant));
                }catch(Exception failure){
                    missing++;if(errors.size()<4)errors.add(e.getKey()+": "+failure.getMessage());
                    if(failure instanceof InterruptedException){Thread.currentThread().interrupt();break;}
                }
            }
            // 语音挂接：防止只更新JAR却未安装日语片段时，仍把素材库误报为全部就绪。
            if(requireHanzo&&clips.stream().noneMatch(c->c.hero().equals("hanzo")&&c.event().equals("ult_cast")&&c.hash().equals(HeroVoicePolicy.HANZO_ULT_HASH))){
                missing++;errors.add("缺少半藏日语片段；执行 tools/prune_voice_defaults.py --apply-private（纯本地裁剪）");
            }
            // 语音挂接：只更新JAR但没恢复就绪/堡垒Q素材时明确报未就绪，不能静默当完成。
            for(String hero:HEROES)if(clips.stream().noneMatch(c->c.hero().equals(hero)&&c.event().equals("ult_ready"))){
                missing++;if(errors.size()<4)errors.add("缺少"+hero+" ult_ready；运行voice_download.py --list research/voice-20261027-feedback5/download-additions.json");
            }
            for(String hero:List.of("bastion","junkrat","zenyatta"))if(clips.stream().noneMatch(c->c.hero().equals(hero)&&c.event().equals("ult_cast"))){
                missing++;if(errors.size()<4)errors.add("缺少"+hero+" ult_cast恢复素材");
            }
            for(String event:WinstonAudioCatalog.VOICES)if(clips.stream().noneMatch(c->c.hero().equals("winston")&&c.event().equals(event))){
                missing++;if(errors.size()<4)errors.add("缺少温斯顿台词 "+event+"；运行 prepare_winston_audio.py --apply-private");
            }
            for(var entry:WinstonAudioCatalog.SFX.entrySet())if(clips.stream().noneMatch(c->WinstonAudioCatalog.allowed(c.hero(),c.event(),c.hash())&&c.event().equals(entry.getKey()))){
                missing++;if(errors.size()<4)errors.add("缺少温斯顿原版音效 "+entry.getKey()+"；运行 prepare_winston_audio.py --apply-private");
            }
            var metadata=new JsonObject();var info=new JsonObject();info.addProperty("pack_format",34);info.addProperty("description","Private OWMC hero voices; local manifest only");metadata.add("pack",info);
            changed|=atomic(pack.resolve("pack.mcmeta"),metadata.toString());
            changed|=atomic(pack.resolve("assets/owmcguest/sounds.json"),definitions.toString());
        }catch(Exception failure){errors.add(failure.getMessage()==null?failure.toString():failure.getMessage());}
        excludedEvents=Map.copyOf(excluded);
        return new Loaded(List.copyOf(clips),count,missing,String.join("; ",errors),stamp,changed);
    }
    private static Path ffmpeg(){
        String explicit=System.getProperty("owmc.heroVoiceFfmpeg","");
        if(!explicit.isBlank())return Files.isRegularFile(Path.of(explicit))?Path.of(explicit):null;
        Path bundled=Path.of(System.getenv().getOrDefault("LOCALAPPDATA",home().resolve("AppData/Local").toString()),"universal-modder/ffmpeg/bin/ffmpeg.exe");
        if(Files.isRegularFile(bundled))return bundled;
        for(String entry:System.getenv().getOrDefault("PATH","").split(java.io.File.pathSeparator)){
            Path candidate=Path.of(entry).resolve("ffmpeg.exe");if(Files.isRegularFile(candidate))return candidate;
        }
        return null;
    }
    private static Path home(){
        // 语音挂接：构建沙箱的JVM user.home可能被重定向，素材仍属于实际Windows用户。
        String profile=System.getenv("USERPROFILE");return Path.of(profile==null||profile.isBlank()?System.getProperty("user.home"):profile);
    }
    private static void convert(Path ffmpeg,byte[] source,Path ogg)throws Exception{
        Path input=ogg.resolveSibling(ogg.getFileName()+".input.mp3"),output=ogg.resolveSibling(ogg.getFileName()+".partial.ogg"),log=ogg.resolveSibling(ogg.getFileName()+".log");
        try{
            Files.write(input,source);
            var process=new ProcessBuilder(ffmpeg.toString(),"-v","error","-nostdin","-threads","1","-i",input.toString(),"-ac","1","-ar","24000","-c:a","libvorbis","-q:a","4","-f","ogg","-y",output.toString()).redirectErrorStream(true).redirectOutput(log.toFile()).start();
            try{
                if(!process.waitFor(20,TimeUnit.SECONDS)){process.destroyForcibly();throw new IllegalStateException("voice conversion timed out");}
                if(process.exitValue()!=0)throw new IllegalStateException("ffmpeg exit="+process.exitValue());
                durationMs(Files.readAllBytes(output));Files.move(output,ogg,StandardCopyOption.ATOMIC_MOVE);
            }finally{if(process.isAlive())process.destroyForcibly();}
        }finally{Files.deleteIfExists(input);Files.deleteIfExists(output);Files.deleteIfExists(log);}
    }
    static long durationMs(byte[] ogg){
        long samples=-1;int rate=0;
        for(int at=0;at+27<=ogg.length;){
            if(ogg[at]!='O'||ogg[at+1]!='g'||ogg[at+2]!='g'||ogg[at+3]!='S')throw new IllegalArgumentException("invalid OGG page");
            long granule=ByteBuffer.wrap(ogg,at+6,8).order(ByteOrder.LITTLE_ENDIAN).getLong();if(granule>=0)samples=granule;
            int segments=ogg[at+26]&255;if(at+27+segments>ogg.length)throw new IllegalArgumentException("truncated OGG");
            int length=27+segments;for(int i=0;i<segments;i++)length+=ogg[at+27+i]&255;
            if(at+length>ogg.length)throw new IllegalArgumentException("truncated OGG payload");
            if(at==0){
                int body=27+segments;
                if(segments==0||(ogg[27]&255)<30||body+30>ogg.length||ogg[body]!=1
                    ||!new String(ogg,body+1,6,java.nio.charset.StandardCharsets.US_ASCII).equals("vorbis"))throw new IllegalArgumentException("Vorbis identity header");
                int channels=ogg[body+11]&255;rate=ByteBuffer.wrap(ogg,body+12,4).order(ByteOrder.LITTLE_ENDIAN).getInt();
                if(channels<1||channels>2||rate<8000||rate>96000)throw new IllegalArgumentException("Vorbis channels/sample rate");
            }
            at+=length;
        }
        if(rate==0||samples<=0||samples>rate*30L)throw new IllegalArgumentException("voice duration bounds");
        long duration=samples*1000/rate;
        if(duration<50||duration>30000)throw new IllegalArgumentException("voice duration bounds");return duration;
    }
    private static String sha(byte[] bytes)throws Exception{return HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(bytes));}
    private static boolean atomic(Path path,String text)throws Exception{
        // JSON ordering/whitespace differs between the pack builder and Gson.
        // Equal definitions are already usable by the initial resource load.
        if(Files.isRegularFile(path))try{
            if(JsonParser.parseString(Files.readString(path)).equals(JsonParser.parseString(text)))return false;
        }catch(JsonParseException ignored){}
        Files.createDirectories(path.getParent());Path temp=path.resolveSibling(path.getFileName()+".tmp");Files.writeString(temp,text);Files.move(temp,path,StandardCopyOption.REPLACE_EXISTING,StandardCopyOption.ATOMIC_MOVE);
        return true;
    }
    @Override public void close(){worker.shutdownNow();}
}
