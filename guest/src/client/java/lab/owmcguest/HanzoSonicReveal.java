package lab.owmcguest;

import net.minecraft.client.MinecraftClient;
import net.minecraft.entity.Entity;

/** Local outline decision only. Does not change server glow or scoreboard teams. */
public final class HanzoSonicReveal {
    public static volatile String status="{}";
    private HanzoSonicReveal(){}
    public static boolean reveals(Entity entity){
        var client=MinecraftClient.getInstance();var v=HanzoSonicArrowRuntime.view;
        if(v==null||entity==null||client.world==null||entity.getWorld()!=client.world||client.player==null
            ||!client.player.isAlive()||client.getServer()==null||!client.player.getUuid().equals(v.owner()))return false;
        long now=System.currentTimeMillis();
        if(!entity.getUuid().equals(v.entities().get(entity.getId())))return false;
        var loc=NativeLocomotionController.INSTANCE;var host=HostPoseReader.INSTANCE.latest();
        if(loc.hero()!=HanzoSonicArrowState.HERO||loc.modelId()!=v.model()||host==null
            ||!host.inputActive()||host.generation()!=v.generation())return false;
        if(now-v.wall()>150||v.wall()>now+50||!client.world.getRegistryKey().getValue().toString().equals(v.dimension())
            ||NativeWorldIdentity.of(client.getServer(),client.world.getRegistryKey())!=v.world())return false;
        return true;
    }
    /** Client-thread observation, not an alternative reveal/attack authority. */
    public static void tick(MinecraftClient client){
        var out=new com.google.gson.JsonObject();var v=HanzoSonicArrowRuntime.view;
        out.addProperty("view",v!=null);var loc=NativeLocomotionController.INSTANCE;
        out.addProperty("hero",loc.hero());out.addProperty("model",loc.modelId());
        var host=HostPoseReader.INSTANCE.latest();out.addProperty("host",host!=null);
        if(host!=null){out.addProperty("hostGeneration",host.generation());out.addProperty("inputActive",host.inputActive());}
        if(v!=null){out.addProperty("viewModel",v.model());out.addProperty("viewGeneration",v.generation());out.addProperty("ageMs",System.currentTimeMillis()-v.wall());
            var entities=new com.google.gson.JsonArray();
            if(client.world!=null)for(var entry:v.entities().entrySet()){
                var row=new com.google.gson.JsonObject();row.addProperty("id",entry.getKey());var entity=client.world.getEntityById(entry.getKey());row.addProperty("loaded",entity!=null);
                if(entity!=null){row.addProperty("uuidMatches",entity.getUuid().equals(entry.getValue()));row.addProperty("directReveal",reveals(entity));row.addProperty("glowing",entity.isGlowing());row.addProperty("outline",client.hasOutline(entity));row.addProperty("color",entity.getTeamColorValue());}
                entities.add(row);
            }out.add("entities",entities);
        }status=out.toString();
    }
}
