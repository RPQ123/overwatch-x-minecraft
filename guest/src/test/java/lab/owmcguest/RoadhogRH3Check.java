package lab.owmcguest;

import java.util.*;
import java.lang.reflect.*;
import lab.owmcguest.NativeShotProtocol.*;
import net.minecraft.util.math.Vec3d;

/** Offline real solver + real server lifecycle tests; no game/client creation. */
public final class RoadhogRH3Check {
    private static int checks;
    private static void check(boolean ok,String reason){checks++;if(!ok)throw new AssertionError(reason);}
    private static void near(double a,double b,String reason){check(Math.abs(a-b)<1e-5,reason+": "+a+" vs "+b);}
    private static Batch batch(Shot shot,Source source){return new Batch(source,0,1,List.of(new Entry(1,shot,null)));}
    public static int run(Shot primary,Shot secondary,Shot q,Source source)throws Exception{
        var owner=UUID.randomUUID();var victim=UUID.randomUUID();long world=11;
        var scope=new RoadhogPresentation.Scope(owner,world,7,source);var cues=new RoadhogSplitCues();
        class World implements NativeShotSimulation.WorldAccess {
            int splitCalls,damageCalls;double contact=-1;boolean block,loaded=true;boolean failNotification;
            public NativeShotSimulation.Hit trace(Vec from,Vec to){
                if(contact>=0&&from.z()<=contact&&to.z()>=contact)return new NativeShotSimulation.Hit(block,block?0:1,new Vec(from.x(),from.y(),contact),loaded);
                return null;
            }
            public double damage(NativeShotSimulation.Hit hit,double hp,long entity){damageCalls++;return hp;}
            public void split(Shot parent,Vec at){splitCalls++;near(at.z(),9, "second stage at actual .15s parent expiry, not the muzzle");
                cues.emit(scope,parent,at,1200);if(failNotification)throw new IllegalStateException("fixture notification failure");}
        }
        var sim=new NativeShotSimulation();var w=new World();sim.admit(batch(secondary,source));
        sim.tick(w,secondary.wallMs()+125);check(w.splitCalls==0,"flight alone does not play second stage");
        sim.tick(w,secondary.wallMs()+200);check(w.splitCalls==1&&sim.roadhogDerivedPellets==25,"one actual split authorizes one sound for25 children");
        sim.admit(batch(secondary,source));sim.tick(w,secondary.wallMs()+300);sim.tick(w,secondary.wallMs()+7000);
        check(w.splitCalls==1,"journal replay and all child expiries cannot replay parent sound");
        var cue=cues.poll();check(cue!=null&&cues.poll()==null,"exactly one queued audio request");
        check(!cues.emit(scope,secondary,new Vec(0,0,9),1300),"repeated producer callback is idempotent");
        check(!cues.emit(scope,primary,new Vec(0,0,9),1300)&&!cues.emit(scope,q,new Vec(0,0,9),1300),"primary andQ cannot borrow split SFX");
        var current=new RoadhogServer.Scope(owner,world,source.hostGeneration(),7);
        check(RoadhogSplitCues.current(cue,current,1200)&&!RoadhogSplitCues.current(cue,current,1451),"fresh scoped cue only; stale audio drops");
        check(!RoadhogSplitCues.current(cue,new RoadhogServer.Scope(owner,12,source.hostGeneration(),7),1200),"cross-world cue cannot play");
        check(!RoadhogSplitCues.current(cue,new RoadhogServer.Scope(owner,world,source.hostGeneration()+1,7),1200),"old native generation cannot play");
        check(!RoadhogSplitCues.current(cue,new RoadhogServer.Scope(owner,world,source.hostGeneration(),8),1200),"changed hero model cannot play");
        for(boolean blocked:new boolean[]{true,false})for(boolean loaded:new boolean[]{true,false}){
            var collided=new NativeShotSimulation();var wall=new World();wall.contact=4;wall.block=blocked;wall.loaded=loaded;collided.admit(batch(secondary,source));collided.tick(wall,secondary.wallMs()+300);
            check(wall.splitCalls==0,"block/entity/unloaded retirement is not a split sound");
        }
        var failed=new NativeShotSimulation();var notification=new World();notification.failNotification=true;failed.admit(batch(secondary,source));
        try{failed.tick(notification,secondary.wallMs()+200);throw new AssertionError("missing fixture failure");}catch(IllegalStateException expected){}
        failed.tick(notification,secondary.wallMs()+300);check(notification.splitCalls==1&&failed.roadhogSplits==1,"failed audio notification cannot repeat physics or sound callback");
        check(RoadhogSoundCatalog.allowed("roadhog",RoadhogSoundCatalog.EVENT,RoadhogSoundCatalog.HASH),"exact original SFX catalog entry");
        check(!RoadhogSoundCatalog.allowed("winston",RoadhogSoundCatalog.EVENT,RoadhogSoundCatalog.HASH)
            &&!RoadhogSoundCatalog.allowed("roadhog","select",RoadhogSoundCatalog.HASH)
            &&!RoadhogSoundCatalog.allowed("roadhog",RoadhogSoundCatalog.EVENT,"00000000000000000000000000000000"),"new asset admission never opens a generic SFX bypass");

        var actors=new RoadhogHookPull.Actors(owner,world,true,victim,world,true,false);
        var pull=new RoadhogHookPull(owner,world,victim);Vec position=new Vec(0,64,2000);
        for(int tick=1;tick<=20;tick++){
            // Repeated forced external displacement and a moving/turning owner
            // prevent normal1m movement from reaching the destination in time.
            position=position.add(new Vec(0,0,50));var feet=new Vec(tick,64,tick*.5);var facing=tick<10?new Vec(0,0,1):new Vec(1,0,0);
            var step=pull.advance(actors,position,feet,facing);check(step!=null&&step.cancelled().isEmpty(),"no range/time/knockback disconnection after capture");
            if(tick<20){check(!step.complete(),"long displacement remains latched");near(Math.sqrt(step.destination().subtract(position).lengthSquared()),1,"bounded ordinary pull step");}
            else{check(step.complete(),"twentieth step forces arrival instead of releasing");var goal=RoadhogRules.hookGoal(feet,facing);near(step.destination().subtract(goal).lengthSquared(),0,"exact current front, even after the owner turns");}
            position=step.destination();
        }
        check(pull.advance(actors,position,new Vec(20,64,10),new Vec(1,0,0))==null,"completed latch is not replayed");
        for(var invalid:List.of(
            new RoadhogHookPull.Actors(owner,world,false,victim,world,true,false),
            new RoadhogHookPull.Actors(owner,world,true,victim,world,false,false),
            new RoadhogHookPull.Actors(owner,world,true,victim,world,true,true),
            new RoadhogHookPull.Actors(owner,world,true,victim,world+1,true,false))){
            var lost=new RoadhogHookPull(owner,world,victim);var result=lost.advance(invalid,new Vec(0,0,5),new Vec(0,0,0),new Vec(0,0,1));
            check(!result.cancelled().isEmpty()&&result.destination()==null,"death/removal/world separation cancels without moving invalid entity");
        }
        // Exercise the actual production suspend/reset/clear methods. Native
        // reader resets must not accidentally clear a confirmed MC target.
        var constructor=RoadhogServer.class.getDeclaredConstructor();constructor.setAccessible(true);var server=constructor.newInstance();
        var hookClass=Class.forName("lab.owmcguest.RoadhogServer$Hook");var hc=hookClass.getDeclaredConstructor();hc.setAccessible(true);var hook=hc.newInstance();
        var stageClass=Class.forName("lab.owmcguest.RoadhogServer$Stage");
        @SuppressWarnings({"unchecked","rawtypes"})Object stage=Enum.valueOf((Class)stageClass,"PULL");
        set(hook,"stage",stage);set(hook,"owner",current);set(hook,"id","actual-hook-token");set(hook,"at",new Vec3d(0,64,8));set(hook,"direction",new Vec3d(0,0,1));
        set(hook,"pull",new RoadhogHookPull(owner,world,victim));set(server,"scope",current);set(server,"hook",hook);
        server.suspend(current);check(server.hookView!=null&&server.hookView.stage().equals("PULL"),"real suspend preserves confirmed target when native lease ends");
        server.resetSession();check(server.hookView!=null&&server.hookView.scope().equals(current),"real global native reader reset preserves latch actor/world authority");
        server.clear();check(server.hookView==null,"actual server/world cleanup leaves no persistent latch");
        System.out.println("PASS: RH3 "+checks+" checks; actual expiry sound-once, replay/contact exclusion, scoped queue, forced latch arrival and real server reset lifecycle");
        return checks;
    }
    private static void set(Object owner,String name,Object value)throws Exception{var f=owner.getClass().getDeclaredField(name);f.setAccessible(true);f.set(owner,value);}
}
