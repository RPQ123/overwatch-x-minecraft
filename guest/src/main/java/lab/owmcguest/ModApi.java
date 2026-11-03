package lab.owmcguest;

import java.lang.reflect.*;

/** Optional author APIs only. No copied mod code or dependency on a foreign loader. */
public final class ModApi {
    private ModApi(){}
    public static Object call(Object receiver,String name,Object... args) throws Exception {
        Class<?> type=receiver instanceof Class<?> c?c:receiver.getClass();
        Method found=null;
        for(Method method:type.getMethods()){
            if(!method.getName().equals(name)||method.getParameterCount()!=args.length)continue;
            boolean match=true;var params=method.getParameterTypes();
            for(int i=0;i<args.length;i++)if(args[i]!=null&&!boxed(params[i]).isInstance(args[i])){match=false;break;}
            if(match){if(found!=null&&found.isBridge()&&!method.isBridge())found=method;else if(found==null)found=method;}
        }
        if(found==null)throw new NoSuchMethodException(type.getName()+"."+name+"/"+args.length);
        try{return found.invoke(receiver instanceof Class<?>?null:receiver,args);}
        catch(InvocationTargetException e){if(e.getCause() instanceof Exception x)throw x;throw e;}
    }
    private static Class<?> boxed(Class<?> c){if(c==int.class)return Integer.class;if(c==boolean.class)return Boolean.class;if(c==long.class)return Long.class;if(c==float.class)return Float.class;if(c==double.class)return Double.class;return c;}
    public static boolean implementsType(Object value,String name){
        if(value==null)return false;
        for(Class<?> c=value.getClass();c!=null;c=c.getSuperclass())for(Class<?> i:c.getInterfaces())if(interfaceNamed(i,name))return true;
        return false;
    }
    private static boolean interfaceNamed(Class<?> c,String name){if(c.getName().equals(name))return true;for(Class<?> i:c.getInterfaces())if(interfaceNamed(i,name))return true;return false;}
}
