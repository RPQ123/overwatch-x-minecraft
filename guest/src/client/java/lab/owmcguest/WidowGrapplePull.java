package lab.owmcguest;

import net.minecraft.client.network.ClientPlayerEntity;
import net.minecraft.util.hit.BlockHitResult;
import net.minecraft.util.hit.HitResult;
import net.minecraft.util.math.BlockPos;
import net.minecraft.util.math.Direction;
import net.minecraft.util.math.Vec3d;
import net.minecraft.world.RaycastContext;

/** MC-owned Grappling Hook geometry. The original hook test runs against the hidden
 * OW map, so MC tests real blocks and moves the real player; native keeps animation,
 * cooldown and HUD. Values are an explicit MC adaptation of the beta's 20 m hook. */
final class WidowGrapplePull {
    static final double RANGE=20, SPEED=1.1, ARRIVE=1.4;
    static final long MAX_MS=1600;
    /** Pull state for one admitted cast. */
    record Pull(Vec3d anchor,boolean ledge,long started,Vec3d start){}

    /** Real block hit within range, else null (a miss pulls nothing). */
    static Pull aim(ClientPlayerEntity p,long now){
        var eye=p.getEyePos();var end=eye.add(p.getRotationVec(1).multiply(RANGE));
        BlockHitResult hit=p.getWorld().raycast(new RaycastContext(eye,end,RaycastContext.ShapeType.COLLIDER,RaycastContext.FluidHandling.NONE,p));
        if(hit.getType()!=HitResult.Type.BLOCK)return null;
        return new Pull(hit.getPos(),ledge(p,hit),now,p.getPos());
    }
    /** Hooking a wall face whose top is within 1.5 blocks and open above lets Widow vault over. */
    private static boolean ledge(ClientPlayerEntity p,BlockHitResult hit){
        if(hit.getSide().getAxis()==Direction.Axis.Y)return false;
        var w=p.getWorld();var pos=hit.getBlockPos();
        for(int up=0;up<=1;up++){
            BlockPos top=pos.up(up);
            if(w.getBlockState(top.up()).getCollisionShape(w,top.up()).isEmpty()&&w.getBlockState(top.up(2)).getCollisionShape(w,top.up(2)).isEmpty())
                return top.getY()+1-hit.getPos().y<=1.5;
            if(w.getBlockState(top.up()).getCollisionShape(w,top.up()).isEmpty())return false;
        }
        return false;
    }
    /** Per-tick displacement toward the anchor, or null when the pull has finished. */
    static Vec3d step(ClientPlayerEntity p,Pull pull,long now){
        if(now-pull.started()>MAX_MS)return null;
        var center=p.getPos().add(0,p.getHeight()*.5,0);var to=pull.anchor().subtract(center);double d=to.length();
        if(d<ARRIVE)return null;
        return to.multiply(Math.min(SPEED,d)/d);
    }
    /** Momentum kept after release; a ledge hook adds a vault over the top. */
    static Vec3d release(ClientPlayerEntity p,Pull pull,Vec3d last){
        var keep=last==null?Vec3d.ZERO:last.multiply(.55);
        return pull.ledge()?new Vec3d(keep.x,Math.max(keep.y,.62),keep.z):keep;
    }
}
