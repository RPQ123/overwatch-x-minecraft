package lab.owmcguest;
import lab.owmcguest.NativeShotProtocol.Vec;
/** Screen-relative left hand, shared by hook and rope. This is an explicitly
 * labelled MC camera adapter; no claim of a measured native bone/pixel fit. */
public final class GrappleHandOrigin {
    public static final MuzzlePresentation.Profile LEFT=new MuzzlePresentation.Profile("Widowmaker left grapple hand",-.34,-.30,.65,4);
    public static Vec offset(MuzzlePresentation.Basis basis,double fov,double aspect){return MuzzlePresentation.offset(LEFT,basis,fov,aspect);}
    private GrappleHandOrigin(){}
}
