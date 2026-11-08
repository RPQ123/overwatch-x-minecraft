package lab.owmcguest;

import java.nio.file.*;

/** Real private manifest/OGG load into a D: fixture profile. No game or playback. */
public final class WinstonAudioAssetCheck {
    private static byte[] ogg(int rate,long samples){
        var b=java.nio.ByteBuffer.allocate(87).order(java.nio.ByteOrder.LITTLE_ENDIAN);
        b.put("OggS".getBytes(java.nio.charset.StandardCharsets.US_ASCII));b.put(26,(byte)1);b.put(27,(byte)30);
        b.position(28);b.put((byte)1).put("vorbis".getBytes(java.nio.charset.StandardCharsets.US_ASCII));b.put(39,(byte)1);b.putInt(40,rate);
        b.position(58);b.put("OggS".getBytes(java.nio.charset.StandardCharsets.US_ASCII));b.putLong(64,samples);b.put(84,(byte)1);b.put(85,(byte)1);return b.array();
    }
    private static void rejects(byte[] bytes){try{HeroVoiceAssets.durationMs(bytes);throw new AssertionError("invalid OGG accepted");}catch(IllegalArgumentException expected){}}
    public static void main(String[] args)throws Exception{
        if(args.length!=2)throw new IllegalArgumentException("voice root + D: fixture parent");
        var root=Path.of(args[0]).toAbsolutePath().normalize();var parent=Path.of(args[1]).toAbsolutePath().normalize();
        if(!root.toString().startsWith("D:")||!parent.toString().startsWith("D:"))throw new IllegalArgumentException("D: fixture only");
        Files.createDirectories(parent);var profile=Files.createTempDirectory(parent,"audio-profile-");
        System.setProperty("owmc.heroVoiceDirectory",root.toString());
        if(HeroVoiceAssets.durationMs(ogg(24000,24000))!=1000||HeroVoiceAssets.durationMs(ogg(48000,48000))!=1000)throw new AssertionError("actual sample rate duration");
        rejects(ogg(48000,0));rejects(ogg(48000,Long.MAX_VALUE));rejects(ogg(1000,1000));
        var invalid=ogg(48000,48000);invalid[28]=0;rejects(invalid);
        try(var assets=new HeroVoiceAssets()){
            var method=HeroVoiceAssets.class.getDeclaredMethod("load",Path.class,long.class);method.setAccessible(true);
            var loaded=(HeroVoiceAssets.Loaded)method.invoke(assets,profile,Files.getLastModifiedTime(root.resolve("manifest.json")).toMillis());
            if(loaded.missing()!=0||!loaded.error().isEmpty())throw new AssertionError(loaded.error()+" missing="+loaded.missing());
            long voices=loaded.clips().stream().filter(c->c.hero().equals("winston")&&WinstonAudioCatalog.VOICES.contains(c.event())).count();
            long effects=loaded.clips().stream().filter(c->WinstonAudioCatalog.allowed(c.hero(),c.event(),c.hash())).count();
            if(voices!=3||effects!=4)throw new AssertionError("W3 voice/effect banks "+voices+"/"+effects);
            for(var clip:loaded.clips())if(clip.durationMs()<=0)throw new AssertionError("empty decoded audio");
            System.out.println("PASS WinstonAudioAssets "+loaded.clips().size()+" real OGG entries,3 Mandarin voices/4 original SFX,0 missing; D: fixture only, no playback");
        }
    }
}
