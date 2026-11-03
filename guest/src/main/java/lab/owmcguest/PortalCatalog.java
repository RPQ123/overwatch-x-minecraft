package lab.owmcguest;

import com.google.gson.*;
import java.util.*;
import net.minecraft.registry.*;
import net.minecraft.registry.tag.TagKey;
import net.minecraft.server.MinecraftServer;
import net.minecraft.util.Identifier;
import net.minecraft.world.World;
import net.minecraft.block.Block;

/** Enumerated actual installed worlds/author portal blocks, never legacy unregistered IDs. */
public final class PortalCatalog {
    public record Entry(String id,String name,String block,String dimension,String kind){}
    public static volatile List<Entry> entries=List.of();
    public static volatile String status="{\"entries\":[]}";
    public static void refresh(MinecraftServer server){
        var rows=new ArrayList<Entry>();
        rows.add(new Entry("nether","地狱","minecraft:nether_portal","minecraft:the_nether","nether"));
        rows.add(new Entry("end","末地","minecraft:end_portal","minecraft:the_end","end"));
        if(server.getWorld(RegistryKey.of(RegistryKeys.WORLD,Identifier.of("aether:the_aether")))!=null)
            rows.add(new Entry("aether","天堂","aether:aether_portal","aether:the_aether","aether"));
        if(Registries.BLOCK.containsId(Identifier.of("twilightforest:twilight_portal")))
            rows.add(new Entry("twilight","暮色森林","twilightforest:twilight_portal","twilightforest:twilight_forest","twilight"));
        int firstModPortal=rows.size();
        for(Block block:Registries.BLOCK){
            var id=Registries.BLOCK.getId(block);if(!id.getNamespace().equals("aoa3")||block.getClass().getSimpleName().equals("NowhereActivityPortal"))continue;
            if(!ModApi.implementsType(block,"net.tslat.aoa3.content.world.teleporter.AoAPortal"))continue;
            try{
                Object key=ModApi.call(block,"getDimension");if(!(key instanceof RegistryKey<?> dimension))continue;
                String world=dimension.getValue().toString();
                if(server.getWorld(RegistryKey.of(RegistryKeys.WORLD,dimension.getValue()))==null)continue;
                rows.add(new Entry(id.toString(),names.getOrDefault(dimension.getValue().getPath(),dimension.getValue().getPath()),id.toString(),world,"aoa"));
            }catch(Exception ignored){}
        }
        rows.subList(firstModPortal,rows.size()).sort(Comparator.comparing(Entry::dimension));
        entries=List.copyOf(rows);var out=new JsonObject();out.add("entries",new Gson().toJsonTree(entries));status=out.toString();
    }
    private static final Map<String,String> names=Map.ofEntries(Map.entry("nowhere","虚无 · Boss竞技场"),Map.entry("abyss","深渊"),Map.entry("barathos","爵士"),Map.entry("celeve","玩具"),Map.entry("crystevia","晶体"),Map.entry("deeplands","深层"),Map.entry("dustopia","异位"),Map.entry("lborean","暴风"),Map.entry("lelyetia","赫尔维蒂"),Map.entry("precasia","传说"),Map.entry("the_nether","虚无式下界"));
}
