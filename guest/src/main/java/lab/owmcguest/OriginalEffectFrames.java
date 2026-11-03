package lab.owmcguest;
import com.google.gson.*;
import java.util.UUID;
import net.minecraft.util.math.Vec3d;
final class OriginalEffectFrames {
    static JsonArray vec(Vec3d p){var a=new JsonArray();a.add(p.x);a.add(p.y);a.add(p.z);return a;}
    static JsonObject frame(UUID owner,long world,long source,long model,long wall){
        var f=new JsonObject();f.addProperty("owner",owner.toString());f.addProperty("world",world);
        f.addProperty("source",source);f.addProperty("model",model);f.addProperty("wall",wall);
        f.add("effects",new JsonArray());return f;
    }
    static JsonObject body(JsonObject frame,String name,Vec3d at,Vec3d scale,float alpha,boolean billboard){
        var e=new JsonObject();e.addProperty("mesh",name);e.add("at",vec(at));e.add("scale",vec(scale));
        e.addProperty("alpha",alpha);e.addProperty("billboard",billboard);
        frame.getAsJsonArray("effects").add(e);return e;
    }
    static void beam(JsonObject frame,String name,Vec3d from,Vec3d to,float width,float alpha){
        var e=new JsonObject();e.addProperty("mesh",name);e.add("at",vec(from));e.add("to",vec(to));
        e.addProperty("width",width);e.addProperty("alpha",alpha);frame.getAsJsonArray("effects").add(e);
    }
}
