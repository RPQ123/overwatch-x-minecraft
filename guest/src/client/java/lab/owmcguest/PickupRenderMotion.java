package lab.owmcguest;

import net.minecraft.util.math.Vec3d;

/** Interpolate only real server samples, with no extrapolation past a pickup. */
final class PickupRenderMotion {
    private PickupRenderMotion(){}
    static Vec3d at(Vec3d previous,Vec3d current,long wall,long now){return previous.lerp(current,Math.clamp((now-wall)/50.,0,1));}
}
