package lab.owmcguest;

import com.google.gson.*;
import java.util.*;
import net.minecraft.entity.EntityType;
import net.minecraft.entity.mob.ZombieEntity;
import net.minecraft.server.MinecraftServer;
import net.minecraft.util.math.Vec3d;

/** Bounded, isolated-world oracle; never enabled in a user's ordinary save. */
public final class SurvivalLab {
    private static ZombieEntity zombie;public static volatile String status="{}";
    public static void action(MinecraftServer server,UUID owner,String action){
        String error="";var p=server.getPlayerManager().getPlayer(owner);
        try{
            if(!server.isOnThread()||!server.isSingleplayer()||!Boolean.getBoolean("owmc.survivalLab")||!System.getProperty("owmc.worldName","").startsWith("Overwatch Twilight Switch G Survival Lab ")||p==null)throw new IllegalArgumentException("isolated G survival lab required");
            switch(action){
                case "enable"->{error=SurvivalRuntime.setEnabled(server,owner,true);}
                case "disable"->{error=SurvivalRuntime.setEnabled(server,owner,false);}
                case "summon-all"->{error=HeroSummonRuntime.summon(server,owner,NativeWorldIdentity.of(server,p.getWorld().getRegistryKey()),-1,()->true);}
                case "clear"->{error=HeroSummonRuntime.summon(server,owner,NativeWorldIdentity.of(server,p.getWorld().getRegistryKey()),-2,()->true);close();}
                case "zombie"->{
                    close();zombie=new ZombieEntity(EntityType.ZOMBIE,p.getServerWorld());
                    var f=p.getRotationVec(1).multiply(1,0,1).normalize();var at=p.getPos().add(f.multiply(1.3));
                    zombie.refreshPositionAndAngles(at.x,at.y,at.z,p.getYaw()+180,0);zombie.setPersistent();zombie.setSilent(true);zombie.addCommandTag("owmc-g-survival-lab");
                    zombie.equipStack(net.minecraft.entity.EquipmentSlot.HEAD,new net.minecraft.item.ItemStack(net.minecraft.item.Items.CARVED_PUMPKIN));
                    if(!p.getServerWorld().isSpaceEmpty(zombie,zombie.getBoundingBox())||!p.getServerWorld().spawnEntity(zombie))throw new IllegalStateException("zombie space blocked");
                    zombie.setTarget(p);
                }
                case "stop-zombie"->close();
                case "fall"->p.damage(p.getDamageSources().fall(),4);
                case "lava"->p.damage(p.getDamageSources().lava(),4);
                case "explosion"->p.damage(p.getDamageSources().explosion(null,null),4);
                case "lethal"->p.damage(p.getDamageSources().genericKill(),1000);
                default->throw new IllegalArgumentException("unknown G lab action");
            }
        }catch(Exception failure){error=failure.toString();}
        var out=new JsonObject();out.addProperty("action",action);out.addProperty("error",error);out.addProperty("wall",System.currentTimeMillis());out.addProperty("zombie",zombie==null?0:zombie.getId());status=out.toString();
    }
    public static void close(){if(zombie!=null){zombie.discard();zombie=null;}}
}
