package lab.owmcguest;

import java.util.Map;
import java.util.List;

/** User-requested W3 exception: four exact original24919 SFX, not generic grunts.
 * Keys are original WEM content MD5 identifiers; the private manifest pins OGG SHA256. */
public final class WinstonAudioCatalog {
    static final Map<String,String> SFX=Map.of(
        "sfx:winston_takeoff","222440cb09c76f30eb15fe9802765f67",
        "sfx:winston_landing","0a31257cd5de15e0960f4aac70c0012f",
        "sfx:winston_barrier_throw","42809ae4cb54c73c8bf81a8d1c8de02d",
        "sfx:winston_barrier_open","cd9364df0e3861d8fe5e9f336fd58cab");
    static final List<String> VOICES=List.of("ability:jump_pack","ability:barrier","ult_cast");
    private WinstonAudioCatalog() {}
    static float gain(WinstonAudioGate.Event event){return event==WinstonAudioGate.Event.LANDING?.70f:.24f;}
    static boolean allowed(String hero,String event,String hash){return hero.equals("winston")&&hash.equals(SFX.get(event));}
    static String event(WinstonAudioGate.Event event){return switch(event){
        case TAKEOFF->"sfx:winston_takeoff";case LANDING->"sfx:winston_landing";
        case THROW->"sfx:winston_barrier_throw";case DEPLOY->"sfx:winston_barrier_open";case PRIMAL->null;
    };}
}
