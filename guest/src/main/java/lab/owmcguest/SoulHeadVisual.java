package lab.owmcguest;

/** Built-in head items first; other victims use their own renderer model/skin. */
public final class SoulHeadVisual {
    public enum Kind { SKELETON,WITHER_SKELETON,ZOMBIE,CREEPER,PIGLIN,DRAGON,PLAYER,ENTITY }
    public static Kind kind(String entity,boolean player,boolean heroNpc){
        if(player||heroNpc)return Kind.PLAYER;
        return switch(entity){
            case "minecraft:skeleton"->Kind.SKELETON;
            case "minecraft:wither_skeleton"->Kind.WITHER_SKELETON;
            case "minecraft:zombie"->Kind.ZOMBIE;
            case "minecraft:creeper"->Kind.CREEPER;
            case "minecraft:piglin"->Kind.PIGLIN;
            case "minecraft:ender_dragon"->Kind.DRAGON;
            default->Kind.ENTITY;
        };
    }
    public static float scale(Kind kind){return kind==Kind.DRAGON?.30f:.60f;}
    public static final double HALO_RADIUS=.28;
    public static final float MESH_EXTENT=.30f;
    private SoulHeadVisual(){}
}
