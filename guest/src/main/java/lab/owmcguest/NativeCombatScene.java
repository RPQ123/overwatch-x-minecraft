package lab.owmcguest;

import com.google.gson.JsonObject;
import com.google.gson.JsonArray;
import java.util.LinkedHashMap;
import net.minecraft.entity.EntityType;
import net.minecraft.entity.passive.VillagerEntity;
import net.minecraft.block.BlockState;
import net.minecraft.block.Blocks;
import net.minecraft.server.MinecraftServer;
import net.minecraft.server.world.ServerWorld;
import net.minecraft.util.math.BlockPos;
import net.minecraft.util.math.Vec3d;
import net.minecraft.text.Text;

/** Explicit local test fixture, never used to aim or create attacks. */
public final class NativeCombatScene {
    private static net.minecraft.entity.mob.MobEntity target;
    private static JsonArray targetReceipts=new JsonArray();
    private static net.minecraft.entity.decoration.EndCrystalEntity crystal;
    private static net.minecraft.entity.projectile.ArrowEntity deflectArrow;
    private static final LinkedHashMap<String,VillagerEntity> beamTargets=new LinkedHashMap<>();
    private static ServerWorld world;
    private static Vec3d wallCenter,look;
    private static final LinkedHashMap<BlockPos,BlockState> blocks=new LinkedHashMap<>();
    private static String error="";
    private static BlockPos flightBase;
    private static net.minecraft.server.network.ServerPlayerEntity injuredPlayer;
    private static ServerWorld injuryWorld;
    private static float savedHealth;
    private static boolean savedRegeneration;
    private static net.minecraft.server.network.ServerPlayerEntity burnedPlayer;
    private static int savedFireTicks;
    private static boolean savedFireInvulnerability;
    private static int orphanChecks;
    private static long orphansRemoved;
    private static boolean cannonLab;
    private static String heroLab="";
    private static final LinkedHashMap<String,net.minecraft.entity.mob.MobEntity> heroTargets=new LinkedHashMap<>();
    private static final LinkedHashMap<net.minecraft.entity.projectile.ArrowEntity,Boolean> shieldArrows=new LinkedHashMap<>();
    private static net.minecraft.server.network.ServerPlayerEntity shieldPlayer,heroMaxPlayer;
    private static net.minecraft.world.GameMode shieldSavedMode;
    private static boolean shieldSavedInvulnerable,shieldSavedFlying,shieldSavedAllowFlying;
    private static double heroSavedMaxHealth,shieldPlayerDamage,shieldDamageAbsorbed;
    private static float shieldLastHealth;
    private static Vec3d shieldOrigin,shieldVelocity;
    private static int shieldAge,shieldShots,shieldBlocked,shieldDamageAttempts;
    private static final JsonArray shieldDamageReceipts=new JsonArray();
    static {net.fabricmc.fabric.api.event.lifecycle.v1.ServerTickEvents.END_SERVER_TICK.register(NativeCombatScene::tickHeroLab);}
    public static void beginSession(){orphanChecks=60;orphansRemoved=0;}
    /** Recover only our unmistakable older lab targets after an interrupted session. */
    public static void recoverOrphans(MinecraftServer server){
        if(orphanChecks<=0)return;if(--orphanChecks%10!=0)return;
        for(var p:server.getPlayerManager().getPlayerList()){
            var w=p.getServerWorld();
            for(var e:w.getEntitiesByClass(VillagerEntity.class,p.getBoundingBox().expand(128),v->v.isAiDisabled()&&v.hasNoGravity()&&v.getCustomName()!=null&&v.getCustomName().getString().equals("Native projectile verification"))){
                if(e==target)continue;e.discard();orphansRemoved++;
            }
            for(var e:w.getEntitiesByClass(VillagerEntity.class,p.getBoundingBox().expand(128),v->v.getCommandTags().contains("owmc-native-tank-probe"))){
                if(e==target||beamTargets.containsValue(e))continue;e.discard();orphansRemoved++;
            }
            for(var e:w.getEntitiesByClass(net.minecraft.entity.mob.MobEntity.class,p.getBoundingBox().expand(128),v->v.getCommandTags().contains("owmc-multipart-probe")&&!TwilightForestTrial.ownsProbe(v))){e.discard();orphansRemoved++;}
            for(var e:w.getEntitiesByClass(VillagerEntity.class,p.getBoundingBox().expand(128),v->v!=target&&v.getCommandTags().contains("owmc-mei-freeze-probe"))){e.discard();orphansRemoved++;}
            for(var e:w.getEntitiesByClass(net.minecraft.entity.mob.EndermanEntity.class,p.getBoundingBox().expand(128),v->v!=target&&v.isAiDisabled()&&v.hasNoGravity()&&v.getCommandTags().contains("owmc-native-enderman-probe"))){e.discard();orphansRemoved++;}
        }
    }
    /** Reversible local lab injury; natural regeneration cannot impersonate a skill. */
    public static void sustainHurt(MinecraftServer server,java.util.UUID owner){
        cleanup();injureForHealing(server,owner);
    }
    /** Reversible fire only after an explicit isolated healing-lab injury.
     * Creates no native phase, damage or ability authority. */
    public static void sustainIgnite(MinecraftServer server,java.util.UUID owner){
        var p=server.getPlayerManager().getPlayer(owner);
        if(p==null||!p.isCreative()||p!=injuredPlayer||injuryWorld!=p.getServerWorld()
            ||!System.getProperty("owmc.worldName","").startsWith("Overwatch Twilight Switch ")){
            error="fire probe requires current isolated healing lab";return;
        }
        if(burnedPlayer==null){
            burnedPlayer=p;savedFireTicks=p.getFireTicks();savedFireInvulnerability=p.getAbilities().invulnerable;
            // Vanilla creative immunity itself clears fire. Disable only that
            // flag in this explicit disposable lab, preserving creative identity
            // and a nonlethal health margin; cleanup restores both exactly.
            p.getAbilities().invulnerable=false;p.sendAbilitiesUpdate();p.setHealth(Math.max(6,p.getHealth()));
        }
        if(burnedPlayer!=p){error="fire probe owner changed";return;}
        p.setFireTicks(200);error="";
    }
    /** Combines reversible solid landing terrain and injury without deleting the floor. */
    public static void bioticLab(MinecraftServer server,java.util.UUID owner){
        flightLab(server,owner,false);if(!error.isEmpty()||flightBase==null)return;
        locomotionOrigin(server,owner);injureForHealing(server,owner);
    }
    private static void injureForHealing(MinecraftServer server,java.util.UUID owner){
        error="";var p=server.getPlayerManager().getPlayer(owner);if(p==null||!p.isCreative()){error="healing lab requires creative player";return;}
        if(injuredPlayer!=null&&(injuredPlayer!=p||injuryWorld!=p.getServerWorld())){error="healing lab owner or world changed; cleanup required";return;}
        if(injuredPlayer==null){
            injuredPlayer=p;injuryWorld=p.getServerWorld();savedHealth=p.getHealth();savedRegeneration=injuryWorld.getGameRules().getBoolean(net.minecraft.world.GameRules.NATURAL_REGENERATION);
        }
        p.getWorld().getGameRules().get(net.minecraft.world.GameRules.NATURAL_REGENERATION).set(false,server);p.setHealth(2);
    }
    /** Injure after real healthy Recall history, preserving its reversible lane. */
    public static void recallHurt(MinecraftServer server,java.util.UUID owner){injureForHealing(server,owner);}
    /** Actual Fabric/vanilla damage path in the isolated creative lab. The
     * generic-kill source bypasses creative's ordinary immunity, with a bounded
     * nonlethal amount. It is not a direct health assignment or ability mock. */
    public static void wraithHit(MinecraftServer server,java.util.UUID owner){
        var p=server.getPlayerManager().getPlayer(owner);
        if(p==null||!p.isCreative()||p.getHealth()<5||!System.getProperty("owmc.worldName","").startsWith("Overwatch Twilight Switch ")){error="Wraith damage probe requires healthy isolated creative lab";return;}
        if(injuredPlayer!=null&&(injuredPlayer!=p||injuryWorld!=p.getServerWorld())){error="healing lab owner or world changed; cleanup required";return;}
        if(injuredPlayer==null){
            injuredPlayer=p;injuryWorld=p.getServerWorld();savedHealth=p.getHealth();savedRegeneration=injuryWorld.getGameRules().getBoolean(net.minecraft.world.GameRules.NATURAL_REGENERATION);
            injuryWorld.getGameRules().get(net.minecraft.world.GameRules.NATURAL_REGENERATION).set(false,server);
        }
        p.damage(p.getDamageSources().genericKill(),2);
    }
    /** Keep actual injury through a portal test; release the cleanup-owned heal. */
    public static void releaseInjury(){
        if(injuryWorld!=null)injuryWorld.getGameRules().get(net.minecraft.world.GameRules.NATURAL_REGENERATION).set(savedRegeneration,injuryWorld.getServer());
        injuredPlayer=null;injuryWorld=null;
    }
    /** Air-only200HP targets:360-degree Q, range and a real solid cover cube. */
    public static void reaperBlossom(MinecraftServer server,java.util.UUID owner,Vec3d eye,Vec3d direction){
        cleanup();error="";var p=server.getPlayerManager().getPlayer(owner);
        if(p==null||!p.isCreative()||!p.getAbilities().flying){error="blossom lab requires creative flight in loaded air";return;}
        world=p.getServerWorld();var forward=direction.multiply(1,0,1).normalize();var side=new Vec3d(-forward.z,0,forward.x);
        if(forward.lengthSquared()<.9){error="blossom lab needs a horizontal view";return;}
        var wall=BlockPos.ofFloored(p.getPos().add(forward.multiply(2)).add(side.multiply(2)));
        var pending=new LinkedHashMap<BlockPos,BlockState>();
        for(int x=-1;x<=1;x++)for(int z=-1;z<=1;z++)for(int y=0;y<4;y++){
            var pos=wall.add(x,y,z);if(!world.isChunkLoaded(pos)||!world.getBlockState(pos).isAir()){error="blossom cover site is not empty loaded air";return;}pending.put(pos,world.getBlockState(pos));
        }
        var positions=new LinkedHashMap<String,Vec3d>();positions.put("near",eye.add(forward.multiply(3)));positions.put("behind",eye.add(forward.multiply(-3)));positions.put("outside",eye.add(side.multiply(10)));positions.put("covered",eye.add(forward.multiply(4)).add(side.multiply(4)));
        for(var at:positions.values())if(!world.isChunkLoaded(BlockPos.ofFloored(at))||!world.isSpaceEmpty(new net.minecraft.util.math.Box(at.add(-.4,-1,-.4),at.add(.4,1,.4)))){error="blossom target site is not empty loaded air";return;}
        blocks.putAll(pending);for(var pos:pending.keySet())world.setBlockState(pos,Blocks.BEDROCK.getDefaultState());
        for(var e:positions.entrySet()){
            var mob=EntityType.VILLAGER.create(world);if(mob==null){error="blossom target creation failed";return;}var at=e.getValue();
            mob.refreshPositionAndAngles(at.x,at.y-.9,at.z,0,0);mob.setAiDisabled(true);mob.setNoGravity(true);mob.setPersistent();mob.getAttributeInstance(net.minecraft.entity.attribute.EntityAttributes.GENERIC_MAX_HEALTH).setBaseValue(200);mob.setHealth(200);mob.setCustomName(Text.literal("Blossom "+e.getKey()));mob.setCustomNameVisible(true);world.spawnEntity(mob);beamTargets.put(e.getKey(),mob);
        }
    }
    /** Reversible air-only platform above this loaded column for native flight tests. */
    public static void flightLab(MinecraftServer server,java.util.UUID owner,boolean ceiling){
        cleanup();error="";var player=server.getPlayerManager().getPlayer(owner);if(player==null)return;
        if(!player.isCreative()){error="flight lab requires creative mode";return;}
        world=player.getServerWorld();var at=player.getBlockPos();
        int surface=world.getBottomY();
        for(int x=-8;x<=8;x++)for(int z=-8;z<=8;z++){
            var column=at.add(x,0,z);if(!world.isChunkLoaded(column)){error="flight lab column is not loaded";return;}
            surface=Math.max(surface,world.getTopY(net.minecraft.world.Heightmap.Type.WORLD_SURFACE,column.getX(),column.getZ()));
        }
        int y=Math.max(at.getY()+12,surface+12);
        if(y+12>=world.getTopY()){error="no safe air volume above player";return;}
        var base=new BlockPos(at.getX(),y,at.getZ());
        var candidates=new LinkedHashMap<BlockPos,BlockState>();
        for(int x=-8;x<=8;x++)for(int z=-8;z<=8;z++)for(int up=0;up<=8;up++){
            var pos=base.add(x,up,z);
            if(!world.isChunkLoaded(pos)||!world.getBlockState(pos).isAir()){error="flight lab needs loaded air at "+pos+"; original terrain preserved";return;}
            if(up==0||(ceiling&&up==6&&Math.abs(x)<=3&&Math.abs(z)<=3)||(x==8&&up<=6))candidates.put(pos,world.getBlockState(pos));
        }
        blocks.putAll(candidates);for(var pos:blocks.keySet())world.setBlockState(pos,Blocks.BEDROCK.getDefaultState());flightBase=base;
        player.getAbilities().flying=true;player.sendAbilitiesUpdate();player.setVelocity(Vec3d.ZERO);
        player.teleport(world,base.getX()+.5,base.getY()+1,base.getZ()+.5,player.getYaw(),player.getPitch());
    }
    /** Recenter each hero on the same reversible fixture; never edit natural terrain. */
    public static void locomotionOrigin(MinecraftServer server,java.util.UUID owner){
        var p=server.getPlayerManager().getPlayer(owner);
        if(p==null||!p.isCreative()||flightBase==null||world!=p.getServerWorld()
            ||!world.getBlockState(flightBase).isOf(Blocks.BEDROCK)){error="current locomotion fixture unavailable";return;}
        p.setVelocity(Vec3d.ZERO);p.getAbilities().flying=false;p.sendAbilitiesUpdate();
        p.teleport(world,flightBase.getX()+.5,flightBase.getY()+1,flightBase.getZ()+.5,p.getYaw(),p.getPitch());
    }
    public static void start(MinecraftServer server,java.util.UUID owner,Vec3d eye,Vec3d direction){
        start(server,owner,eye,direction,6);
    }
    /** AI-active zero-walk-speed target: real vanilla velocity travel remains
     * active, unlike the deliberately immobile NoAI damage-only fixture. */
    public static void pushTarget(MinecraftServer server,java.util.UUID owner,Vec3d eye,Vec3d direction){
        start(server,owner,eye,direction,4);
        if(target!=null){target.setAiDisabled(false);var speed=target.getAttributeInstance(net.minecraft.entity.attribute.EntityAttributes.GENERIC_MOVEMENT_SPEED);if(speed!=null)speed.setBaseValue(0);}
    }
    /** HP margin and active AI only; cannot create a freeze, hit or damage. */
    public static void meiTarget(MinecraftServer server,java.util.UUID owner,Vec3d eye,Vec3d direction){
        var p=server.getPlayerManager().getPlayer(owner);
        if(p==null||!p.isCreative()||!System.getProperty("owmc.worldName","").startsWith("Overwatch Twilight Switch ")){error="Mei fixture requires isolated creative lab";return;}
        start(server,owner,eye,direction,4);
        if(target!=null){target.setAiDisabled(false);target.getAttributeInstance(net.minecraft.entity.attribute.EntityAttributes.GENERIC_MAX_HEALTH).setBaseValue(200);target.setHealth(200);target.getAttributeInstance(net.minecraft.entity.attribute.EntityAttributes.GENERIC_MOVEMENT_SPEED).setBaseValue(.5);target.addCommandTag("owmc-mei-freeze-probe");}
    }
    /** Actual vanilla velocity attempt on our sole ordinary mob, before/during/after. */
    public static void meiStruggle(MinecraftServer server,java.util.UUID owner){
        var p=server.getPlayerManager().getPlayer(owner);
        if(p==null||world!=p.getServerWorld()||target==null||!target.getCommandTags().contains("owmc-mei-freeze-probe")){error="current Mei probe unavailable";return;}
        target.setVelocity(.25,0,0);target.velocityModified=true;
    }
    public static void start(MinecraftServer server,java.util.UUID owner,Vec3d eye,Vec3d direction,double distance){
        cleanup();placeTarget(server,owner,eye,direction,distance);
    }
    /** Real target/health probe while preserving the reversible pickup floor. */
    public static void soulTarget(MinecraftServer server,java.util.UUID owner,Vec3d eye,Vec3d direction){
        var p=server.getPlayerManager().getPlayer(owner);
        if(p==null||!p.isCreative()||flightBase==null||world!=p.getServerWorld()||!p.isOnGround()){error="Soul pickup needs a current grounded air lab";return;}
        if(target!=null)target.discard();placeTarget(server,owner,eye,direction,2);if(error.isEmpty())injureForHealing(server,owner);
    }
    /** Real reversible obstruction added after a Shadow Step was confirmed. */
    public static void shadowBlock(MinecraftServer server,java.util.UUID owner){
        var p=server.getPlayerManager().getPlayer(owner);var v=NativeShadowRuntime.view;
        if(p==null||!p.isCreative()||world!=p.getServerWorld()||v==null||v.phase()!=1||v.destination()==null||!v.scope().owner().equals(owner)||v.scope().world()!=NativeWorldIdentity.of(server,p.getWorld().getRegistryKey())){error="Shadow obstruction needs a current admitted air-lab cast";return;}
        var at=BlockPos.ofFloored(v.destination());
        for(int y=0;y<2;y++)if(!world.isChunkLoaded(at.up(y))||!world.getBlockState(at.up(y)).isAir()){error="Shadow obstruction site is occupied; no blocks changed";return;}
        for(int y=0;y<2;y++){var pos=at.up(y);blocks.putIfAbsent(pos,world.getBlockState(pos));world.setBlockState(pos,Blocks.BEDROCK.getDefaultState());}
    }
    private static void placeTarget(MinecraftServer server,java.util.UUID owner,Vec3d eye,Vec3d direction,double distance){
        error="";var player=server.getPlayerManager().getPlayer(owner);if(player==null)return;
        world=player.getServerWorld();look=direction.normalize();wallCenter=eye.add(look.multiply(distance/2));var center=eye.add(look.multiply(distance));
        // Fixed villager at the observed view direction; it does not follow later shots or turns.
        var box=new net.minecraft.util.math.Box(center.x-.4,center.y-1,center.z-.4,center.x+.4,center.y+1,center.z+.4);
        if(!world.isSpaceEmpty(box)){error="target corridor is obstructed; no blocks changed";return;}
        target=EntityType.VILLAGER.create(world);if(target==null){error="villager creation failed";return;}
        target.refreshPositionAndAngles(center.x,center.y-.9,center.z,0,0);target.setAiDisabled(true);target.setNoGravity(true);target.setPersistent();target.setCustomName(Text.literal("Native projectile verification"));target.setCustomNameVisible(true);
        world.spawnEntity(target);
    }
    /** Original vanilla damage response; never overrides HP or teleport logic. */
    public static void enderman(MinecraftServer server,java.util.UUID owner,Vec3d eye,Vec3d direction,boolean melee){
        cleanup();error="";var player=server.getPlayerManager().getPlayer(owner);
        if(player==null||!player.isCreative()){error="Enderman fixture requires creative player";return;}
        world=player.getServerWorld();look=direction.normalize();var center=eye.add(look.multiply(melee?2:6));
        var mob=EntityType.ENDERMAN.create(world);if(mob==null){error="Enderman creation failed";return;}
        mob.refreshPositionAndAngles(center.x,center.y-1.45,center.z,0,0);var box=mob.getBoundingBox();
        for(var pos:BlockPos.iterate(BlockPos.ofFloored(box.minX,box.minY,box.minZ),BlockPos.ofFloored(box.maxX,box.maxY,box.maxZ)))
            if(!world.isChunkLoaded(pos)||!world.getWorldBorder().contains(pos)||pos.getY()<world.getBottomY()||pos.getY()>=world.getTopY()){error="Enderman needs loaded space inside world bounds";return;}
        if(!world.isSpaceEmpty(mob,box)){error="Enderman site occupied; original terrain preserved";return;}
        mob.setAiDisabled(true);mob.setNoGravity(true);mob.setPersistent();mob.addCommandTag("owmc-native-enderman-probe");
        mob.setCustomName(Text.literal("Native projectile verification"));mob.setCustomNameVisible(true);target=mob;
        if(!world.spawnEntity(mob)){target=null;error="Enderman spawn refused";}
    }
    public static void damageReceipt(net.minecraft.entity.Entity entity,double amount,net.minecraft.entity.damage.DamageSource source,boolean applied,double loss){
        if(target==null||entity!=target||target.getType()!=EntityType.ENDERMAN||targetReceipts.size()>=32)return;
        var row=new JsonObject();row.addProperty("entityId",entity.getId());row.addProperty("incoming",amount);row.addProperty("type",source.getName());
        row.addProperty("projectile",source.isIn(net.minecraft.registry.tag.DamageTypeTags.IS_PROJECTILE));row.addProperty("explosion",source.isIn(net.minecraft.registry.tag.DamageTypeTags.IS_EXPLOSION));
        row.addProperty("applied",applied);row.addProperty("healthLost",loss);targetReceipts.add(row);
    }
    /** Explicit fixture. Reject terrain near the blast rather than edit it. */
    public static void crystal(MinecraftServer server,java.util.UUID owner,Vec3d eye,Vec3d direction){
        cleanup();error="";var player=server.getPlayerManager().getPlayer(owner);if(player==null)return;
        world=player.getServerWorld();var center=eye.add(direction.normalize().multiply(8));var origin=BlockPos.ofFloored(center);
        for(var pos:BlockPos.iterate(origin.add(-7,-7,-7),origin.add(7,7,7)))
            if(!world.isChunkLoaded(pos)||!world.getBlockState(pos).isAir()){error="crystal fixture requires loaded empty blast radius; no blocks changed";return;}
        crystal=new net.minecraft.entity.decoration.EndCrystalEntity(world,center.x,center.y-1,center.z);
        crystal.setShowBottom(false);world.spawnEntity(crystal);
    }
    public static void wall(boolean enabled){
        restoreWall();if(!enabled||target==null||!target.isAlive())return;
        int axis=Math.abs(look.x)>Math.abs(look.y)?(Math.abs(look.x)>Math.abs(look.z)?0:2):(Math.abs(look.y)>Math.abs(look.z)?1:2);
        var center=BlockPos.ofFloored(wallCenter);
        for(int a=-1;a<=1;a++)for(int b=-1;b<=1;b++){
            var pos=center.add(axis==0?0:a,axis==1?0:(axis==0?a:b),axis==2?0:b);
            if(!world.getBlockState(pos).isAir()){restoreWall();error="wall site occupied; original blocks preserved";return;}
            blocks.put(pos,world.getBlockState(pos));world.setBlockState(pos,Blocks.STONE.getDefaultState());
        }
    }
    /** A real vanilla incoming arrow, owned by the temporary target only. */
    public static void deflectArrow(MinecraftServer server,java.util.UUID owner,boolean lethal){
        var player=server.getPlayerManager().getPlayer(owner);
        if(player==null||!player.isCreative()||target==null||!target.isAlive()||world!=player.getServerWorld()||look==null){error="Deflect fixture needs a current creative target";return;}
        if(deflectArrow!=null&&!deflectArrow.isRemoved())deflectArrow.discard();
        if(lethal)target.setHealth(1);
        deflectArrow=EntityType.ARROW.create(world);if(deflectArrow==null){error="vanilla arrow creation failed";return;}
        var eye=player.getEyePos();var start=eye.add(look.multiply(5));deflectArrow.setPosition(start);deflectArrow.setOwner(target);deflectArrow.setVelocity(look.multiply(-1.5));
        world.spawnEntity(deflectArrow);
    }
    /** Air-only blast lab. Real rockets are still required to affect it. */
    public static void rocket(MinecraftServer server,java.util.UUID owner,Vec3d eye,Vec3d direction){
        cleanup();error="";var player=server.getPlayerManager().getPlayer(owner);if(player==null)return;
        world=player.getServerWorld();look=direction.normalize();wallCenter=eye.add(look.multiply(7));
        var center=BlockPos.ofFloored(wallCenter);
        for(var pos:BlockPos.iterate(center.add(-8,-8,-8),center.add(8,8,8)))
            if(!world.isChunkLoaded(pos)||!world.getBlockState(pos).isAir()){error="rocket fixture requires loaded empty blast radius; no blocks changed";return;}
        boolean xNormal=Math.abs(look.x)>Math.abs(look.z);
        for(int side=-2;side<=2;side++)for(int up=-2;up<=2;up++){
            var pos=center.add(xNormal?0:side,up,xNormal?side:0);blocks.put(pos,world.getBlockState(pos));world.setBlockState(pos,Blocks.STONE.getDefaultState());
        }
        for(int up:new int[]{-1,1}){
            var pos=center.add(xNormal?0:up*2,up*2,xNormal?up*2:0);world.setBlockState(pos,(up==1?Blocks.BEDROCK:Blocks.OBSIDIAN).getDefaultState());
        }
        var side=new Vec3d(-look.z,0,look.x).normalize();
        var centers=new LinkedHashMap<String,Vec3d>();
        centers.put("rocketNear",wallCenter.subtract(look.multiply(1.8)).add(side.multiply(1.3)));
        centers.put("rocketOutside",wallCenter.subtract(look.multiply(1.8)).add(side.multiply(5)));
        for(var entry:centers.entrySet()){
            var entity=EntityType.VILLAGER.create(world);if(entity==null)continue;
            var at=entry.getValue();entity.refreshPositionAndAngles(at.x,at.y-.9,at.z,0,0);entity.setAiDisabled(true);entity.setNoGravity(true);entity.setPersistent();
            entity.setCustomName(Text.literal(entry.getKey()));entity.setCustomNameVisible(true);world.spawnEntity(entity);beamTargets.put(entry.getKey(),entity);
        }
    }
    /** Disposable empty-air Tank impact/splash/cover/range lab; no fake shots. */
    public static void tankCannon(MinecraftServer server,java.util.UUID owner,Vec3d eye,Vec3d direction,int mode){
        cleanup();error="";var player=server.getPlayerManager().getPlayer(owner);
        if(!Boolean.getBoolean("owmc.twilightTrial")||!System.getProperty("owmc.worldName","").startsWith("Overwatch Twilight Switch ")
            ||player==null||!player.isCreative()||!player.getAbilities().flying||mode<0||mode>2){error="cannon lab requires isolated creative flight";return;}
        world=player.getServerWorld();look=direction.normalize();
        var side=new Vec3d(-look.z,0,look.x).normalize();
        if(Math.abs(look.y)>.02||side.lengthSquared()<.99){error="cannon lab requires horizontal view";return;}
        var center=eye.add(look.multiply(mode==2?48:8));var base=BlockPos.ofFloored(center);
        var pending=new LinkedHashMap<BlockPos,BlockState>();
        for(var pos:BlockPos.iterate(base.add(-7,-3,-7),base.add(7,3,7)))
            if(!world.isChunkLoaded(pos)||!world.isSpaceEmpty(new net.minecraft.util.math.Box(pos))){error="cannon impact area occupied or unloaded; no blocks changed";return;}
        if(mode==1){
            boolean xNormal=Math.abs(look.x)>Math.abs(look.z);
            for(int lateral=-3;lateral<=3;lateral++)for(int up=-2;up<=2;up++){
                var pos=base.add(xNormal?0:lateral,up,xNormal?lateral:0);pending.put(pos,world.getBlockState(pos));
            }
        }else if(mode==0){
            // A full solid screen between the impact and covered-side victim.
            // It sits off the primary ray and is preserved by the Tank blast.
            boolean sideX=Math.abs(side.x)>Math.abs(side.z);var cover=BlockPos.ofFloored(center.add(side.multiply(2)));
            for(int along=-3;along<=3;along++)for(int up=-2;up<=2;up++){
                var pos=cover.add(sideX?0:along,up,sideX?along:0);pending.put(pos,world.getBlockState(pos));
            }
        }
        var positions=new LinkedHashMap<String,Vec3d>();
        if(mode!=1)positions.put(mode==2?"cannonFar":"cannonDirect",center);
        if(mode==0){
            positions.put("cannonNear",center.add(side.multiply(-2.2)));
            positions.put("cannonEdge",center.add(side.multiply(-4.1)));
            positions.put("cannonOutside",center.add(side.multiply(-5.5)));
            positions.put("cannonCovered",center.add(side.multiply(3.5)));
        }else if(mode==1){
            positions.put("cannonNear",center.subtract(look.multiply(1.8)).add(side.multiply(1.4)));
            positions.put("cannonOutside",center.subtract(look.multiply(1.8)).add(side.multiply(5.5)));
            positions.put("cannonBehindWall",center.add(look.multiply(1.5)));
        }
        for(var at:positions.values()){
            var box=new net.minecraft.util.math.Box(at.add(-.4,-1,-.4),at.add(.4,1,.4));
            if(!world.isChunkLoaded(BlockPos.ofFloored(at))||!world.isSpaceEmpty(box)){error="cannon target area occupied; no blocks changed";return;}
        }
        blocks.putAll(pending);for(var pos:pending.keySet())world.setBlockState(pos,Blocks.STONE.getDefaultState());
        for(var entry:positions.entrySet()){
            var entity=EntityType.VILLAGER.create(world);if(entity==null){cleanup();error="cannon target creation failed";return;}
            var at=entry.getValue();entity.refreshPositionAndAngles(at.x,at.y-.9,at.z,0,0);
            entity.setAiDisabled(true);entity.setNoGravity(true);entity.setPersistent();entity.addCommandTag("owmc-native-tank-probe");
            entity.setCustomName(Text.literal(entry.getKey()));entity.setCustomNameVisible(true);world.spawnEntity(entity);
            if(entry.getKey().equals("cannonDirect")||entry.getKey().equals("cannonFar"))target=entity;else beamTargets.put(entry.getKey(),entity);
        }
        cannonLab=true;
    }
    /** Reversible soft-block wall plus an unbreakable witness; no fake explosion. */
    public static void explosiveTerrain(MinecraftServer server,java.util.UUID owner,Vec3d eye,Vec3d direction){
        cleanup();error="";var p=server.getPlayerManager().getPlayer(owner);
        if(!Boolean.getBoolean("owmc.twilightTrial")||!System.getProperty("owmc.worldName","").startsWith("Overwatch Twilight Switch ")
            ||p==null||!p.isCreative()||!p.getAbilities().flying){error="explosion lab requires isolated creative flight";return;}
        world=p.getServerWorld();look=direction.normalize();
        if(Math.abs(look.y)>.02){error="explosion lab requires horizontal view";return;}
        var base=BlockPos.ofFloored(eye.add(look.multiply(4)));boolean xNormal=Math.abs(look.x)>Math.abs(look.z);
        var pending=new LinkedHashMap<BlockPos,BlockState>();
        for(int side=-2;side<=2;side++)for(int up=-2;up<=2;up++){
            var at=base.add(xNormal?0:side,up,xNormal?side:0);
            if(!world.isChunkLoaded(at)||!world.getBlockState(at).isAir()){error="explosion fixture area occupied or unloaded";return;}
            pending.put(at,world.getBlockState(at));
        }
        blocks.putAll(pending);for(var at:pending.keySet())world.setBlockState(at,Blocks.GLASS.getDefaultState());
        world.setBlockState(base.add(xNormal?0:1,0,xNormal?1:0),Blocks.BEDROCK.getDefaultState());
    }
    /** Temporary 3-by-4 mantle wall and an air-only landing platform for flying tests. */
    /** Reversible 25x25 stone floor directly under the player, flight off: grounded skill fixture. Air only. */
    public static void groundLab(MinecraftServer server,java.util.UUID owner){
        cleanup();error="";var player=server.getPlayerManager().getPlayer(owner);if(player==null||!player.isCreative()){error="ground lab requires creative player";return;}
        world=player.getServerWorld();var floor=BlockPos.ofFloored(player.getPos()).down();
        // The player's own 3x3x2 standing volume must have no collision; search upward (<=40) for one.
        BlockPos found=null;
        for(int up=0;up<=40&&found==null;up++){var f=floor.up(up);boolean ok=true;
            for(int x=-1;x<=1&&ok;x++)for(int z=-1;z<=1&&ok;z++)for(int y=1;y<=2&&ok;y++){var q=f.add(x,y,z);
                ok=world.isChunkLoaded(q)&&world.getBlockState(q).getCollisionShape(world,q).isEmpty();}
            if(ok)found=f;}
        if(found==null){error="ground lab found no clear standing volume";return;}
        floor=found;player.requestTeleport(floor.getX()+.5,floor.getY()+1,floor.getZ()+.5);player.setVelocity(Vec3d.ZERO);player.fallDistance=0;
        for(int x=-12;x<=12;x++)for(int z=-12;z<=12;z++){var pos=floor.add(x,0,z);
            if(world.isChunkLoaded(pos)&&world.getBlockState(pos).isAir()){blocks.putIfAbsent(pos,world.getBlockState(pos));world.setBlockState(pos,Blocks.STONE.getDefaultState());}}
        player.getAbilities().flying=false;player.sendAbilitiesUpdate();
    }
    /** 美实测：地面实验场 + 前方 5 格一个固定村民（暴雪/冰冻目标）。 */
    public static void meiLab(MinecraftServer server,java.util.UUID owner,Vec3d direction){meiLab(server,owner,direction,5);}
    public static void meiLab(MinecraftServer server,java.util.UUID owner,Vec3d direction,double distance){
        groundLab(server,owner);if(!error.isEmpty())return;var player=server.getPlayerManager().getPlayer(owner);
        var h=new Vec3d(direction.x,0,direction.z);if(h.lengthSquared()<1e-4)h=new Vec3d(1,0,0);
        placeTarget(server,owner,new Vec3d(player.getX(),player.getY()+1.62,player.getZ()),h.normalize(),distance);
    }
    /** 语音实测专用：mei-lab 目标设为静音，避免村民受伤/死亡声与击杀语音叠在一起干扰音频相关性。 */
    public static void meiLabSilent(MinecraftServer server,java.util.UUID owner,Vec3d direction){
        meiLab(server,owner,direction);if(error.isEmpty()&&target!=null)target.setSilent(true);
    }
    /** New8 fixtures only: ordinary entities/terrain, never native nodes or module calls.
     * All setup is reversible through the same ground/mei/cleanup ownership as older labs. */
    public static void heroLab(MinecraftServer server,java.util.UUID owner,Vec3d direction,String name){
        var p=server.getPlayerManager().getPlayer(owner);
        if(p==null||!p.isCreative()||!Boolean.getBoolean("owmc.twilightTrial")
            ||!System.getProperty("owmc.worldName","").startsWith("Overwatch Twilight Switch ")){
            error="hero fixture requires isolated creative Switch lab";return;
        }
        var h=direction.multiply(1,0,1);
        if(h.lengthSquared()<.01){error="hero fixture requires horizontal aim";return;}h=h.normalize();
        double distance=switch(name){
            case "mercy-far","zen-body","zen-covered"->16;
            case "roadhog-hook","roadhog-hook-wall"->12;
            case "reinhardt-lab","reinhardt-cover-lab"->3;
            case "roadhog-secondary"->4;
            case "roadhog-split-lab"->12;
            default->5;
        };
        boolean shield=name.equals("reinhardt-shield-lab")||name.equals("zarya-shield-lab");
        boolean heal=name.equals("roadhog-heal");
        cleanup();error="";
        int extent=(int)Math.max(12,distance+2);
        if(!heroGroundOrigin(p,extent))return;
        if(shield||heal)groundLab(server,owner);else meiLab(server,owner,h,distance);
        if(!error.isEmpty())return;
        heroLab=name;
        // Extend the existing 25x25 safe floor for 12/16m targets; never replace terrain.
        var floor=p.getBlockPos().down();
        for(int x=-extent;x<=extent;x++)for(int z=-extent;z<=extent;z++){
            var at=floor.add(x,0,z);
            if(world.getBlockState(at).isAir()){blocks.putIfAbsent(at,world.getBlockState(at));world.setBlockState(at,Blocks.STONE.getDefaultState());}
        }
        if(target!=null)configureHeroTarget(target,name.startsWith("zen-")||name.startsWith("roadhog-")||name.startsWith("dva-")?200:20);
        switch(name){
            case "mercy-support","mercy-covered","mercy-far","mercy-hostile","mercy-foreign","lucio-support"->supportHeroLab(p,h,name);
            case "zen-covered","reinhardt-cover-lab","zarya-cover-lab","roadhog-hook-wall","dva-pistol-wall"->heroCover(p,p.getEyePos().add(h.multiply(distance/2)),h,2);
            case "reinhardt-shield-lab","zarya-shield-lab"->beginShieldProbe(server,p,h);
            case "roadhog-heal"->{
                injureForHealing(server,owner);
                heroMaxPlayer=p;var max=p.getAttributeInstance(net.minecraft.entity.attribute.EntityAttributes.GENERIC_MAX_HEALTH);
                heroSavedMaxHealth=max.getBaseValue();max.setBaseValue(Math.max(40,heroSavedMaxHealth));p.setHealth(5);
                // Normal native-health coupling remains active; no fixture tick writes HP.
            }
            case "roadhog-split-lab"->{}
            case "roadhog-q"->replaceHeroTarget(EntityType.RAVAGER,200,new Vec3d(target.getX(),p.getY(),target.getZ()));
            case "symmetra-placement"->{
                // A separate hostile is off the placement ray, within 10m of the floor hit.
                var side=new Vec3d(-h.z,0,h.x);
                replaceHeroTarget(EntityType.HUSK,200,p.getPos().add(h.multiply(5)).add(side.multiply(3)));
            }
            case "zen-body","reinhardt-lab","zarya-lab","roadhog-scatter","roadhog-secondary","roadhog-hook","dva-pistol","dva-pilot-attempt"->{}
            default->error="unknown hero fixture: "+name;
        }
        if(!error.isEmpty()){var failure=error;cleanup();error=failure;}
    }
    /** Find loaded empty air above this column before calling the existing ground lab.
     * The entire corridor (including far targets, cover and incoming arrows) is checked. */
    private static boolean heroGroundOrigin(net.minecraft.server.network.ServerPlayerEntity p,int extent){
        var w=p.getServerWorld();var initial=p.getBlockPos().down();
        for(int x=-extent;x<=extent;x++)for(int z=-extent;z<=extent;z++){
            var at=initial.add(x,0,z);
            if(!w.isChunkLoaded(at)||!w.getWorldBorder().contains(at)){error="hero corridor is unloaded or outside world border";return false;}
        }
        for(int up=0;up<=40;up++){
            var floor=initial.up(up);if(floor.getY()<w.getBottomY()||floor.getY()+5>=w.getTopY())continue;
            boolean clear=true;
            for(int x=-extent;x<=extent&&clear;x++)for(int z=-extent;z<=extent&&clear;z++){
                var state=w.getBlockState(floor.add(x,0,z));
                clear=state.isAir()||state.isOf(Blocks.STONE)||state.isOf(Blocks.DIRT)||state.isOf(Blocks.GRASS_BLOCK);
                for(int y=1;y<=4&&clear;y++)clear=w.getBlockState(floor.add(x,y,z)).isAir();
            }
            if(!clear)continue;
            var volume=new net.minecraft.util.math.Box(Vec3d.of(floor.add(-extent,1,-extent)),Vec3d.of(floor.add(extent+1,5,extent+1)));
            if(!w.getOtherEntities(p,volume,e->e instanceof net.minecraft.entity.LivingEntity&&e.isAlive()).isEmpty())continue;
            p.requestTeleport(floor.getX()+.5,floor.getY()+1,floor.getZ()+.5);p.setVelocity(Vec3d.ZERO);p.fallDistance=0;return true;
        }
        error="hero lab found no loaded empty corridor within 40 blocks; original terrain preserved";return false;
    }
    private static void configureHeroTarget(net.minecraft.entity.mob.MobEntity mob,double maxHealth){
        mob.setAiDisabled(true);mob.setNoGravity(true);mob.setPersistent();mob.setSilent(true);
        mob.clearStatusEffects();mob.setAbsorptionAmount(0);
        mob.getAttributeInstance(net.minecraft.entity.attribute.EntityAttributes.GENERIC_MAX_HEALTH).setBaseValue(maxHealth);
        for(var attr:java.util.List.of(net.minecraft.entity.attribute.EntityAttributes.GENERIC_ARMOR,net.minecraft.entity.attribute.EntityAttributes.GENERIC_ARMOR_TOUGHNESS)){
            var instance=mob.getAttributeInstance(attr);if(instance!=null)instance.setBaseValue(0);
        }
        mob.setHealth((float)maxHealth);mob.addCommandTag("owmc-new8-hero-probe");
    }
    private static net.minecraft.entity.mob.MobEntity spawnHeroTarget(EntityType<? extends net.minecraft.entity.mob.MobEntity> type,Vec3d feet,double maxHealth){
        var mob=type.create(world);if(mob==null){error="hero target creation failed";return null;}
        mob.refreshPositionAndAngles(feet.x,feet.y,feet.z,0,0);configureHeroTarget(mob,maxHealth);
        mob.setCustomName(Text.literal("New8 "+heroLab));mob.setCustomNameVisible(true);
        if(!world.isChunkLoaded(mob.getBlockPos())||!world.isSpaceEmpty(mob,mob.getBoundingBox())||!world.spawnEntity(mob)){
            mob.discard();error="hero target site occupied or spawn refused";return null;
        }return mob;
    }
    private static void replaceHeroTarget(EntityType<? extends net.minecraft.entity.mob.MobEntity> type,double maxHealth,Vec3d feet){
        if(target!=null)target.discard();target=spawnHeroTarget(type,feet,maxHealth);
    }
    /** Adds cover without wall(true), whose legacy restore would remove the safe floor. */
    private static void heroCover(net.minecraft.server.network.ServerPlayerEntity p,Vec3d center,Vec3d normal,int radius){
        boolean xNormal=Math.abs(normal.x)>Math.abs(normal.z);
        var base=new BlockPos(BlockPos.ofFloored(center).getX(),p.getBlockY(),BlockPos.ofFloored(center).getZ());
        var pending=new LinkedHashMap<BlockPos,BlockState>();
        for(int side=-radius;side<=radius;side++)for(int y=0;y<4;y++){
            var at=base.add(xNormal?0:side,y,xNormal?side:0);
            if(!world.isChunkLoaded(at)||!world.getBlockState(at).isAir()){error="hero cover site occupied; original blocks preserved";return;}
            pending.put(at,world.getBlockState(at));
        }
        for(var entry:pending.entrySet()){
            blocks.putIfAbsent(entry.getKey(),entry.getValue());world.setBlockState(entry.getKey(),Blocks.STONE.getDefaultState());
        }
    }
    private static void supportHeroLab(net.minecraft.server.network.ServerPlayerEntity p,Vec3d h,String name){
        target.setHealth(4);
        if(name.equals("mercy-hostile")){var at=target.getPos();replaceHeroTarget(EntityType.HUSK,20,at);if(target!=null)target.setHealth(4);return;}
        if(name.equals("mercy-covered")){heroCover(p,p.getEyePos().add(h.multiply(2.5)),h,2);return;}
        if(name.equals("mercy-foreign"))target.addStatusEffect(new net.minecraft.entity.effect.StatusEffectInstance(net.minecraft.entity.effect.StatusEffects.STRENGTH,600,1,false,false));
        if(!name.equals("mercy-support")&&!name.equals("lucio-support"))return;
        var side=new Vec3d(-h.z,0,h.x);var covered=p.getEyePos().add(h.multiply(5)).add(side.multiply(4));
        var ally=spawnHeroTarget(EntityType.VILLAGER,covered.add(0,-.9,0),20);
        if(ally==null)return;ally.setHealth(4);beamTargets.put("covered",(VillagerEntity)ally);
        var hostile=spawnHeroTarget(EntityType.HUSK,p.getEyePos().add(h.multiply(5)).add(side.multiply(-4)).add(0,-.9,0),20);
        if(hostile==null)return;hostile.setHealth(4);heroTargets.put("hostile",hostile);
        heroCover(p,p.getEyePos().lerp(covered,.5),h,1);
    }
    /** Keep Suite's creative/invulnerable/full-HP identity throughout both probes.
     * Reinhardt: real vanilla arrows, counted only when embedded in BARRIER.
     * Zarya: explicit MC damage probe, not an ordinary-arrow acceptance. Vanilla
     * generic_kill bypasses creative immunity but still consumes absorption in 1.21.1.
     * Never damage an unshielded player, grant absorption, or call a hero module. */
    private static void beginShieldProbe(MinecraftServer server,net.minecraft.server.network.ServerPlayerEntity p,Vec3d h){
        if(shieldPlayer!=null)cleanupHeroLab();  // 保留已有的前一轮探针回收保护
        if(!p.isCreative()||!p.getAbilities().invulnerable||p.getHealth()!=p.getMaxHealth()){
            error="shield probe requires creative invulnerable full-health owner";return;
        }
        if(heroLab.equals("zarya-shield-lab")&&p.getAbsorptionAmount()!=0){
            error="Zarya absorption probe requires no pre-existing absorption";return;
        }
        shieldPlayer=p;shieldSavedMode=p.interactionManager.getGameMode();
        shieldSavedInvulnerable=p.getAbilities().invulnerable;shieldSavedFlying=p.getAbilities().flying;shieldSavedAllowFlying=p.getAbilities().allowFlying;
        shieldLastHealth=p.getHealth();shieldOrigin=p.getEyePos().add(h.multiply(8));shieldVelocity=h.multiply(-1.5);
        shieldAge=shieldShots=shieldBlocked=shieldDamageAttempts=0;shieldPlayerDamage=shieldDamageAbsorbed=0;shieldDamageReceipts.asList().clear();
    }
    private static void tickHeroLab(MinecraftServer server){
        var p=shieldPlayer;if(p==null||p.getServer()!=server)return;
        if(!p.isAlive()||p.getServerWorld()!=world){error="shield probe owner died or changed world";return;}
        shieldPlayerDamage+=Math.max(0,shieldLastHealth-p.getHealth());shieldLastHealth=p.getHealth();shieldAge++;
        if(heroLab.equals("zarya-shield-lab")){
            // Fixed independent schedule, spaced beyond vanilla hurt immunity. Only actual
            // absorption can admit a bounded damage call; there are no fixture HP writes.
            if(shieldAge==12||shieldAge==24||shieldAge==36){
                float before=p.getAbsorptionAmount(),hp=p.getHealth();
                if(before>=1&&p.isCreative()&&p.getAbilities().invulnerable&&hp==p.getMaxHealth()){
                    shieldDamageAttempts++;boolean applied=p.damage(p.getDamageSources().genericKill(),1);
                    double consumed=Math.max(0,before-p.getAbsorptionAmount());shieldDamageAbsorbed+=consumed;
                    var receipt=new JsonObject();receipt.addProperty("applied",applied);receipt.addProperty("beforeAbsorption",before);
                    receipt.addProperty("afterAbsorption",p.getAbsorptionAmount());receipt.addProperty("healthLost",Math.max(0,hp-p.getHealth()));shieldDamageReceipts.add(receipt);
                }
            }
            return;
        }
        if(shieldShots<3&&shieldAge==12+shieldShots*6){
            var arrow=EntityType.ARROW.create(world);
            if(arrow==null){error="shield probe arrow creation failed";return;}
            arrow.setPosition(shieldOrigin);arrow.setVelocity(shieldVelocity);arrow.setDamage(.5);
            arrow.pickupType=net.minecraft.entity.projectile.PersistentProjectileEntity.PickupPermission.DISALLOWED;
            if(world.spawnEntity(arrow)){shieldArrows.put(arrow,false);shieldShots++;}else error="shield probe arrow spawn refused";
        }
        for(var entry:shieldArrows.entrySet()){
            var arrow=entry.getKey();if(arrow.isRemoved()||entry.getValue())continue;
            // Vanilla serializes the actual embedded block state. A planned ray intersection
            // or a live module report is deliberately insufficient to count a blocked shot.
            var nbt=arrow.writeNbt(new net.minecraft.nbt.NbtCompound());
            if(nbt.getBoolean("inGround")&&nbt.getCompound("inBlockState").getString("Name").equals("minecraft:barrier")){
                shieldBlocked++;entry.setValue(true);
            }
            if(shieldAge>80)arrow.discard();
        }
    }
    /** 测试世界是创造模式实验场：cleanup 时把被场景留在生存/掉血状态的玩家恢复为创造满血。 */
    public static void restoreCreative(net.minecraft.server.network.ServerPlayerEntity p){
        if(p==null||!p.isAlive())return;
        if(p.interactionManager.getGameMode()!=net.minecraft.world.GameMode.CREATIVE)p.changeGameMode(net.minecraft.world.GameMode.CREATIVE);
        p.getAbilities().invulnerable=true;p.sendAbilitiesUpdate();p.setHealth(p.getMaxHealth());
    }
    private static void cleanupHeroLab(){
        for(var arrow:shieldArrows.keySet())arrow.discard();shieldArrows.clear();
        if(shieldPlayer!=null){
            shieldPlayer.changeGameMode(shieldSavedMode);shieldPlayer.getAbilities().invulnerable=shieldSavedInvulnerable;
            shieldPlayer.getAbilities().flying=shieldSavedFlying;shieldPlayer.getAbilities().allowFlying=shieldSavedAllowFlying;shieldPlayer.sendAbilitiesUpdate();shieldPlayer=null;
        }
        if(heroMaxPlayer!=null){heroMaxPlayer.getAttributeInstance(net.minecraft.entity.attribute.EntityAttributes.GENERIC_MAX_HEALTH).setBaseValue(heroSavedMaxHealth);heroMaxPlayer=null;}
        for(var mob:heroTargets.values())mob.discard();heroTargets.clear();heroLab="";
        shieldAge=shieldShots=shieldBlocked=shieldDamageAttempts=0;shieldPlayerDamage=shieldDamageAbsorbed=0;shieldDamageReceipts.asList().clear();shieldOrigin=shieldVelocity=null;
    }
    private static void addHeroStatus(JsonObject out){
        if(heroLab.isEmpty())return;out.addProperty("heroLab",heroLab);
        if(target!=null)out.addProperty("targetMaxHealth",target.getMaxHealth());
        if(!heroTargets.isEmpty()){
            var group=out.has("beamTargets")?out.getAsJsonObject("beamTargets"):new JsonObject();
            for(var entry:heroTargets.entrySet())group.addProperty(entry.getKey(),entry.getValue().getHealth());out.add("beamTargets",group);
        }
        if(heroLab.startsWith("mercy-")&&target!=null){
            var support=new JsonObject();var strength=target.getStatusEffect(net.minecraft.entity.effect.StatusEffects.STRENGTH);
            support.addProperty("strengthAmplifier",strength==null?-1:strength.getAmplifier());support.addProperty("strengthTicks",strength==null?0:strength.getDuration());out.add("supportLab",support);
        }
        if(heroLab.equals("lucio-support")){
            var support=new JsonObject();supportStatus(support,"friend",target);supportStatus(support,"occluded",beamTargets.get("covered"));supportStatus(support,"enemy",heroTargets.get("hostile"));out.add("lucioSupport",support);
        }
        if(shieldPlayer!=null){
            var probe=new JsonObject();probe.addProperty("shots",shieldShots);probe.addProperty("blocked",shieldBlocked);probe.addProperty("playerDamage",shieldPlayerDamage);
            probe.addProperty("mode",heroLab.equals("zarya-shield-lab")?"creative-absorption-damage":"creative-barrier-arrows");
            probe.addProperty("playerCreative",shieldPlayer.isCreative());probe.addProperty("playerInvulnerable",shieldPlayer.getAbilities().invulnerable);probe.addProperty("playerMaxHealth",shieldPlayer.getMaxHealth());
            probe.addProperty("damageSource",heroLab.equals("zarya-shield-lab")?"minecraft:generic_kill":"minecraft:arrow");
            probe.addProperty("damageAttempts",shieldDamageAttempts);probe.addProperty("absorptionConsumed",shieldDamageAbsorbed);probe.add("damageReceipts",shieldDamageReceipts.deepCopy());
            probe.addProperty("playerHealth",shieldPlayer.getHealth());probe.addProperty("playerAbsorption",shieldPlayer.getAbsorptionAmount());out.add("shieldProbe",probe);
        }
        if(heroMaxPlayer!=null){out.addProperty("ownerHealth",heroMaxPlayer.getHealth());out.addProperty("ownerMaxHealth",heroMaxPlayer.getMaxHealth());}
    }
    private static void supportStatus(JsonObject out,String prefix,net.minecraft.entity.mob.MobEntity mob){
        if(mob==null)return;out.addProperty(prefix+"Health",mob.getHealth());out.addProperty(prefix+"Absorption",mob.getAbsorptionAmount());
        out.addProperty(prefix+"Speed",mob.getAttributeValue(net.minecraft.entity.attribute.EntityAttributes.GENERIC_MOVEMENT_SPEED));
        out.addProperty(prefix+"BaseSpeed",mob.getAttributeBaseValue(net.minecraft.entity.attribute.EntityAttributes.GENERIC_MOVEMENT_SPEED));
        var speed=mob.getStatusEffect(net.minecraft.entity.effect.StatusEffects.SPEED);
        out.addProperty(prefix+"SpeedAmplifier",speed==null?-1:speed.getAmplifier());out.addProperty(prefix+"SpeedTicks",speed==null?0:speed.getDuration());
    }
    /** Reversible 5x5 stone wall 10 blocks ahead: Grappling Hook pull-distance fixture. Air only. */
    public static void grappleWall(MinecraftServer server,java.util.UUID owner,Vec3d eye,Vec3d direction){
        cleanup();error="";var player=server.getPlayerManager().getPlayer(owner);if(player==null||!player.isCreative()){error="grapple fixture requires creative player";return;}
        world=player.getServerWorld();var h=new Vec3d(direction.x,0,direction.z);
        if(h.lengthSquared()<.81){error="grapple fixture needs a horizontal view";return;}
        h=h.normalize();var center=BlockPos.ofFloored(eye.add(h.multiply(10)));boolean xNormal=Math.abs(h.x)>Math.abs(h.z);
        var planned=new LinkedHashMap<BlockPos,BlockState>();
        for(int a=-2;a<=2;a++)for(int y=-2;y<=2;y++){
            var pos=xNormal?center.add(0,y,a):center.add(a,y,0);
            if(!world.isChunkLoaded(pos)||!world.getBlockState(pos).isAir()){error="grapple wall site occupied; no blocks changed";return;}
            planned.put(pos,world.getBlockState(pos));
        }
        for(var e:planned.entrySet()){blocks.putIfAbsent(e.getKey(),e.getValue());world.setBlockState(e.getKey(),Blocks.STONE.getDefaultState());}
    }
    /** Fixed probe villager 1.5 blocks from the current stuck Venom Mine (toward the owner). */
    public static void venomTarget(MinecraftServer server,java.util.UUID owner){
        error="";var player=server.getPlayerManager().getPlayer(owner);var v=NativeVenomRuntime.view;
        if(player==null||!player.isCreative()||v==null||!v.stuck()||!v.owner().equals(owner)){error="no stuck Venom Mine for this player";return;}
        if(world!=null&&world!=player.getServerWorld()&&!blocks.isEmpty()){error="venom target: fixture blocks belong to another world; run cleanup first";return;}
        world=player.getServerWorld();var toward=player.getPos().subtract(v.at());toward=new Vec3d(toward.x,0,toward.z);
        if(toward.lengthSquared()<1e-4)toward=new Vec3d(1,0,0);
        var at=v.at().add(toward.normalize().multiply(1.5)).add(v.normal().multiply(.05));
        var mob=EntityType.VILLAGER.create(world);if(mob==null){error="villager creation failed";return;}
        mob.refreshPositionAndAngles(at.x,at.y,at.z,0,0);
        if(!world.isSpaceEmpty(mob,mob.getBoundingBox())){error="venom target site occupied";return;}
        if(target!=null)target.discard();
        mob.setAiDisabled(true);mob.setNoGravity(true);mob.setPersistent();mob.setCustomName(Text.literal("Native projectile verification"));mob.setCustomNameVisible(true);
        target=mob;world.spawnEntity(mob);
    }
    public static void climbWall(MinecraftServer server,java.util.UUID owner,Vec3d feet,Vec3d direction){
        cleanup();error="";var player=server.getPlayerManager().getPlayer(owner);if(player==null)return;
        world=player.getServerWorld();
        var horizontal=new Vec3d(direction.x,0,direction.z).normalize();
        if(horizontal.lengthSquared()<.9){error="climb fixture needs a horizontal view";return;}
        var center=BlockPos.ofFloored(feet.add(horizontal.multiply(3)));
        boolean xNormal=Math.abs(horizontal.x)>Math.abs(horizontal.z);
        var candidates=new LinkedHashMap<BlockPos,BlockState>();
        if(player.getAbilities().flying){
            var floor=BlockPos.ofFloored(feet).down();
            for(int x=-2;x<=2;x++)for(int z=-2;z<=2;z++){
                var pos=floor.add(x,0,z);
                if(!world.isChunkLoaded(pos)||!world.getBlockState(pos).isAir()){
                    error="climb platform site occupied; original blocks preserved";return;
                }
                candidates.put(pos,world.getBlockState(pos));
            }
        }
        for(int side=-1;side<=1;side++)for(int up=0;up<4;up++){
            var pos=center.add(xNormal?0:side,up,xNormal?side:0);
            if(!world.isChunkLoaded(pos)||!world.getBlockState(pos).isAir()){
                error="climb wall site occupied; original blocks preserved";return;
            }
            candidates.put(pos,world.getBlockState(pos));
        }
        blocks.putAll(candidates);
        for(var pos:blocks.keySet())world.setBlockState(pos,Blocks.STONE.getDefaultState());
    }
    /** Air-only flat lane and end wall for measuring roll distance/collision. */
    public static void rollLane(MinecraftServer server,java.util.UUID owner,Vec3d feet,Vec3d direction){
        cleanup();error="";var player=server.getPlayerManager().getPlayer(owner);if(player==null)return;
        world=player.getServerWorld();
        if(!player.getAbilities().flying){error="roll lane requires flight in an empty volume";return;}
        var base=BlockPos.ofFloored(feet).down();var candidates=new LinkedHashMap<BlockPos,BlockState>();
        boolean xNormal=Math.abs(direction.x)>Math.abs(direction.z);int sign=(xNormal?direction.x:direction.z)<0?-1:1;
        for(int x=-8;x<=8;x++)for(int z=-8;z<=8;z++)for(int y=0;y<=3;y++){
            var at=base.add(x,y,z);
            if(!world.isChunkLoaded(at)||!world.getBlockState(at).isAir()){error="roll lane site occupied; original blocks preserved";return;}
            if(y==0||(xNormal?x:z)==8*sign)candidates.put(at,world.getBlockState(at));
        }
        blocks.putAll(candidates);for(var pos:blocks.keySet())world.setBlockState(pos,Blocks.STONE.getDefaultState());
    }
    /** Four stationary targets exercise multi-target, range and cone admission. */
    public static void beam(MinecraftServer server,java.util.UUID owner,Vec3d eye,Vec3d direction){
        cleanup();error="";var player=server.getPlayerManager().getPlayer(owner);if(player==null)return;
        world=player.getServerWorld();look=direction.normalize();
        var side=new Vec3d(-look.z,0,look.x).normalize();
        if(side.lengthSquared()<.9){error="beam fixture needs a horizontal view";return;}
        var centers=new LinkedHashMap<String,Vec3d>();
        centers.put("inside4",eye.add(look.multiply(4)));
        centers.put("inside6",eye.add(look.multiply(6)));
        centers.put("outsideRange9",eye.add(look.multiply(9)));
        centers.put("outsideAngle30",eye.add(look.multiply(6*Math.cos(Math.toRadians(30)))).add(side.multiply(3)));
        for(var center:centers.values()){
            var box=new net.minecraft.util.math.Box(center.x-.4,center.y-1,center.z-.4,center.x+.4,center.y+1,center.z+.4);
            if(!world.isChunkLoaded(BlockPos.ofFloored(center))||!world.isSpaceEmpty(box)){error="beam target site occupied; original blocks preserved";return;}
        }
        for(var entry:centers.entrySet()){
            var entity=EntityType.VILLAGER.create(world);if(entity==null){cleanup();error="beam villager creation failed";return;}
            var center=entry.getValue();entity.refreshPositionAndAngles(center.x,center.y-.9,center.z,0,0);
            entity.setAiDisabled(true);entity.setNoGravity(true);entity.setPersistent();entity.setCustomName(Text.literal(entry.getKey()));entity.setCustomNameVisible(true);
            world.spawnEntity(entity);beamTargets.put(entry.getKey(),entity);
        }
    }
    /** More than six real targets, including armor/resistance/absorption. */
    public static void deadeyeCrowd(MinecraftServer server,java.util.UUID owner,Vec3d eye,Vec3d direction){
        cleanup();error="";var player=server.getPlayerManager().getPlayer(owner);if(player==null||!player.isCreative())return;
        world=player.getServerWorld();look=direction.normalize();var side=new Vec3d(-look.z,0,look.x).normalize();
        if(side.lengthSquared()<.9){error="deadeye fixture needs horizontal view";return;}
        for(int i=0;i<12;i++){
            var at=eye.add(look.multiply(i<6?12:19)).add(side.multiply((i%6-2.5)*2.6));
            if(!world.isChunkLoaded(BlockPos.ofFloored(at))||!world.isSpaceEmpty(new net.minecraft.util.math.Box(at.x-.4,at.y-1,at.z-.4,at.x+.4,at.y+1,at.z+.4))){cleanup();error="crowd fixture needs loaded empty space";return;}
            var entity=EntityType.VILLAGER.create(world);if(entity==null){cleanup();error="crowd villager creation failed";return;}
            entity.refreshPositionAndAngles(at.x,at.y-.9,at.z,0,0);entity.setAiDisabled(true);entity.setNoGravity(true);entity.setPersistent();
            if(i%3==0){entity.getAttributeInstance(net.minecraft.entity.attribute.EntityAttributes.GENERIC_ARMOR).setBaseValue(20);entity.getAttributeInstance(net.minecraft.entity.attribute.EntityAttributes.GENERIC_ARMOR_TOUGHNESS).setBaseValue(8);}
            if(i%4==0)entity.addStatusEffect(new net.minecraft.entity.effect.StatusEffectInstance(net.minecraft.entity.effect.StatusEffects.RESISTANCE,400,0));
            if(i%5==0)entity.setAbsorptionAmount(4);
            String name="Deadeye crowd "+i;entity.setCustomName(Text.literal(name));entity.setCustomNameVisible(true);world.spawnEntity(entity);beamTargets.put(name,entity);
        }
    }
    private static void restoreWall(){if(world!=null)for(var e:blocks.entrySet()){
        var state=world.getBlockState(e.getKey());
        if(state.isOf(Blocks.STONE)||state.isOf(Blocks.OBSIDIAN)||state.isOf(Blocks.BEDROCK)||state.isOf(Blocks.GLASS))world.setBlockState(e.getKey(),e.getValue());
    }blocks.clear();}
    public static void cleanup(){
        SupportCommitFixtures.cleanup();
        SymmetraLab.cleanup();
        // integrator: idempotent with explicit HTTP/close cleanup; also reclaim on fixture switches.
        NativeBuildersLab.cleanup();
        cleanupHeroLab();
        if(burnedPlayer!=null){burnedPlayer.setFireTicks(savedFireTicks);burnedPlayer.getAbilities().invulnerable=savedFireInvulnerability;burnedPlayer.sendAbilitiesUpdate();burnedPlayer=null;}
        if(injuredPlayer!=null){if(injuredPlayer.isAlive())injuredPlayer.setHealth(savedHealth);var rule=injuryWorld.getGameRules().get(net.minecraft.world.GameRules.NATURAL_REGENERATION);rule.set(savedRegeneration,injuryWorld.getServer());injuredPlayer=null;injuryWorld=null;}
        restoreWall();flightBase=null;cannonLab=false;if(deflectArrow!=null&&!deflectArrow.isRemoved())deflectArrow.discard();deflectArrow=null;if(target!=null)target.discard();target=null;targetReceipts=new JsonArray();if(crystal!=null&&!crystal.isRemoved())crystal.discard();crystal=null;for(var entity:beamTargets.values())entity.discard();beamTargets.clear();world=null;
    }
    public static void addStatus(MinecraftServer server,JsonObject out){
        out.addProperty("testError",error);out.addProperty("wallBlocks",blocks.size());
        out.addProperty("cannonLab",cannonLab);
        if(burnedPlayer!=null){out.addProperty("testFireTicks",burnedPlayer.getFireTicks());out.addProperty("testBurning",burnedPlayer.isOnFire());out.addProperty("testFireInvulnerable",burnedPlayer.getAbilities().invulnerable);}
        out.addProperty("testOrphansRemoved",orphansRemoved);
        if(flightBase!=null){out.addProperty("flightFloorY",flightBase.getY()+1);out.addProperty("flightRoofY",flightBase.getY()+6);}
        if(world!=null&&!blocks.isEmpty()){
            out.addProperty("testGlassRemaining",blocks.keySet().stream().filter(pos->world.getBlockState(pos).isOf(Blocks.GLASS)).count());
            out.addProperty("testStoneRemaining",blocks.keySet().stream().filter(pos->world.getBlockState(pos).isOf(Blocks.STONE)).count());
            out.addProperty("testProtectedRemaining",blocks.keySet().stream().filter(pos->world.getBlockState(pos).isOf(Blocks.BEDROCK)||world.getBlockState(pos).isOf(Blocks.OBSIDIAN)).count());
        }
        if(crystal!=null){out.addProperty("crystalAlive",crystal.isAlive());out.addProperty("crystalRemoved",crystal.isRemoved());}
        if(deflectArrow!=null){out.addProperty("testArrowAlive",!deflectArrow.isRemoved());out.addProperty("testArrowOwnerPlayer",deflectArrow.getOwner() instanceof net.minecraft.server.network.ServerPlayerEntity);}
        if(target!=null){out.addProperty("targetMovementSpeed",target.getAttributeValue(net.minecraft.entity.attribute.EntityAttributes.GENERIC_MOVEMENT_SPEED));out.addProperty("targetBaseMovementSpeed",target.getAttributeBaseValue(net.minecraft.entity.attribute.EntityAttributes.GENERIC_MOVEMENT_SPEED));out.addProperty("targetId",target.getId());out.addProperty("targetType",net.minecraft.registry.Registries.ENTITY_TYPE.getId(target.getType()).toString());out.addProperty("targetHealth",target.getHealth());out.addProperty("targetAlive",target.isAlive());out.addProperty("targetX",target.getX());out.addProperty("targetY",target.getY());out.addProperty("targetZ",target.getZ());if(target.getType()==EntityType.ENDERMAN)out.add("targetDamageReceipts",targetReceipts.deepCopy());}
        if(target!=null){var slow=target.getStatusEffect(net.minecraft.entity.effect.StatusEffects.SLOWNESS);out.addProperty("targetSlownessTicks",slow==null?0:slow.getDuration());out.addProperty("targetSlownessAmplifier",slow==null?-1:slow.getAmplifier());out.addProperty("targetPotionParticles",slow!=null&&slow.shouldShowParticles());}
        if(target!=null){out.addProperty("targetAiDisabled",target.isAiDisabled());out.addProperty("targetFrozen",NativeMeiFreezeRuntime.frozen(target));}
        if(!beamTargets.isEmpty()){var group=new JsonObject();for(var entry:beamTargets.entrySet())group.addProperty(entry.getKey(),entry.getValue().getHealth());out.add("beamTargets",group);}
        addHeroStatus(out);
        SupportCommitFixtures.addStatus(server,out);
    }
}
