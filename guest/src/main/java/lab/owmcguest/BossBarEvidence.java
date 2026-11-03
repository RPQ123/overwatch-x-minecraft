package lab.owmcguest;

import java.io.*;
import java.lang.reflect.*;
import java.util.*;

/** Bounded server-side metadata inspection. No trial entity is ever inserted into a world.
 * Unknown/unreadable classes fail closed. Detects lazy/null bars, inherited/generic
 * holders and custom boss/HUD protocols, rather than relying on entity size or live viewers. */
public final class BossBarEvidence {
    public enum Verdict { CLEAR,HAS_BAR,UNKNOWN }
    private static final Set<Class<?>> barTypes=java.util.concurrent.ConcurrentHashMap.newKeySet();
    private static final Set<Class<?>> sharedBases=java.util.concurrent.ConcurrentHashMap.newKeySet();
    private BossBarEvidence(){}
    /** Supply actual runtime Class identities, which remain correct after Fabric/Connector remapping. */
    public static void registerBarType(Class<?> type){barTypes.add(type);}
    public static void registerSharedBase(Class<?> type){sharedBases.add(type);}
    private static boolean barType(Type type,Set<Type> seen){
        if(!seen.add(type))return false;
        if(type instanceof Class<?> cls){
            if(barTypes.stream().anyMatch(root->root.isAssignableFrom(cls)))return true;
            return cls.isArray()&&barType(cls.getComponentType(),seen);
        }
        if(type instanceof ParameterizedType generic){for(Type arg:generic.getActualTypeArguments())if(barType(arg,seen))return true;}
        if(type instanceof GenericArrayType array)return barType(array.getGenericComponentType(),seen);
        if(type instanceof WildcardType wildcard){for(Type bound:wildcard.getUpperBounds())if(barType(bound,seen))return true;for(Type bound:wildcard.getLowerBounds())if(barType(bound,seen))return true;}
        if(type instanceof TypeVariable<?> variable){for(Type bound:variable.getBounds())if(barType(bound,seen))return true;}
        return false;
    }
    private static boolean signal(String text){
        String s=text.toLowerCase(Locale.ROOT).replace("_","");
        return s.contains("bossbar")||s.contains("bossevent")||s.contains("bossinfo")||s.contains("bosshud")||s.contains("bossoverlay")||s.contains("bosshealth")||s.contains("healthbar")||s.contains("bosssync")||s.contains("bossupdate")||s.contains("bossdisplay");
    }
    private static boolean base(Class<?> type){
        return sharedBases.contains(type)||Set.of("net.minecraft.entity.Entity","net.minecraft.entity.LivingEntity","net.minecraft.entity.mob.MobEntity","java.lang.Object").contains(type.getName());
    }
    private static final ClassValue<Verdict> metadata=new ClassValue<>(){
        @Override protected Verdict computeValue(Class<?> type){
            if(base(type))return Verdict.CLEAR;
            String name=type.getSimpleName().toLowerCase(Locale.ROOT);
            if(name.contains("boss")||signal(type.getName()))return Verdict.HAS_BAR;
            try{
                for(Class<?> it:type.getInterfaces()){
                    if(it.getSimpleName().toLowerCase(Locale.ROOT).contains("boss")||signal(it.getName()))return Verdict.HAS_BAR;
                    var inherited=BossBarEvidence.metadata.get(it);if(inherited!=Verdict.CLEAR)return inherited;
                }
                for(Field field:type.getDeclaredFields())if(!Modifier.isStatic(field.getModifiers())&&(barType(field.getGenericType(),new HashSet<>())||signal(field.getName())||signal(field.getGenericType().getTypeName())))return Verdict.HAS_BAR;
                for(Method method:type.getDeclaredMethods())if(barType(method.getGenericReturnType(),new HashSet<>())||signal(method.getName())||signal(method.getGenericReturnType().getTypeName()))return Verdict.HAS_BAR;
                // Author custom bars commonly have no vanilla BossBar field: their
                // packet/channel/helper references still appear in the class constant pool.
                String resource="/"+type.getName().replace('.','/')+".class";
                try(var stream=type.getResourceAsStream(resource)){
                    if(stream==null)return Verdict.UNKNOWN;
                    var in=new DataInputStream(new BufferedInputStream(stream));if(in.readInt()!=0xcafebabe)return Verdict.UNKNOWN;
                    in.readUnsignedShort();in.readUnsignedShort();int count=in.readUnsignedShort();
                    for(int i=1;i<count;i++)switch(in.readUnsignedByte()){
                        case 1->{String value=in.readUTF();if(!value.endsWith(".java")&&!value.equals(type.getName().replace('.','/'))&&signal(value))return Verdict.HAS_BAR;}
                        case 3,4->in.skipNBytes(4);
                        case 5,6->{in.skipNBytes(8);i++;}
                        case 7,8,16,19,20->in.skipNBytes(2);
                        case 9,10,11,12,17,18->in.skipNBytes(4);
                        case 15->in.skipNBytes(3);
                        default->{return Verdict.UNKNOWN;}
                    }
                }
                return Verdict.CLEAR;
            }catch(IOException|RuntimeException|LinkageError failure){return Verdict.UNKNOWN;}
        }
    };
    public static Verdict inspect(Object entity){
        return inspect(entity,0,Collections.newSetFromMap(new IdentityHashMap<>()),new int[]{128});
    }
    private static Verdict inspect(Object entity,int depth,Set<Object> seen,int[] budget){
        if(entity==null)return Verdict.UNKNOWN;
        if(depth>4||--budget[0]<0)return Verdict.UNKNOWN;
        if(!seen.add(entity))return Verdict.CLEAR;
        if(barType(entity.getClass(),new HashSet<>()))return Verdict.HAS_BAR;
        if(entity instanceof Number||entity instanceof String||entity instanceof Boolean||entity instanceof UUID)return Verdict.CLEAR;
        if(entity instanceof Optional<?> optional)return optional.isEmpty()?Verdict.CLEAR:inspect(optional.get(),depth+1,seen,budget);
        if(entity instanceof Map<?,?> map){for(Object value:map.values()){var result=inspect(value,depth+1,seen,budget);if(result!=Verdict.CLEAR)return result;}return Verdict.CLEAR;}
        if(entity instanceof Iterable<?> list){for(Object value:list){var result=inspect(value,depth+1,seen,budget);if(result!=Verdict.CLEAR)return result;}return Verdict.CLEAR;}
        if(entity instanceof Object[] array){for(Object value:array){var result=inspect(value,depth+1,seen,budget);if(result!=Verdict.CLEAR)return result;}return Verdict.CLEAR;}
        for(Class<?> type=entity.getClass();type!=null&&!base(type);type=type.getSuperclass()){
            var result=metadata.get(type);if(result!=Verdict.CLEAR)return result;
            // Inspect opaque custom HUD holders only; traversing World/AI graphs would
            // confuse references to other creatures with this entity's own bar.
            for(Field field:type.getDeclaredFields()){
                if(Modifier.isStatic(field.getModifiers())||field.getType().isPrimitive())continue;
                String name=field.getName().toLowerCase(Locale.ROOT);
                if(!name.contains("bar")&&!name.contains("hud")&&!name.contains("overlay"))continue;
                try{
                    if(!field.trySetAccessible())return Verdict.UNKNOWN;
                    Object value=field.get(entity);if(value==null)continue;
                    var nested=inspect(value,depth+1,seen,budget);if(nested!=Verdict.CLEAR)return nested;
                }catch(IllegalAccessException|RuntimeException failure){return Verdict.UNKNOWN;}
            }
        }
        return Verdict.CLEAR;
    }
    public static boolean bossTag(String id){return id.toLowerCase(Locale.ROOT).contains("boss");}
}
