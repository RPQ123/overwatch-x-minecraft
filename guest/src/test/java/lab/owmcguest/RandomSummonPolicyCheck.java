package lab.owmcguest;

import java.util.*;

/** No game/server launch. Exercises exclusion boundaries and the actual paged root mapping. */
public final class RandomSummonPolicyCheck {
    private static int checks;
    private static void require(boolean value,String message){checks++;if(!value)throw new AssertionError(message);}
    public static void main(String[] args){
        for(String id:List.of("minecraft:ender_dragon","minecraft:wither","twilightforest:naga","twilightforest:hydra","twilightforest:ur_ghast","aoa3:tyrosaur","aoa3:elite_tyrosaur"))
            require(RandomSummonPolicy.blacklisted(id),"world Boss excluded even if scaled small: "+id);
        for(String id:List.of("aether:slider","aether:valkyrie_queen","twilightforest:lich","aoa3:smash"))
            require(RandomSummonPolicy.blacklisted(id),"small/medium known Boss-bar owners are now excluded: "+id);
        for(String id:List.of("custom:mini_wither","custom:ender_dragon_pet"))require(!RandomSummonPolicy.blacklisted(id),"exact IDs do not ban unrelated names: "+id);
        require(RandomSummonPolicy.BATCH_SIZE==8&&RandomSummonPolicy.MAX_ATTEMPTS==80,"random request targets 8 with bounded attempts");
        require(RandomSummonPolicy.fits(1.95,2.2,1.95),"ravager-sized combatant allowed");
        require(RandomSummonPolicy.fits(2,4,2),"height boundary allowed");
        require(RandomSummonPolicy.fits(3,2,3),"width/depth and volume boundaries allowed");
        for(double[] size:List.of(new double[]{3.001,1,1},new double[]{1,4.001,1},new double[]{1,1,3.001},new double[]{3,2.001,3},new double[]{0,1,1},new double[]{1,-1,1},new double[]{Double.NaN,1,1},new double[]{1,Double.POSITIVE_INFINITY,1},new double[]{1,1,Double.NaN}))
            require(!RandomSummonPolicy.fits(size[0],size[1],size[2]),"oversized/invalid bounds rejected");
        require(RandomSummonPolicy.combatant("custom:hostile",true,false,false,false,0),"mod MONSTER group");
        require(RandomSummonPolicy.combatant("custom:misc_monster",false,true,false,false,0),"mod Monster marker outside MONSTER group");
        require(RandomSummonPolicy.combatant("custom:neutral",false,false,true,false,0),"Angerable neutral");
        require(RandomSummonPolicy.combatant("minecraft:llama",false,false,false,true,0),"ranged retaliation neutral");
        require(RandomSummonPolicy.combatant("custom:defensive_animal",false,false,false,false,2),"non-Angerable retaliation via attack attribute");
        require(!RandomSummonPolicy.combatant("minecraft:cow",false,false,false,false,0),"passive animal excluded");
        require(!RandomSummonPolicy.combatant("custom:ambient",false,false,false,false,Double.NaN),"invalid damage does not imply neutral");
        require(!RandomSummonPolicy.combatant("minecraft:snow_golem",false,false,false,true,0),"friendly ranged snow golem excluded");
        for(String id:List.of("minecraft:allay","minecraft:axolotl","minecraft:cat","minecraft:fox","minecraft:frog","minecraft:ocelot","minecraft:parrot","minecraft:rabbit"))
            require(!RandomSummonPolicy.combatant(id,false,false,false,false,3),"hunting/variant-only attack attribute is not player retaliation: "+id);
        require(RandomSummonPolicy.choose(List.of(),bound->{throw new AssertionError("empty pool must not call RNG");})==null,"empty pool handled");
        var pool=List.of("custom:hostile_a","custom:neutral_b","aether:slider");
        for(int index=0;index<pool.size();index++){
            final int pick=index;
            require(RandomSummonPolicy.choose(pool,bound->{require(bound==pool.size(),"RNG covers every candidate type");return pick;}).equals(pool.get(index)),"each registered candidate reachable");
        }
        var root=SummonMenuOptions.ROOT;
        require(root.size()==5&&root.getFirst().selection().equals(RandomSummonPolicy.SELECTION),"new random option is first");
        require(root.get(1).selection().equals("batch:random8"),"old 8-mob batch retained");
        require(root.get(2).selection().equals("batch:cats")&&root.get(3).selection().equals("batch:animals8"),"cat and animal batches present");
        require(root.get(4).selection().equals(SummonMenuOptions.ALL),"5 opens all single creatures");
        require(root.stream().noneMatch(o->o.selection().startsWith("test:")),"enderman/villager test targets removed");
        var k=new PortalMenuKeys();int count=root.size();k.poll(true,0,false,count);k.poll(true,1,false,count);
        require(k.open(),"root opens");k.poll(true,0,false,count);
        require(k.poll(true,2,false,count)==1,"root digit 1 selects new random request");
        require(k.poll(true,2,false,count)==0,"held key does not summon twice");k.poll(true,0,false,count);
        require(k.poll(true,2,true,count)==0,"pending request rejects new summon");
        k.firstPage();require(k.page()==0&&k.poll(true,2,false,count)==0,"page reset preserves held-key edge guard");
        k.poll(false,2,false,count);require(!k.open(),"focus loss closes menu");
        require(k.poll(true,2,false,count)==0&&!k.open(),"focus return cannot replay held selection");
        System.out.println("PASS: random monster policy/root paging ("+checks+" checks); no game launched");
    }
}
