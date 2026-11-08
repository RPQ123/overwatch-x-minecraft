package lab.owmcguest;

/** Owned24919 entity0295 terminal effect057d -> sound009ca -> media2af1d.
 * CKey is the private sound identity; it is not an invented or downloaded SFX. */
public final class RoadhogSoundCatalog {
    public static final String HASH="7e9c9953e1af642cda6e733c20066108";
    public static final String EVENT="sfx:roadhog_split";
    /** Source-20.83LUFS/-2.51dBTP -> listener-22.77LUFS/-4.45dBTP.
     * The old.45 spatial source at9m was effectively.196875 (-34.95LUFS). */
    public static final float SPLIT_GAIN=.80f;
    private RoadhogSoundCatalog(){}
    public static boolean allowed(String hero,String event,String hash){return "roadhog".equals(hero)&&EVENT.equals(event)&&HASH.equals(hash);}
}
