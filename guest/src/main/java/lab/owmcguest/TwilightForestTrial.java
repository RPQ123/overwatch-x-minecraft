package lab.owmcguest;

import com.google.gson.JsonArray;
import com.google.gson.JsonObject;
import java.util.UUID;
import net.fabricmc.loader.api.FabricLoader;
import net.minecraft.block.Blocks;
import net.minecraft.entity.LivingEntity;
import net.minecraft.registry.Registries;
import net.minecraft.server.MinecraftServer;
import net.minecraft.util.Identifier;
import net.minecraft.util.math.BlockPos;
import net.minecraft.util.math.Vec3d;
import net.minecraft.world.World;

/** Optional real-mod trial, confined to an explicitly selected separate save. */
public final class TwilightForestTrial {
    public static volatile String status="{}";
    private static String error="";
    private static BlockPos portal;
    private static long builds;
    private static net.minecraft.entity.mob.MobEntity probe;
    private static net.minecraft.server.world.ServerWorld probeWorld;
    private static UUID probeOwner;
    private static boolean savedGriefing;
    private static int probeDelay;
    private static JsonObject probeResult;
    private static boolean nativeProbe;
    private static int nativeTicks;
    private static JsonArray nativeReceipts=new JsonArray();
    public static boolean ownsProbe(net.minecraft.entity.Entity entity){return entity==probe;}
    private static boolean allowed(){return Boolean.getBoolean("owmc.twilightTrial")
        &&System.getProperty("owmc.worldName","").startsWith("Overwatch Twilight ");}
    public static void buildPortal(MinecraftServer server,UUID owner,Vec3d forward){
        buildPortal(server,owner,forward,false);
    }
    public static void buildPlayerPortal(MinecraftServer server,UUID owner,Vec3d forward){
        buildPortal(server,owner,forward,true);
    }
    private static void buildPortal(MinecraftServer server,UUID owner,Vec3d forward,boolean explicitPlayerRequest){
        var p=server.getPlayerManager().getPlayer(owner);var id=Identifier.of("twilightforest","twilight_portal");
        if((!explicitPlayerRequest&&!allowed())||p==null||!p.isAlive()||!SurvivalRuntime.permitted(p)||p.getWorld().getRegistryKey()!=World.OVERWORLD){error="Portal builder requires a creative Overworld player";report(server);return;}
        if(!Registries.BLOCK.containsId(id)){error="Real Twilight Forest portal block is not loaded";report(server);return;}
        var direction=new Vec3d(forward.x,0,forward.z).normalize();
        if(direction.lengthSquared()<.5){error="Look horizontally before building the trial portal";report(server);return;}
        var w=p.getServerWorld();var b=BlockPos.ofFloored(p.getPos().add(direction.multiply(5))).down();
        if(b.getY()-1<w.getBottomY()||b.getY()+4>=w.getTopY()){error="Portal is outside world height";report(server);return;}
        for(int x=-1;x<=2;x++)for(int z=-1;z<=2;z++){
            var at=b.add(x,0,z);
            if(!w.isChunkLoaded(at)||!w.getWorldBorder().contains(at)){error="Portal needs loaded terrain inside the border";report(server);return;}
        }
        // Finish every support/edge/flower before placing fluid. Building active
        // portal blocks beside an unfinished edge made the mod replace them with water.
        for(int x=-1;x<=2;x++)for(int z=-1;z<=2;z++){
            var at=b.add(x,0,z);w.setBlockState(at.down(),Blocks.DIRT.getDefaultState());
            for(int up=1;up<=3;up++)w.setBlockState(at.up(up),Blocks.AIR.getDefaultState());
            boolean inner=x>=0&&x<=1&&z>=0&&z<=1;
            w.setBlockState(at,inner?Blocks.AIR.getDefaultState():Blocks.GRASS_BLOCK.getDefaultState());
            if(!inner)w.setBlockState(at.up(),Blocks.POPPY.getDefaultState());
        }
        for(int x=0;x<2;x++)for(int z=0;z<2;z++)w.setBlockState(b.add(x,0,z),Blocks.WATER.getDefaultState());
        var catalyst=new net.minecraft.entity.ItemEntity(w,b.getX()+1,b.getY()+.25,b.getZ()+1,new net.minecraft.item.ItemStack(net.minecraft.item.Items.DIAMOND));
        catalyst.setVelocity(Vec3d.ZERO);w.spawnEntity(catalyst);
        portal=b;builds++;error="";
        try {
            // Invoke the installed mod's own validated activation, consuming the
            // real diamond and producing its real lightning/portal/travel rules.
            var block=Registries.BLOCK.get(id);var method=java.util.Arrays.stream(block.getClass().getMethods())
                .filter(m->m.getName().equals("tryToCreatePortal")&&m.getParameterCount()==4)
                .filter(m->{var t=m.getParameterTypes();return t[0].isInstance(w)&&t[1].isInstance(b)&&t[2].isInstance(catalyst)&&t[3].isInstance(p);}).findFirst();
            if(method.isPresent()&&!Boolean.TRUE.equals(method.get().invoke(block,w,b,catalyst,p)))error="The real mod refused portal activation; diamond left in the completed pool";
            // If this mod release has no public method, its ordinary nearby
            // catalyst scanner still sees the real diamond in the actual water.
        }catch(ReflectiveOperationException failure){error="Portal activation: "+failure.getClass().getSimpleName();}
        report(server);
    }
    /** A real mod/server fixture; this does not stand in for a native firing test. */
    public static void startProbe(MinecraftServer server,UUID owner,boolean hydra){
        startProbe(server,owner,hydra,null);
    }
    /** Holds a real Naga for native firing. Never applies fixture damage. */
    public static void startNativeProbe(MinecraftServer server,UUID owner,Vec3d direction){
        startProbe(server,owner,false,direction);
    }
    private static void startProbe(MinecraftServer server,UUID owner,boolean hydra,Vec3d direction){
        cleanupProbe();probeResult=null;error="";var p=server.getPlayerManager().getPlayer(owner);
        if(!allowed()||p==null||!p.isCreative()||!p.getWorld().getRegistryKey().getValue().toString().equals("twilightforest:twilight_forest")){error="Multipart fixture requires the separate creative Twilight trial";return;}
        var id=Identifier.of("twilightforest",hydra?"hydra":"naga");
        if(!Registries.ENTITY_TYPE.containsId(id)){error="Original mod entity is not registered";return;}
        var w=p.getServerWorld();var at=p.getBlockPos().up(12).south(6);
        boolean live=direction!=null;
        if(live){
            if(!p.getAbilities().flying||!Double.isFinite(direction.lengthSquared())||direction.lengthSquared()<.5||Math.abs(direction.normalize().y)>.15){error="Native boss fixture needs creative flight and horizontal aim";return;}
            at=BlockPos.ofFloored(p.getEyePos().add(direction.normalize().multiply(10))).down();
        }
        var min=live?at.add(-26,-6,-26):at.add(-4,0,-4);var max=live?at.add(26,6,26):at.add(4,6,4);
        for(var block:BlockPos.iterate(min,max))if(block.getY()<w.getBottomY()||block.getY()>=w.getTopY()||!w.getWorldBorder().contains(block)||!w.isChunkLoaded(block)||!w.getBlockState(block).isAir()){error="Multipart fixture requires loaded empty air; original terrain preserved";return;}
        var e=Registries.ENTITY_TYPE.get(id).create(w);
        if(!(e instanceof net.minecraft.entity.mob.MobEntity mob)){error="Unexpected boss entity type";return;}
        float facing=live?(float)Math.toDegrees(Math.atan2(-direction.x,direction.z))+90:0;
        mob.refreshPositionAndAngles(at.getX()+.5,at.getY(),at.getZ()+.5,facing,0);mob.setHeadYaw(facing);mob.setBodyYaw(facing);
        // Live firing keeps original AI/boss-bar updates. Only the short direct
        // server-damage fixture pauses AI; no custom bar/health writes here.
        mob.setAiDisabled(!live);mob.setNoGravity(true);
        mob.addCommandTag("owmc-multipart-probe");probeWorld=w;probe=mob;probeOwner=owner;
        savedGriefing=w.getGameRules().getBoolean(net.minecraft.world.GameRules.DO_MOB_GRIEFING);
        w.getGameRules().get(net.minecraft.world.GameRules.DO_MOB_GRIEFING).set(false,server);
        if(!w.spawnEntity(mob)){cleanupProbe();error="Boss fixture spawn refused";return;}
        nativeProbe=live;nativeTicks=1200;nativeReceipts=new JsonArray();probeDelay=10;probeResult=new JsonObject();probeResult.addProperty("type",id.toString());probeResult.addProperty("pending",true);
        probeResult.addProperty("kind",live?"native-fire-only":"server-damage-fixture");probeResult.addProperty("before",mob.getHealth());probeResult.addProperty("aiDisabled",mob.isAiDisabled());
    }
    /** Receipts only while the opted-in fixture is live. No new damage path. */
    public static void damageReceipt(net.minecraft.server.world.ServerWorld world,net.minecraft.entity.Entity entity,
            net.minecraft.server.network.ServerPlayerEntity player,double amount,net.minecraft.entity.damage.DamageSource source,boolean applied,double loss){
        if(!nativeProbe||probe==null||world!=probeWorld||!player.getUuid().equals(probeOwner)||NativeDamageTargets.owner(entity)!=probe||nativeReceipts.size()>=32)return;
        var row=new JsonObject();row.addProperty("entityId",entity.getId());row.addProperty("part",entity.getClass().getSimpleName());
        row.addProperty("ownerId",probe.getId());row.addProperty("incoming",amount);row.addProperty("explosion",source.isIn(net.minecraft.registry.tag.DamageTypeTags.IS_EXPLOSION));
        row.addProperty("projectile",source.isIn(net.minecraft.registry.tag.DamageTypeTags.IS_PROJECTILE));
        row.addProperty("applied",applied);row.addProperty("healthLost",loss);nativeReceipts.add(row);
    }
    private static void nativeSnapshot(){
        if(!nativeProbe||probe==null)return;
        probeResult.addProperty("health",probe.getHealth());probeResult.addProperty("ownerId",probe.getId());
        var parts=new JsonArray();
        for(var e:OptionalMultipartTargets.parts(probeWorld).values())if(NativeDamageTargets.owner(e)==probe){
            var row=new JsonObject();var b=e.getBoundingBox();var c=b.getCenter();
            row.addProperty("id",e.getId());row.addProperty("part",e.getClass().getSimpleName());
            row.addProperty("x",c.x);row.addProperty("y",c.y);row.addProperty("z",c.z);
            row.addProperty("width",b.getLengthX());row.addProperty("height",b.getLengthY());row.addProperty("depth",b.getLengthZ());parts.add(row);
        }
        probeResult.add("targets",parts);probeResult.addProperty("pending",false);
        probeResult.add("damageReceipts",nativeReceipts.deepCopy());
    }
    public static void stopNativeProbe(MinecraftServer server){
        if(nativeProbe){nativeSnapshot();probeResult.addProperty("ended","explicit-cleanup");cleanupProbe();}report(server);
    }
    private static void finishProbe(MinecraftServer server){
        try {
            var p=server.getPlayerManager().getPlayer(probeOwner);
            if(p==null||p.getServerWorld()!=probeWorld)throw new IllegalStateException("Fixture owner changed dimension");
            var parts=OptionalMultipartTargets.parts(probeWorld).values().stream().filter(e->NativeDamageTargets.owner(e)==probe).toList();
            var part=parts.stream().filter(e->e.getClass().getSimpleName().equals("HydraHead")).findFirst().orElse(parts.isEmpty()?null:parts.getFirst());
            if(part==null)throw new IllegalStateException("Original multipart array is unavailable");
            var bounds=part.getBoundingBox().expand(.01);boolean admitted=NativeDamageTargets.in(probeWorld,p,bounds).contains(part);
            boolean resolved=NativeDamageTargets.resolve(probeWorld,part.getId())==part;
            boolean hidden=!OptionalMultipartTargets.hiddenRoot(probe)||!NativeDamageTargets.in(probeWorld,p,probe.getBoundingBox()).contains(probe);
            float before=probe.getHealth();var blast=NativeDamageTargets.explosionDamage(probeWorld,part,p,40);float afterBlast=probe.getHealth();
            var result=NativeDamageTargets.projectileDamage(probeWorld,part,p,40);
            probeResult.addProperty("pending",false);probeResult.addProperty("parts",parts.size());probeResult.addProperty("part",part.getClass().getSimpleName());
            probeResult.addProperty("admitted",admitted);probeResult.addProperty("resolved",resolved);probeResult.addProperty("rootHandled",hidden);
            probeResult.addProperty("before",before);probeResult.addProperty("after",probe.getHealth());probeResult.addProperty("healthLost",result.healthLost());
            probeResult.addProperty("afterExplosion",afterBlast);probeResult.addProperty("explosionHealthLost",blast.healthLost());
            boolean immunity=probe.getType()==Registries.ENTITY_TYPE.get(Identifier.of("twilightforest","naga"))?blast.healthLost()==0&&afterBlast==before:blast.healthLost()>0;
            probeResult.addProperty("explosionSemanticsPassed",immunity);
            probeResult.addProperty("passed",admitted&&resolved&&hidden&&result.healthLost()>0&&immunity);
        }catch(Exception failure){error=failure.toString();probeResult.addProperty("pending",false);probeResult.addProperty("passed",false);probeResult.addProperty("error",error);}
        finally{cleanupProbe();}
    }
    private static void cleanupProbe(){
        if(probe!=null){
            for(var part:OptionalMultipartTargets.parts(probeWorld).values())if(NativeDamageTargets.owner(part)==probe)part.discard();
            probe.discard();probe=null;
        }
        if(probeWorld!=null){probeWorld.getGameRules().get(net.minecraft.world.GameRules.DO_MOB_GRIEFING).set(savedGriefing,probeWorld.getServer());probeWorld=null;}
        probeOwner=null;probeDelay=0;nativeProbe=false;nativeTicks=0;OptionalMultipartTargets.reset();
    }
    public static void tick(MinecraftServer server){
        if(probe!=null){
            if(nativeProbe){
                var p=server.getPlayerManager().getPlayer(probeOwner);
                if(p==null||p.getServerWorld()!=probeWorld||!p.isAlive()||!p.isCreative()||!p.getAbilities().flying||--nativeTicks<=0){
                    nativeSnapshot();probeResult.addProperty("ended","owner-changed-or-deadline");cleanupProbe();
                }else if(server.getTicks()%2==0)nativeSnapshot();
            }else if(--probeDelay<=0)finishProbe(server);
        }
        if(server.getTicks()%10==0)report(server);
    }
    private static void report(MinecraftServer server){
        var out=new JsonObject();out.addProperty("enabled",allowed());out.addProperty("loaded",FabricLoader.getInstance().isModLoaded("twilightforest"));
        FabricLoader.getInstance().getModContainer("twilightforest").ifPresent(m->out.addProperty("version",m.getMetadata().getVersion().getFriendlyString()));
        out.addProperty("error",error);out.addProperty("portalBuilds",builds);
        out.addProperty("probeActive",probe!=null);
        if(probeResult!=null)out.add("multipartProbe",probeResult);
        if(portal!=null){out.addProperty("portalX",portal.getX());out.addProperty("portalY",portal.getY());out.addProperty("portalZ",portal.getZ());
            var w=server.getOverworld();int active=0;var types=new JsonArray();
            for(int x=0;x<2;x++)for(int z=0;z<2;z++){var state=w.getBlockState(portal.add(x,0,z));var type=Registries.BLOCK.getId(state.getBlock());types.add(type.toString());if(type.equals(Identifier.of("twilightforest","twilight_portal")))active++;}
            out.addProperty("portalActiveBlocks",active);out.addProperty("portalActive",active==4);out.add("portalBlocks",types);
        }
        var dimensions=new JsonArray();for(var w:server.getWorlds())dimensions.add(w.getRegistryKey().getValue().toString());out.add("dimensions",dimensions);
        var p=server.getPlayerManager().getPlayerList().stream().findFirst().orElse(null);
        if(p!=null){
            out.addProperty("mobGriefing",p.getServerWorld().getGameRules().getBoolean(net.minecraft.world.GameRules.DO_MOB_GRIEFING));
            out.addProperty("dimension",p.getWorld().getRegistryKey().getValue().toString());
            out.addProperty("biome",p.getWorld().getBiome(p.getBlockPos()).getKey().map(k->k.getValue().toString()).orElse("unknown"));
            var entities=new JsonArray();
            if(allowed())for(var e:p.getServerWorld().getEntitiesByClass(LivingEntity.class,p.getBoundingBox().expand(24),e->e!=p&&e.isAlive())){
                if(entities.size()>=32)break;var row=new JsonObject();row.addProperty("id",e.getId());row.addProperty("type",Registries.ENTITY_TYPE.getId(e.getType()).toString());
                row.addProperty("health",e.getHealth());row.addProperty("x",e.getX());row.addProperty("y",e.getY());row.addProperty("z",e.getZ());entities.add(row);
            }
            out.add("nearby",entities);
        }
        status=out.toString();
    }
    public static void close(){cleanupProbe();portal=null;builds=0;error="";status="{}";}
}
