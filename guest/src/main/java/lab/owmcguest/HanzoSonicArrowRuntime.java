package lab.owmcguest;

import java.util.Map;
import java.util.LinkedHashMap;
import java.util.UUID;
import com.google.gson.JsonObject;
import net.minecraft.entity.LivingEntity;
import net.minecraft.server.MinecraftServer;
import net.minecraft.util.math.BlockPos;
import net.minecraft.util.math.Box;
import lab.owmcguest.NativeShotProtocol.Shot;
import lab.owmcguest.NativeShotSimulation.Hit;
import lab.owmcguest.HanzoSonicArrowState.Scope;
import lab.owmcguest.HanzoSonicArrowState.Point;

/** Server collision drives a private client reveal; never applies a global
 * glowing potion, modifies teams, adds damage, grants charge or changes native CD.
 * Receives accepted original factories and retired real MC sweep contacts. */
public final class HanzoSonicArrowRuntime {
    private static final HanzoSonicArrowState state=new HanzoSonicArrowState();
    public record View(UUID owner,String dimension,long world,long generation,long model,
                       long wall,Map<Integer,UUID> entities,java.util.List<HanzoSonicArrowState.Pulse> pulses) {}
    public static volatile View view;
    public static volatile String status="{\"active\":false,\"integrated\":true}";
    private static boolean matches(MinecraftServer server,Scope scope){
        if(scope==null||!scope.valid())return false;
        var owner=server.getPlayerManager().getPlayer(scope.owner());
        return owner!=null&&owner.isAlive()
            &&NativeWorldIdentity.of(server,owner.getWorld().getRegistryKey())==scope.world()
            &&NativeEliminationRuntime.sessionMatches(scope.owner(),scope.world(),HanzoSonicArrowState.HERO,scope.model(),scope.generation());
    }
    public static boolean isSonic(Shot shot){
        return shot!=null&&!shot.hitscan()&&!shot.beam()&&shot.effect()!=null
            &&shot.effect().hero()==HanzoSonicArrowState.HERO
            &&HanzoSonicArrowState.sonicResource(shot.effect().resource());
    }
    /** Call only for the already validated/deduplicated original factory admissions. */
    public static void admit(MinecraftServer server,Scope scope,Shot shot){
        if(!isSonic(shot)||!matches(server,scope))return;
        state.configure(scope);
        state.admit(scope,shot.identity(),shot.effect().resource(),shot.wallMs(),shot.lifetime(),System.currentTimeMillis(),server.getTicks());
    }
    /** Call once from the actual resolved trace, including block impacts. */
    public static void impact(MinecraftServer server,Scope scope,Shot shot,Hit hit){
        if(!isSonic(shot)||hit==null||!matches(server,scope))return;
        var p=server.getPlayerManager().getPlayer(scope.owner());var point=hit.point();
        boolean loaded=hit.loaded()&&p.getServerWorld().isChunkLoaded(BlockPos.ofFloored(point.x(),point.y(),point.z()));
        state.impact(scope,shot.identity(),new Point(point.x(),point.y(),point.z()),loaded,server.getTicks());
    }
    public static void tick(MinecraftServer server){
        Scope scope=state.scope();
        if(!matches(server,scope)){resetSession();return;}
        state.advance(scope,server.getTicks());
        var owner=server.getPlayerManager().getPlayer(scope.owner());var world=owner.getServerWorld();
        var revealed=new LinkedHashMap<Integer,UUID>();
        for(var pulse:state.pulses()){
            var at=pulse.at();double radius=HanzoSonicArrowState.RADIUS;
            if(!world.isChunkLoaded(BlockPos.ofFloored(at.x(),at.y(),at.z())))continue;
            // Intentional through-wall sensing. Ordinary damage still uses its
            // existing independent collision/cover query and is not changed.
            for(var entity:world.getOtherEntities(owner,new Box(at.x()-radius,at.y()-radius,at.z()-radius,at.x()+radius,at.y()+radius,at.z()+radius),
                    e->e instanceof LivingEntity&&e.isAlive()&&!e.isSpectator()&&!owner.isTeammate(e))){
                var center=entity.getBoundingBox().getCenter();
                if(state.reveals(new Point(center.x,center.y,center.z)))revealed.put(entity.getId(),entity.getUuid());
            }
        }
        view=new View(scope.owner(),world.getRegistryKey().getValue().toString(),scope.world(),scope.generation(),scope.model(),System.currentTimeMillis(),Map.copyOf(revealed),state.pulses());
        var json=new JsonObject();json.addProperty("integrated",true);json.addProperty("active",!state.pulses().isEmpty());json.addProperty("admitted",state.admitted);json.addProperty("impacts",state.impacts);json.addProperty("refused",state.refused);json.addProperty("duplicates",state.duplicates);json.addProperty("expired",state.expired);json.addProperty("flights",state.flights());json.addProperty("pulses",state.pulses().size());json.addProperty("revealed",revealed.size());json.addProperty("durationTicks",HanzoSonicArrowState.DURATION_TICKS);json.addProperty("radius",HanzoSonicArrowState.RADIUS);json.addProperty("world",scope.world());json.addProperty("model",scope.model());json.addProperty("attachment","fixed MC impact; beta moving attachment not authenticated");
        var ids=new com.google.gson.JsonArray();for(int id:revealed.keySet())ids.add(id);json.add("entityIds",ids);
        var anchors=new com.google.gson.JsonArray();for(var pulse:state.pulses()){var anchor=new JsonObject();anchor.addProperty("x",pulse.at().x());anchor.addProperty("y",pulse.at().y());anchor.addProperty("z",pulse.at().z());anchor.addProperty("expires",pulse.expires());anchors.add(anchor);}json.add("anchors",anchors);
        status=json.toString();
    }
    public static void resetSession(){state.clear();view=null;status="{\"active\":false,\"integrated\":true}";}
}
