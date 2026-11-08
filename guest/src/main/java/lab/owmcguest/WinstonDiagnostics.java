package lab.owmcguest;

import com.google.gson.*;

/** Last Winston sample survives selecting another hero. No unbounded polling log. */
public final class WinstonDiagnostics {
    private static final JsonObject data=new JsonObject();
    private static String lastStage="";private static long lastLog;
    public static synchronized void value(String key,long value){data.addProperty(key,value);}
    public static synchronized void value(String key,double value){data.addProperty(key,value);}
    public static synchronized void value(String key,boolean value){data.addProperty(key,value);}
    public static synchronized void value(String key,String value){data.addProperty(key,value);}
    public static synchronized void increment(String key){data.addProperty(key,data.has(key)?data.get(key).getAsLong()+1:1);}
    public static synchronized void stage(String stage,String error){
        long now=System.currentTimeMillis();data.addProperty("stage",stage);data.addProperty("wall",now);data.addProperty("error",error);
        if(!error.isEmpty()){data.addProperty("lastFailure",error);data.addProperty("lastFailureWall",now);}
        if(!stage.equals(lastStage)&&now-lastLog>=250){System.out.println("[OWMCWinston] "+snapshot());lastLog=now;}
        lastStage=stage;
    }
    public static synchronized JsonObject snapshot(){return data.deepCopy();}
    private WinstonDiagnostics(){}
}
