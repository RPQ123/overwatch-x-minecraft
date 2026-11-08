package lab.owmcguest;

import com.google.gson.*;
import java.util.*;
import java.util.function.BooleanSupplier;
import net.minecraft.server.MinecraftServer;
import net.minecraft.util.math.*;
import net.minecraft.world.Heightmap;

/** F5 owns only its own ephemeral training NPCs; F9 mobs remain independent. */
public final class HeroSummonRuntime {
    private static final List<HeroNpcEntity> entities=new ArrayList<>();
    private static long spawned,kills,cleared,requests;private static String error="";
    public static volatile String status="{}";
    public static String summon(MinecraftServer server,UUID owner,long world,int choice,BooleanSupplier admitted){
        requests++;var p=server.getPlayerManager().getPlayer(owner);
        if(!server.isOnThread()||!server.isSingleplayer()||p==null||!p.isAlive()||!SurvivalRuntime.permitted(p)
            ||NativeWorldIdentity.of(server,p.getWorld().getRegistryKey())!=world||!admitted.getAsBoolean())return "等待当前英雄和世界就绪";
        if(choice==-2){
            var own=entities.stream().filter(e->owner.equals(e.summonedBy)).toList();
            for(var e:own){e.discard();entities.remove(e);cleared++;}tick(server);return "";
        }
        var selected=new ArrayList<Integer>();if(choice==-1)for(int i=0;i<HeroNpcCatalog.ENTRIES.size();i++)selected.add(i);else{HeroNpcCatalog.entry(choice);selected.add(choice);}
        if(entities.stream().filter(e->e.isAlive()&&owner.equals(e.summonedBy)).count()+selected.size()>48)return "最多召唤 48 位英雄，请先清除召唤";
        var worldObject=p.getServerWorld();var forward=p.getRotationVec(1).multiply(1,0,1).normalize();if(forward.lengthSquared()<.5)forward=new Vec3d(0,0,1);
        var right=new Vec3d(-forward.z,0,forward.x);var staged=new ArrayList<HeroNpcEntity>();
        for(int i:selected){
            HeroNpcEntity npc=null;
            for(int slot=0;slot<48;slot++){
                var at=p.getPos().add(forward.multiply(3+(slot/4)*1.8)).add(right.multiply((slot%4-1.5)*1.5));var pos=BlockPos.ofFloored(at);
                if(!worldObject.isChunkLoaded(pos))continue;
                // A loaded solid platform near the player's feet is preferred;
                // natural terrain uses its actual motion-blocking surface.
                var floor=pos;boolean ground=false;
                for(int dy=3;dy>=-4;dy--){var candidate=pos.add(0,dy,0);if(worldObject.getBlockState(candidate.down()).isSolidBlock(worldObject,candidate.down())&&worldObject.getBlockState(candidate).isAir()&&worldObject.getBlockState(candidate.up()).isAir()){floor=candidate;ground=true;break;}}
                if(!ground)continue;
                var candidate=new HeroNpcEntity(HeroNpcEntity.TYPE,worldObject);candidate.configure(i,owner);candidate.refreshPositionAndAngles(floor.getX()+.5,floor.getY(),floor.getZ()+.5,p.getYaw()+180,0);
                var box=candidate.getBoundingBox();
                if(!worldObject.isSpaceEmpty(candidate,box)||!worldObject.getOtherEntities(candidate,box).isEmpty()||staged.stream().anyMatch(e->e.getBoundingBox().intersects(box))){candidate.discard();continue;}
                npc=candidate;break;
            }
            if(npc==null){for(var e:staged)e.discard();return "前方没有足够的安全空地，请换个位置";}staged.add(npc);
        }
        if(!admitted.getAsBoolean()){for(var e:staged)e.discard();return "召唤已取消";}
        var added=new ArrayList<HeroNpcEntity>();
        for(var e:staged){if(!worldObject.spawnEntity(e)){for(var n:staged)n.discard();entities.removeAll(added);return "英雄生成失败";}added.add(e);}
        entities.addAll(added);spawned+=added.size();error="";tick(server);return "";
    }
    public static void killed(HeroNpcEntity e){if(!e.getWorld().isClient&&e.getServer()!=null&&e.getServer().isOnThread()&&entities.stream().anyMatch(owned->owned==e))kills++;}
    public static void tick(MinecraftServer server){
        entities.removeIf(e->e.isRemoved());var out=new JsonObject();var rows=new JsonArray();
        for(var e:entities){var o=new JsonObject();o.addProperty("id",e.getId());o.addProperty("hero",HeroNpcCatalog.entry(e.heroIndex()).id());o.addProperty("health",e.getHealth());o.addProperty("alive",e.isAlive());o.addProperty("x",e.getX());o.addProperty("y",e.getY());o.addProperty("z",e.getZ());rows.add(o);}
        out.addProperty("active",entities.stream().filter(HeroNpcEntity::isAlive).count());out.addProperty("spawned",spawned);out.addProperty("kills",kills);out.addProperty("cleared",cleared);out.addProperty("requests",requests);out.addProperty("error",error);out.add("entities",rows);status=out.toString();
    }
    public static void close(){for(var e:List.copyOf(entities))e.discard();entities.clear();}
}
