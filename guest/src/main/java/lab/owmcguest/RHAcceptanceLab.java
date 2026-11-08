package lab.owmcguest;

import com.google.gson.*;
import java.util.*;
import net.minecraft.block.*;
import net.minecraft.entity.*;
import net.minecraft.entity.attribute.EntityAttributes;
import net.minecraft.entity.mob.*;
import net.minecraft.entity.passive.*;
import net.minecraft.server.MinecraftServer;
import net.minecraft.server.network.ServerPlayerEntity;
import net.minecraft.server.world.ServerWorld;
import net.minecraft.util.math.*;

/** Opt-in disposable-world fixtures. Only ordinary targets/terrain/MC damage;
 * never native input, factory events, damage receipts, ability state or cooldowns. */
public final class RHAcceptanceLab {
    private static final Map<BlockPos,BlockState> blocks=new LinkedHashMap<>();
    private static final List<LivingEntity> entities=new ArrayList<>();
    private static final Map<BlockPos,BlockState> wallBaseline=new LinkedHashMap<>();
    private static ServerWorld world;private static ServerPlayerEntity player;private static LivingEntity target,npc,fallMob;
    private static String action="",error="";private static float fallPlayerBefore,fallNpcBefore,fallMobBefore;private static long requests;
    private static Boolean savedRegeneration;
    private static String fingerprint="";private static Vec3d savedTopFeet;
    public static volatile String status="{}";
    private RHAcceptanceLab(){}
    public static boolean enabled(){return Boolean.getBoolean("owmc.roadhogLab")&&System.getProperty("owmc.worldName","").startsWith("Overwatch Twilight Switch G Survival Lab RH ");}
    private static void set(BlockPos at,BlockState state){if(!world.isChunkLoaded(at))throw new IllegalArgumentException("fixture chunk unavailable");blocks.putIfAbsent(at,world.getBlockState(at));world.setBlockState(at,state);}
    private static Vec3d forward(){var f=player.getRotationVec(1).multiply(1,0,1);return f.lengthSquared()<1e-6?new Vec3d(0,0,-1):f.normalize();}
    private static void floor(){
        var base=player.getBlockPos().down();
        for(int x=-12;x<=12;x++)for(int z=-12;z<=12;z++){set(base.add(x,0,z),Blocks.STONE.getDefaultState());for(int y=1;y<=4;y++)set(base.add(x,y,z),Blocks.AIR.getDefaultState());}
    }
    private static LivingEntity spawn(String kind,Vec3d at){
        LivingEntity e=switch(kind){
            case "npc"->new HeroNpcEntity(HeroNpcEntity.TYPE,world);
            case "villager"->new VillagerEntity(EntityType.VILLAGER,world);
            case "cow"->new CowEntity(EntityType.COW,world);
            case "ravager"->new RavagerEntity(EntityType.RAVAGER,world);
            default->new HuskEntity(EntityType.HUSK,world);
        };
        if(e instanceof HeroNpcEntity hero)hero.configure(12,player.getUuid());
        else {e.getAttributeInstance(EntityAttributes.GENERIC_MAX_HEALTH).setBaseValue(200);e.setHealth(200);}
        if(e instanceof MobEntity mob){mob.setAiDisabled(true);mob.setPersistent();}
        e.setSilent(true);e.refreshPositionAndAngles(at.x,at.y,at.z,player.getYaw()+180,0);e.addCommandTag("owmc-rh-acceptance");
        if(!world.isSpaceEmpty(e,e.getBoundingBox())||!world.spawnEntity(e))throw new IllegalArgumentException("fixture target blocked");
        entities.add(e);return e;
    }
    public static void apply(MinecraftServer server,UUID owner,String requested){
        requests++;error="";action=requested;
        try{
            var p=server.getPlayerManager().getPlayer(owner);
            if(!enabled()||!server.isOnThread()||!server.isSingleplayer()||p==null)throw new IllegalArgumentException("isolated RH lab required");
            if(world!=null&&world!=p.getServerWorld())close();world=p.getServerWorld();player=p;
            String name=requested.substring(3);
            if(name.startsWith("target-")){
                for(var e:entities)e.discard();entities.clear();target=npc=fallMob=null;
                String[] parts=name.split("-");int distance=Integer.parseInt(parts[2]);if(distance<2||distance>20)throw new IllegalArgumentException("fixture range");
                floor();target=spawn(parts[1],p.getPos().add(forward().multiply(distance)));
            }else switch(name){
                case "health-one"->{if(target!=null)target.setHealth(1);}
                case "motion"->{if(target instanceof MobEntity mob){mob.setAiDisabled(false);mob.getAttributeInstance(EntityAttributes.GENERIC_MOVEMENT_SPEED).setBaseValue(0);}}
                case "measure-on"->MuzzlePresentation.measurementMask=true;
                case "measure-off"->MuzzlePresentation.measurementMask=false;
                case "pack-wall"->{
                    if(NativeTorbjornRuntime.packViews.isEmpty())throw new IllegalArgumentException("real landed pack required");
                    var at=NativeTorbjornRuntime.packViews.getFirst();var toward=p.getPos().subtract(at).multiply(1,0,1).normalize();
                    target=spawn("cow",at.add(toward.multiply(2.4)).add(0,.05,0));
                    var side=new Vec3d(-toward.z,0,toward.x);var center=at.add(toward.multiply(1.2));
                    for(int x=-2;x<=2;x++)for(int y=0;y<5;y++){var q=BlockPos.ofFloored(center.add(side.multiply(x)).add(0,y,0));wallBaseline.putIfAbsent(q,world.getBlockState(q));set(q,Blocks.STONE.getDefaultState());}
                }
                case "unwall"->{for(var e:wallBaseline.entrySet())world.setBlockState(e.getKey(),e.getValue());wallBaseline.clear();}
                case "pack-follow"->{
                    if(target==null||!target.isAlive()||NativeTorbjornRuntime.packViews.isEmpty())throw new IllegalArgumentException("existing recipient/real pack required");
                    var at=NativeTorbjornRuntime.packViews.getLast().add(1.5,.05,0);var delta=at.subtract(target.getPos());
                    if(!world.isSpaceEmpty(target,target.getBoundingBox().offset(delta)))throw new IllegalArgumentException("recipient follow position occupied");
                    target.requestTeleport(at.x,at.y,at.z);
                }
                case "persist-target"->{if(target==null||!target.isAlive())throw new IllegalArgumentException("real grown recipient required");target.addCommandTag("owmc-rh-growth-save");entities.remove(target);}
                case "read-persisted"->{
                    target=null;for(var e:world.iterateEntities())if(e instanceof LivingEntity living&&e.getCommandTags().contains("owmc-rh-growth-save")){if(target!=null)throw new IllegalArgumentException("duplicate persisted fixture");target=living;}
                    if(target==null)throw new IllegalArgumentException("saved growth entity absent");entities.add(target);target.removeCommandTag("owmc-rh-growth-save");
                }
                case "environment-kill"->{if(target!=null)target.damage(target.getDamageSources().genericKill(),1000);}
                case "survival-on"->{error=SurvivalRuntime.setEnabled(server,owner,true);if(savedRegeneration==null)savedRegeneration=world.getGameRules().getBoolean(net.minecraft.world.GameRules.NATURAL_REGENERATION);world.getGameRules().get(net.minecraft.world.GameRules.NATURAL_REGENERATION).set(false,server);}
                case "survival-off"->error=SurvivalRuntime.setEnabled(server,owner,false);
                case "hurt"->p.damage(p.getDamageSources().generic(),20);
                case "hit-four"->p.damage(p.getDamageSources().generic(),4);
                case "lethal"->p.damage(p.getDamageSources().genericKill(),1000);
                case "full-health"->p.setHealth(p.getMaxHealth());
                case "floor"->floor();
                case "home"->{p.teleport(world,p.getX(),96,p.getZ(),p.getYaw(),p.getPitch());p.setVelocity(Vec3d.ZERO);p.getAbilities().flying=false;p.sendAbilitiesUpdate();floor();}
                case "hash"->{
                    var digest=java.security.MessageDigest.getInstance("SHA-256");
                    for(var at:blocks.keySet())digest.update((at.toShortString()+"="+world.getBlockState(at).toString()+"\n").getBytes(java.nio.charset.StandardCharsets.UTF_8));
                    fingerprint=java.util.HexFormat.of().formatHex(digest.digest());
                }
                case "top"->{
                    if(savedTopFeet==null)savedTopFeet=p.getPos();p.teleport(world,p.getX(),world.getTopY()-12,p.getZ(),p.getYaw(),p.getPitch());p.setVelocity(Vec3d.ZERO);floor();
                }
                case "back"->{if(savedTopFeet!=null){var at=savedTopFeet;savedTopFeet=null;p.teleport(world,at.x,at.y,at.z,p.getYaw(),p.getPitch());p.setVelocity(Vec3d.ZERO);}}
                case "fall"->{
                    floor();fallPlayerBefore=p.getHealth();fallNpcBefore=fallMobBefore=200;
                    var at=p.getPos();npc=spawn("npc",at.add(5,20,0));fallNpcBefore=npc.getHealth();fallMob=spawn("husk",at.add(-5,20,0));fallMobBefore=fallMob.getHealth();
                    if(npc instanceof MobEntity mob)mob.setAiDisabled(false);
                    if(fallMob instanceof MobEntity mob){mob.setAiDisabled(false);mob.getAttributeInstance(EntityAttributes.GENERIC_MOVEMENT_SPEED).setBaseValue(0);}
                    p.getAbilities().flying=false;p.sendAbilitiesUpdate();p.requestTeleport(at.x,at.y+20,at.z);
                }
                case "wall","wall-two"->{
                    var f=forward();var right=new Vec3d(-f.z,0,f.x);var at=p.getPos().add(f.multiply(name.equals("wall")?1.25:2.25));
                    for(int x=-2;x<=2;x++)for(int y=0;y<4;y++)set(BlockPos.ofFloored(at.add(right.multiply(x)).add(0,y,0)),Blocks.STONE.getDefaultState());
                }
                case "grapple"->{
                    floor();var f=forward();var right=new Vec3d(-f.z,0,f.x);var at=p.getPos().add(f.multiply(10));
                    for(int x=-3;x<=3;x++)for(int y=0;y<8;y++)set(BlockPos.ofFloored(at.add(right.multiply(x)).add(0,y,0)),Blocks.STONE.getDefaultState());
                }
                case "terrain-flat","terrain-slab","terrain-stair","terrain-step","terrain-steep","terrain-low"->{
                    floor();var f=forward();var right=new Vec3d(-f.z,0,f.x);var at=p.getPos().add(f.multiply(4));
                    for(int x=-6;x<=6;x++)for(int z=-2;z<=2;z++){
                        var point=BlockPos.ofFloored(at.add(right.multiply(x)).add(f.multiply(z)));var state=Blocks.STONE.getDefaultState();
                        if(name.endsWith("slab"))state=Blocks.STONE_SLAB.getDefaultState();
                        if(name.endsWith("stair"))state=Blocks.STONE_STAIRS.getDefaultState();
                        if(name.endsWith("step")&&x>0)point=point.up();
                        if(name.endsWith("steep")&&x>0)point=point.up(3);
                        set(point.down(),state);if(name.endsWith("low"))set(point.up(3),Blocks.STONE.getDefaultState());
                    }
                }
                case "clear"->{close();}
                default->throw new IllegalArgumentException("unknown RH fixture");
            }
        }catch(Exception failure){error=failure.toString();}
        publish();
    }
    public static void tick(MinecraftServer server){if(world!=null)publish();}
    private static void add(JsonObject out,String name,LivingEntity e){
        if(e==null)return;var o=new JsonObject();o.addProperty("id",e.getId());o.addProperty("health",e.getHealth());o.addProperty("alive",e.isAlive());o.addProperty("x",e.getX());o.addProperty("y",e.getY());o.addProperty("z",e.getZ());o.addProperty("onGround",e.isOnGround());o.addProperty("scale",e.getScale());o.addProperty("width",e.getWidth());o.addProperty("height",e.getHeight());out.add(name,o);
    }
    private static void publish(){
        var o=new JsonObject();o.addProperty("action",action);o.addProperty("error",error);o.addProperty("requests",requests);o.addProperty("blocks",blocks.size());o.addProperty("wall",System.currentTimeMillis());if(target!=null)o.addProperty("targetUuid",target.getUuidAsString());
        add(o,"target",target);add(o,"npc",npc);add(o,"fallMob",fallMob);add(o,"player",player);
        o.addProperty("fallPlayerBefore",fallPlayerBefore);o.addProperty("fallNpcBefore",fallNpcBefore);o.addProperty("fallMobBefore",fallMobBefore);o.addProperty("blockFingerprint",fingerprint);status=o.toString();
    }
    public static void close(){
        MuzzlePresentation.measurementMask=false;
        if(player!=null&&world!=null&&savedTopFeet!=null){var at=savedTopFeet;savedTopFeet=null;player.teleport(world,at.x,at.y,at.z,player.getYaw(),player.getPitch());player.setVelocity(Vec3d.ZERO);}
        for(var e:entities)e.discard();entities.clear();target=npc=fallMob=null;wallBaseline.clear();
        if(world!=null){for(var entry:blocks.entrySet())world.setBlockState(entry.getKey(),entry.getValue());if(savedRegeneration!=null)world.getGameRules().get(net.minecraft.world.GameRules.NATURAL_REGENERATION).set(savedRegeneration,world.getServer());}savedRegeneration=null;blocks.clear();world=null;player=null;publish();
    }
}
