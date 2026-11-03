package lab.owmcguest;

import com.mojang.blaze3d.systems.RenderSystem;
import com.sun.net.httpserver.HttpServer;
import java.net.InetSocketAddress;
import java.nio.ByteBuffer;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.util.concurrent.Executors;
import net.fabricmc.api.ClientModInitializer;
import net.fabricmc.fabric.api.client.event.lifecycle.v1.ClientTickEvents;
import net.fabricmc.fabric.api.client.event.lifecycle.v1.ClientLifecycleEvents;
import net.fabricmc.fabric.api.client.rendering.v1.WorldRenderEvents;
import net.fabricmc.fabric.api.client.rendering.v1.WorldRenderContext;
import net.minecraft.client.MinecraftClient;
import net.minecraft.world.level.LevelInfo;
import net.minecraft.world.GameMode;
import net.minecraft.world.Difficulty;
import net.minecraft.world.GameRules;
import net.minecraft.resource.DataConfiguration;
import net.minecraft.world.gen.GeneratorOptions;
import net.minecraft.world.gen.WorldPresets;
import net.minecraft.registry.RegistryKeys;
import org.lwjgl.glfw.GLFW;
import org.lwjgl.opengl.GL11;
import org.lwjgl.opengl.GL15;
import org.lwjgl.opengl.GL21;
import org.lwjgl.opengl.GL30;
import org.lwjgl.opengl.GL32;

/** Actual vanilla world color/depth at WorldRenderer return, before MC hands/HUD.
 * No OW process, hook, synthetic OS input, patch mesh, or host collision is used. */
