package lab.owmcguest;

import com.google.gson.*;
import java.nio.file.*;
import java.util.*;
import net.fabricmc.loader.api.FabricLoader;
import net.minecraft.entity.player.PlayerEntity;
import net.minecraft.server.MinecraftServer;
import net.minecraft.server.network.ServerPlayerEntity;
import net.minecraft.entity.attribute.EntityAttributes;
import net.minecraft.world.GameMode;

/** MC owns damage/healing/death. The client mirrors a fresh server snapshot into OW. */
public final class SurvivalRuntime {
    public record Scope(UUID owner,long world,long source,long model,long hero,double maximum){}
    public record View(Scope scope,boolean enabled,boolean alive,float health,float maximum,long wall){}
    private static volatile Scope scope;private static long lease;
    private static boolean loaded;private static volatile boolean enabled;
    private static ServerPlayerEntity configured;private static Scope configuredScope;private static boolean configuredMode;
    private static long damageEvents,deaths,respawns,requests;private static double damageTaken;
    private static String error="",lastDamage="";
    public static volatile View view;
    public static volatile String status="{}";
    private SurvivalRuntime(){}
    private static Path config(){return FabricLoader.getInstance().getGameDir().resolve("config/owmc-survival.json");}
    public static boolean enabled(){return enabled;}
    public static boolean permitted(PlayerEntity p){return p!=null&&(p.isCreative()||enabled&&scope!=null&&scope.owner().equals(p.getUuid()));}
    private static void load(){
        if(loaded)return;loaded=true;enabled=false;
        try{if(Files.exists(config())){
            if(Files.size(config())>4096)throw new IllegalArgumentException("survival config size");
            var d=JsonParser.parseString(Files.readString(config())).getAsJsonObject();
            if(d.get("version").getAsInt()!=1||!d.get("enabled").getAsJsonPrimitive().isBoolean())throw new IllegalArgumentException("survival config schema");
            enabled=d.get("enabled").getAsBoolean();
        }}catch(Exception e){error=e.toString();}
    }
    public static void refresh(MinecraftServer server,Scope next,long wall){
        if(!server.isOnThread()||!server.isSingleplayer()||next.owner()==null||next.source()==0||next.model()==0||next.hero()==0
            ||!Double.isFinite(next.maximum())||next.maximum()<=0||next.maximum()>10000||Math.abs(System.currentTimeMillis()-wall)>250)return;
        var p=server.getPlayerManager().getPlayer(next.owner());
        if(p==null||NativeWorldIdentity.of(server,p.getWorld().getRegistryKey())!=next.world())return;
        load();scope=next;lease=wall;
    }
    public static String setEnabled(MinecraftServer server,UUID owner,boolean next){
        requests++;load();var p=server.getPlayerManager().getPlayer(owner);
        if(!server.isOnThread()||!server.isSingleplayer()||p==null||!p.isAlive()||scope==null||!scope.owner().equals(owner)
            ||System.currentTimeMillis()-lease>500)return "生存设置等待当前英雄血量连接";
        try{
            Files.createDirectories(config().getParent());var d=new JsonObject();d.addProperty("version",1);d.addProperty("enabled",next);
            var temporary=config().resolveSibling("owmc-survival.pending.json");Files.writeString(temporary,d.toString()+"\n");
            Files.move(temporary,config(),StandardCopyOption.REPLACE_EXISTING,StandardCopyOption.ATOMIC_MOVE);
            enabled=next;configured=null;error="";tick(server);return "";
        }catch(Exception e){error=e.toString();return "无法保存生存设置："+e.getMessage();}
    }
    public static void damage(ServerPlayerEntity p,net.minecraft.entity.damage.DamageSource source,float amount){
        if(scope!=null&&scope.owner().equals(p.getUuid())&&enabled&&amount>0){damageEvents++;damageTaken+=amount;lastDamage=source.getName();}
    }
    public static void died(ServerPlayerEntity p){if(scope!=null&&scope.owner().equals(p.getUuid())&&enabled)deaths++;}
    public static void tick(MinecraftServer server){
        load();var p=scope==null?null:server.getPlayerManager().getPlayer(scope.owner());long now=System.currentTimeMillis();
        if(p!=null&&NativeWorldIdentity.of(server,p.getWorld().getRegistryKey())==scope.world()){
            boolean fresh=now-lease<=500;
            if(p.isAlive()){
                if(configured!=p||!samePawn(configuredScope,scope)||configuredMode!=enabled){
                    boolean returned=configured!=null&&configured!=p&&samePawn(configuredScope,scope);
                    float ratio=p.getMaxHealth()>0?p.getHealth()/p.getMaxHealth():1;
                    p.changeGameMode(enabled?GameMode.SURVIVAL:GameMode.CREATIVE);
                    p.getAttributeInstance(EntityAttributes.GENERIC_MAX_HEALTH).setBaseValue(enabled?scope.maximum()*SurvivalHealthPlan.SCALE:20);
                    // A new native pawn or a vanilla respawn starts full. Opening
                    // menus/focus gaps/dimension changes never initialize again.
                    p.setHealth(configured==null||!samePawn(configuredScope,scope)||returned?p.getMaxHealth():Math.min(p.getMaxHealth(),ratio*p.getMaxHealth()));
                    if(returned)respawns++;
                    p.getAbilities().allowFlying=true;p.getAbilities().flying=false;p.fallDistance=0;
                    configured=p;configuredScope=scope;configuredMode=enabled;p.sendAbilitiesUpdate();
                }
                boolean invulnerable=!enabled||!fresh;
                if(p.getAbilities().invulnerable!=invulnerable){p.getAbilities().invulnerable=invulnerable;p.sendAbilitiesUpdate();}
            }
            view=new View(scope,enabled,p.isAlive(),p.getHealth(),p.getMaxHealth(),now);
        }else view=null;
        var o=new JsonObject();o.addProperty("enabled",enabled);o.addProperty("ready",p!=null&&now-lease<=500);o.addProperty("damageEvents",damageEvents);
        o.addProperty("damageTaken",damageTaken);o.addProperty("lastDamage",lastDamage);o.addProperty("deaths",deaths);o.addProperty("respawns",respawns);o.addProperty("requests",requests);o.addProperty("error",error);
        o.addProperty("deathPolicy","vanilla-minecraft-respawn-at-spawn");o.addProperty("config",config().toString());o.addProperty("wall",now);
        if(view!=null){o.addProperty("owner",scope.owner().toString());o.addProperty("world",scope.world());o.addProperty("source",scope.source());o.addProperty("model",scope.model());o.addProperty("hero",scope.hero());o.addProperty("health",view.health());o.addProperty("maximum",view.maximum());o.addProperty("alive",view.alive());o.addProperty("nativeMaximum",scope.maximum());o.addProperty("invulnerable",p.getAbilities().invulnerable);o.addProperty("creative",p.isCreative());}
        status=o.toString();
    }
    private static boolean samePawn(Scope a,Scope b){return a!=null&&b!=null&&a.owner().equals(b.owner())&&a.source()==b.source()&&a.model()==b.model()&&a.hero()==b.hero();}
    public static void close(){scope=configuredScope=null;configured=null;view=null;lease=0;loaded=false;}
}
