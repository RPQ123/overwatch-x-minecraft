package lab.owmcguest;

import net.minecraft.entity.damage.DamageSource;
import net.minecraft.entity.decoration.ArmorStandEntity;
import net.minecraft.nbt.NbtCompound;
import net.minecraft.server.world.ServerWorld;

/** MC 适配的临时可伤害实体。复用 MC 的同步/碰撞；禁止盔甲架的箭矢秒拆语义和存档残留。 */
final class NativeBuildersBody extends ArmorStandEntity {
    private final java.util.UUID owner;
    NativeBuildersBody(ServerWorld world,double x,double y,double z,java.util.UUID owner){
        super(world,x,y,z);this.owner=owner;setInvisible(true);setSilent(true);setNoGravity(true);addCommandTag("owmc-builders-body");
    }
    @Override public boolean damage(DamageSource source,float amount){
        if(getWorld().isClient||!isAlive()||!Float.isFinite(amount)||amount<=0||isInvulnerableTo(source)
            ||source.getAttacker()!=null&&source.getAttacker().getUuid().equals(owner))return false;
        setHealth(Math.max(0,getHealth()-amount));
        if(getHealth()<=0){onDeath(source);discard();}
        return true;
    }
    @Override public boolean saveNbt(NbtCompound nbt){return false;}
}
