package lab.owmcguest;

import com.google.gson.JsonObject;
import net.minecraft.entity.decoration.ArmorStandEntity;
import net.minecraft.server.MinecraftServer;
import net.minecraft.util.math.Vec3d;

/** 原版 0232 创建节点32驱动，MC 适配轮胎碰撞、控制、爬墙、相机和无伤害超时回收。
 * MC 适配值：速度12m/s、爬墙8m/s、10s寿命、100OW生命。
 * 没有认证的0233轮胎实体引爆提交信号：禁用攻击，M1和寿命到期都不能制造伤害。 */
public final class NativeJunkratTireRuntime {
    public record View(Vec3d at,float yaw,int age,long world,long wall,boolean climbing,NativeJunkratTireIdentity identity){}
    private static NativeJunkratRuntime.Scope scope;
    private static ArmorStandEntity body;
    private static Vec3d direction=Vec3d.ZERO;private static int bits,age;private static long inputWall;
    private static long casts,detonations,hits,wallTicks,cancelled,destroyed,expired,castAttempts;private static double travelled,damageApplied;
    private static String lastCastRejection="";
    public static volatile View view;public static volatile String status="{}";
    public static boolean active(){return body!=null;}
    public static void cast(MinecraftServer server,NativeJunkratRuntime.Scope next){
        castAttempts++;
        if(!NativeJunkratRuntime.current(next)){reject("scope-not-current");return;}
        if(active()){reject("already-active");return;}
        var p=server.getPlayerManager().getPlayer(next.owner());if(p==null||!p.isAlive()){reject("owner-not-alive");return;}
        var w=p.getServerWorld();var at=p.getPos().add(p.getRotationVec(1).multiply(1,0,1).normalize().multiply(1.2));
        var b=new NativeBuildersBody(w,at.x,at.y,at.z,next.owner());b.getAttributeInstance(net.minecraft.entity.attribute.EntityAttributes.GENERIC_SCALE).setBaseValue(.5);
        b.setHealth(10);if(!w.isSpaceEmpty(b,b.getBoundingBox())){b.discard();reject("occupied-spawn");return;}
        if(!w.spawnEntity(b)){b.discard();reject("spawn-refused");return;}
        scope=next;body=b;age=0;inputWall=0;bits=0;casts++;lastCastRejection="";publish(false);
    }
    private static void reject(String reason){lastCastRejection=reason;publish(view!=null&&view.climbing());}
    /** Only same-owner, current-frame input can steer an already authenticated tire. */
    public static void input(NativeJunkratRuntime.Scope expected,Vec3d forward,int movement,long wall){
        if(!expected.equals(scope)||!NativeJunkratRuntime.current(expected)||body==null||forward==null)return;
        if(!Double.isFinite(forward.x)||!Double.isFinite(forward.z)||forward.horizontalLengthSquared()<.001)return;
        long now=System.currentTimeMillis();if(now-wall>150||wall>now+50)return;
        direction=forward.multiply(1,0,1).normalize();bits=movement;inputWall=wall;
    }
    public static void tick(MinecraftServer server){
        if(body==null)return;
        var p=server.getPlayerManager().getPlayer(scope.owner());
        if(p==null||!p.isAlive()||!NativeJunkratRuntime.current(scope)||NativeWorldIdentity.of(server,p.getWorld().getRegistryKey())!=scope.world()){cancelled++;clear();return;}
        if(body.isRemoved()||!body.isAlive()){destroyed++;clear();return;}
        if(++age>=200){expired++;clear();return;}
        var before=body.getPos();boolean fresh=System.currentTimeMillis()-inputWall<=150;
        int f=fresh?((bits&1)!=0?1:0)-((bits&2)!=0?1:0):0,r=fresh?((bits&8)!=0?1:0)-((bits&4)!=0?1:0):0;
        var right=new Vec3d(-direction.z,0,direction.x);var horizontal=direction.multiply(f).add(right.multiply(r));
        if(horizontal.lengthSquared()>0)horizontal=horizontal.normalize().multiply(.6);
        var velocity=horizontal.add(0,Math.max(-.6,body.getVelocity().y-.05),0);
        body.move(net.minecraft.entity.MovementType.SELF,velocity);
        boolean climb=fresh&&(bits&16)!=0&&body.horizontalCollision&&horizontal.lengthSquared()>0;
        if(climb){body.move(net.minecraft.entity.MovementType.SELF,new Vec3d(0,.4,0));wallTicks++;}
        body.setVelocity(0,body.isOnGround()||climb?0:velocity.y,0);
        travelled+=before.distanceTo(body.getPos());publish(climb);
    }
    private static void publish(boolean climbing){
        view=body==null?null:new View(body.getPos(),(float)Math.toDegrees(Math.atan2(-direction.x,direction.z)),age,scope.world(),System.currentTimeMillis(),climbing,
            new NativeJunkratTireIdentity(scope.owner(),scope.world(),scope.source(),scope.model()));
        var o=new JsonObject();o.addProperty("active",body!=null);o.addProperty("casts",casts);o.addProperty("detonations",detonations);o.addProperty("hits",hits);
        o.addProperty("wallTicks",wallTicks);o.addProperty("travelled",travelled);o.addProperty("damageApplied",damageApplied);o.addProperty("cancelled",cancelled);o.addProperty("destroyed",destroyed);
        o.addProperty("age",age);o.addProperty("climbing",climbing);o.addProperty("trigger","native-0232-create32");o.addProperty("physics","MC adaptation");
        o.addProperty("detonationEnabled",false);o.addProperty("detonationPolicy","blocked: no authenticated native 0233 detonation commit");o.addProperty("expired",expired);status=o.toString();
        o.addProperty("castAttempts",castAttempts);o.addProperty("lastCastRejection",lastCastRejection);status=o.toString();
    }
    public static void clear(){if(body!=null)body.discard();body=null;scope=null;bits=age=0;inputWall=0;direction=Vec3d.ZERO;publish(false);}
}
