package lab.owmcguest;

import com.google.gson.*;
import java.nio.file.*;
import net.fabricmc.fabric.api.client.rendering.v1.EntityRendererRegistry;
import net.minecraft.client.render.*;
import net.minecraft.client.render.entity.*;
import net.minecraft.client.util.math.MatrixStack;
import net.minecraft.util.Identifier;
import net.minecraft.util.math.RotationAxis;

/** Original private 24919 hero body meshes; MC owns the training NPC simulation. */
public final class HeroNpcRenderer extends EntityRenderer<HeroNpcEntity> {
    private static final float[][] bounds=new float[HeroNpcCatalog.ENTRIES.size()][];
    public static volatile String error="";public static long draws;
    public HeroNpcRenderer(EntityRendererFactory.Context context){super(context);shadowRadius=.35f;}
    static void register(){EntityRendererRegistry.register(HeroNpcEntity.TYPE,HeroNpcRenderer::new);}
    @Override public Identifier getTexture(HeroNpcEntity entity){return Identifier.ofVanilla("textures/block/iron_block.png");}
    @Override public void render(HeroNpcEntity e,float yaw,float tickDelta,MatrixStack matrices,VertexConsumerProvider buffers,int light){
        int index=e.heroIndex();var entry=HeroNpcCatalog.entry(index);String name="hero-npc-"+entry.id();
        try{
            var pack=OriginalMeshPack.get(name);if(pack==null)throw new IllegalStateException(OriginalMeshPack.ERRORS.getOrDefault(name,"hero mesh unavailable"));
            if(bounds[index]==null){
                var path=PrivateAssetPaths.meshes().resolve(name).resolve("pack.json");if(Files.size(path)>16*1024*1024)throw new IllegalArgumentException("hero mesh size");
                var data=JsonParser.parseString(Files.readString(path)).getAsJsonObject();var positions=data.getAsJsonArray("positions");
                float min=Float.POSITIVE_INFINITY,max=Float.NEGATIVE_INFINITY;for(int j=1;j<positions.size();j+=3){float y=positions.get(j).getAsFloat();min=Math.min(min,y);max=Math.max(max,y);}
                if(!Float.isFinite(min)||max-min<.5||max-min>5)throw new IllegalArgumentException("hero body bounds");bounds[index]=new float[]{min,max};
            }
            matrices.push();try{
                // This renderer derives directly from EntityRenderer, so it
                // must apply LivingEntity's synced scale itself (vanilla mob
                // renderers already do so). Collision uses the same attribute.
                float size=e.getScale();matrices.scale(size,size,size);shadowRadius=.35f*size;
                matrices.multiply(RotationAxis.POSITIVE_Y.rotationDegrees(-yaw));matrices.translate(0,-bounds[index][0],0);
                var immediate=buffers instanceof VertexConsumerProvider.Immediate i?i:net.minecraft.client.MinecraftClient.getInstance().getBufferBuilders().getEntityVertexConsumers();
                pack.draw(immediate,matrices.peek(),light,1,e.hurtTime>0?.45f:1,e.hurtTime>0?.45f:1,1);draws++;error="";
            }finally{matrices.pop();}
        }catch(Exception failure){error=name+": "+failure;}
        super.render(e,yaw,tickDelta,matrices,buffers,light);
    }
}
