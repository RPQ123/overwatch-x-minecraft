package lab.owmcguest;

import java.nio.*;
import java.util.*;
import lab.owmcguest.NativeShotProtocol.*;

/** Pure offline contracts; no client launch, input, window or native attachment. */
public final class WinstonCheck {
    private static int assertions;
    private static void check(boolean ok,String message){assertions++;if(!ok)throw new AssertionError(message);}
    private static void near(double actual,double expected,String message){check(Math.abs(actual-expected)<1e-7,message+": "+actual);}
    private static void rejects(Runnable action,String message){boolean rejected=false;try{action.run();}catch(IllegalArgumentException e){rejected=true;}check(rejected,message);}
    private static void phase(){
        var p=new WinstonRules.Phase();check(p.observe(50,true)==0,"Attach to active rage never heals/replays");
        check(p.observe(50,true)==0,"Unchanged active baseline stays inert");check(p.observe(51,false)==0,"End is not a cast");
        check(p.observe(52,true)==52,"Fresh native Begin admits");check(p.observe(52,true)==52,"Lease retains one token");
        check(p.observe(53,false)==0,"Native End clears lease");check(p.observe(54,true)==54,"Next swing is independent");
        check(p.observe(1,true)==0,"Clock rollback rebuilds baseline");p.reset();check(p.observe(54,true)==0,"Reconnect cannot replay old Begin");
        p.observe(55,false);check(p.observe(56,true)==56,"Fresh cast after reconnect");
        var fists=new WinstonFistPhase();check(fists.observe(0,false)==0,"Fist baseline");
        check(fists.observe(100,true)==100&&fists.observe(101,false)==0,"Begin and End yield one fist only");
        check(fists.observe(201,false)==201&&fists.observe(201,false)==0,"Missed 100ms window is admitted once from its End");
        fists.reset();check(fists.observe(300,true)==0&&fists.observe(301,false)==0,"Attaching to old fist suppresses its End");
        check(fists.observe(401,false)==401,"Next completed native fist remains valid");
        check(fists.observe(1,false)==0,"Fist clock rollback is baseline");
        var strike=new WinstonPrimalStrike();strike.observe(0,false,0,false,1000);
        check(strike.observe(0,false,100,true,1050)==0,"Real native fist animation waits for its original350ms hit gate");
        check(strike.observe(0,false,100,true,1399)==0&&strike.observe(0,false,100,true,1400)==100,"Missing server target scan still delivers the native swing");
        check(strike.observe(120,true,100,true,1401)==0&&strike.observe(121,false,101,false,1450)==0,"Late TrackTargets and Anim End cannot double hit");
        check(strike.observe(121,false,200,true,1700)==0&&strike.observe(220,true,200,true,2000)==200,"Fresh native target gate can authorize the next strike");
        check(strike.observe(221,false,201,false,2100)==0,"Delivered strike has no timer replay");
        strike.reset();check(strike.observe(300,true,300,true,2200)==0&&strike.observe(301,false,301,false,2600)==0,"Attached native animations never replay");
        var owner=UUID.randomUUID();var scope=new WinstonServer.Scope(owner,1,2,3);
        check(scope.matches(owner,1,WinstonRules.HERO,3,2),"Focus/camera preserves the exact authenticated Q pawn");
        check(!scope.matches(owner,1,WinstonRules.HERO,4,2)&&!scope.matches(owner,2,WinstonRules.HERO,3,2)
            &&!scope.matches(owner,1,WinstonRules.HERO,3,4)&&!scope.matches(owner,1,1,3,2)
            &&!scope.matches(UUID.randomUUID(),1,WinstonRules.HERO,3,2),"Pawn/world/source/hero/player changes revoke Q");
    }
    private static void geometry(){
        check(WinstonRules.barrierRim(0,3)>WinstonRules.barrierRim(1,3),"Original mask has a brighter silhouette");
        check(WinstonRules.barrierRim(1,0)>WinstonRules.barrierRim(1,1),"Original equator gets a bounded outer rim");
        Vec c=new Vec(0,0,0),from=new Vec(-10,1,0),to=new Vec(10,1,0);
        near(WinstonBarrierGeometry.intersection(from,to,c),(10-Math.sqrt(24))/20,"Fast arrow crossing both sides finds first entry");
        near(WinstonBarrierGeometry.intersection(new Vec(0,1,0),new Vec(10,1,0),c),Math.sqrt(24)/10,"Hostile shot inside finds exit");
        near(WinstonBarrierGeometry.intersection(new Vec(-10,5,0),new Vec(10,5,0),c),.5,"Tangent at hemisphere top");
        check(Double.isNaN(WinstonBarrierGeometry.intersection(new Vec(-10,-1,0),new Vec(10,-1,0),c)),"No underground shield");
        check(Double.isNaN(WinstonBarrierGeometry.intersection(from,from,c)),"Zero segment");
        check(Double.isNaN(WinstonBarrierGeometry.intersection(new Vec(Double.NaN,0,0),to,c)),"Nonfinite refused");
        for(int i=0;i<80;i++){
            var v=WinstonRules.jump(new Vec(Math.sin(i*.1),Math.sin(i*.2),Math.cos(i*.1)));
            check(Double.isFinite(v.lengthSquared())&&v.y()>=.45&&v.y()<=1.5&&Math.hypot(v.x(),v.z())<=1.100001,"Bounded directional jump");
            var push=WinstonRules.knockback(new Vec(5,2,5),new Vec(i-40,1,1),true);
            check(Math.hypot(push.x(),push.z())<=1.800001&&push.y()<=.8,"Primal strong impulse cannot stack unbounded");
        }
        near(WinstonRules.landingDamage(0),50,"Original50 maximum");near(WinstonRules.landingDamage(4),10,"Original falloff5 within4m track");
        near(WinstonRules.landingDamage(4.001),0,"Outside authenticated landing volume");rejects(()->WinstonRules.jump(c),"Zero look");
    }
    private static byte[][] base(){
        byte[][] raw=new byte[3][320];
        ByteBuffer.wrap(raw[0]).order(ByteOrder.LITTLE_ENDIAN).putInt(1).putFloat(400).putFloat(300);
        ByteBuffer.wrap(raw[2]).order(ByteOrder.LITTLE_ENDIAN).putInt(1).putFloat(100).putFloat(100);return raw;
    }
    private static void health(){
        double[] config={400,0,100};var raw=base();var p=WinstonHealthPools.plan(raw,config,false,400);
        near(p.maximum(),500,"Ordinary maximum remains original500");near(p.current(),400,"Ordinary current sums active slots");
        rejects(()->WinstonHealthPools.plan(base(),config,true,500),"Primal must not silently fall back to ordinary500HP HUD");
        rejects(()->WinstonHealthPools.plan(base(),config,false,Double.POSITIVE_INFINITY),"Infinite health target refused");
        ByteBuffer.wrap(raw[0]).order(ByteOrder.LITTLE_ENDIAN).position(20).putInt(1).putFloat(500).putFloat(250).putLong(0x12345678L);
        var before=Arrays.stream(raw).map(byte[]::clone).toArray(byte[][]::new);
        rejects(()->WinstonHealthPools.plan(raw,config,false,500),"No successful native rage means no extra pool write");
        p=WinstonHealthPools.plan(raw,config,true,900);near(p.maximum(),1000,"Original500 bonus included");near(p.current(),650,"Bonus current included");
        near(p.writes().stream().mapToDouble(w->ByteBuffer.wrap(w.bytes()).order(ByteOrder.LITTLE_ENDIAN).getFloat(8)).sum(),900,"HP mapping preserves total");
        check(Arrays.deepEquals(raw,before),"Planner never modifies input/metadata");
        check(p.writes().stream().allMatch(w->w.bytes().length==12),"No write touches owner/source metadata");
        rejects(()->WinstonHealthPools.plan(raw,config,true,1001),"Health cannot exceed real pools");
        ByteBuffer.wrap(raw[0]).order(ByteOrder.LITTLE_ENDIAN).putFloat(24,501);
        rejects(()->WinstonHealthPools.plan(raw,config,true,500),"Unrecognized bonus amount refused");
        ByteBuffer.wrap(raw[0]).order(ByteOrder.LITTLE_ENDIAN).putFloat(24,500).position(40).putInt(1).putFloat(500).putFloat(100);
        rejects(()->WinstonHealthPools.plan(raw,config,true,500),"Second bonus refused");
        rejects(()->WinstonHealthPools.plan(base(),new double[]{400,0,200},true,500),"Other hero health cannot borrow extension");
        rejects(()->SurvivalHealthPlan.plan(before,config,500),"Generic health guard remains strict");
        var folded=base();ByteBuffer.wrap(folded[0]).order(ByteOrder.LITTLE_ENDIAN).putFloat(4,900).putFloat(8,800);
        p=WinstonHealthPools.plan(folded,config,true,1000);near(p.maximum(),1000,"Existing folded native bonus is recognized");
        near(p.writes().stream().mapToDouble(w->ByteBuffer.wrap(w.bytes()).order(ByteOrder.LITTLE_ENDIAN).getFloat(8)).sum(),1000,"Folded maximum can mirror full MC Q health");
        rejects(()->WinstonHealthPools.plan(folded,config,false,500),"Folded bonus requires a successful live Q lease");
        ByteBuffer.wrap(folded[0]).order(ByteOrder.LITTLE_ENDIAN).putFloat(4,901);
        rejects(()->WinstonHealthPools.plan(folded,config,true,500),"Only the exact original500 bonus is accepted");
    }
    private static void transport(){
        for(boolean hitscan:new boolean[]{true,false}){
            var sim=new NativeShotSimulation();int[] damage={0},blocks={0},explosions={0};
            var effect=new Effect(0x02e0000000000008L,0x0400000000000033L,1,0,120,3,0,0,0);
            var shot=new Shot(1,12,1000,new Vec(-10,1,0),new Vec(hitscan?1:80,0,0),40,5,hitscan,100,"original-shot",false,false,effect);
            var batch=new Batch(new Source(1,2,3,4),0,1,List.of(new Entry(1,shot,"")));
            var w=new NativeShotSimulation.WorldAccess(){
                public NativeShotSimulation.Hit trace(Vec a,Vec b){return b.x()>0?new NativeShotSimulation.Hit(false,1,new Vec(0,1,0)):null;}
                public NativeShotSimulation.Hit trace(Shot s,Vec a,Vec b){
                    double t=WinstonBarrierGeometry.intersection(a,b,new Vec(0,0,0));
                    if(Double.isFinite(t)){blocks[0]++;return new NativeShotSimulation.Hit(true,0,a.add(b.subtract(a).multiply(t)),false);}return trace(a,b);
                }
                public double damage(NativeShotSimulation.Hit hit,double n,long entity){damage[0]++;return n;}
                public double armoryExplosion(Shot s,NativeShotSimulation.Hit hit){explosions[0]++;return 0;}
            };
            sim.admit(batch);sim.tick(w,1250);sim.admit(batch);sim.tick(w,1500);
            check(blocks[0]==1&&damage[0]==0&&explosions[0]==0,"Shield retires ray/projectile once without target or terrain damage");
            check(sim.active()==0&&sim.blockHits==1,"Journal replay cannot consume shield twice");
        }
        // A real Tesla sample retains all distinct targets and its original time slice.
        var sim=new NativeShotSimulation();int[] hits={0};
        var beam=new Shot(1,0,1000,new Vec(0,1,0),new Vec(0,0,1),60,.05,false,8,"tesla-original",true);
        var batch=new Batch(new Source(1,2,3,4),0,1,List.of(new Entry(1,beam,"")));
        var w=new NativeShotSimulation.WorldAccess(){
            public NativeShotSimulation.Hit trace(Vec a,Vec b){return null;}
            public List<NativeShotSimulation.Hit> beam(Vec a,Vec d,double range){return List.of(new NativeShotSimulation.Hit(false,1,new Vec(0,1,2)),new NativeShotSimulation.Hit(false,2,new Vec(0,1,3)));}
            public double damage(NativeShotSimulation.Hit h,double n,long entity){hits[0]++;near(n,.3,"60DPS native50ms at0.1 mapping");return n;}
        };
        sim.admit(batch);sim.tick(w,1000);sim.admit(batch);sim.tick(w,1100);
        check(hits[0]==2,"Multi-target native Tesla replay remains exactly once");
        check(MuzzlePresentation.profile(WinstonRules.HERO,0,0)!=null,"Tesla has its own aperture profile");
        check(HeroNpcCatalog.ENTRIES.stream().anyMatch(e->e.id().equals("winston")&&e.health()==500),"F5 catalog contains original500HP Winston");
    }
    public static void main(String[] args){phase();geometry();health();transport();System.out.println("PASS Winston "+assertions+" offline assertions (no game acceptance)");}
}
