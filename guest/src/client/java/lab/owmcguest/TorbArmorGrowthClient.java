package lab.owmcguest;

import com.google.gson.*;
import net.minecraft.client.MinecraftClient;
import net.minecraft.entity.LivingEntity;
import net.minecraft.entity.attribute.EntityAttributes;

/** Numeric observation of real synced client dimensions, on the client tick. */
final class TorbArmorGrowthClient {
    static volatile String status="[]";
    static void tick(MinecraftClient c){
        var rows=new JsonArray();
        if(c.world!=null)try{var server=JsonParser.parseString(TorbArmorGrowthRuntime.status).getAsJsonObject();
            var expectedRows=new JsonArray();if(server.has("recipients"))server.getAsJsonArray("recipients").forEach(expectedRows::add);
            var fixture=JsonParser.parseString(NativeBuildersLab.packRecipientStatus).getAsJsonObject();
            if(fixture.has("entityId"))expectedRows.add(fixture);
            var seen=new java.util.HashSet<String>();for(var value:expectedRows){
                var expected=value.getAsJsonObject();var entity=c.world.getEntityById(expected.get("entityId").getAsInt());
                if(!(entity instanceof LivingEntity e)||!e.getUuidAsString().equals(expected.get("id").getAsString()))continue;
                if(!seen.add(e.getUuidAsString()))continue;
                var row=new JsonObject();row.addProperty("id",e.getUuidAsString());row.addProperty("scale",e.getAttributeValue(EntityAttributes.GENERIC_SCALE));row.addProperty("width",e.getBoundingBox().getLengthX());row.addProperty("height",e.getBoundingBox().getLengthY());rows.add(row);
            }
        }catch(RuntimeException ignored){}status=rows.toString();
    }
}
