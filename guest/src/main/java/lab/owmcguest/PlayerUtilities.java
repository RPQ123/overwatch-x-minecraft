package lab.owmcguest;

import com.google.gson.JsonObject;
import java.util.*;
import net.minecraft.entity.EntityType;
import net.minecraft.entity.mob.MobEntity;
import net.minecraft.server.MinecraftServer;
import net.minecraft.util.math.*;

/** Explicit player-requested local creative conveniences, on the server thread. */
public final class PlayerUtilities {
    private static final List<EntityType<? extends MobEntity>> TYPES=List.of(EntityType.ZOMBIE,EntityType.HUSK,EntityType.SKELETON,EntityType.STRAY,EntityType.SPIDER,EntityType.SLIME,EntityType.ENDERMAN,EntityType.PILLAGER);
    private static long batches,spawned;private static String error="";
    public static volatile String status="{}";
    public static void spawnBatch(MinecraftServer server,UUID owner){
        var p=server.getPlayerManager().getPlayer(owner);int count=0;
        if(p==null||!p.isAlive()||!SurvivalRuntime.permitted(p)){publish(0,"Random mobs require a living creative player");return;}
        var world=p.getServerWorld();var random=world.getRandom();
        for(int attempt=0;attempt<80&&count<8;attempt++){
            double angle=random.nextDouble()*Math.PI*2,distance=7+random.nextDouble()*6;
            int x=(int)Math.floor(p.getX()+Math.cos(angle)*distance),z=(int)Math.floor(p.getZ()+Math.sin(angle)*distance);
            var column=new BlockPos(x,p.getBlockY(),z);if(!world.isChunkLoaded(column))continue;
            BlockPos landing=null;
            // Search near the actual player first, including Nether interiors.
            for(int dy=3;dy>=-12;dy--){var at=column.up(dy);if(at.getY()<=world.getBottomY()||at.getY()+3>=world.getTopY())continue;
                if(world.getBlockState(at.down()).isSolidBlock(world,at.down())&&world.getBlockState(at).isAir()&&world.getBlockState(at.up()).isAir()&&world.getBlockState(at.up(2)).isAir()){landing=at;break;}}
            if(landing==null)continue;
            var type=TYPES.get(random.nextInt(TYPES.size()));var mob=type.create(world);if(mob==null)continue;
            mob.refreshPositionAndAngles(landing.getX()+.5,landing.getY(),landing.getZ()+.5,random.nextFloat()*360,0);
            if(!world.getWorldBorder().contains(mob.getBoundingBox())||!world.isSpaceEmpty(mob,mob.getBoundingBox()))continue;
            mob.addCommandTag("owmc-player-random-mob");
            if(world.spawnEntity(mob))count++;
        }
        batches++;spawned+=count;publish(count,count==0?"No loaded safe ground nearby; no mobs spawned":"");
    }
    private static void publish(int last,String failure){error=failure;var o=new JsonObject();o.addProperty("batches",batches);o.addProperty("spawned",spawned);o.addProperty("lastBatch",last);o.addProperty("error",error);status=o.toString();}
    public static void cleanupTestBatch(MinecraftServer server){
        if(!Boolean.getBoolean("owmc.twilightTrial")||!System.getProperty("owmc.worldName","").startsWith("Overwatch Twilight Switch "))return;
        for(var w:server.getWorlds())for(var entity:w.iterateEntities())if(entity.getCommandTags().contains("owmc-player-random-mob"))entity.discard();
    }
}
