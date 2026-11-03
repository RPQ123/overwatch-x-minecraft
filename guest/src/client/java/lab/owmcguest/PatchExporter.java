package lab.owmcguest;

import com.google.gson.Gson;
import java.nio.ByteBuffer;
import java.nio.ByteOrder;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.StandardCopyOption;
import java.util.ArrayList;
import java.util.LinkedHashMap;
import net.fabricmc.api.ClientModInitializer;
import net.fabricmc.fabric.api.client.event.lifecycle.v1.ClientTickEvents;
import net.minecraft.block.Block;
import net.minecraft.block.Blocks;
import net.minecraft.client.MinecraftClient;
import net.minecraft.client.texture.NativeImage;
import net.minecraft.client.texture.Sprite;
import net.minecraft.registry.Registries;
import net.minecraft.util.Identifier;
import net.minecraft.util.math.Direction;
import net.minecraft.util.math.random.Random;
import net.minecraft.world.level.LevelInfo;
import net.minecraft.world.GameMode;
import net.minecraft.world.Difficulty;
import net.minecraft.world.GameRules;
import net.minecraft.resource.DataConfiguration;
import net.minecraft.world.gen.GeneratorOptions;
import net.minecraft.world.gen.WorldPresets;
import net.minecraft.registry.RegistryKeys;
import org.lwjgl.glfw.GLFW;

