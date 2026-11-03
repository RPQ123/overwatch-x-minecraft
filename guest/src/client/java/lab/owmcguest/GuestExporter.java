package lab.owmcguest;

import java.nio.ByteBuffer;
import java.nio.ByteOrder;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.StandardCopyOption;
import java.util.ArrayList;
import net.fabricmc.api.ClientModInitializer;
import net.fabricmc.fabric.api.client.event.lifecycle.v1.ClientTickEvents;
import net.minecraft.block.Blocks;
import net.minecraft.client.MinecraftClient;
import net.minecraft.client.texture.NativeImage;
import net.minecraft.util.Identifier;
import net.minecraft.util.math.Direction;
import net.minecraft.util.math.random.Random;

/** One real model/material exported from a real block in the isolated guest world. */
public final class GuestExporter implements ClientModInitializer {
    private boolean exported;
    @Override public void onInitializeClient() {
        ClientTickEvents.END_CLIENT_TICK.register(client -> {
            if (exported || !Boolean.getBoolean("owmc.exportProof") || client.world == null || GuestMod.proofBlock == null) return;
            if (!client.world.getBlockState(GuestMod.proofBlock).isOf(Blocks.STONE)) return;
            exported = true;
            try { export(client); }
            catch (Exception error) { System.err.println("[OWMCGuest] Export failed: " + error); }
        });
    }
    private void export(MinecraftClient client) throws Exception {
        var state = client.world.getBlockState(GuestMod.proofBlock);
        var model = client.getBlockRenderManager().getModel(state);
        var vertices = new ArrayList<float[]>();
        for (Direction face : Direction.values()) {
            for (var quad : model.getQuads(state, face, Random.create(42))) {
                int[] data = quad.getVertexData();
                if (data.length != 32) throw new IllegalArgumentException("Unexpected quad vertex format");
                var sprite = quad.getSprite();
                float shade = switch (face) { case UP -> 1; case DOWN -> .5f; case EAST, WEST -> .6f; default -> .8f; };
                for (int index : new int[]{0, 1, 2, 0, 2, 3}) {
                    int offset = index * 8;
                    vertices.add(new float[]{Float.intBitsToFloat(data[offset]), Float.intBitsToFloat(data[offset + 1]),
                        Float.intBitsToFloat(data[offset + 2]),
                        (Float.intBitsToFloat(data[offset + 4]) - sprite.getMinU()) / (sprite.getMaxU() - sprite.getMinU()),
                        (Float.intBitsToFloat(data[offset + 5]) - sprite.getMinV()) / (sprite.getMaxV() - sprite.getMinV()), shade});
                }
            }
        }
        if (vertices.size() != 36) throw new IllegalArgumentException("Expected the actual six-face stone cube");
        var resource = client.getResourceManager().getResource(Identifier.ofVanilla("textures/block/stone.png")).orElseThrow();
        Path directory = Path.of(System.getProperty("owmc.exportDirectory"));
        Files.createDirectories(directory);
        try (var stream = resource.getInputStream(); var image = NativeImage.read(stream)) {
            if (image.getWidth() > 256 || image.getHeight() > 256) throw new IllegalArgumentException("Proof texture exceeds budget");
            ByteBuffer output = ByteBuffer.allocate(24 + vertices.size() * 24 + image.getWidth() * image.getHeight() * 4)
                                          .order(ByteOrder.LITTLE_ENDIAN);
            output.put("OWMCB001".getBytes(java.nio.charset.StandardCharsets.US_ASCII));
            output.putInt(1).putInt(vertices.size()).putInt(image.getWidth()).putInt(image.getHeight());
            for (float[] vertex : vertices) for (float value : vertex) output.putFloat(value);
            // NativeImage 1.21.1 uses ABGR-packed color; wire texture is RGBA8.
            for (int y = 0; y < image.getHeight(); y++) for (int x = 0; x < image.getWidth(); x++) {
                int abgr = image.getColor(x, y);
                output.put((byte)abgr).put((byte)(abgr >> 8)).put((byte)(abgr >> 16)).put((byte)(abgr >> 24));
            }
            Path temporary = directory.resolve("stone-mesh.tmp");
            Files.write(temporary, output.array());
            Files.move(temporary, directory.resolve("stone-mesh.bin"), StandardCopyOption.REPLACE_EXISTING, StandardCopyOption.ATOMIC_MOVE);
            String metadata = "{\"source\":\"real-minecraft-client-model\",\"block\":\"minecraft:stone\",\"vertices\":36,"
                + "\"worldTick\":" + client.world.getTime() + ",\"worldPosition\":[" + GuestMod.proofBlock.getX() + ","
                + GuestMod.proofBlock.getY() + "," + GuestMod.proofBlock.getZ() + "]}";
            Files.writeString(directory.resolve("stone-mesh-source.json"), metadata);
            System.out.println("[OWMCGuest] Exported original stone block model/texture: " + directory);
        }
    }
}
