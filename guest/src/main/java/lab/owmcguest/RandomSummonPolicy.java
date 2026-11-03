package lab.owmcguest;

import java.util.List;
import java.util.Set;
import java.util.function.IntUnaryOperator;

/** Explicit MC adaptation for the F9 random pool, not a general Boss classification.
 * Width/depth <=3 blocks, height <=4, bounding volume <=18 cubic blocks.
 * Every Boss-bar owner is now excluded, including small/medium Bosses. */
public final class RandomSummonPolicy {
    public static final String SELECTION="random:monster";
    public static final int BATCH_SIZE=8;
    public static final int MAX_ATTEMPTS=BATCH_SIZE*10;
    public static final double MAX_WIDTH=3,MAX_HEIGHT=4,MAX_VOLUME=18;
    private static final Set<String> WORLD_BOSSES=Set.of(
        "minecraft:ender_dragon","minecraft:wither",
        "twilightforest:naga","twilightforest:lich","twilightforest:minoshroom","twilightforest:hydra",
        "twilightforest:knight_phantom","twilightforest:ur_ghast","twilightforest:alpha_yeti","twilightforest:snow_queen",
        "aether:slider","aether:valkyrie_queen","aether:sun_spirit",
        "aoa3:smash","aoa3:nethengeic_wither","aoa3:king_bambambam","aoa3:tyrosaur",
        "aoa3:elite_smash","aoa3:elite_nethengeic_wither","aoa3:elite_king_bambambam","aoa3:elite_tyrosaur");
    // These vanilla passives expose attack attributes or ranged AI for hunting /
    // special variants, but their ordinary summoned form does not retaliate at players.
    private static final Set<String> PASSIVE_COMBATANTS=Set.of(
        "minecraft:allay","minecraft:axolotl","minecraft:cat","minecraft:fox",
        "minecraft:frog","minecraft:ocelot","minecraft:parrot","minecraft:rabbit","minecraft:snow_golem");
    private RandomSummonPolicy(){}
    public static boolean blacklisted(String id){return WORLD_BOSSES.contains(id);}
    public static boolean fits(double width,double height,double depth){
        return Double.isFinite(width)&&Double.isFinite(height)&&Double.isFinite(depth)
            &&width>0&&height>0&&depth>0&&width<=MAX_WIDTH&&depth<=MAX_WIDTH
            &&height<=MAX_HEIGHT&&width*height*depth<=MAX_VOLUME;
    }
    /** Custom mod neutrals need not implement vanilla Angerable. Attack attributes
     * and RangedAttackMob cover retaliation-only goats/dolphins/pandas/llamas too.
     * Vanilla hunting-only passives and friendly ranged constructs are excluded. */
    public static boolean combatant(String id,boolean monsterGroup,boolean monster,boolean angerable,boolean ranged,double attackDamage){
        if(PASSIVE_COMBATANTS.contains(id))return false;
        return monsterGroup||monster||angerable||ranged||Double.isFinite(attackDamage)&&attackDamage>0;
    }
    public static <T> T choose(List<T> candidates,IntUnaryOperator nextInt){
        return candidates.isEmpty()?null:candidates.get(nextInt.applyAsInt(candidates.size()));
    }
}