public final class WorldFrameExporter implements ClientModInitializer {
    private static final class Slot {int pbo,capacity;long fence;WorldFrameMapping.Capture pose;}
    private final Slot[] ring={new Slot(),new Slot(),new Slot()};
    private volatile WorldFrameMapping mapping;
    private HttpServer api;
    private boolean started,poseSceneStarted,daylightStarted,survivalSpawnChecked;
    private volatile boolean hidden,failed,capturePaused,comparisonVisible;
    private volatile long captured,skipped,restorations,sourceGeneration;
    private volatile String error="";
    private volatile String playerStatus="null";
    private final boolean survival=Boolean.getBoolean("owmc.survivalWorld");
    private final boolean creative=Boolean.getBoolean("owmc.creativeWorld");
    private boolean creativeConfigured,respawnRequested;
    private String reloadWorld;
    private String startupScreen="";
    private boolean startupWorldJoined;
    private long lastCapture;
    private final int captureFps=Math.max(30,Math.min(360,Integer.getInteger("owmc.captureFps",60)));
    // The live replacement shader consumes only color. Keep real depth opt-in
    // for depth-compositing labs rather than resolving it every live frame.
    private final boolean exportDepth=Boolean.getBoolean("owmc.exportDepth");
    private final long capturePeriod=1_000_000_000L/captureFps;
    private volatile int sourceWidth,sourceHeight;
    private long lastRender;
    private final FrameTimings renderIntervals=new FrameTimings(),captureTime=new FrameTimings(),combatTime=new FrameTimings(),dashTime=new FrameTimings();
    private final NativeCombatFeed combat=new NativeCombatFeed();
    private final DeadeyeExportGrade deadeyeGrade=new DeadeyeExportGrade();
    @Override public void onInitializeClient() {
        if(!Boolean.getBoolean("owmc.frameExport")) return;
        System.out.println("[OWMCStartup] client_initialized");
        DeadeyeBloodParticle.register();
        net.fabricmc.fabric.api.client.networking.v1.ClientPlayConnectionEvents.DISCONNECT.register((handler,client)->{
            NativeSessionGuard.disconnected();creativeConfigured=false;respawnRequested=false;
        });
        ClientTickEvents.END_CLIENT_TICK.register(client->{
            if(client.world!=null&&!StartupCompilerBudget.restored())StartupCompilerBudget.restore();
            if(!startupWorldJoined&&client.player==null) {
                String screen=client.currentScreen==null?"none":client.currentScreen.getClass().getName();
                if(!screen.equals(startupScreen)) {
                    startupScreen=screen;System.out.println("[OWMCStartup] screen="+screen+" title="+(client.currentScreen==null?"":client.currentScreen.getTitle().getString()));
                }
            }
            if(client.options.getParticles().getValue()!=net.minecraft.client.option.ParticlesMode.ALL)
                client.options.getParticles().setValue(net.minecraft.client.option.ParticlesMode.ALL);
            if(client.player!=null)startupWorldJoined=true;
            TwilightTrialStartup.tick(client,started&&!startupWorldJoined);
            if(reloadWorld!=null&&client.player==null&&client.world==null&&client.getServer()==null&&client.getOverlay()==null){
                var name=reloadWorld;reloadWorld=null;client.createIntegratedServerLoader().start(name,()->{});
            }
            if(!started&&client.getOverlay()==null) {
                // Native camera owns presentation motion; extra MC walk bob
                // is absent from the paired camera metadata and must be off.
                client.options.getBobView().setValue(false);
                // This process supplies offscreen pixels. Waiting for its own
                // display swap interval serializes two games on one GPU.
                client.options.getEnableVsync().setValue(false);
                client.options.getViewDistance().setValue(Math.max(8,Math.min(32,Integer.getInteger("owmc.renderDistance",16))));
                // Vanilla accepts at most 260 (its unlimited value). An invalid
                // 360 silently resets the option to 120 rather than raising it.
                client.options.getMaxFps().setValue(Math.min(260,captureFps));client.options.getGamma().setValue(1.0);
                System.out.println("[OWMCStartup] world_load_requested");
                started=true;startWorld(client);
            }
            if(creative&&!SurvivalRuntime.enabled()&&client.player!=null&&client.getServer()!=null) {
                if(!client.player.isAlive()&&!respawnRequested){respawnRequested=true;client.player.requestRespawn();client.setScreen(null);}
                if(client.player.isAlive()&&!creativeConfigured){creativeConfigured=true;var id=client.player.getUuid();client.getServer().execute(()->{
                    var p=client.getServer().getPlayerManager().getPlayer(id);if(p!=null){p.changeGameMode(GameMode.CREATIVE);p.getAbilities().flying=false;p.getAbilities().invulnerable=true;p.sendAbilitiesUpdate();}
                });}
            }
            if(survival&&!survivalSpawnChecked&&client.player!=null&&client.getServer()!=null) {
                survivalSpawnChecked=true;var marker=client.runDirectory.toPath().resolve("saves").resolve(worldName()).resolve("owmc-ground-spawn-v1");
                if(worldName().equals("Overwatch Survival World")&&!Files.exists(marker)) {var server=client.getServer();var id=client.player.getUuid();server.execute(()->{
                    var p=server.getPlayerManager().getPlayer(id);if(p==null)return;var world=p.getServerWorld();var origin=p.getBlockPos();
                    net.minecraft.util.math.BlockPos landing=null;
                    search:for(int radius=0;radius<=32;radius+=2)for(int dx=-radius;dx<=radius;dx+=2)for(int dz=-radius;dz<=radius;dz+=2) {
                        if(Math.max(Math.abs(dx),Math.abs(dz))!=radius)continue;
                        var at=world.getTopPosition(net.minecraft.world.Heightmap.Type.MOTION_BLOCKING_NO_LEAVES,origin.add(dx,0,dz));var below=world.getBlockState(at.down());
                        if(below.isOf(net.minecraft.block.Blocks.GRASS_BLOCK)&&world.getBlockState(at).isAir()&&world.getBlockState(at.up()).isAir()&&world.getBlockState(at.up(2)).isAir()) {landing=at;break search;}
                    }
                    if(landing!=null) {p.requestTeleport(landing.getX()+.5,landing.getY(),landing.getZ()+.5);p.getAbilities().flying=false;p.sendAbilitiesUpdate();
                        try {Files.writeString(marker,landing.toShortString());}catch(java.io.IOException e) {System.err.println("[OWMCFrames] Ground-spawn marker: "+e);}
                        System.out.println("[OWMCFrames] Natural survival ground spawn: "+landing);
                    } else System.err.println("[OWMCFrames] No open grass within 32 blocks; keeping vanilla spawn");
                });}
            }
            if(client.player!=null&&client.world!=null) {
                PortalMenu.tick(client);TwilightBossMenu.tick(client);
                var p=client.player;var position=p.getBlockPos();var ground=position.down();
                playerStatus="{\"x\":"+p.getX()+",\"feetY\":"+p.getY()+",\"eyeY\":"+p.getEyeY()+",\"z\":"+p.getZ()+",\"onGround\":"+p.isOnGround()+",\"velocityY\":"+p.getVelocity().y+",\"health\":"+p.getHealth()+",\"alive\":"+p.isAlive()+",\"invulnerable\":"+p.getAbilities().invulnerable+",\"cameraBobbing\":"+client.options.getBobView().getValue()+",\"capturePaused\":"+capturePaused+",\"screen\":"+new com.google.gson.Gson().toJson(client.currentScreen==null?"none":client.currentScreen.getClass().getSimpleName())+",\"flying\":"+p.getAbilities().flying+",\"allowFlying\":"+p.getAbilities().allowFlying+",\"survival\":"+(client.interactionManager!=null&&client.interactionManager.getCurrentGameMode()==GameMode.SURVIVAL)+",\"groundBlock\":"+new com.google.gson.Gson().toJson(net.minecraft.registry.Registries.BLOCK.getId(client.world.getBlockState(ground).getBlock()).toString())+"}";
                if(mapping!=null){
                    NativeLocomotionController.INSTANCE.tick(client);
                    var server=client.getServer();var pose=HostPoseReader.INSTANCE.latest();
                    long world=server==null||client.world==null?0:NativeWorldIdentity.of(server,client.world.getRegistryKey());
                    long hostGeneration=pose==null?0:pose.generation();
                    NativePulseController.INSTANCE.prime(client,pose,world,
                        NativeLocomotionController.INSTANCE.hero(),NativeLocomotionController.INSTANCE.modelId());
                    boolean transition=NativeSessionGuard.observe(client,world,NativeLocomotionController.INSTANCE.hero(),NativeLocomotionController.INSTANCE.modelId(),hostGeneration,pose!=null&&pose.inputActive());
                    if(transition&&server!=null)server.execute(NativeSessionGuard::resetServerState);
                    mapping.publishBody(client);
                    if(!transition){
                        long t=System.nanoTime();combat.tick(client,mapping.generation());combatTime.add(System.nanoTime()-t);
                        t=System.nanoTime();NativeDashController.INSTANCE.tick(client);dashTime.add(System.nanoTime()-t);
                        NativeUltimateController.INSTANCE.tick(client);NativeChargeController.INSTANCE.tick(client);NativeMeleeController.INSTANCE.tick(client);NativeDeflectController.INSTANCE.tick(client);NativeSustainController.INSTANCE.tick(client);NativeInfraSightController.INSTANCE.tick(client);NativeBioticController.INSTANCE.tick(client);NativePulseController.INSTANCE.tick(client);NativeRecallController.INSTANCE.tick(client);NativeReaperController.INSTANCE.tick(client);NativeWraithController.INSTANCE.tick(client);NativeShadowController.INSTANCE.tick(client);NativeGrappleController.INSTANCE.tick(client);NativeMeiSkillController.INSTANCE.tick(client);NativeJunkratController.INSTANCE.tick(client);NativeHanzoSkillController.INSTANCE.tick(client);NativeTorbjornController.INSTANCE.tick(client);HeroClientModules.tick(client);NativePortalController.INSTANCE.tick(client);NativeUtilityController.INSTANCE.tick(client);NativeDeadeyeController.INSTANCE.tick(client);EarlyChineseVoices.INSTANCE.tick(client);PharahBarrageSound.INSTANCE.tick(client);BioticFieldSound.INSTANCE.tick(client);CombatFeedbackSound.INSTANCE.tick(client);
                    }
                }
                if(mapping!=null){NativeRollController.INSTANCE.tick(client);HanzoSonicReveal.tick(client);}
            } else playerStatus="null";
            if(Boolean.getBoolean("owmc.daylightLab")&&!daylightStarted&&client.player!=null&&client.getServer()!=null) {
                daylightStarted=true;var server=client.getServer();server.execute(()->{
                    server.getOverworld().setTimeOfDay(6000);server.getOverworld().setWeather(6000,0,false,false);
                });
            }
            if(Boolean.getBoolean("owmc.poseTest")&&!poseSceneStarted&&client.player!=null&&client.getServer()!=null) {
                poseSceneStarted=true;var id=client.player.getUuid();var server=client.getServer();
                server.execute(()->{
                    var world=server.getOverworld();world.setTimeOfDay(6000);world.setWeather(0,6000,false,false);
                    for(int i=-2;i<=2;i++) for(int y=-60;y<=-55;y++) {
                        world.setBlockState(new net.minecraft.util.math.BlockPos(8,y,i),net.minecraft.block.Blocks.GOLD_BLOCK.getDefaultState());
                        world.setBlockState(new net.minecraft.util.math.BlockPos(-8,y,i),net.minecraft.block.Blocks.REDSTONE_BLOCK.getDefaultState());
                        world.setBlockState(new net.minecraft.util.math.BlockPos(i,y,8),net.minecraft.block.Blocks.BLUE_WOOL.getDefaultState());
                        world.setBlockState(new net.minecraft.util.math.BlockPos(i,y,-8),net.minecraft.block.Blocks.LIME_WOOL.getDefaultState());
                    }
                    var player=server.getPlayerManager().getPlayer(id);if(player!=null) player.requestTeleport(.5,-60,.5);
                });
            }
            if(Boolean.getBoolean("owmc.startHidden")) {
                BackgroundWindowVisibility.enforce(client.getWindow().getHandle());hidden=BackgroundWindowVisibility.hidden();
            } else if(!hidden&&!comparisonVisible&&client.world!=null&&mapping!=null&&mapping.published>0&&Boolean.getBoolean("owmc.backgroundExport")) {GLFW.glfwHideWindow(client.getWindow().getHandle());hidden=true;}
            HeroVoiceEvents.INSTANCE.tick(client); // 语音挂接：复用本tick已更新的controller/runtime回执。
        });
        WorldRenderEvents.START.register(render->NativeUltimateController.INSTANCE.presentSword(MinecraftClient.getInstance()));
        WorldRenderEvents.END.register(render->{
            // Vanilla also composites its real outline framebuffer later in
            // GameRenderer.render. Keep the same final capture boundary for
            // both renderer configurations; source hands are scoped out there.
            pendingRender=render;
        });
        instance=this;
        VanillaBossOverlay.register();
        OriginalWorldRenderer.register();PharahRocketRenderer.register();VenomMineRenderer.register();HeroClientModules.registerRender();JunkratRenderer.register();HanzoDragonRenderer.register();HanzoArrowRenderer.register();PharahBarrageRenderer.register();MccreeEffectsRenderer.register();PharahConcussiveRenderer.register();BioticFieldRenderer.register();PulseBombRenderer.register();SoulGlobeRenderer.register();HelixRocketRenderer.register();BastionTankRenderer.register();
        ClientLifecycleEvents.CLIENT_STOPPING.register(client->close());
        try {
            api=HttpServer.create(new InetSocketAddress("127.0.0.1",32133),4);
            api.setExecutor(Executors.newSingleThreadExecutor(r->{Thread t=new Thread(r,"owmc-frame-status");t.setDaemon(true);return t;}));
            api.createContext("/",exchange->{
                int code=404;String result="{\"error\":\"route\"}";
                if(exchange.getRequestHeaders().containsKey("Origin")) {code=403;result="{\"error\":\"origin\"}";}
                else if(exchange.getRequestURI().getPath().equals("/health")&&exchange.getRequestMethod().equals("GET")) {
                    var transport=mapping;boolean transportFailed=transport!=null&&!transport.failure.isEmpty();
                    var pose=HostPoseReader.applied;
                    code=200;result="{\"worldName\":"+new com.google.gson.Gson().toJson(worldName())+",\"lighting\":"+NativeWorldSettings.status+",\"villageSetup\":"+VillageWorldSetup.status+",\"fullBright\":"+Boolean.getBoolean("owmc.fullBright")+",\"mode\":\"full-world-frame-proof\",\"worldKind\":\""+(survival?(creative?"creative-natural":"survival-natural"):"creative-flat")+"\",\"player\":"+playerStatus+",\"sourcePid\":"+ProcessHandle.current().pid()+",\"generation\":"+sourceGeneration+",\"captured\":"+captured+",\"published\":"+(transport==null?0:transport.published)+",\"skipped\":"+skipped+",\"glRestorations\":"+restorations+",\"failed\":"+(failed||transportFailed)+",\"hidden\":"+hidden+",\"hostPoseConnected\":"+(pose!=null)+",\"hostFrame\":"+(pose==null?0:pose.frame())+",\"hostGeneration\":"+(pose==null?0:pose.generation())+",\"hostPoseFlags\":"+(pose==null?0:pose.flags())+",\"error\":"+new com.google.gson.Gson().toJson(transportFailed?transport.failure:error)+"}";
                    result=result.substring(0,result.length()-1)+",\"startupCompilerBudget\":"+StartupCompilerBudget.status()+"}";
                } else if(exchange.getRequestURI().getPath().equals("/survival")&&exchange.getRequestMethod().equals("GET")) {
                    var survivalStatus=com.google.gson.JsonParser.parseString(SurvivalRuntime.status).getAsJsonObject();
                    survivalStatus.add("native",com.google.gson.JsonParser.parseString(SurvivalClient.status));
                    survivalStatus.add("menu",com.google.gson.JsonParser.parseString(SurvivalMenu.status));
                    survivalStatus.add("worldMenu",com.google.gson.JsonParser.parseString(WorldSettingsMenu.status));
                    survivalStatus.add("portalMenu",com.google.gson.JsonParser.parseString(PortalMenu.status));
                    survivalStatus.add("mobMenu",com.google.gson.JsonParser.parseString(SummonMenu.status));
                    survivalStatus.add("bossMenu",com.google.gson.JsonParser.parseString(TwilightBossMenu.status));
                    survivalStatus.add("summons",com.google.gson.JsonParser.parseString(HeroSummonRuntime.status));
                    survivalStatus.add("lab",com.google.gson.JsonParser.parseString(SurvivalLab.status));
                    survivalStatus.addProperty("npcDraws",HeroNpcRenderer.draws);survivalStatus.addProperty("npcRenderError",HeroNpcRenderer.error);code=200;result=survivalStatus.toString();
                } else if(exchange.getRequestURI().getPath().startsWith("/survival/test/")&&exchange.getRequestMethod().equals("POST")) {
                    if(Boolean.getBoolean("owmc.survivalLab")&&worldName().startsWith("Overwatch Twilight Switch G Survival Lab ")){
                        String action=exchange.getRequestURI().getPath().substring("/survival/test/".length());
                        MinecraftClient.getInstance().execute(()->{var c=MinecraftClient.getInstance();var s=c.getServer();if(s!=null&&c.player!=null){var id=c.player.getUuid();s.execute(()->SurvivalLab.action(s,id,action));}});code=202;result="{\"accepted\":true}";
                    }else{code=403;result="{\"error\":\"isolated G survival lab required\"}";}
                } else if(exchange.getRequestURI().getPath().equals("/performance")&&exchange.getRequestMethod().equals("GET")) {
                    var m=mapping;code=200;result="{\"width\":"+sourceWidth+",\"height\":"+sourceHeight+",\"exportDepth\":"+exportDepth+",\"bytesPerFrame\":"+((long)sourceWidth*sourceHeight*(exportDepth?8:4))+",\"captureFps\":"+captureFps+",\"renderInterval\":"+renderIntervals.json()+",\"captureCpu\":"+captureTime.json()+",\"combatPoll\":"+combatTime.json()+",\"dashPoll\":"+dashTime.json()+",\"publishCpu\":"+(m==null?"null":m.publishTime.json())+",\"pixelBufferAllocations\":"+(m==null?0:m.bufferAllocations())+",\"publisherDropped\":"+(m==null?0:m.dropped)+"}";
                } else if(exchange.getRequestURI().getPath().equals("/world")&&exchange.getRequestMethod().equals("GET")) {
                    var diagnostic=com.google.gson.JsonParser.parseString(TwilightForestTrial.status).getAsJsonObject();
                    diagnostic.add("bossHud",com.google.gson.JsonParser.parseString(VanillaBossOverlay.status));diagnostic.add("bossTravel",com.google.gson.JsonParser.parseString(TwilightBossTravel.status));diagnostic.add("randomBossTravel",com.google.gson.JsonParser.parseString(RandomBossTravel.status));diagnostic.add("bossTravelMenu",com.google.gson.JsonParser.parseString(TwilightBossMenu.status));diagnostic.add("nearbyBosses",com.google.gson.JsonParser.parseString(BossObservations.status));diagnostic.add("aoaBossTravel",com.google.gson.JsonParser.parseString(AoABossTravel.status));diagnostic.add("portalMenu",com.google.gson.JsonParser.parseString(PortalMenu.status));diagnostic.add("portalCatalog",com.google.gson.JsonParser.parseString(PortalCatalog.status));diagnostic.add("portalBuild",com.google.gson.JsonParser.parseString(PortalBuildRuntime.status));diagnostic.addProperty("switchTrialError",NativeSwitchTrial.error);code=200;result=diagnostic.toString();
                } else if(exchange.getRequestURI().getPath().equals("/world/portals/undo-test")&&exchange.getRequestMethod().equals("POST")) {
                    MinecraftClient.getInstance().execute(()->{var c=MinecraftClient.getInstance();if(c.player==null||c.getServer()==null)return;var s=c.getServer();var owner=c.player.getUuid();s.execute(()->PortalBuildRuntime.undoTest(s,owner));});code=202;result="{\"accepted\":true}";
                } else if(exchange.getRequestURI().getPath().startsWith("/world/switch-test/")&&exchange.getRequestMethod().equals("POST")) {
                    var name=exchange.getRequestURI().getPath().substring("/world/switch-test/".length());
                    if(name.equals("reload")&&Boolean.getBoolean("owmc.twilightTrial")&&worldName().startsWith("Overwatch Twilight Switch ")){
                        MinecraftClient.getInstance().execute(()->{var c=MinecraftClient.getInstance();if(c.player!=null&&c.player.isCreative()&&c.getServer()!=null&&reloadWorld==null){reloadWorld=worldName();c.world.disconnect();c.disconnect();}});code=202;result="{\"accepted\":true}";
                    }else if(java.util.Set.of("overworld","nether","end","twilight").contains(name)){
                        MinecraftClient.getInstance().execute(()->{var c=MinecraftClient.getInstance();var server=c.getServer();if(server==null||c.player==null)return;var owner=c.player.getUuid();server.execute(()->NativeSwitchTrial.travel(server,owner,name));});code=202;result="{\"accepted\":true}";
                    }else{code=400;result="{\"error\":\"dimension\"}";}
                } else if(exchange.getRequestURI().getPath().equals("/world/twilight/portal")&&exchange.getRequestMethod().equals("POST")) {
                    MinecraftClient.getInstance().execute(()->{
                        var c=MinecraftClient.getInstance();var server=c.getServer();
                        if(server==null||c.player==null)return;
                        var owner=c.player.getUuid();var forward=c.player.getRotationVec(1f);
                        server.execute(()->TwilightForestTrial.buildPortal(server,owner,forward));
                    });code=202;result="{\"accepted\":true}";
                } else if((exchange.getRequestURI().getPath().equals("/world/twilight/native-naga")||exchange.getRequestURI().getPath().equals("/world/twilight/native-cleanup"))&&exchange.getRequestMethod().equals("POST")) {
                    boolean cleanup=exchange.getRequestURI().getPath().endsWith("native-cleanup");
                    MinecraftClient.getInstance().execute(()->{var c=MinecraftClient.getInstance();var server=c.getServer();if(server==null||c.player==null)return;var owner=c.player.getUuid();var direction=c.player.getRotationVec(1f);server.execute(()->{if(cleanup)TwilightForestTrial.stopNativeProbe(server);else TwilightForestTrial.startNativeProbe(server,owner,direction);});});
                    code=202;result="{\"accepted\":true}";
                } else if((exchange.getRequestURI().getPath().equals("/world/twilight/probe-naga")||exchange.getRequestURI().getPath().equals("/world/twilight/probe-hydra"))&&exchange.getRequestMethod().equals("POST")) {
                    boolean hydra=exchange.getRequestURI().getPath().endsWith("probe-hydra");
                    MinecraftClient.getInstance().execute(()->{var c=MinecraftClient.getInstance();var server=c.getServer();if(server==null||c.player==null)return;var owner=c.player.getUuid();server.execute(()->TwilightForestTrial.startProbe(server,owner,hydra));});
                    code=202;result="{\"accepted\":true}";
                } else if((exchange.getRequestURI().getPath().equals("/combat/sonic-client")||exchange.getRequestURI().getPath().equals("/combat/infra-client"))&&exchange.getRequestMethod().equals("GET")) {
                    code=200;result=exchange.getRequestURI().getPath().endsWith("infra-client")?NativeInfraSightController.status:HanzoSonicReveal.status;
                } else if(exchange.getRequestURI().getPath().equals("/combat")&&exchange.getRequestMethod().equals("GET")) {
                    var diagnostic=com.google.gson.JsonParser.parseString(NativeCombatRuntime.status).getAsJsonObject();diagnostic.addProperty("feedError",combat.error);diagnostic.addProperty("nativeVelocityAimDot",combat.aimDot);diagnostic.add("dash",com.google.gson.JsonParser.parseString(NativeDashRuntime.status));diagnostic.addProperty("dashError",NativeDashController.error);diagnostic.add("dashBinding",com.google.gson.JsonParser.parseString(NativeDashController.bindingStatus));var ultimate=new com.google.gson.JsonObject();ultimate.addProperty("charge",NativeUltimateController.charge);ultimate.addProperty("cost",NativeUltimateController.cost);ultimate.addProperty("active",NativeUltimateController.active);ultimate.addProperty("swings",NativeUltimateRuntime.swings);ultimate.addProperty("hits",NativeUltimateRuntime.hits);ultimate.addProperty("damageApplied",NativeUltimateRuntime.damageApplied);ultimate.addProperty("error",NativeUltimateController.error);ultimate.add("voice",com.google.gson.JsonParser.parseString(GenjiUltimateVoice.status));diagnostic.add("ultimate",ultimate);diagnostic.add("genjiParticles",com.google.gson.JsonParser.parseString(GenjiCombatParticles.status));diagnostic.add("earlyChineseVoices",com.google.gson.JsonParser.parseString(EarlyChineseVoices.status));diagnostic.add("barrageVisuals",com.google.gson.JsonParser.parseString(PharahBarrageRenderer.status));diagnostic.add("barrageSound",com.google.gson.JsonParser.parseString(PharahBarrageSound.status));diagnostic.addProperty("particleMode",MinecraftClient.getInstance().options.getParticles().getValue().name());diagnostic.add("locomotion",com.google.gson.JsonParser.parseString(NativeLocomotionController.status));diagnostic.add("climb",com.google.gson.JsonParser.parseString(WallClimbController.status));diagnostic.add("melee",com.google.gson.JsonParser.parseString(NativeMeleeRuntime.status));diagnostic.addProperty("meleeError",NativeMeleeController.error);diagnostic.add("portals",com.google.gson.JsonParser.parseString(NativePortalRuntime.status));diagnostic.addProperty("portalError",NativePortalController.error);code=200;result=diagnostic.toString();
                    diagnostic.add("biotic",com.google.gson.JsonParser.parseString(NativeBioticRuntime.status));diagnostic.addProperty("bioticError",NativeBioticController.error);diagnostic.addProperty("bioticRenderFrames",BioticFieldRenderer.frames);diagnostic.add("pulse",com.google.gson.JsonParser.parseString(NativePulseRuntime.status));diagnostic.addProperty("pulseError",NativePulseController.error);diagnostic.addProperty("pulseRenderFrames",PulseBombRenderer.frames);diagnostic.add("recall",com.google.gson.JsonParser.parseString(NativeRecallRuntime.status));diagnostic.addProperty("recallError",NativeRecallController.error);diagnostic.addProperty("recallLocked",NativeRecallController.rewinding());diagnostic.add("reaper",com.google.gson.JsonParser.parseString(NativeReaperRuntime.status));diagnostic.addProperty("reaperError",NativeReaperController.error);diagnostic.add("wraith",com.google.gson.JsonParser.parseString(NativeWraithRuntime.status));diagnostic.addProperty("wraithError",NativeWraithController.error);diagnostic.add("shadow",com.google.gson.JsonParser.parseString(NativeShadowRuntime.status));diagnostic.addProperty("shadowError",NativeShadowController.error);diagnostic.add("grapple",com.google.gson.JsonParser.parseString(NativeGrappleController.status));diagnostic.addProperty("grappleError",NativeGrappleController.error);HeroServerModules.status(diagnostic);HeroClientModules.errors(diagnostic);diagnostic.add("torb",com.google.gson.JsonParser.parseString(NativeTorbjornRuntime.status));diagnostic.addProperty("torbError",NativeTorbjornController.error);diagnostic.add("hanzoSkills",com.google.gson.JsonParser.parseString(NativeHanzoSkillRuntime.status));diagnostic.addProperty("hanzoSkillError",NativeHanzoSkillController.error);diagnostic.add("hanzoControls",com.google.gson.JsonParser.parseString(HanzoControlController.status));diagnostic.addProperty("junkratRendererFrames",JunkratRenderer.frames);diagnostic.addProperty("hanzoDragonRendererFrames",HanzoDragonRenderer.frames);diagnostic.addProperty("hanzoDragonRendererErrors",HanzoDragonRenderer.errors);diagnostic.addProperty("hanzoDragonRendererError",HanzoDragonRenderer.error);diagnostic.add("hanzoArrowFx",HanzoArrowRenderer.diagnostics());diagnostic.add("hanzoArrowVisualLab",com.google.gson.JsonParser.parseString(HanzoArrowVisualLab.status));diagnostic.addProperty("hanzoArrowRenderFrames",HanzoArrowRenderer.frames);diagnostic.addProperty("hanzoArrowRenderErrors",HanzoArrowRenderer.errors);diagnostic.addProperty("hanzoArrowRenderError",HanzoArrowRenderer.error);diagnostic.addProperty("hanzoArrowPrimaryFrames",HanzoArrowRenderer.primaryFrames);diagnostic.addProperty("hanzoArrowSonicFrames",HanzoArrowRenderer.sonicFrames);diagnostic.addProperty("hanzoArrowScatterParentFrames",HanzoArrowRenderer.scatterParentFrames);diagnostic.addProperty("hanzoArrowScatterChildFrames",HanzoArrowRenderer.scatterChildFrames);diagnostic.addProperty("hanzoArrowStuckFrames",HanzoArrowRenderer.stuckFrames);diagnostic.addProperty("hanzoSonicPulseFrames",HanzoArrowRenderer.pulseFrames);diagnostic.addProperty("hanzoArrowSegments",HanzoArrowPresentation.segments);diagnostic.addProperty("hanzoArrowEmbedded",HanzoArrowPresentation.embedded);diagnostic.addProperty("hanzoArrowPresentationRefused",HanzoArrowPresentation.refused);diagnostic.addProperty("meshErrors",OriginalMeshPack.ERRORS.toString());diagnostic.add("junkrat",com.google.gson.JsonParser.parseString(NativeJunkratRuntime.status));diagnostic.addProperty("junkratError",NativeJunkratController.error);diagnostic.add("iceWall",com.google.gson.JsonParser.parseString(NativeIceWallRuntime.status));diagnostic.add("blizzard",com.google.gson.JsonParser.parseString(NativeBlizzardRuntime.status));diagnostic.addProperty("meiSkillError",NativeMeiSkillController.error);diagnostic.add("venom",com.google.gson.JsonParser.parseString(NativeVenomRuntime.status));diagnostic.addProperty("venomRendererFrames",VenomMineRenderer.frames);diagnostic.addProperty("venomRendererError",VenomMineRenderer.error);diagnostic.add("souls",com.google.gson.JsonParser.parseString(NativeSoulRuntime.status));diagnostic.add("bioticSound",com.google.gson.JsonParser.parseString(BioticFieldSound.status));
                    diagnostic.add("roll",com.google.gson.JsonParser.parseString(NativeRollController.status));diagnostic.add("flight",com.google.gson.JsonParser.parseString(NativeFlightController.status));diagnostic.add("blink",com.google.gson.JsonParser.parseString(NativeBlinkController.status));diagnostic.add("motor",com.google.gson.JsonParser.parseString(NativeMotorController.status));diagnostic.add("utilities",com.google.gson.JsonParser.parseString(NativeUtilityController.status));diagnostic.add("randomMobs",com.google.gson.JsonParser.parseString(PlayerUtilities.status));diagnostic.add("mccreeVoice",com.google.gson.JsonParser.parseString(MccreeVoice.status));diagnostic.add("deadeyeShotSound",com.google.gson.JsonParser.parseString(DeadeyeShotSound.status));diagnostic.add("combatFeedbackSound",com.google.gson.JsonParser.parseString(CombatFeedbackSound.status));diagnostic.addProperty("combatHitEvents",NativeCombatFeedback.hitEvents);diagnostic.addProperty("combatKillEvents",NativeCombatFeedback.killEvents);diagnostic.addProperty("deadeyeKillBursts",DeadeyeKillEffects.bursts);diagnostic.addProperty("deadeyeJumpLocked",NativeDeadeyeController.jumpLocked());diagnostic.add("deadeyeGrade",com.google.gson.JsonParser.parseString(DeadeyeExportGrade.status));diagnostic.addProperty("deadeyeError",NativeDeadeyeController.error);diagnostic.addProperty("deadeyeLastFailure",NativeDeadeyeController.lastFailure);diagnostic.addProperty("deadeyePresentationIoFailures",NativeDeadeyeController.presentationIoFailures);diagnostic.addProperty("deadeyeNativeEndRequests",NativeDeadeyeFinish.requests);diagnostic.addProperty("flashbangRenderFrames",MccreeEffectsRenderer.grenadeFrames);diagnostic.addProperty("deadeyeRenderFrames",MccreeEffectsRenderer.lockFrames);diagnostic.add("nativeCharge",com.google.gson.JsonParser.parseString(NativeChargeController.status));diagnostic.add("deflect",com.google.gson.JsonParser.parseString(NativeDeflectRuntime.status));diagnostic.addProperty("deflectError",NativeDeflectController.error);diagnostic.add("sustain",com.google.gson.JsonParser.parseString(NativeSustainRuntime.status));diagnostic.addProperty("sustainError",NativeSustainController.error);result=diagnostic.toString();
                    diagnostic.addProperty("modelsRenderFrames",OriginalWorldRenderer.frames);
                    diagnostic.addProperty("modelsSubmissions",OriginalWorldRenderer.submissions);
                    diagnostic.addProperty("modelsRejected",OriginalWorldRenderer.rejected);
                    diagnostic.addProperty("modelsError",OriginalWorldRenderer.error);
                    diagnostic.add("hanzoCombatLab", com.google.gson.JsonParser.parseString(HanzoCombatLab.status));
                    diagnostic.add("pulseBinding",com.google.gson.JsonParser.parseString(NativePulseController.status));
                    diagnostic.add("recallSound",com.google.gson.JsonParser.parseString(RecallStartSound.status));
                    diagnostic.addProperty("tankShellGlowFrames",BastionTankRenderer.glowFrames);
                    diagnostic.addProperty("tankShellGlowError",BastionTankRenderer.glowError);
                    // integrator: builders/colors diagnostics; existing error fields retained once.
                    diagnostic.addProperty("junkTireRendererFrames",JunkratRenderer.tireFrames);
                    diagnostic.addProperty("torbTurretRendererFrames",JunkratRenderer.turretFrames);
                    diagnostic.addProperty("torbScrapHudFrames",JunkratRenderer.scrapHudFrames);
                    diagnostic.addProperty("hanzoDragonSkinDraws",HanzoDragonRenderer.skinDraws);
                    diagnostic.addProperty("hanzoDragonSkinFallbackDraws",HanzoDragonRenderer.skinFallbackDraws);
                    diagnostic.addProperty("hanzoDragonSwimBones",HanzoDragonRenderer.lastSwimBones);
                    diagnostic.addProperty("hanzoDragonAnimationMode",HanzoDragonRenderer.animationMode);
                    var originalEffectMaterials=new com.google.gson.JsonObject();
                    for(String name:new String[]{"zenyatta-primary-core","zenyatta-secondary-core",
                        "zenyatta-primary-glow","zenyatta-secondary-glow","zarya-grenade","zarya-grenade-blue",
                        "zarya-graviton","hanzo-sonic-pulse","hanzo-sonic-sense","hanzo-dragon-blue","hanzo-dragon-red"})
                        originalEffectMaterials.add(name,OriginalMeshPack.diagnostics(name));
                    diagnostic.add("originalEffectMaterials",originalEffectMaterials);
                    // 语音挂接：纯快照，HTTP线程不访问声卡或游戏对象。
                    diagnostic.add("heroVoice",com.google.gson.JsonParser.parseString(HeroVoiceEvents.status));
                    diagnostic.add("survival",com.google.gson.JsonParser.parseString(SurvivalRuntime.status));diagnostic.add("heroSummons",com.google.gson.JsonParser.parseString(HeroSummonRuntime.status));result=diagnostic.toString();
                } else if(exchange.getRequestURI().getPath().equals("/combat/test/recall-empty-history")&&exchange.getRequestMethod().equals("POST")) {
                    if(!Boolean.getBoolean("owmc.twilightTrial")||!worldName().startsWith("Overwatch Twilight Switch ")){
                        code=403;result="{\"error\":\"Recall fixture requires the isolated Switch save\"}";
                    }else{
                        MinecraftClient.getInstance().execute(()->{
                            var c=MinecraftClient.getInstance();var server=c.getServer();var pose=HostPoseReader.INSTANCE.latest();
                            if(server==null||c.player==null||c.world==null||pose==null||pose.flags()!=1)return;
                            var expected=new NativeRecallRuntime.Scope(c.player.getUuid(),NativeWorldIdentity.of(server,c.world.getRegistryKey()),
                                pose.generation(),NativeLocomotionController.INSTANCE.modelId());
                            server.execute(()->NativeRecallRuntime.pauseHistoryForTest(server,expected));
                        });
                        // Queuing is not proof that the server accepted the
                        // fixture. Tests must observe the exact scoped pause.
                        code=202;result="{\"queued\":true}";
                    }
                } else if(exchange.getRequestURI().getPath().startsWith("/combat/test/cannon-")&&exchange.getRequestMethod().equals("POST")) {
                    var name=exchange.getRequestURI().getPath().substring("/combat/test/cannon-".length());
                    if(!java.util.Set.of("direct","splash","far").contains(name)){
                        code=400;result="{\"error\":\"cannon fixture\"}";
                    }else if(!Boolean.getBoolean("owmc.twilightTrial")||!worldName().startsWith("Overwatch Twilight Switch ")){
                        code=403;result="{\"error\":\"cannon fixture requires the isolated Switch save\"}";
                    }else{
                        MinecraftClient.getInstance().execute(()->{
                            var c=MinecraftClient.getInstance();var server=c.getServer();var pose=HostPoseReader.INSTANCE.latest();
                            if(server==null||c.player==null||pose==null||pose.flags()!=1)return;
                            var owner=c.player.getUuid();var eye=c.player.getEyePos();var direction=new org.joml.Vector3f(0,0,-1).rotate(pose.rotation());
                            var forward=new net.minecraft.util.math.Vec3d(direction.x,direction.y,direction.z);
                            server.execute(()->NativeCombatScene.tankCannon(server,owner,eye,forward,name.equals("direct")?0:name.equals("splash")?1:2));
                        });code=202;result="{\"queued\":true}";
                    }
                } else if(exchange.getRequestURI().getPath().startsWith("/combat/test/voice-status-")
        && exchange.getRequestMethod().equals("POST")) {
    var kind=exchange.getRequestURI().getPath().substring("/combat/test/voice-status-".length());
    if(!java.util.Set.of("slowed","poisoned","debuffed","damage_boosted").contains(kind)) {
        code=400;result="{\"error\":\"unsupported voice status fixture\"}";
    } else {
        MinecraftClient.getInstance().execute(()->{
            var c=MinecraftClient.getInstance();var server=c.getServer();
            if(server==null||c.player==null)return;
            var owner=c.player.getUuid();
            server.execute(()->HeroVoiceStatusLab.apply(server,owner,kind));
        });
        code=202;result="{\"queued\":true}";
    }
                } else if(exchange.getRequestURI().getPath().startsWith("/combat/test/")&&exchange.getRequestMethod().equals("POST")) {
                    var action=exchange.getRequestURI().getPath().substring("/combat/test/".length());
                    if(java.util.Set.of(
                        "hanzo-combat-lab",
                        "torb-pack-recipient-lab",
                        "mercy-pistol","mercy-guardian","mercy-passive",
"zen-harmony","zen-discord","zen-transcendence","lucio-boop","lucio-wallride",
                        "roadhog-split-lab",
                        "torb-scrap-lab","torb-repair-lab","torb-approach-lab","torb-pack-lab","torb-core-target","junk-death-lab","junk-respawn-lab",
                        "symmetra-beam-lab","symmetra-far-lab","symmetra-ally-lab","symmetra-cover","symmetra-shield-hit",
                        "mercy-support","mercy-covered","mercy-far","mercy-hostile","mercy-foreign",
                        "zen-body","zen-covered",
                        "reinhardt-lab","reinhardt-cover-lab","reinhardt-shield-lab",
                        "zarya-lab","zarya-cover-lab","zarya-shield-lab",
                        "roadhog-scatter","roadhog-secondary","roadhog-hook","roadhog-hook-wall","roadhog-heal","roadhog-q",
                        "dva-pistol","dva-pistol-wall",
                        "dva-pilot-attempt","symmetra-placement","lucio-support",
                        "mei-target","mei-struggle","start","grapple-wall","venom-target","ground-lab","mei-lab","mei-lab-silent","hanzo-arrows-visual","far-lab","push-target","melee","blade-near","blade-far","blade-outside","deadeye-crowd","reaper-blossom","enderman","enderman-melee","sustain-hurt","sustain-ignite","soul-target","shadow-block","wraith-hit","recall-hurt","release-injury","biotic-lab","deflect-arrow","deflect-lethal","beam","wall","climb-wall","roll-lane","explosive-terrain","flight-open","locomotion-origin","flight-ceiling","open","replay","cleanup","random-cleanup","crystal","rocket").contains(action)){
                        MinecraftClient.getInstance().execute(()->{
                            var c=MinecraftClient.getInstance();var server=c.getServer();var pose=HostPoseReader.INSTANCE.latest();
                            if(server==null||c.player==null||pose==null||pose.flags()!=1)return;
                            var owner=c.player.getUuid();var eye=c.player.getEyePos();var feet=c.player.getPos();var direction=new org.joml.Vector3f(0,0,-1).rotate(pose.rotation());
                            var forward=new net.minecraft.util.math.Vec3d(direction.x,direction.y,direction.z);
                            server.execute(()->{switch(action){
                                case "hanzo-combat-lab" -> HanzoCombatLab.start(server, owner, forward);
                                case "torb-pack-recipient-lab" -> NativeBuildersLab.action(server,owner,forward,action);
                                case "mercy-pistol","mercy-guardian","mercy-passive",
                                     "zen-harmony","zen-discord","zen-transcendence","lucio-boop","lucio-wallride"
                                    ->SupportCommitFixtures.setup(server,owner,forward,action);
                                case "roadhog-split-lab"->NativeCombatScene.heroLab(server,owner,forward,action);
                                case "torb-scrap-lab","torb-repair-lab","torb-approach-lab","torb-pack-lab","torb-core-target","junk-death-lab","junk-respawn-lab"
                                    -> NativeBuildersLab.action(server,owner,forward,action);
                                case "symmetra-beam-lab","symmetra-far-lab","symmetra-ally-lab","symmetra-placement","symmetra-cover","symmetra-shield-hit"
                                    ->SymmetraLab.action(server,owner,forward,action);
                                case "mercy-support","mercy-covered","mercy-far","mercy-hostile","mercy-foreign"->NativeCombatScene.heroLab(server,owner,forward,action);
                                case "zen-body","zen-covered"->NativeCombatScene.heroLab(server,owner,forward,action);
                                case "reinhardt-lab","reinhardt-cover-lab","reinhardt-shield-lab"->NativeCombatScene.heroLab(server,owner,forward,action);
                                case "zarya-lab","zarya-cover-lab","zarya-shield-lab"->NativeCombatScene.heroLab(server,owner,forward,action);
                                case "roadhog-scatter","roadhog-secondary","roadhog-hook","roadhog-hook-wall","roadhog-heal","roadhog-q"->NativeCombatScene.heroLab(server,owner,forward,action);
                                case "dva-pistol","dva-pistol-wall"->NativeCombatScene.heroLab(server,owner,forward,action);
                                // integrator: placement now uses SymmetraLab ownership/cleanup.
                                case "dva-pilot-attempt","lucio-support"->NativeCombatScene.heroLab(server,owner,forward,action);
                                case "mei-target"->NativeCombatScene.meiTarget(server,owner,eye,forward);case "mei-struggle"->NativeCombatScene.meiStruggle(server,owner);case "start"->NativeCombatScene.start(server,owner,eye,forward);case "push-target"->NativeCombatScene.pushTarget(server,owner,eye,forward);case "melee"->NativeCombatScene.start(server,owner,eye,forward,2);case "blade-near"->NativeCombatScene.start(server,owner,eye,forward,1);case "blade-far"->NativeCombatScene.start(server,owner,eye,forward,4);case "blade-outside"->NativeCombatScene.start(server,owner,eye,forward,7);case "enderman"->NativeCombatScene.enderman(server,owner,eye,forward,false);case "enderman-melee"->NativeCombatScene.enderman(server,owner,eye,forward,true);case "sustain-hurt"->NativeCombatScene.sustainHurt(server,owner);case "sustain-ignite"->NativeCombatScene.sustainIgnite(server,owner);case "biotic-lab"->NativeCombatScene.bioticLab(server,owner);case "shadow-block"->NativeCombatScene.shadowBlock(server,owner);case "soul-target"->NativeCombatScene.soulTarget(server,owner,eye,forward);case "wraith-hit"->NativeCombatScene.wraithHit(server,owner);case "recall-hurt"->NativeCombatScene.recallHurt(server,owner);case "release-injury"->NativeCombatScene.releaseInjury();case "deflect-arrow"->NativeCombatScene.deflectArrow(server,owner,false);case "deflect-lethal"->NativeCombatScene.deflectArrow(server,owner,true);case "beam"->NativeCombatScene.beam(server,owner,eye,forward);case "deadeye-crowd"->NativeCombatScene.deadeyeCrowd(server,owner,eye,forward);case "reaper-blossom"->NativeCombatScene.reaperBlossom(server,owner,eye,forward);case "rocket"->NativeCombatScene.rocket(server,owner,eye,forward);case "climb-wall"->NativeCombatScene.climbWall(server,owner,feet,forward);case "grapple-wall"->NativeCombatScene.grappleWall(server,owner,eye,forward);case "venom-target"->NativeCombatScene.venomTarget(server,owner);case "ground-lab"->NativeCombatScene.groundLab(server,owner);case "mei-lab"->NativeCombatScene.meiLab(server,owner,forward);case "hanzo-arrows-visual"->HanzoArrowVisualLab.start(server,owner,forward);case "mei-lab-silent"->NativeCombatScene.meiLabSilent(server,owner,forward);case "far-lab"->NativeCombatScene.meiLab(server,owner,forward,16);case "roll-lane"->NativeCombatScene.rollLane(server,owner,feet,forward);case "explosive-terrain"->NativeCombatScene.explosiveTerrain(server,owner,eye,forward);case "flight-open"->NativeCombatScene.flightLab(server,owner,false);case "locomotion-origin"->NativeCombatScene.locomotionOrigin(server,owner);case "flight-ceiling"->NativeCombatScene.flightLab(server,owner,true);case "crystal"->NativeCombatScene.crystal(server,owner,eye,forward);case "wall"->NativeCombatScene.wall(true);case "open"->NativeCombatScene.wall(false);case "replay"->NativeCombatRuntime.replay(server);case "random-cleanup"->PlayerUtilities.cleanupTestBatch(server);case "cleanup"->{HanzoCombatLab.cleanup();NativeBuildersLab.cleanup();HanzoArrowVisualLab.cleanup();NativeCombatScene.cleanup();NativeCombatScene.restoreCreative(server.getPlayerManager().getPlayer(owner));NativeBioticRuntime.resetSession();NativePulseRuntime.resetSession();NativeRecallRuntime.cancelForTests();NativeReaperRuntime.resetSession();NativeWraithRuntime.resetSession();NativeShadowRuntime.clear();NativeVenomRuntime.clear();NativeBlizzardRuntime.clear();NativeIceWallRuntime.clear();NativeJunkratRuntime.clear();NativeHanzoSkillRuntime.clear();NativeTorbjornRuntime.clear();HeroServerModules.clear();NativeSoulRuntime.clearForTests();}default->throw new IllegalStateException();}});
                        });code=202;result="{\"accepted\":true}";
                    }
                } else if(exchange.getRequestURI().getPath().equals("/window/show")&&exchange.getRequestMethod().equals("POST")) {
                    if(!BackgroundWindowVisibility.allowShow()) {
                        code=409;result="{\"accepted\":false,\"reason\":\"window-show-disabled-by-session\"}";
                    } else {
                        MinecraftClient.getInstance().execute(()->{
                            if(BackgroundWindowVisibility.show(MinecraftClient.getInstance().getWindow().getHandle())) {
                                comparisonVisible=true;hidden=BackgroundWindowVisibility.hidden();
                            }
                        });
                        code=202;result="{\"accepted\":true}";
                    }
                } else if((exchange.getRequestURI().getPath().equals("/export/pause")||exchange.getRequestURI().getPath().equals("/export/resume"))&&exchange.getRequestMethod().equals("POST")) {
                    boolean pause=exchange.getRequestURI().getPath().equals("/export/pause");MinecraftClient.getInstance().execute(()->capturePaused=pause);
                    code=202;result="{\"accepted\":true}";
                } else if(exchange.getRequestURI().getPath().equals("/respawn")&&exchange.getRequestMethod().equals("POST")) {
                    MinecraftClient.getInstance().execute(()->{var c=MinecraftClient.getInstance();if(c.player!=null&&!c.player.isAlive()){c.player.requestRespawn();c.setScreen(null);}});
                    code=202;result="{\"accepted\":true}";
                } else if(exchange.getRequestURI().getPath().equals("/shutdown")&&exchange.getRequestMethod().equals("POST")) {
                    MinecraftClient.getInstance().execute(()->MinecraftClient.getInstance().scheduleStop());code=202;result="{\"accepted\":true}";
                }
                byte[] bytes=result.getBytes(StandardCharsets.UTF_8);exchange.getResponseHeaders().set("Content-Type","application/json");exchange.sendResponseHeaders(code,bytes.length);
                try(var out=exchange.getResponseBody()) {out.write(bytes);}finally {exchange.close();}
            });api.start();
        } catch(java.io.IOException e) {failed=true;error=e.toString();System.err.println("[OWMCFrames] Status endpoint unavailable: "+e);}
    }
    private static WorldFrameExporter instance;
    private WorldRenderContext pendingRender;
    /** Final world plus vanilla entity-outline composite, before GUI/postprocessing. */
    public static void captureFinalWorld(){var self=instance;if(self!=null&&self.pendingRender!=null){var render=self.pendingRender;self.pendingRender=null;self.capture(render);}}
    private void startWorld(MinecraftClient client) {
        String name=worldName();
        boolean existing=Files.isRegularFile(client.runDirectory.toPath().resolve("saves").resolve(name).resolve("level.dat"));
        boolean allowedNew=Boolean.getBoolean("owmc.createWorld");
        if(!name.equals("Overwatch Survival World")&&!name.equals("Overwatch Pose Test")&&!name.equals("Overwatch Passthrough World")&&!name.equals("Overwatch Seed World")&&!existing&&!allowedNew)throw new IllegalArgumentException("Selected world has no level.dat");
        if(existing) client.createIntegratedServerLoader().start(name,()->{});
        else client.createIntegratedServerLoader().createAndStart(name,
            new LevelInfo(name,survival?GameMode.SURVIVAL:GameMode.CREATIVE,false,Difficulty.NORMAL,!survival,new GameRules(),DataConfiguration.SAFE_MODE),
            new GeneratorOptions(Long.getLong("owmc.worldSeed",20261014L),survival,false),registries->registries.get(RegistryKeys.WORLD_PRESET).get(survival?WorldPresets.DEFAULT:WorldPresets.FLAT).createDimensionsRegistryHolder(),null);
    }
    private String worldName(){
        String name=Boolean.getBoolean("owmc.poseTest")?"Overwatch Pose Test":System.getProperty("owmc.worldName",survival?"Overwatch Survival World":"Overwatch Passthrough World");
        if(name.isBlank()||name.equals(".")||name.equals("..")||name.indexOf('/')>=0||name.indexOf('\\')>=0||name.indexOf(':')>=0)throw new IllegalArgumentException("Invalid world folder");
        return name;
    }
    private void capture(WorldRenderContext render) {
        long begin=System.nanoTime();if(lastRender!=0)renderIntervals.add(begin-lastRender);lastRender=begin;
        if(failed||capturePaused) return;RenderSystem.assertOnRenderThread();
        var client=MinecraftClient.getInstance();var target=client.getFramebuffer();int w=target.textureWidth,h=target.textureHeight;
        sourceWidth=w;sourceHeight=h;
        if(w<1||h<1||w>WorldFrameMapping.MAX_W||h>WorldFrameMapping.MAX_H) {skipped++;return;}
        int oldRead=GL11.glGetInteger(GL30.GL_READ_FRAMEBUFFER_BINDING),oldReadBuffer=GL11.glGetInteger(GL11.GL_READ_BUFFER),oldPack=GL11.glGetInteger(GL21.GL_PIXEL_PACK_BUFFER_BINDING);
        int[] packNames={GL11.GL_PACK_ALIGNMENT,GL11.GL_PACK_ROW_LENGTH,GL11.GL_PACK_SKIP_ROWS,GL11.GL_PACK_SKIP_PIXELS,GL11.GL_PACK_SWAP_BYTES};
        int[] oldStore=new int[packNames.length];for(int i=0;i<packNames.length;i++) oldStore[i]=GL11.glGetInteger(packNames[i]);
        try {
            if(mapping==null) {mapping=new WorldFrameMapping();sourceGeneration=mapping.generation();System.out.println("[OWMCFrames] Actual world/depth exporter connected to "+WorldFrameMapping.NAME);}
            for(Slot s:ring) if(s.fence!=0) {
                int wait=GL32.glClientWaitSync(s.fence,0,0);
                if(wait==GL32.GL_TIMEOUT_EXPIRED) continue;
                if(wait==GL32.GL_WAIT_FAILED) throw new IllegalStateException("GPU fence failed");
                GL15.glBindBuffer(GL21.GL_PIXEL_PACK_BUFFER,s.pbo);int bytes=s.pose.width()*s.pose.height()*(exportDepth?8:4);
                ByteBuffer mapped=GL30.glMapBufferRange(GL21.GL_PIXEL_PACK_BUFFER,0,bytes,GL30.GL_MAP_READ_BIT);
                if(mapped==null) throw new IllegalStateException("GPU readback unavailable");
                byte[] data=mapping.acquireBytes(bytes);boolean valid;
                try {if(data!=null)mapped.get(data);}catch(RuntimeException e){if(data!=null)mapping.releaseBytes(data);throw e;}
                finally{valid=GL15.glUnmapBuffer(GL21.GL_PIXEL_PACK_BUFFER);GL32.glDeleteSync(s.fence);s.fence=0;}
                if(data==null){skipped++;continue;}
                if(valid) {var p=s.pose;mapping.submit(new WorldFrameMapping.Capture(p.frame(),p.captureNs(),p.hostFrame(),p.hostGeneration(),p.width(),p.height(),p.near(),p.far(),p.fov(),p.x(),p.y(),p.z(),p.yaw(),p.pitch(),p.roll(),p.projection(),data,p.boss()));}
                else {mapping.releaseBytes(data);skipped++;}
            }
            long now=System.nanoTime();if(now-lastCapture<capturePeriod) return;
            Slot next=null;for(Slot s:ring) if(s.fence==0) {next=s;break;}if(next==null) {skipped++;return;}
            int bytes=w*h*(exportDepth?8:4);GL15.glBindBuffer(GL21.GL_PIXEL_PACK_BUFFER,next.pbo==0?(next.pbo=GL15.glGenBuffers()):next.pbo);
            if(next.capacity!=bytes) {GL15.glBufferData(GL21.GL_PIXEL_PACK_BUFFER,bytes,GL15.GL_STREAM_READ);next.capacity=bytes;}
            int colorFbo=deadeyeGrade.colorFramebuffer(target.fbo,target.getColorAttachment(),w,h);
            GL30.glBindFramebuffer(GL30.GL_READ_FRAMEBUFFER,colorFbo);GL11.glReadBuffer(GL30.GL_COLOR_ATTACHMENT0);
            GL11.glPixelStorei(GL11.GL_PACK_ALIGNMENT,1);for(int i=1;i<packNames.length;i++) GL11.glPixelStorei(packNames[i],0);
            GL11.glReadPixels(0,0,w,h,GL11.GL_RGBA,GL11.GL_UNSIGNED_BYTE,0L);
            if(exportDepth){GL30.glBindFramebuffer(GL30.GL_READ_FRAMEBUFFER,target.fbo);GL11.glReadPixels(0,0,w,h,GL11.GL_DEPTH_COMPONENT,GL11.GL_FLOAT,(long)w*h*4);}
            var projection=render.projectionMatrix();var camera=render.camera();var pos=camera.getPos();float near=projection.perspectiveNear(),far=projection.perspectiveFar();
            if(!Float.isFinite(near)||!Float.isFinite(far)||near<=0||far<=near) throw new IllegalStateException("Invalid actual world projection");
            var applied=HostPoseReader.applied;
            var base=new org.joml.Quaternionf().rotationYXZ((float)Math.PI-(float)Math.toRadians(camera.getYaw()),-(float)Math.toRadians(camera.getPitch()),0);
            var relative=base.conjugate().mul(camera.getRotation());float roll=(float)Math.toDegrees(2*Math.atan2(relative.z,relative.w));if(roll>180) roll-=360;if(roll< -180) roll+=360;
            var boss=NativeBossRuntime.latest;
            if(boss!=null&&(client.getServer()==null||client.world==null||boss.world()!=NativeWorldIdentity.of(client.getServer(),client.world.getRegistryKey())))boss=null;
            next.pose=new WorldFrameMapping.Capture(++captured,now,applied==null?0:applied.frame(),applied==null?0:applied.generation(),w,h,near,far,(float)Math.toDegrees(2*Math.atan(1/projection.m11())),pos.x,pos.y,pos.z,camera.getYaw(),camera.getPitch(),roll,projection.get(new float[16]),null,boss);
            next.fence=GL32.glFenceSync(GL32.GL_SYNC_GPU_COMMANDS_COMPLETE,0);GL11.glFlush();
            lastCapture=now-(now-lastCapture)%capturePeriod;
        } catch(Exception e) {failed=true;error=e.toString();System.err.println("[OWMCFrames] Export disabled: "+e);}
        finally {
            GL15.glBindBuffer(GL21.GL_PIXEL_PACK_BUFFER,oldPack);GL30.glBindFramebuffer(GL30.GL_READ_FRAMEBUFFER,oldRead);GL11.glReadBuffer(oldReadBuffer);
            for(int i=0;i<packNames.length;i++) GL11.glPixelStorei(packNames[i],oldStore[i]);
            boolean restored=GL11.glGetInteger(GL30.GL_READ_FRAMEBUFFER_BINDING)==oldRead&&GL11.glGetInteger(GL11.GL_READ_BUFFER)==oldReadBuffer&&GL11.glGetInteger(GL21.GL_PIXEL_PACK_BUFFER_BINDING)==oldPack;
            for(int i=0;i<packNames.length;i++) restored&=GL11.glGetInteger(packNames[i])==oldStore[i];
            if(restored) restorations++;else {failed=true;error="OpenGL state restoration failed";System.err.println("[OWMCFrames] "+error);}
            captureTime.add(System.nanoTime()-begin);
        }
    }
    private void close() {
        deadeyeGrade.close();
        NativeRollController.INSTANCE.close();
        NativeBlinkController.INSTANCE.close();
        NativeMotorController.INSTANCE.close();
        NativeLocomotionController.INSTANCE.close();
        NativeUltimateController.INSTANCE.close();
        EarlyChineseVoices.INSTANCE.close();
        HeroVoiceEvents.INSTANCE.close(); // 语音挂接：停止自有声道与后台素材处理。
        NativeChargeController.INSTANCE.close();
        NativeMeleeController.INSTANCE.close();
        NativeDeflectController.INSTANCE.close();
        NativeSustainController.INSTANCE.close();
        NativeBioticController.INSTANCE.close();
        BioticFieldSound.INSTANCE.reset();
        NativePortalController.INSTANCE.close();
        NativeUtilityController.INSTANCE.close();NativeDeadeyeController.INSTANCE.close();
        NativeDashController.INSTANCE.close();
        if(api!=null) api.stop(0);if(mapping!=null) mapping.close();HostPoseReader.INSTANCE.close();
        for(Slot s:ring) {if(s.fence!=0) GL32.glDeleteSync(s.fence);if(s.pbo!=0) GL15.glDeleteBuffers(s.pbo);}
    }
}
