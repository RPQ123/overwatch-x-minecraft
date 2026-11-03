package lab.owmcguest;

import java.util.*;
import lab.owmcguest.HanzoCombatSite.*;

/** Safety fixtures with a fake world: no Minecraft process or native attacks. */
public final class HanzoCombatLabCheck {
    private static void check(boolean b,String why){if(!b)throw new AssertionError(why);}
    private static void rejects(Runnable run,String why){try{run.run();throw new AssertionError(why);}catch(IllegalArgumentException|IllegalStateException expected){}}
    private static class Space implements HanzoCombatSite.Space {
        public Blockage blocked(Cell c,boolean floor){return null;}
        public boolean occupied(Cell c){return false;}
    }
    private static class Blocks implements HanzoLabBlocks.Access<String>{
        final Map<Cell,String> states=new HashMap<>();final Set<Cell> unloaded=new HashSet<>();Cell postWriteFailure;int writes;
        public boolean loaded(Cell c){return !unloaded.contains(c);}
        public String read(Cell c){if(!loaded(c))throw new AssertionError("forced unloaded read");return states.getOrDefault(c,"AIR");}
        public boolean air(String s){return s.equals("AIR");}public boolean placed(String s){return s.equals("STONE");}
        public boolean write(Cell c,String s){writes++;states.put(c,s);return !c.equals(postWriteFailure);}
    }
    public static void main(String[] args){
        String lab="Overwatch Twilight Switch Test";
        HanzoCombatSite.requireIsolated(true,lab,lab,true);
        rejects(()->HanzoCombatSite.requireIsolated(true,lab,"Survival",true),"ordinary actual save admitted");
        rejects(()->HanzoCombatSite.requireIsolated(false,lab,lab,true),"nontrial admitted");
        rejects(()->HanzoCombatSite.requireIsolated(true,"Survival",lab,true),"ordinary configured save admitted");
        rejects(()->HanzoCombatSite.requireIsolated(true,lab,lab,false),"noncreative/dead owner admitted");
        var crater=HanzoCombatSite.find(0,63,0,-64,320,new Space());check(crater.floor().equals(new Cell(0,63,0)),"air crater floor can be rebuilt without clearing terrain");
        var obstruction=HanzoCombatSite.find(0,63,0,-64,320,new Space(){
            public Blockage blocked(Cell c,boolean floor){return !floor&&c.x()==16&&c.z()==0&&c.y()==64?new Blockage("occupied-corridor","stone at old 16m target",c):null;}
        });
        check(obstruction.floor()!=null&&obstruction.attempts()>1&&obstruction.rejected().containsKey("occupied-corridor"),"16m obstruction beyond old 12m floor selects nearby clear corridor");
        var unloaded=HanzoCombatSite.find(0,63,0,-64,320,new Space(){public Blockage blocked(Cell c,boolean floor){return new Blockage("unloaded","not loaded",c);}});
        check(unloaded.floor()==null&&unloaded.attempts()==369&&unloaded.samples().size()==13&&unloaded.rejected().get("unloaded")==369,"bounded failure preserves precise unloaded reason");
        var border=HanzoCombatSite.find(0,318,0,-64,320,new Space());check(border.floor()==null&&border.rejected().containsKey("world-height"),"dimension ceiling refused");
        var entity=HanzoCombatSite.find(0,63,0,-64,320,new Space(){public boolean occupied(Cell c){return c.x()==0&&c.z()==0;}});
        check(entity.floor()!=null&&!entity.floor().equals(new Cell(0,63,0)),"living entities are preserved by relocation");
        var center=new Cell(0,63,0);var a=new Cell(1,63,0);var dirt=new Cell(-1,63,0);var external=new Cell(0,63,1);var foreign=new Cell(7,63,7);
        var world=new Blocks();world.states.put(dirt,"DIRT");world.states.put(foreign,"STONE");var journal=new HanzoLabBlocks<>(center,2,"STONE");
        check(!journal.place(dirt,world)&&world.read(dirt).equals("DIRT"),"existing terrain not replaced or claimed");
        check(journal.place(a,world)&&journal.place(external,world),"only original air becomes owned floor");
        int writes=world.writes;rejects(()->journal.place(foreign,world),"out-of-owned-region write accepted");check(world.writes==writes,"rejected mutation wrote nothing");
        world.states.put(external,"CHEST");world.unloaded.add(a);var pending=journal.restore(world);
        check(pending.pending()==1&&pending.preservedExternalChanges()==1&&world.read(external).equals("CHEST"),"external modification preserved and unloaded ownership retained");
        world.unloaded.clear();var restored=journal.restore(world);
        check(restored.pending()==0&&restored.restored()==1&&world.read(a).equals("AIR")&&world.read(foreign).equals("STONE"),"loaded retry restores only owned original state");
        var partial=new HanzoLabBlocks<>(center,2,"STONE");world.postWriteFailure=a;rejects(()->partial.place(a,world),"failed placement did not report failure");
        world.postWriteFailure=null;check(partial.restore(world).restored()==1&&world.read(a).equals("AIR"),"partially acknowledged placement rolls back safely");
        System.out.println("HanzoCombatLabCheck passed (isolation, 16m relocation, bounded refusal, owned rollback)");
    }
}
