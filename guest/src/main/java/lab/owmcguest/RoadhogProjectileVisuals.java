package lab.owmcguest;

/** Existing24919 mesh selections. Q has no separate solid bullet in its native
 * factory: its original sprite is retained over the hero's own debris meshes.
 * Size, orientation and the reuse in flight are explicit MC presentation. */
public final class RoadhogProjectileVisuals {
    public record Body(String name,float centerY,float scale,float fireSize){}
    private static final Body A=new Body("roadhog-rh2-scrap-a",.055724211f,.45f,.20f);
    private static final Body B=new Body("roadhog-rh2-scrap-b",.067215964f,.24f,.20f);
    private static final Body PARENT=new Body("roadhog-rh2-secondary",.20232895f,.65f,.38f);
    private RoadhogProjectileVisuals(){}
    public static Body body(long resource,String identity){
        if(resource==RoadhogRules.SECONDARY)return PARENT;
        if(resource!=RoadhogRules.SCRAP&&resource!=RoadhogRules.WHOLE_HOG)throw new IllegalArgumentException("Roadhog visual resource");
        return (identity.hashCode()&1)==0?A:B;
    }
}