/** Bounded actual world/model/atlas snapshots; no reconstructed MC content. */
public final class PatchExporter implements ClientModInitializer {
    private record Vertex(float x,float y,float z,float u,float v,float shade,int tint) {}
    private record Occupancy(int x,int y,int z,int state) {}
    private final long session=(new java.security.SecureRandom().nextLong()&Long.MAX_VALUE)|1;
    private long sequence;
    private int ticks;
    private boolean hidden;
    private boolean worldStarted;
    private final LinkedHashMap<Identifier,Integer> materials=new LinkedHashMap<>();
    private final byte[] atlas=new byte[128*128*4];
    @Override public void onInitializeClient() {
        if(!Boolean.getBoolean("owmc.exportPatch")) return;
        ClientTickEvents.END_CLIENT_TICK.register(client->{
            if(PatchWorld.NEW_WORLD&&!worldStarted&&client.getOverlay()==null) {
                worldStarted=true;String name="Overwatch Minecraft World";
                if(Files.exists(client.runDirectory.toPath().resolve("saves").resolve(name).resolve("level.dat")))
                    client.createIntegratedServerLoader().start(name,()->{});
                else client.createIntegratedServerLoader().createAndStart(name,
                    new LevelInfo(name,GameMode.CREATIVE,false,Difficulty.NORMAL,true,new GameRules(),DataConfiguration.SAFE_MODE),
                    new GeneratorOptions(20261014L,false,false),
                    registries->registries.get(RegistryKeys.WORLD_PRESET).get(WorldPresets.FLAT).createDimensionsRegistryHolder(),null);
            }
            if(client.world==null||PatchWorld.origin==null||++ticks%10!=0) return;
            if(sequence==0&&!client.world.getBlockState(PatchWorld.origin.add(-4,-1,-4)).isOf(Blocks.GRASS_BLOCK)) return;
            try {
                export(client);
                if(!hidden&&Boolean.getBoolean("owmc.backgroundExport")) { GLFW.glfwHideWindow(client.getWindow().getHandle());hidden=true; }
            } catch(Exception error) { System.err.println("[OWMCGuest] Patch export rejected: "+error); }
        });
    }
    private int material(MinecraftClient client,Sprite sprite) throws Exception {
        Identifier id=sprite.getContents().getId();Integer known=materials.get(id);if(known!=null) return known;
        if(materials.size()>=64) throw new IllegalArgumentException("Atlas material budget");
        int tile=materials.size();
        Identifier resourceId=Identifier.of(id.getNamespace(),"textures/"+id.getPath()+".png");
        var resource=client.getResourceManager().getResource(resourceId).orElseThrow();
        try(var stream=resource.getInputStream();var image=NativeImage.read(stream)) {
            if(image.getWidth()!=16||image.getHeight()!=16) throw new IllegalArgumentException("Lab supports static original 16x16 materials");
            for(int y=0;y<16;y++) for(int x=0;x<16;x++) {
                int abgr=image.getColor(x,y),offset=((tile/8*16+y)*128+tile%8*16+x)*4;
                atlas[offset]=(byte)abgr;atlas[offset+1]=(byte)(abgr>>8);atlas[offset+2]=(byte)(abgr>>16);atlas[offset+3]=(byte)(abgr>>24);
            }
        }materials.put(id,tile);return tile;
    }
    private void export(MinecraftClient client) throws Exception {
        var vertices=new ArrayList<Vertex>();var occupancy=new ArrayList<Occupancy>();var states=new LinkedHashMap<Integer,String>();
        var origin=PatchWorld.origin;
        int cx=PatchWorld.NEW_WORLD?PatchWorld.centerX:0,cz=PatchWorld.NEW_WORLD?PatchWorld.centerZ:0;
        for(int x=cx+PatchWorld.LOW;x<=cx+PatchWorld.HIGH;x++) for(int z=cz+PatchWorld.LOW;z<=cz+PatchWorld.HIGH;z++) for(int y=PatchWorld.BOTTOM;y<=PatchWorld.TOP;y++) {
            if(!client.world.isChunkLoaded(x>>4,z>>4)) return; // Keep last complete window while actual chunks load.
            var pos=origin.add(x,y,z);var state=client.world.getBlockState(pos);if(state.isAir()) continue;
            if(!state.isOf(Blocks.GRASS_BLOCK)&&!state.isOf(Blocks.STONE)&&!state.isOf(Blocks.STONE_BRICKS)
                &&!state.isOf(Blocks.OAK_LOG)&&!state.isOf(Blocks.OAK_PLANKS)&&!state.isOf(Blocks.DIRT)&&!state.isOf(Blocks.BEDROCK)) throw new IllegalArgumentException("Unsupported lab block "+state);
            int raw=Block.getRawIdFromState(state);occupancy.add(new Occupancy(x,y,z,raw));states.put(raw,Registries.BLOCK.getId(state.getBlock()).toString());
            var model=client.getBlockRenderManager().getModel(state);
            for(Direction face:Direction.values()) {
                if(!Block.shouldDrawSide(state,client.world,pos,face,pos.offset(face))) continue;
                for(var quad:model.getQuads(state,face,Random.create(state.getRenderingSeed(pos)))) {
                    int[] data=quad.getVertexData();if(data.length!=32) throw new IllegalArgumentException("Quad format");
                    var sprite=quad.getSprite();int tile=material(client,sprite);
                    int tint=quad.hasColor()?client.getBlockColors().getColor(state,client.world,pos,quad.getColorIndex()):0xffffff;
                    tint|=0xff000000;
                    float shade=quad.hasShade()?switch(face) {case UP->1;case DOWN->.5f;case EAST,WEST->.6f;default->.8f;}:1;
                    for(int index:new int[]{0,1,2,0,2,3}) {
                        int offset=index*8;
                        float u=(Float.intBitsToFloat(data[offset+4])-sprite.getMinU())/(sprite.getMaxU()-sprite.getMinU());
                        float v=(Float.intBitsToFloat(data[offset+5])-sprite.getMinV())/(sprite.getMaxV()-sprite.getMinV());
                        vertices.add(new Vertex(x+Float.intBitsToFloat(data[offset]),y+Float.intBitsToFloat(data[offset+1]),z+Float.intBitsToFloat(data[offset+2]),
                            (tile%8*16+.5f+u*15)/128,(tile/8*16+.5f+v*15)/128,shade,tint));
                    }
                }
            }
        }
        if(vertices.size()>(PatchWorld.CREATIVE?65536:16384)||occupancy.size()>(PatchWorld.CREATIVE?12288:320)) throw new IllegalArgumentException("Patch budget");
        ByteBuffer wire=ByteBuffer.allocate(64+occupancy.size()*16+vertices.size()*28+atlas.length).order(ByteOrder.LITTLE_ENDIAN);
        wire.put((PatchWorld.NEW_WORLD?"OWMCB004":PatchWorld.CREATIVE?"OWMCB003":"OWMCB002").getBytes(java.nio.charset.StandardCharsets.US_ASCII));wire.putInt(PatchWorld.NEW_WORLD?4:PatchWorld.CREATIVE?3:2).putInt(vertices.size()).putInt(128).putInt(128);
        wire.putLong(session).putLong(++sequence).putLong(client.world.getTime()).putLong(System.currentTimeMillis());wire.putInt(occupancy.size()).putInt(0);
        for(var block:occupancy) wire.putInt(block.x).putInt(block.y).putInt(block.z).putInt(block.state);
        for(var vertex:vertices) wire.putFloat(vertex.x).putFloat(vertex.y).putFloat(vertex.z).putFloat(vertex.u).putFloat(vertex.v).putFloat(vertex.shade).putInt(vertex.tint);
        wire.put(atlas);
        Path directory=Path.of(System.getProperty("owmc.exportDirectory"));Files.createDirectories(directory);
        Files.write(directory.resolve("patch-mesh.tmp"),wire.array());
        Files.move(directory.resolve("patch-mesh.tmp"),directory.resolve("patch-mesh.bin"),StandardCopyOption.REPLACE_EXISTING,StandardCopyOption.ATOMIC_MOVE);
        var metadata=new LinkedHashMap<String,Object>();metadata.put("source","actual-minecraft-world-baked-models");metadata.put("session",session);
        metadata.put("sequence",sequence);metadata.put("worldTick",client.world.getTime());metadata.put("blocks",occupancy.size());metadata.put("vertices",vertices.size());
        metadata.put("states",states);metadata.put("mode",PatchWorld.NEW_WORLD?"minecraft-flat-world":PatchWorld.CREATIVE?"creative-superflat":"patch-lab");metadata.put("center",new int[]{cx,cz});metadata.put("materials",materials.keySet().stream().map(Identifier::toString).toList());
        Files.writeString(directory.resolve("patch-source.json"),new Gson().toJson(metadata));
        if(sequence==1||sequence%120==0) System.out.println("[OWMCGuest] Actual patch exported: "+metadata);
    }
}
