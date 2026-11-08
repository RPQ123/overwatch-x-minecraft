package lab.owmcguest;

import java.util.*;
import com.google.gson.*;
import lab.owmcguest.NativeShotProtocol.*;

/** Offline protocol/physics/lifecycle oracles. Does not launch either game. */
public final class RoadhogCheck {
    private static int assertions;
    private static final long NOW=1000;
    private static final Source SOURCE=new Source(1,2,3,4);
    private static final Expected EXPECTED=new Expected(1,2,4,3,11,1.62,7,RoadhogRules.HERO);
    private static void check(boolean b,String why){assertions++;if(!b)throw new AssertionError(why);}
    private static void close(double a,double b,String why){check(Math.abs(a-b)<1e-5,why+": "+a+" != "+b);}
    private static JsonObject report(long resource){
        boolean q=resource==RoadhogRules.WHOLE_HOG,secondary=resource==RoadhogRules.SECONDARY;
        var root=new JsonObject();
        for(var item:new Object[][]{{"probeVersion",17},{"protocol",3},{"pid",1},{"creation",2},{"epoch",3},{"hostGeneration",4},{"modelId",7},{"hero",RoadhogRules.HERO},
            {"heartbeat",NOW},{"failures",0},{"acknowledged",0},{"baseId",1},{"lastId",1}})root.addProperty((String)item[0],(Number)item[1]);
        root.addProperty("enabled",true);root.addProperty("restored",false);root.addProperty("overflow",false);root.addProperty("factoryCalibration",false);
        var e=new JsonObject();
        for(var item:new Object[][]{{"id",1},{"entity",0},{"owner",7},{"mcPid",2},{"mcGeneration",3},{"worldId",11},{"hostGeneration",4},
            {"wallMs",NOW},{"kind",4},{"hero",RoadhogRules.HERO},{"flags",313},{"volley",256},{"tick",100},{"shot",0},{"pellet",0},
            {"status",secondary?8:0},{"factoryType",q?3:secondary?1:2},{"flight",q?0:1},{"eyeHeight",1.62},
            {"gravity",0},{"splashDamage",0},{"outerRadius",0},{"innerRadius",0},{"outerScale",.125},{"fuse",0},{"terrain",0},{"effect",0},{"bounces",0},
            {"damage",q?7:secondary?50:9},{"lifetime",q?0:secondary?RoadhogRules.SECONDARY_SECONDS:5},{"range",100}})e.addProperty((String)item[0],(Number)item[1]);
        e.addProperty("resource",Long.toUnsignedString(resource,16));e.add("position",JsonParser.parseString("[0,1.62,0]"));e.add("nativeFeet",JsonParser.parseString("[0,0,0]"));e.add("mcFeet",JsonParser.parseString("[0,0,0]"));
        e.add("velocity",JsonParser.parseString("[0,0,"+(q?1:secondary?60:80)+"]"));var entries=new JsonArray();entries.add(e);root.add("events",entries);return root;
    }
    private static JsonObject row(JsonObject report){return report.getAsJsonArray("events").get(0).getAsJsonObject();}
    private static Batch decode(JsonObject json){return NativeShotProtocol.decode(json.toString(),EXPECTED,NOW);}
    private static Shot shot(long resource){var s=decode(report(resource)).entries().getFirst().shot();check(s!=null,"calibrated Roadhog factory admitted without diagnostics");return s;}
    private static Batch batch(Shot shot){return new Batch(SOURCE,0,1,List.of(new Entry(1,shot,"")));}
    private static final class World implements NativeShotSimulation.WorldAccess {
        double at=Double.POSITIVE_INFINITY,damage;boolean block,loaded=true;int hits,contacts;
        public NativeShotSimulation.Hit trace(Vec a,Vec b){
            if(a.z()<=at&&b.z()>=at)return new NativeShotSimulation.Hit(block,5,new Vec(a.x(),a.y(),at),loaded);
            return null;
        }
        public void impact(Shot s,NativeShotSimulation.Hit h){contacts++;}
        public double damage(NativeShotSimulation.Hit hit,double amount,long entity){hits++;damage+=amount;return amount;}
        public double weaponHit(Shot s,NativeShotSimulation.Hit hit){return damage(hit,RoadhogRules.nativeDamage(s,hit.point())*NativeShotSimulation.HP_SCALE,0);}
    }
    public static void main(String[] args)throws Exception{
        var primary=shot(RoadhogRules.SCRAP);var secondary=shot(RoadhogRules.SECONDARY);var q=shot(RoadhogRules.WHOLE_HOG);
        for(long resource:new long[]{RoadhogRules.SCRAP,RoadhogRules.SECONDARY,RoadhogRules.WHOLE_HOG}){
            for(String field:new String[]{"damage","factoryType","status","effect","gravity","worldId","owner"}){
                var bad=report(resource);var e=row(bad);e.addProperty(field,e.get(field).getAsDouble()+1);
                check(decode(bad).entries().getFirst().shot()==null,"altered Roadhog "+field+" rejected");
            }
            var old=report(resource);old.addProperty("probeVersion",16);check(decode(old).entries().getFirst().shot()==null,"old producer cannot claim Roadhog production proof");
            var otherHero=report(resource);row(otherHero).addProperty("hero",0x02e0000000000002L);check(decode(otherHero).entries().getFirst().shot()==null,"cross-hero resources rejected");
            var stale=report(resource);row(stale).addProperty("wallMs",400);check(decode(stale).entries().getFirst().shot()==null,"stale shot retired without damage");
        }
        var sim=new NativeShotSimulation();var world=new World();sim.admit(batch(secondary));
        sim.tick(world,1100);check(sim.active()==1&&sim.roadhogSplits==0,"parent does not split before original lifetime");
        sim.tick(world,1151);check(sim.active()==25&&sim.roadhogSplits==1&&sim.admitted==1,"one parent expires into one declared MC volley");
        var children=sim.activeProjectiles();var identities=new HashSet<String>();
        for(var child:children){
            close(child.start().z(),60*RoadhogRules.SECONDARY_SECONDS,"split starts at actual 9m endpoint");close(child.velocity().lengthSquared(),6400,"child original speed80");
            check(child.velocity().z()/80>=Math.cos(Math.toRadians(10))-.001,"all split children stay in forward cone");
            check(child.id()<0&&identities.add(child.identity()),"derived identities distinct from native queue");
            close(child.nativeDamage(),9,"child damage declared9");
        }
        sim.admit(batch(secondary));sim.tick(world,1200);check(sim.roadhogSplits==1&&sim.active()==25,"journal replay cannot duplicate child volley");
        sim.tick(world,8000);check(sim.active()==0&&sim.roadhogSplits==1,"children expire without recursively splitting");
        for(boolean block:new boolean[]{true,false})for(boolean loaded:new boolean[]{true,false}){
            var collision=new NativeShotSimulation();var corridor=new World();corridor.at=4;corridor.block=block;corridor.loaded=loaded;collision.admit(batch(secondary));
            collision.tick(corridor,1200);collision.tick(corridor,1400);collision.admit(batch(secondary));collision.tick(corridor,1500);
            check(collision.roadhogSplits==0&&collision.active()==0&&corridor.contacts==1,"parent contact retires before any split; replay inert");
            check(corridor.hits==(!block&&loaded?1:0),"blocked/unloaded contacts cannot damage; entity exactly once");
            if(!block&&loaded)close(corridor.damage,5,"near parent50 OW maps to5 MC");
        }
        var cancelled=new NativeShotSimulation();cancelled.admit(batch(secondary));cancelled.clear();cancelled.tick(new World(),1300);check(cancelled.active()==0&&cancelled.roadhogSplits==0,"scope reset cancels pending split");
        close(RoadhogRules.nativeDamage(primary,new Vec(0,1.62,10)),9,"full near primary damage");
        close(RoadhogRules.nativeDamage(primary,new Vec(0,1.62,20)),2.7,"original outer falloff .3 at20m");
        close(RoadhogRules.nativeDamage(q,new Vec(0,1.62,40)),2.1,"Q original outer falloff at40m");
        var stream=new NativeShotSimulation();var target=new World();target.at=3;stream.admit(batch(q));for(int i=0;i<30;i++)stream.tick(target,1000+i*50);
        check(target.hits==1&&stream.admitted==1,"Q window never manufactures missing factory pellets");
        var push=new Vec(0,0,0);for(int i=0;i<128;i++)push=RoadhogRules.knockback(push,new Vec(0,0,1));
        close(push.z(),1.4,"Q strong horizontal impulse bounded");check(push.y()<=.35,"Q does not vertically multiply per pellet");
        var goal=RoadhogRules.hookGoal(new Vec(0,4,0),new Vec(0,.2,1));close(goal.z(),2.75,"hook stops in front of Roadhog, not under his feet");
        var step=RoadhogRules.pullStep(new Vec(0,4,20),goal);close(step.lengthSquared(),1,"hook uses bounded1m step, not teleport");
        close(RoadhogRules.pullStep(new Vec(0,4,2.8),goal).z(),-.05,"short final hook step cannot overshoot front anchor");
        var healing=new RoadhogRules.Healing();double total=0;
        for(int i=0;i<90;i++){healing.refresh(10);total+=healing.tick();}close(total,30,"E total300OW maps to30MC once despite repeated samples");
        healing.refresh(0);healing.refresh(10);close(healing.tick(),0,"ended token cannot reopen budget");
        healing.refresh(11);close(healing.tick(),1,"new native cast receives own budget");healing.clear();close(healing.tick(),0,"death/reset removes healing");
        var phase=new RoadhogClient.Phase();check(phase.update(new NativeSkillReader.Entry(10,true))==0,"first active snapshot baselined");
        phase.update(new NativeSkillReader.Entry(11,false));check(phase.update(new NativeSkillReader.Entry(12,true))==12,"new native Begin opens one token");
        check(phase.update(new NativeSkillReader.Entry(13,true))==12,"active ticks do not recast");check(phase.update(new NativeSkillReader.Entry(14,false))==0,"native End closes token");
        check(HeroNpcCatalog.ENTRIES.size()>=13&&HeroNpcCatalog.entry(12).hero()==0x40&&HeroNpcCatalog.entry(12).health()==600,"F5 retains600HP Roadhog after unchanged12 heroes and permits appended heroes");
        check(HeroNpcCatalog.entry(0).hero()==0x29&&HeroNpcCatalog.entry(11).hero()==10,"existing summon indices preserved");
        check(MuzzlePresentation.profile(RoadhogRules.HERO,0,0)!=null,"Roadhog connected to shared muzzle presentation");
        // The hand root and the outgoing hook must use one left-palm origin;
        // translating/turning the camera later must not drag a launched head.
        var hookVisual=new RoadhogHookPresentation();hookVisual.begin("cast1",1000);
        var camera=new Vec(0,0,0);var basis=new MuzzlePresentation.Basis(new Vec(0,0,1),new Vec(1,0,0),new Vec(0,1,0));
        var hand=hookVisual.hand("cast1",camera,basis,40,16./9,1000);
        check(hand.x()<0&&hand.y()<0&&hand.z()>0,"specific Roadhog left palm, below eye and in front");
        var firstHead=new Vec(0,0,2);var firstDraw=hookVisual.position("cast1",firstHead,hand,camera,"OUT");
        close(firstDraw.subtract(hand).lengthSquared(),0,"late first server sample starts at the same left palm as the chain");
        var movedHand=hand.add(new Vec(2,0,0));var flight1=hookVisual.position("cast1",new Vec(0,0,4),movedHand,camera,"OUT");
        var flight2=hookVisual.position("cast1",new Vec(0,0,4),hand,camera,"OUT");
        close(flight1.subtract(flight2).lengthSquared(),0,"moving hand cannot steer an already outgoing hook");
        var atSix=new Vec(0,0,6);close(hookVisual.position("cast1",atSix,movedHand,camera,"OUT").subtract(atSix).lengthSquared(),0,"outbound joins the actual sweep by4m additional travel");
        close(hookVisual.position("cast1",atSix,hand,camera,"PULL").subtract(atSix).lengthSquared(),0,"attached hook remains on the real target");
        close(hookVisual.position("cast1",camera,hand,camera,"RETURN").subtract(hand).lengthSquared(),0,"retraction ends at left palm, not eye or gun");
        hookVisual.clear();close(hookVisual.position("cast1",atSix,hand,camera,"OUT").subtract(atSix).lengthSquared(),0,"scope reset retires old origin");
        var pScope=new RoadhogPresentation.Scope(UUID.randomUUID(),11,7,SOURCE);
        RoadhogPresentation.reset();RoadhogPresentation.segment(pScope,primary,new Vec(0,0,0),new Vec(0,0,4),null,0,.05,1000);
        RoadhogPresentation.segment(pScope,primary,new Vec(0,0,4),new Vec(0,0,6),new NativeShotSimulation.Hit(true,0,new Vec(0,0,6)),.05,.075,1000);
        RoadhogPresentation.publish(pScope,1000);var presentation=RoadhogPresentation.view.flights().getFirst();
        for(long ms:new long[]{0,10,50,75,100,150}){
            var visible=RoadhogPresentation.sample(presentation,1000+ms,1000);if(visible==null)continue;
            check(visible.trailFrom().z()>=0&&visible.trailFrom().z()<=visible.at().z()&&visible.at().z()<=6,"mesh and trail stay inside actually swept contact prefix");
        }
        for(long resource:new long[]{RoadhogRules.SCRAP,RoadhogRules.SECONDARY,RoadhogRules.WHOLE_HOG}){
            var visual=RoadhogProjectileVisuals.body(resource,"real-factory:1");check(visual.name().startsWith("roadhog-rh2-"),"all admitted weapon resources select audited original solid mesh");
            check(visual.fireSize()>0&&visual.fireSize()<1,"bounded cosmetic original-sprite fire scale");
        }
        check(!RoadhogProjectileVisuals.body(RoadhogRules.SCRAP,"1").name().equals(RoadhogProjectileVisuals.body(RoadhogRules.SCRAP,"2").name()),"two actual original debris variants, no authored prism");
        RoadhogPresentation.reset();
        assertions+=RoadhogRH3Check.run(primary,secondary,q,SOURCE);
        assertions+=RoadhogAudioLevelCheck.run(SOURCE);
        System.out.println("PASS: RoadhogCheck "+assertions+" assertions (offline fixtures; no native pixels/play acceptance)");
    }
}
