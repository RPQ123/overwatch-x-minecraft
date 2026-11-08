package lab.owmcguest;
import java.util.UUID;
import lab.owmcguest.NativeShotProtocol.*;
import net.minecraft.client.sound.SoundInstance;
import net.minecraft.client.sound.AbstractSoundInstance;
/** Real production sound factory, measured source levels and attenuation math. */
public final class RoadhogAudioLevelCheck {
    private static int checks;
    private static void check(boolean value,String why){checks++;if(!value)throw new AssertionError(why);}
    public static int run(Source source){
        var scope=new RoadhogPresentation.Scope(UUID.randomUUID(),11,7,source);
        var sound=RoadhogSplitSound.create(new RoadhogSplitCues.Cue(scope,"actual-parent",new Vec(0,64,9),1000));
        // The real sound manager resolves the private OGG before getVolume();
        // this asset-free fixture inspects the factory's source gain directly.
        double now;
        try {var volume=AbstractSoundInstance.class.getDeclaredField("volume");volume.setAccessible(true);now=volume.getFloat(sound);}
        catch(ReflectiveOperationException e){throw new AssertionError("production source gain",e);}
        double old=.45*(1-9./16);
        check(sound.getAttenuationType()==SoundInstance.AttenuationType.NONE,"second-stage parent sound does not lose another9m of local loudness");
        check(now>old&&now<=1,"audible gain remains inside the normal MC source range");
        double delta=20*Math.log10(now/old),lufs=-20.83+20*Math.log10(now),peak=-2.51+20*Math.log10(now);
        check(delta>12&&delta<12.5,"correct the measured spatial attenuation plus source gain, not just the slider");
        check(lufs> -23&&lufs< -22,"source reaches the reference hero-voice/ordinary SFX audibility range");
        check(peak< -4,"measured original true peak keeps over4dB single-source headroom");
        check(sound.getX()==0&&sound.getY()==64&&sound.getZ()==9,"retain actual split location/panning");
        System.out.println("PASS: RH4 sound factory6 checks;9m effective gain.196875->.8,+12.18dB,-22.77LUFS,-4.45dBTP (offline source estimate)");
        return checks;
    }
}
