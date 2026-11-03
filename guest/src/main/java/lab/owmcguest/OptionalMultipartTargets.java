package lab.owmcguest;

import java.lang.reflect.Method;
import java.util.IdentityHashMap;
import java.util.LinkedHashMap;
import java.util.Map;
import net.minecraft.entity.Entity;
import net.minecraft.server.world.ServerWorld;

/** Optional Porting Lib contract: real part entities retain their own damage rules. */
public final class OptionalMultipartTargets {
    private static Class<?> multipart,partType;
    private static Method getParts,getParent;
    private static String error="";
    private record Frame(long tick,Map<Integer,Entity> parts){}
    private static final Map<ServerWorld,Frame> frames=new IdentityHashMap<>();
    static {
        try {
            multipart=Class.forName("io.github.fabricators_of_create.porting_lib.entity.MultiPartEntity");
            partType=Class.forName("io.github.fabricators_of_create.porting_lib.entity.PartEntity");
            getParts=multipart.getMethod("getParts");getParent=partType.getMethod("getParent");
            if(!Entity.class.isAssignableFrom(partType)||!getParts.getReturnType().isArray()
                ||getParts.getReturnType().getComponentType()!=partType||!Entity.class.isAssignableFrom(getParent.getReturnType()))throw new ReflectiveOperationException("Unexpected multipart API");
        }catch(ClassNotFoundException absent){multipart=null;partType=null;}
        catch(ReflectiveOperationException failure){error=failure.toString();multipart=null;partType=null;}
    }
    public static Entity owner(Entity e){
        if(partType==null||!partType.isInstance(e))return e;
        try {var p=getParent.invoke(e);if(p instanceof Entity parent&&parent!=e&&parent.getWorld()==e.getWorld())return parent;}
        catch(ReflectiveOperationException failure){error=failure.toString();}
        return e;
    }
    /** Hydra root is an undamageable bookkeeping box; its original parts own hits. */
    public static boolean hiddenRoot(Entity e){return multipart!=null&&multipart.isInstance(e)
        &&e.getClass().getName().equals("twilightforest.entity.boss.Hydra");}
    public static Map<Integer,Entity> parts(ServerWorld world){
        if(multipart==null)return Map.of();long tick=world.getTime();var cached=frames.get(world);
        if(cached!=null&&cached.tick()==tick)return cached.parts();
        var result=new LinkedHashMap<Integer,Entity>();
        // Once per real server tick, not one whole-world scan per pellet/ray.
        for(var parent:world.iterateEntities())if(parent.isAlive()&&multipart.isInstance(parent)){
            try {
                var raw=getParts.invoke(parent);if(raw==null)continue;
                int count=java.lang.reflect.Array.getLength(raw);if(count>128)throw new ReflectiveOperationException("Multipart count bound");
                for(int i=0;i<count;i++){
                    var value=java.lang.reflect.Array.get(raw,i);
                    if(value instanceof Entity part&&partType.isInstance(part)&&!part.isRemoved()
                        &&part.getWorld()==world&&owner(part)==parent&&part.getId()!=0){
                        if(result.putIfAbsent(part.getId(),part)!=null)throw new ReflectiveOperationException("Duplicate multipart identity");
                    }
                }
            }catch(ReflectiveOperationException failure){error=failure.toString();result.clear();break;}
        }
        frames.put(world,new Frame(tick,java.util.Collections.unmodifiableMap(result)));return result;
    }
    public static String status(){return "{\"available\":"+(multipart!=null)+",\"error\":"+new com.google.gson.Gson().toJson(error)+"}";}
    public static void reset(){frames.clear();}
}
