package lab.owmcguest;

import java.util.List;
import lab.owmcguest.NativeShotProtocol.*;

public final class NativeCombatCheck {
    static void check(boolean value,String name){if(!value)throw new AssertionError(name);}
    static final Source SOURCE=new Source(1,2,3,4);
    static Shot shot(long id,long entity){return new Shot(id,entity,1000,new Vec(0,1,0),new Vec(0,0,60),35,5);}
    static Batch batch(long ack,Entry... entries){return new Batch(SOURCE,ack,ack+entries.length,List.of(entries));}
    static final class Corridor implements NativeShotSimulation.WorldAccess {
        boolean wall;double hp=20;int hits;
        public NativeShotSimulation.Hit trace(Vec start,Vec end){
            double z=wall?2:4;
            return start.z()<=z&&end.z()>=z?new NativeShotSimulation.Hit(wall,17,new Vec(0,1,z)):null;
        }
        public double damage(NativeShotSimulation.Hit hit,double amount,long entity){hits++;hp-=amount;return amount;}
    }
    private static void sonicChecks(String base,Expected expected){
        String sonic=base.replace("\"probeVersion\":11","\"probeVersion\":16").replace("40000000000004a","400000000000149")
            .replace("207165582859042818",Long.toUnsignedString(HanzoSonicArrowState.HERO))
            .replace("\"flight\":0","\"flight\":1").replace("\"factoryType\":2","\"factoryType\":1")
            .replace("\"lifetime\":0","\"lifetime\":5").replace("[0,0,1]","[0,0,90]")
            .replace("\"damage\":7","\"damage\":125").replace("\"gravity\":0","\"gravity\":9.800000190734863");
        var batch=NativeShotProtocol.decode(sonic,expected,1000);
        check(batch.entries().getFirst().shot()!=null,"Actual calibrated strong Sonic protocol");
        check(NativeShotProtocol.decode(sonic.replace("\"probeVersion\":16","\"probeVersion\":17"),expected,1000).entries().getFirst().shot()!=null,"Shared emission17 preserves calibrated Sonic");
        String weak=sonic.replace("400000000000149","40000000000020d").replace("[0,0,90]","[0,0,25]").replace("\"damage\":125","\"damage\":25");
        check(NativeShotProtocol.decode(weak,expected,1000).entries().getFirst().shot()!=null,"Calibrated weak Sonic protocol");
        for(String bad:new String[]{sonic.replace("\"probeVersion\":16","\"probeVersion\":15"),sonic.replace("\"gravity\":9.800000190734863","\"gravity\":0"),
            sonic.replace("\"damage\":125","\"damage\":126"),sonic.replace("[0,0,90]","[0,0,91]"),sonic.replace("\"factoryType\":1","\"factoryType\":2"),
            sonic.replace(Long.toUnsignedString(HanzoSonicArrowState.HERO),Long.toUnsignedString(0x02e0000000000002L))})
            check(NativeShotProtocol.decode(bad,expected,1000).entries().getFirst().shot()==null,"Uncalibrated Sonic producer/owner/flight/damage rejected");
        for(boolean block:new boolean[]{false,true})for(boolean loaded:new boolean[]{false,true}){
            var sim=new NativeShotSimulation();int[] contacts={0},hits={0};var scope=new HanzoSonicArrowState.Scope(java.util.UUID.randomUUID(),11,4,8);
            var state=new HanzoSonicArrowState();state.configure(scope);var shot=batch.entries().getFirst().shot();
            sim.admit(batch);check(sim.admissions().size()==1,"One real admitted Sonic factory");
            check(state.admit(scope,shot.identity(),shot.effect().resource(),1000,5,1000,1),"Arm only admitted original Sonic");
            var world=new NativeShotSimulation.WorldAccess(){
                public NativeShotSimulation.Hit trace(Vec a,Vec b){return b.z()>=6?new NativeShotSimulation.Hit(block,17,b,loaded):null;}
                public void impact(Shot s,NativeShotSimulation.Hit h){
                    check(sim.active()==0,"Sonic flight retired before external impact");contacts[0]++;
                    state.impact(scope,s.identity(),new HanzoSonicArrowState.Point(h.point().x(),h.point().y(),h.point().z()),h.loaded(),2);
                }
                public double damage(NativeShotSimulation.Hit h,double n,long entity){hits[0]++;return n;}
            };
            sim.tick(world,1025);check(contacts[0]==0&&state.pulses().isEmpty(),"No input-only or midflight reveal");
            sim.tick(world,1100);sim.admit(batch);sim.tick(world,1200);
            check(contacts[0]==1&&state.pulses().size()==(loaded?1:0),"One real block/entity contact; unloaded refuses; replay inert");
            check(hits[0]==(!block&&loaded?1:0),"Sonic contact cannot double or bypass ordinary damage");
        }
    }
    private static void tankShellChecks(String armoryJson,Expected expected){
        String tankJson=armoryJson.replace("\"probeVersion\":11","\"probeVersion\":16").replace("40000000000004a","4000000000003ce")
            .replace("207165582859042818",Long.toUnsignedString(0x02e0000000000015L)).replace("\"flight\":0","\"flight\":1").replace("\"factoryType\":2","\"factoryType\":1")
            .replace("\"lifetime\":0","\"lifetime\":5").replace("[0,0,1]","[0,0,60]").replace("\"damage\":7","\"damage\":50")
            .replace("\"splashDamage\":0","\"splashDamage\":140").replace("\"outerRadius\":0","\"outerRadius\":4").replace("\"innerRadius\":0","\"innerRadius\":1")
            .replace("\"outerScale\":0.125","\"outerScale\":0.30000001192092896").replace("\"effect\":0","\"effect\":1");
        var tankBatch=NativeShotProtocol.decode(tankJson,expected,1000);var tank=tankBatch.entries().getFirst().shot();
        check(tank!=null&&tank.tankShell()&&!tank.rocket()&&!tank.helix()&&!tank.barrage(),"Only calibrated beta Tank03ce gets its dedicated MC presentation");
        check(NativeShotProtocol.decode(tankJson.replace("\"probeVersion\":16","\"probeVersion\":17"),expected,1000).entries().getFirst().shot()!=null,"Shared emission17 preserves calibrated Tank");
        check(NativeShotProtocol.decode(tankJson,new Expected(1,2,4,3,-1,1.62,8,0x02e0000000000015L),1000).entries().getFirst().shot()!=null,"Tank receipt agrees with current model and hero");
        for(String invalid:new String[]{tankJson.replace("\"probeVersion\":16","\"probeVersion\":15"),tankJson.replace("\"factoryType\":1","\"factoryType\":2"),tankJson.replace("\"status\":8","\"status\":0"),
            tankJson.replace("[0,0,60]","[0,0,50]"),tankJson.replace("\"damage\":50","\"damage\":500"),tankJson.replace("\"splashDamage\":140","\"splashDamage\":80"),
            tankJson.replace("\"terrain\":0","\"terrain\":2"),tankJson.replace("\"gravity\":0","\"gravity\":1"),tankJson.replace("\"worldId\":18446744073709551615","\"worldId\":2")})
            check(NativeShotProtocol.decode(invalid,expected,1000).entries().getFirst().shot()==null,"Unproved Tank source, physics, amount or world refused");
        check(NativeShotProtocol.decode(tankJson,new Expected(1,2,4,3,-1,1.62,9,0x02e0000000000015L),1000).entries().getFirst().shot()==null,"Departed Tank model cannot admit a new shell");
        check(NativeShotProtocol.decode(tankJson,new Expected(1,2,4,3,-1,1.62,8,0x02e0000000000042L),1000).entries().getFirst().shot()==null,"Old Tank shot cannot borrow a replacement hero");
        for(boolean block:new boolean[]{false,true}){
            var sim=new NativeShotSimulation();int[] blasts={0};var world=new NativeShotSimulation.WorldAccess(){
                public NativeShotSimulation.Hit trace(Vec a,Vec b){return b.z()>=6?new NativeShotSimulation.Hit(block,17,new Vec(a.x(),a.y(),6)):null;}
                public double damage(NativeShotSimulation.Hit h,double amount,long entity){throw new AssertionError("Tank direct must be combined with its one explosion callback");}
                public double armoryExplosion(Shot s,NativeShotSimulation.Hit h){check(sim.active()==0,"Retire Tank before external blast callback");check(s.tankShell()&&h.point().z()==6,"Tank explodes at its first real sweep contact");blasts[0]++;return block?14:19;}
            };
            sim.admit(tankBatch);sim.tick(world,1050);check(sim.active()==1&&blasts[0]==0,"Tank travels at original60m/s, not an instant ray");
            // No Q state or guessed duration in projectile authority. An empty
            // current-scope prefix (e.g. after native End) cannot erase an
            // already fired original projectile before its real collision.
            sim.admit(new Batch(tankBatch.source(),1,1,List.of()));sim.tick(world,1100);
            check(blasts[0]==1&&sim.active()==0&&sim.damageApplied==(block?14:19),"Already admitted Tank shell finishes once under the same identity after native End");
            sim.admit(tankBatch);sim.tick(world,1200);check(blasts[0]==1,"Tank journal replay cannot repeat direct or splash");
        }
        var unloaded=new NativeShotSimulation();unloaded.admit(tankBatch);
        unloaded.tick(new NativeShotSimulation.WorldAccess(){
            public NativeShotSimulation.Hit trace(Vec a,Vec b){return new NativeShotSimulation.Hit(true,0,b,false);}
            public double damage(NativeShotSimulation.Hit h,double n,long e){throw new AssertionError("Unloaded Tank damaged");}
            public double armoryExplosion(Shot s,NativeShotSimulation.Hit h){throw new AssertionError("Unloaded Tank exploded");}
        },1050);check(unloaded.active()==0&&unloaded.explosions==0,"Unloaded Tank boundary cancels without generating terrain");
        var changed=new NativeShotSimulation();changed.admit(tankBatch);
        changed.admit(new Batch(new Source(1,2,30,4),0,0,List.of()));check(changed.activeProjectiles().isEmpty(),"Replacement source clears all older Tank flights");
        changed.admit(tankBatch);changed.clear();check(changed.activeProjectiles().isEmpty(),"Runtime world/model reset cannot leave queued Tank damage");
        var ranged=new NativeShotSimulation();ranged.admit(tankBatch);
        ranged.tick(new NativeShotSimulation.WorldAccess(){
            public NativeShotSimulation.Hit trace(Vec a,Vec b){check(b.z()<=100.00001,"Tank sweep stays within native100m range");return null;}
            public double damage(NativeShotSimulation.Hit h,double n,long e){throw new AssertionError("Expired Tank damaged");}
            public double armoryExplosion(Shot s,NativeShotSimulation.Hit h){throw new AssertionError("No Tank contact means no blast");}
        },6000);check(ranged.active()==0&&ranged.explosions==0,"Tank range expiry creates no fake contact");
        for(double age=0;age<1.66;age+=.003){
            var at=BastionTankPresentation.center(tank,age);var ray=tank.start().add(tank.velocity().multiply(age));
            check(at.equals(ray),"Tank rebuilt cosmetic shell never shifts the authoritative ray");
        }
        check(NativeBlastFalloff.scale(1,1,4,.30000001192092896)==1&&Math.abs(NativeBlastFalloff.scale(4,1,4,.30000001192092896)-.30000001192092896)<1e-12,"Tank original inner/outer blast ring endpoints preserved");
    }
    public static void main(String[] args){
        var phase=new NativeDashPhase();
        check(!phase.observe(1,10,10,true,1000)&&!phase.active(1000),"existing native active state is a baseline, not a new dash");
        phase.observe(1,10,11,false,1010);check(phase.observe(1,10,12,true,1020)&&phase.active(1020),"actual native Begin admits dash");
        check(!phase.observe(1,10,12,true,1030)&&phase.active(1030),"same native phase cannot begin twice");
        check(!phase.active(1131),"missing native refresh expires movement");phase.invalidate();check(!phase.observe(1,10,12,true,1140)&&!phase.active(1140),"failed read cannot replay same native dash");
        phase.observe(1,10,13,false,1150);check(phase.observe(1,10,14,true,1160),"later original dash may begin");
        check(!phase.observe(2,10,1,true,1170)&&!phase.active(1170),"new native source resets to baseline");
        check(!phase.observe(2,11,0,false,1180),"replaced hero establishes a new idle baseline in the same host session");
        check(phase.observe(2,11,1,true,1190),"reset native clock on new hero admits its first dash");
        var sim=new NativeShotSimulation();var corridor=new Corridor();corridor.wall=true;
        var first=batch(0,new Entry(1,shot(1,11),""));sim.admit(first);sim.tick(corridor,1100);
        check(sim.admissions().size()==1&&sim.activeProjectiles().isEmpty(),"real admission remains available for a muzzle flash after immediate impact");
        check(sim.blockHits==1&&corridor.hp==20,"swept wall stops native 60m/s shot before creature");
        sim.admit(first);sim.tick(corridor,1200);check(corridor.hp==20&&sim.duplicates==1,"journal replay cannot cross wall twice");
        check(sim.admissions().isEmpty(),"journal replay cannot manufacture a second muzzle flash");
        corridor.wall=false;var second=batch(1,new Entry(2,shot(2,12),""),new Entry(3,shot(3,13),""),new Entry(4,shot(4,14),""));sim.admit(second);sim.tick(corridor,1100);
        check(corridor.hits==3&&corridor.hp==9.5,"each original pellet applies 35 OW hp mapped to 3.5 MC hp");
        sim.admit(second);sim.tick(corridor,1300);check(corridor.hp==9.5,"exact IDs replay cannot damage again");
        sim.admit(batch(4,new Entry(5,shot(5,12),"")));sim.tick(corridor,1400);check(corridor.hp==9.5,"reused native entity deduplicated after acknowledgement");
        sim.admit(batch(5,new Entry(6,null,"stale")));check(sim.cursor()==6&&sim.rejected==1,"rejected events retire in order");
        try{sim.admit(batch(7));throw new AssertionError("future ack accepted");}catch(IllegalArgumentException expected){}
        String event="{\"kind\":0,\"id\":1,\"wallMs\":1000,\"entity\":7,\"owner\":8,\"componentOwner\":8,\"flags\":31,\"resource\":\"4000000000007ca\",\"mcPid\":2,\"mcGeneration\":3,\"hostGeneration\":4,\"worldId\":18446744073709551615,\"position\":[1000,1001.2,1000],\"nativeFeet\":[1000,1000,1000],\"mcFeet\":[10,64,10],\"velocity\":[0,0,60],\"damage\":35,\"lifetime\":5}";
        String json="{\"protocol\":3,\"probeVersion\":11,\"pid\":1,\"hostGeneration\":4,\"enabled\":true,\"failures\":0,\"overflow\":false,\"heartbeat\":1000,\"creation\":2,\"epoch\":3,\"acknowledged\":0,\"baseId\":1,\"lastId\":1,\"events\":["+event+"]}";
        var expected=new Expected(1,2,4,3,-1,1.62);var decoded=NativeShotProtocol.decode(json,expected,1000);
        String owned=json.replace("\"protocol\":3","\"protocol\":3,\"modelId\":8,\"hero\":99");
        try{NativeShotProtocol.decode(owned,new Expected(1,2,4,3,-1,1.62,9,99),1000);throw new AssertionError("new-pawn prefix consumed under old owner");}catch(NativeShotProtocol.OwnerPending pending){}
        check(NativeShotProtocol.decode(owned,new Expected(1,2,4,3,-1,1.62,8,99),1100).entries().getFirst().shot()!=null,"same fresh original shot survives a deferred owner bind");
        // Matching producer scope does not permit old per-entry owners or time.
        check(NativeShotProtocol.decode(owned.replace("\"owner\":8","\"owner\":7"),new Expected(1,2,4,3,-1,1.62,8,99),1000).entries().getFirst().shot()==null,"departed entry still retires after current scope agrees");
        String freshHeader=owned.replace("\"heartbeat\":1000","\"heartbeat\":1600");
        check(NativeShotProtocol.decode(freshHeader,new Expected(1,2,4,3,-1,1.62,8,99),1600).entries().getFirst().shot()==null,"owner deferral never extends shot freshness");
        check(Math.abs(decoded.entries().getFirst().shot().start().y()-65.62)<1e-8,"unsigned world identity and muzzle height mapping");
        check(NativeShotProtocol.decode(json.replace("\"mcGeneration\":3","\"mcGeneration\":30"),expected,1000).entries().getFirst().shot()==null,"wrong guest generation rejected");
        check(NativeShotProtocol.decode(json.replace("\"flags\":31","\"flags\":15"),expected,1000).entries().getFirst().shot()==null,"unbound native damage rejected");
        try{NativeShotProtocol.decode(json,expected,1501);throw new AssertionError("stale source accepted");}catch(IllegalArgumentException rejected){}
        String ray="{\"kind\":1,\"id\":1,\"wallMs\":1000,\"entity\":0,\"owner\":8,\"flags\":57,\"resource\":\"4000000000002a7\",\"volley\":18446744073709551615,\"tick\":100,\"shot\":0,\"pellet\":0,\"status\":8,\"mcPid\":2,\"mcGeneration\":3,\"hostGeneration\":4,\"worldId\":18446744073709551615,\"position\":[1000,1001.55,1000],\"nativeFeet\":[1000,1000,1000],\"mcFeet\":[0,0,0],\"velocity\":[0,0,1],\"damage\":70,\"lifetime\":0,\"range\":100}";
        String rayJson=json.replace(event,ray);
        var rayBatch=NativeShotProtocol.decode(rayJson,expected,1000);var rayShot=rayBatch.entries().getFirst().shot();
        check(rayShot!=null&&rayShot.hitscan()&&Math.abs(rayShot.start().y()-1.62)<1e-8,"original zero-lifetime ray and McCree eye mapping");
        var raySim=new NativeShotSimulation();var rayWorld=new Corridor();raySim.admit(rayBatch);raySim.tick(rayWorld,1000);
        check(rayWorld.hp==13&&raySim.active()==0,"hitscan resolves immediately at emission time, 70 OW HP maps to 7 MC HP");
        raySim.admit(rayBatch);raySim.tick(rayWorld,1050);check(rayWorld.hp==13,"replayed ray cannot double damage");
        var later=new Shot(2,0,1000,rayShot.start(),rayShot.velocity(),70,0,true,100,rayShot.identity()+":next-native-tick");
        raySim.admit(batch(1,new Entry(2,later,"")));rayWorld.wall=true;raySim.tick(rayWorld,1000);
        check(rayWorld.hp==13&&raySim.blockHits==1,"wall occludes an instant native ray");
        raySim.admit(batch(2,new Entry(3,new Shot(3,0,1000,rayShot.start(),rayShot.velocity(),70,0,true,100,rayShot.identity()),"")));
        check(raySim.active()==0,"native firing identity deduplicates beyond journal ACK");
        var next=NativeShotProtocol.decode(rayJson.replace("\"tick\":100","\"tick\":101"),expected,1000).entries().getFirst().shot();
        check(!next.identity().equals(rayShot.identity()),"same volley, next native tick is another shot");
        for(String invalid:new String[]{rayJson.replace("\"range\":100","\"range\":1000"),rayJson.replace("\"status\":8","\"status\":3"),rayJson.replace("[0,0,1]","[0,0,60]"),rayJson.replace("\"mcGeneration\":3","\"mcGeneration\":9")})
            check(NativeShotProtocol.decode(invalid,expected,1000).entries().getFirst().shot()==null,"unproven or cross-world ray refused");
        String beamJson=rayJson.replace("\"kind\":1","\"kind\":2").replace("\"flags\":57","\"flags\":217").replace("4000000000002a7","5800000000000fe")
            .replace("\"volley\":18446744073709551615","\"volley\":50").replace("\"range\":100","\"range\":8").replace("\"damage\":70","\"damage\":60").replace("\"lifetime\":0","\"lifetime\":0.05").replace("1001.55","1001");
        var beamBatch=NativeShotProtocol.decode(beamJson,expected,1000);var beamShot=beamBatch.entries().getFirst().shot();
        check(beamShot!=null&&beamShot.beam()&&Math.abs(beamShot.start().y()-1.12)<1e-8,"native beam phase maps original origin and duration");
        var beamSim=new NativeShotSimulation();double[] beamHp={20,20};
        var beamWorld=new NativeShotSimulation.WorldAccess(){
            public NativeShotSimulation.Hit trace(Vec a,Vec b){throw new AssertionError("beam is not a single projectile");}
            public List<NativeShotSimulation.Hit> beam(Vec a,Vec direction,double range){return List.of(new NativeShotSimulation.Hit(false,0,a),new NativeShotSimulation.Hit(false,1,a),new NativeShotSimulation.Hit(true,0,a));}
            public double damage(NativeShotSimulation.Hit hit,double amount,long nativeEntity){throw new AssertionError("beam cannot inherit projectile damage semantics");}
            public double beamDamage(NativeShotSimulation.Hit hit,double amount){beamHp[(int)hit.target()]-=amount;return amount;}
        };
        beamSim.admit(beamBatch);beamSim.tick(beamWorld,1000);
        check(Math.abs(beamHp[0]-19.7)<1e-8&&Math.abs(beamHp[1]-19.7)<1e-8&&beamSim.blockHits==1&&beamSim.active()==0,"native 50ms interval damages all visible targets once; occluded target blocked");
        beamSim.admit(beamBatch);beamSim.tick(beamWorld,1050);check(Math.abs(beamHp[0]-19.7)<1e-8,"beam replay has no damage");
        for(String invalid:new String[]{beamJson.replace("\"lifetime\":0.05","\"lifetime\":0.5"),beamJson.replace("\"range\":8","\"range\":80"),beamJson.replace("\"volley\":50","\"volley\":100")})
            check(NativeShotProtocol.decode(invalid,expected,1000).entries().getFirst().shot()==null,"invalid beam phase bounds refused");
        var visualSim=new NativeShotSimulation();var segments=new java.util.ArrayList<Vec>();
        var visualWorld=new NativeShotSimulation.WorldAccess(){
            public NativeShotSimulation.Hit trace(Vec a,Vec b){return b.z()>=4?new NativeShotSimulation.Hit(true,0,new Vec(0,1,4)):null;}
            public void present(Shot shot,Vec a,Vec b,NativeShotSimulation.Hit hit){segments.add(b);}
            public double damage(NativeShotSimulation.Hit hit,double amount,long nativeEntity){throw new AssertionError("visual cannot deal independent damage");}
        };
        visualSim.admit(first);visualSim.tick(visualWorld,1050);
        check(visualSim.activeProjectiles().size()==1&&segments.size()==1&&segments.getFirst().z()==3,"admitted projectile exposes one native-speed flight");
        visualSim.tick(visualWorld,1100);
        check(visualSim.activeProjectiles().isEmpty()&&segments.getLast().z()==4,"visual ends exactly at swept wall, not beyond it");
        visualSim.admit(first);visualSim.tick(visualWorld,1200);
        check(segments.size()==2,"acknowledged replay cannot recreate a visual entity");
        visualSim.admit(batch(1,new Entry(2,null,"wrong world")));visualSim.tick(visualWorld,1200);
        check(segments.size()==2,"rejected world/session events never create visuals");
        var flightSim=new NativeShotSimulation();flightSim.admit(first);flightSim.clear();
        check(flightSim.activeProjectiles().isEmpty(),"session reset leaves no projectile entity owners");
        check(raySim.activeProjectiles().isEmpty()&&beamSim.activeProjectiles().isEmpty(),"hitscan and beam never become slow projectile entities");
        String rocketJson=rayJson.replace("\"kind\":1","\"kind\":3").replace("4000000000002a7","400000000000033")
            .replace("[0,0,1]","[0,0,35]").replace("\"damage\":70","\"damage\":40").replace("\"lifetime\":0","\"lifetime\":5")
            .replace("1001.55","1001.35").replace("\"range\":100","\"range\":100,\"splashDamage\":80,\"innerRadius\":0.5,\"outerRadius\":2.5,\"outerScale\":0.125");
        var rocketBatch=NativeShotProtocol.decode(rocketJson,expected,1000);var rocket=rocketBatch.entries().getFirst().shot();
        check(rocket!=null&&rocket.rocket()&&!rocket.hitscan()&&Math.abs(rocket.start().y()-1.62)<1e-8,"confirmed Pharah native factory flight and eye mapping");
        for(String invalid:new String[]{rocketJson.replace("[0,0,35]","[0,0,60]"),rocketJson.replace("\"status\":8","\"status\":0"),rocketJson.replace("\"outerRadius\":2.5","\"outerRadius\":25"),rocketJson.replace("\"splashDamage\":80","\"splashDamage\":800"),rocketJson.replace("\"worldId\":18446744073709551615","\"worldId\":9")})
            check(NativeShotProtocol.decode(invalid,expected,1000).entries().getFirst().shot()==null,"uncalibrated rocket/source refused");
        var rocketSim=new NativeShotSimulation();int[] detonations={0};
        var rocketWorld=new NativeShotSimulation.WorldAccess(){
            public NativeShotSimulation.Hit trace(Vec a,Vec b){return b.z()>=4?new NativeShotSimulation.Hit(true,0,new Vec(0,1,4)):null;}
            public double damage(NativeShotSimulation.Hit hit,double amount,long entity){throw new AssertionError("rocket direct damage must be combined with splash once");}
            public double explode(Shot s,NativeShotSimulation.Hit hit){check(rocketSim.active()==0,"retire before explosion callback");check(hit.point().z()==4,"explode at swept collision");detonations[0]++;return 8;}
        };
        rocketSim.admit(rocketBatch);rocketSim.tick(rocketWorld,1100);check(detonations[0]==0&&rocketSim.active()==1,"rocket travels at35 rather than immediate explosion");
        rocketSim.tick(rocketWorld,1200);rocketSim.admit(rocketBatch);rocketSim.tick(rocketWorld,1300);
        check(detonations[0]==1&&rocketSim.explosions==1&&rocketSim.damageApplied==8,"one impact/explosion, no replay damage or block destruction");
        var unloaded=new NativeShotSimulation();unloaded.admit(rocketBatch);
        unloaded.tick(new NativeShotSimulation.WorldAccess(){
            public NativeShotSimulation.Hit trace(Vec a,Vec b){return new NativeShotSimulation.Hit(true,0,b,false);}
            public double damage(NativeShotSimulation.Hit h,double amount,long e){throw new AssertionError();}
        },1200);
        check(unloaded.active()==0&&unloaded.explosions==0,"unloaded boundary retires rocket without a blast");
        var timed=new NativeShotSimulation();timed.admit(rocketBatch);
        timed.tick(new NativeShotSimulation.WorldAccess(){
            public NativeShotSimulation.Hit trace(Vec a,Vec b){check(b.z()<=100.00001,"range cap before collision");return null;}
            public double damage(NativeShotSimulation.Hit h,double amount,long e){throw new AssertionError();}
        },6000);check(timed.active()==0&&timed.explosions==0,"no impact means no terrain explosion");
        check(NativeRocketExplosion.falloff(.5)==1&&NativeRocketExplosion.falloff(2.5)==.125&&NativeRocketExplosion.falloff(2.51)==0,"measured80 to10 splash rings");
        String armoryJson=rayJson.replace("\"kind\":1","\"kind\":4").replace("\"flags\":57","\"flags\":313").replace("4000000000002a7","40000000000004a")
            .replace("\"damage\":70","\"damage\":7").replace("\"range\":100","\"range\":100,\"hero\":207165582859042818,\"flight\":0,\"factoryType\":2,\"eyeHeight\":1.55,\"gravity\":0,\"splashDamage\":0,\"outerRadius\":0,\"innerRadius\":0,\"outerScale\":0.125,\"fuse\":0,\"terrain\":0,\"effect\":0,\"bounces\":0");
        var armoryBatch=NativeShotProtocol.decode(armoryJson,expected,1000);
        check(armoryBatch.entries().getFirst().shot()!=null,"original typed Reaper pellet factory proof");
        var armorySim=new NativeShotSimulation();var armoryWorld=new Corridor();armorySim.admit(armoryBatch);armorySim.tick(armoryWorld,1000);
        check(Math.abs(armoryWorld.hp-19.3)<1e-8,"one factory pellet applies actual7 native HP");
        armorySim.admit(armoryBatch);armorySim.tick(armoryWorld,1100);check(armoryWorld.hits==1,"generic pellet replay cannot duplicate damage");
        check(NativeBlastFalloff.scale(0,1,3,.5)==1&&NativeBlastFalloff.scale(1,1,3,.5)==1&&NativeBlastFalloff.scale(2,1,3,.5)==.75&&NativeBlastFalloff.scale(3,1,3,.5)==.5,"Native Helix ring endpoints and linear interpolation");
        check(NativeBlastFalloff.scale(3.001,1,3,.5)==0&&NativeBlastFalloff.scale(Double.NaN,1,3,.5)==0&&NativeBlastFalloff.scale(1,3,1,.5)==0,"Outside, nonfinite and inverted rings refused");
        String helixJson=armoryJson.replace("\"flight\":0","\"flight\":1").replace("\"lifetime\":0","\"lifetime\":5").replace("[0,0,1]","[0,0,50]")
            .replace("\"damage\":7","\"damage\":40").replace("\"splashDamage\":0","\"splashDamage\":80").replace("\"outerRadius\":0","\"outerRadius\":3").replace("\"innerRadius\":0","\"innerRadius\":1").replace("\"outerScale\":0.125","\"outerScale\":0.5").replace("\"effect\":0","\"effect\":1");
        var helixBatch=NativeShotProtocol.decode(helixJson,expected,1000);var helix=helixBatch.entries().getFirst().shot();
        check(helix!=null&&helix.effect().splash()==80&&helix.effect().innerRadius()==1&&helix.effect().outerScale()==.5,"Bound native blast profile crosses protocol");
        var helixSim=new NativeShotSimulation();int[] helixExplosions={0};var helixWorld=new NativeShotSimulation.WorldAccess(){
            public NativeShotSimulation.Hit trace(Vec a,Vec b){return b.z()>=4?new NativeShotSimulation.Hit(false,17,new Vec(0,1,4)):null;}
            public double damage(NativeShotSimulation.Hit hit,double amount,long entity){throw new AssertionError("Do not double apply blast direct damage");}
            public double armoryExplosion(Shot s,NativeShotSimulation.Hit hit){helixExplosions[0]++;return 12;}
        };
        helixSim.admit(helixBatch);helixSim.tick(helixWorld,1100);helixSim.admit(helixBatch);helixSim.tick(helixWorld,1200);
        check(helixExplosions[0]==1&&helixSim.damageApplied==12,"Generic blast retires and combines impact once, replay stays harmless");
        for(String invalid:new String[]{armoryJson.replace("\"hero\":207165582859042818","\"hero\":2"),armoryJson.replace("\"flight\":0","\"flight\":2"),armoryJson.replace("\"flags\":313","\"flags\":57"),armoryJson.replace("\"worldId\":18446744073709551615","\"worldId\":2")})
            check(NativeShotProtocol.decode(invalid,expected,1000).entries().getFirst().shot()==null,"foreign hero, invalid flight/proof/world cannot admit armory shot");
        var flashEffect=new Effect(0x02e0000000000042L,0x040000000000037dL,2,20,0,3,0,0,0);
        var flash=new Shot(1,0,1000,new Vec(0,1,0),new Vec(0,0,30),25,5,false,7,"flash-1",false,false,flashEffect);
        for(boolean impact:new boolean[]{false,true}){
            var grenadeSim=new NativeShotSimulation();int[] detonated={0};
            var grenadeWorld=new NativeShotSimulation.WorldAccess(){
                public NativeShotSimulation.Hit trace(Vec a,Vec b){return impact&&b.z()>=2?new NativeShotSimulation.Hit(true,0,new Vec(0,1,2)):null;}
                public double damage(NativeShotSimulation.Hit h,double n,long e){throw new AssertionError("Flashbang may not double-apply direct damage");}
                public double controlImpact(Shot s,NativeShotSimulation.Hit h){detonated[0]++;return 7.5;}
            };
            var grenades=batch(0,new Entry(1,flash,""));grenadeSim.admit(grenades);grenadeSim.tick(grenadeWorld,1300);grenadeSim.admit(grenades);grenadeSim.tick(grenadeWorld,1500);
            check(detonated[0]==1&&grenadeSim.damageApplied==7.5&&grenadeSim.active()==0,"Real collision or travel-limit flash detonates exactly once; replay inert");
        }
        var unloadedFlash=new NativeShotSimulation();unloadedFlash.admit(batch(0,new Entry(1,flash,"")));
        unloadedFlash.tick(new NativeShotSimulation.WorldAccess(){
            public NativeShotSimulation.Hit trace(Vec a,Vec b){return new NativeShotSimulation.Hit(true,0,a,false);}
            public double damage(NativeShotSimulation.Hit h,double n,long e){throw new AssertionError("unloaded flash damaged");}
            public double controlImpact(Shot s,NativeShotSimulation.Hit h){throw new AssertionError("unloaded flash detonated");}
        },1050);check(unloadedFlash.active()==0,"unloaded grenade is retired without blast/status");
        String concussive=armoryJson.replace("\"probeVersion\":11","\"probeVersion\":13").replace("40000000000004a","40000000000010f").replace("207165582859042818","207165582859042824")
            .replace("\"flight\":0","\"flight\":1").replace("\"factoryType\":2","\"factoryType\":1").replace("\"lifetime\":0","\"lifetime\":5").replace("[0,0,1]","[0,0,60]")
            .replace("\"damage\":7","\"damage\":1").replace("\"effect\":0","\"effect\":3").replace("\"outerRadius\":0","\"outerRadius\":8");
        var eBatch=NativeShotProtocol.decode(concussive,expected,1000);check(eBatch.entries().getFirst().shot()!=null,"Exact native Pharah E receipt admitted");
        for(String bad:new String[]{concussive.replace("\"probeVersion\":13","\"probeVersion\":12"),concussive.replace("[0,0,60]","[0,0,30]"),concussive.replace("\"outerRadius\":8","\"outerRadius\":9"),concussive.replace("\"damage\":1","\"damage\":10"),concussive.replace("40000000000010f","400000000000052")})
            check(NativeShotProtocol.decode(bad,expected,1000).entries().getFirst().shot()==null,"Wrong Pharah E observer/resource/flight/ring/amount refused");
        var eSim=new NativeShotSimulation();int[] pushes={0};var eWorld=new NativeShotSimulation.WorldAccess(){
            public NativeShotSimulation.Hit trace(Vec a,Vec b){return b.z()>=3?new NativeShotSimulation.Hit(true,0,new Vec(0,1,3)):null;}
            public double damage(NativeShotSimulation.Hit h,double n,long entity){throw new AssertionError("Concussive Blast cannot apply receipt amount as health damage");}
            public double controlImpact(Shot s,NativeShotSimulation.Hit h){check(eSim.active()==0,"Retire E before external physics callback");pushes[0]++;return 0;}
        };
        eSim.admit(eBatch);eSim.tick(eWorld,1100);eSim.admit(eBatch);eSim.tick(eWorld,1200);check(pushes[0]==1&&eSim.damageApplied==0,"Real E collision pushes once, no replay or health damage");
        String waveA="{\"start\":0,\"fade\":0.2,\"phase\":0.25,\"frequency\":0.5,\"magnitude\":1,\"rotation\":90,\"spiral\":true}";
        String waveB=waveA.replace("true","false");
        String barrageJson=helixJson.replace("\"probeVersion\":11","\"probeVersion\":14").replace("40000000000004a","400000000000052").replace("207165582859042818","207165582859042824").replace("[0,0,50]","[0,0,45]").replace("\"damage\":40","\"damage\":10").replace("\"splashDamage\":80","\"splashDamage\":30").replace("\"outerRadius\":3","\"outerRadius\":1.5").replace("\"innerRadius\":1","\"innerRadius\":0.5").replace("\"outerScale\":0.5","\"outerScale\":0.3").replace("\"bounces\":0","\"bounces\":0,\"waves\":["+waveA+","+waveB+"]");
        var barrageBatch=NativeShotProtocol.decode(barrageJson,expected,1000);var barrage=barrageBatch.entries().getFirst().shot();
        check(barrage!=null&&barrage.barrage(),"Barrage requires sampled native Wave data");
        check(NativeShotProtocol.decode(barrageJson,new Expected(1,2,4,3,-1,1.62,8,0x02e0000000000008L),1000).entries().getFirst().shot()!=null,"Fresh same-model Barrage admitted");
        check(NativeShotProtocol.decode(barrageJson,new Expected(1,2,4,3,-1,1.62,9,0x02e0000000000008L),1000).entries().getFirst().shot()==null,"Unacknowledged old-model projectile cannot reappear after hero reset");
        check(NativeShotProtocol.decode(barrageJson,new Expected(1,2,4,3,-1,1.62,8,0x02e0000000000042L),1000).entries().getFirst().shot()==null,"Old-hero projectile cannot gain a new hero identity");

        for(String bad:new String[]{barrageJson.replace("\"probeVersion\":14","\"probeVersion\":13"),barrageJson.replace("\"frequency\":0.5","\"frequency\":999"),barrageJson.replace("\"magnitude\":1","\"magnitude\":99"),barrageJson.replace("\"waves\":","\"missingWaves\":")})
            check(NativeShotProtocol.decode(bad,expected,1000).entries().getFirst().shot()==null,"Barrage refuses old producer, corrupt or missing original motion");
        check(PharahBarrageMotion.position(barrage,0).equals(barrage.start()),"Barrage starts exactly at original factory origin");
        var atWave=PharahBarrageMotion.position(barrage,.2);check(Math.abs(atWave.x()-barrage.start().x())>.1,"Native Wave is not silently straightened");
        check(Math.abs(atWave.x()-barrage.start().x()+1.61803398875)<1e-6&&Math.abs(atWave.y()-barrage.start().y()+.58778525229)<1e-6,"Native-axis golden Wave displacement agrees with original arithmetic");
        var curvedSim=new NativeShotSimulation();int[] curvedHits={0},segmentsSeen={0};
        var curvedWorld=new NativeShotSimulation.WorldAccess(){
            public NativeShotSimulation.Hit trace(Vec a,Vec b){segmentsSeen[0]++;return b.z()>=4?new NativeShotSimulation.Hit(true,0,b):null;}
            public double damage(NativeShotSimulation.Hit h,double n,long e){throw new AssertionError("Barrage must use one blast resolution");}
            public double armoryExplosion(Shot s,NativeShotSimulation.Hit h){check(curvedSim.active()==0,"Barrage retired before external blast callback");curvedHits[0]++;return 4;}
        };
        curvedSim.admit(barrageBatch);curvedSim.tick(curvedWorld,1400);curvedSim.admit(barrageBatch);curvedSim.tick(curvedWorld,1600);
        check(curvedHits[0]==1&&curvedSim.damageApplied==4&&segmentsSeen[0]>10,"Curved corridor swept in small steps, replay cannot repeat blast");
        curvedSim.clear();check(curvedSim.activeProjectiles().isEmpty(),"World/hero reset removes wave flights");
        tankShellChecks(armoryJson,expected);
        sonicChecks(armoryJson,expected);
        System.out.println("PASS: native projectile/ray/beam/rocket/Tank/E guards, swept collision, range/unloaded bounds, exact-once explosion and replay deduplication");
    }
}
