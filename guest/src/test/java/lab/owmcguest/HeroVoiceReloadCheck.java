package lab.owmcguest;

import com.google.gson.*;
import java.nio.ByteBuffer;
import java.nio.ByteOrder;
import java.nio.file.*;
import java.nio.file.attribute.FileTime;
import java.security.MessageDigest;
import java.util.*;

/** Offline asset/reload checks. No Minecraft client, audio device or game is started. */
public final class HeroVoiceReloadCheck {
    private static void check(boolean value,String message){if(!value)throw new AssertionError(message);}
    private static HeroVoiceAssets.Loaded load(Path profile)throws Exception{
        try(var assets=new HeroVoiceAssets()){
            var method=HeroVoiceAssets.class.getDeclaredMethod("load",Path.class,long.class);method.setAccessible(true);
            return (HeroVoiceAssets.Loaded)method.invoke(assets,profile,1L);
        }
    }
    public static void main(String[] args)throws Exception{
        Path temporary=Path.of(System.getProperty("java.io.tmpdir")).toRealPath();
        Path root=Files.createTempDirectory(temporary,"owmc-voice-reload-").toRealPath();
        check(root.startsWith(temporary),"fixture output stays in configured temporary directory");
        String previous=System.getProperty("owmc.heroVoiceDirectory");
        try{
            System.setProperty("owmc.heroVoiceDirectory",root.toString());
            String hash=HeroVoicePolicy.HANZO_ULT_HASH;
            // A structural 100 ms OGG fixture, only inspected; never decoded/played.
            byte[] blob=new byte[27];System.arraycopy(new byte[]{'O','g','g','S'},0,blob,0,4);
            ByteBuffer.wrap(blob).order(ByteOrder.LITTLE_ENDIAN).putLong(6,2400L);
            String pin=HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(blob));
            Path input=root.resolve("hanzo/"+hash+".ogg");Files.createDirectories(input.getParent());Files.write(input,blob);
            var entry=new JsonObject();entry.addProperty("hero","hanzo");entry.addProperty("event","ult_cast");
            entry.addProperty("format","ogg");entry.addProperty("file","hanzo/"+hash+".ogg");
            entry.addProperty("sha256",pin);entry.addProperty("originalMp3Sha256","1".repeat(64));
            var entries=new JsonObject();entries.add(hash,entry);var manifest=new JsonObject();manifest.add("entries",entries);
            Files.writeString(root.resolve("manifest.json"),manifest.toString());
            Path profile=root.resolve("profile");var first=load(profile);
            check(first.clips().size()==1&&first.resourcesChanged(),"new OGG/definitions require a resource load: "+first.error());
            Path pack=profile.resolve("resourcepacks/"+HeroVoiceAssets.PACK);
            Path definitions=pack.resolve("assets/owmcguest/sounds.json"),metadata=pack.resolve("pack.mcmeta");
            FileTime stamp=FileTime.fromMillis(1_000_000L);Files.setLastModifiedTime(definitions,stamp);Files.setLastModifiedTime(metadata,stamp);
            var second=load(profile);
            check(!second.resourcesChanged()&&second.clips().equals(first.clips()),"prebuilt receipt cache remains unchanged");
            check(Files.getLastModifiedTime(definitions).equals(stamp)&&Files.getLastModifiedTime(metadata).equals(stamp),"unchanged resource JSON is not rewritten");
            check(!second.reusable(true,true,c->true),"incomplete roster cannot certify successful reuse");
            var ready=new HeroVoiceAssets.Loaded(second.clips(),1,0,"",1,false);
            check(ready.reusable(true,true,c->c.hash().equals(hash)),"verified active registered resources can reuse the loaded bank");
            check(!ready.reusable(false,true,c->true)&&!ready.reusable(true,false,c->true),"enabled/active gates are independent");
            check(!ready.reusable(true,true,c->false),"stale/missing sound registry forces reload");
            check(!new HeroVoiceAssets.Loaded(second.clips(),1,0,"",1,true).reusable(true,true,c->true),"changed content forces reload despite matching IDs");
            Files.writeString(definitions,new GsonBuilder().setPrettyPrinting().create().toJson(JsonParser.parseString(Files.readString(definitions))));
            check(!load(profile).resourcesChanged(),"equivalent Python/Gson JSON formatting does not reload");
            Files.writeString(definitions,"{}");check(load(profile).resourcesChanged(),"removed definitions force reload");
            Files.writeString(metadata,"{\"pack\":{\"pack_format\":35}}");check(load(profile).resourcesChanged(),"metadata change forces reload");
            Path cached=pack.resolve("assets/owmcguest/sounds/private/full/"+hash+".ogg");
            byte[] tampered=blob.clone();tampered[tampered.length-1]=1;Files.write(cached,tampered);
            var corrupt=load(profile);check(corrupt.clips().isEmpty()&&!corrupt.error().isEmpty(),"corrupt OGG never becomes a reusable loaded bank");
            check(Arrays.equals(Files.readAllBytes(cached),tampered),"user-modified OGG is preserved");
            System.out.println("HeroVoiceReloadCheck passed: unchanged prebuilt cache, registry gates, metadata changes, incomplete/error and modified OGG refusal");
        }finally{
            if(previous==null)System.clearProperty("owmc.heroVoiceDirectory");else System.setProperty("owmc.heroVoiceDirectory",previous);
            check(root.startsWith(temporary),"cleanup stays inside owned temporary directory");
            try(var paths=Files.walk(root)){for(Path path:paths.sorted(Comparator.reverseOrder()).toList())Files.delete(path);}
        }
    }
}
