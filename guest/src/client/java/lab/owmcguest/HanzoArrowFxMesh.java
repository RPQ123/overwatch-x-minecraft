package lab.owmcguest;

import com.google.gson.*;
import java.nio.file.*;
import java.security.MessageDigest;
import java.util.*;
import net.minecraft.client.MinecraftClient;
import net.minecraft.client.render.*;
import net.minecraft.client.texture.*;
import net.minecraft.client.util.math.MatrixStack;
import net.minecraft.util.Identifier;

/** Original 00801 star sprite / 075d trail mesh, UVs and texture samples.
 * BC4 is an intensity mask, never an iron/grey diffuse fallback. Native dynamic
 * colors are unresolved: mask tint (18,30,255) is an approximation derived by
 * normalizing the alpha-visible RGB mean of original BLUE 12d1, not RED 2dad.
 * getEyes is Minecraft's additive, unlit layer already used by native rockets. */
final class HanzoArrowFxMesh {
    private record Spec(String entity,String model,String material,String texture,boolean mask){}
    private static final Map<String,Spec> SPECS=Map.of(
        "primary-glow",new Spec("0144","0801","9537fc6e","12d1",false),
        "primary-trail",new Spec("0144","075d","98d4b643","0ac4",true),
        "sonic-glow",new Spec("0149","0801","6966f477","0242",true),
        "scatter-glow",new Spec("01a4","0801","2ded6c3b","12d1",false),
        "scatter-trail",new Spec("01a4","075d","181b690c","0ac4",true));
    private static final Map<String,HanzoArrowFxMesh> CACHE=new HashMap<>();
    private final float[] positions,normals,uv;private final int[] indices;private final Identifier texture;private final boolean tint;
    private HanzoArrowFxMesh(float[] p,float[] n,float[] t,int[] ids,Identifier tex,boolean color){positions=p;normals=n;uv=t;indices=ids;texture=tex;tint=color;}
    static HanzoArrowFxMesh get(String role)throws Exception{
        var existing=CACHE.get(role);if(existing!=null)return existing;var spec=SPECS.get(role);
        if(spec==null)throw new IllegalArgumentException("Hanzo FX role");String name="hanzo-arrow-"+role;
        var root=PrivateAssetPaths.meshes().resolve(name).toRealPath();
        var proof=JsonParser.parseString(Files.readString(root.resolve("provenance.json"))).getAsJsonObject();var files=proof.getAsJsonObject("files");
        String tex="0c0000000000"+spec.texture();
        if(!"0.8.0.24919".equals(proof.get("clientBuild").getAsString())||!files.has("pack.json")||!files.has(tex+".png"))throw new IllegalArgumentException("Hanzo FX provenance");
        for(var e:files.entrySet()){
            var path=root.resolve(e.getKey()).toRealPath();if(!path.startsWith(root)||Files.size(path)>16*1024*1024)throw new IllegalArgumentException("Hanzo FX path/size");
            var hash=HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(Files.readAllBytes(path)));
            if(!hash.equals(e.getValue().getAsString()))throw new IllegalArgumentException("Hanzo FX hash");
        }
        var d=JsonParser.parseString(Files.readString(root.resolve("pack.json"))).getAsJsonObject();var gson=new Gson();
        if(d.get("schema").getAsInt()!=1||!"meters".equals(d.get("units").getAsString())
            ||!("040000000000"+spec.entity()).equals(d.get("entity").getAsString())
            ||!("0d0000000000"+spec.model()).equals(d.get("model").getAsString())
            ||!("0e000000"+spec.material()).equals(d.get("material").getAsString()))throw new IllegalArgumentException("Hanzo FX identity");
        float[] p=gson.fromJson(d.get("positions"),float[].class),n=gson.fromJson(d.get("normals"),float[].class),t=gson.fromJson(d.get("uv"),float[].class);
        int count=spec.model().equals("075d")?18:8;
        if(p.length!=count*3||n.length!=p.length||t.length!=count*2)throw new IllegalArgumentException("Hanzo FX arrays");
        for(float[] a:new float[][]{p,n,t})for(float v:a)if(!Float.isFinite(v)||Math.abs(v)>4)throw new IllegalArgumentException("Hanzo FX array bounds");
        var ids=new ArrayList<Integer>();for(var ge:d.getAsJsonArray("groups"))for(int i:gson.fromJson(ge.getAsJsonObject().get("indices"),int[].class)){
            if(i<0||i>=count)throw new IllegalArgumentException("Hanzo FX index");ids.add(i);
        }
        if(ids.size()!=(count==18?16:4)*3)throw new IllegalArgumentException("Hanzo FX triangles");
        NativeImage image;try(var in=Files.newInputStream(root.resolve(tex+".png"))){image=NativeImage.read(NativeImage.Format.RGBA,in);}
        for(int y=0;y<image.getHeight();y++)for(int x=0;x<image.getWidth();x++){
            int color=image.getColor(x,y),alpha=spec.mask()?color&255:(color>>>24)&255;
            int r=spec.mask()?alpha:(color&255)*alpha/255,g=spec.mask()?alpha:((color>>>8)&255)*alpha/255,b=spec.mask()?alpha:((color>>>16)&255)*alpha/255;
            image.setColor(x,y,(alpha<<24)|(b<<16)|(g<<8)|r);
        }
        var id=Identifier.of("owmcguest","private/hanzo/fx/"+role);MinecraftClient.getInstance().getTextureManager().registerTexture(id,new NativeImageBackedTexture(image));
        var mesh=new HanzoArrowFxMesh(p,n,t,ids.stream().mapToInt(Integer::intValue).toArray(),id,spec.mask());CACHE.put(role,mesh);return mesh;
    }
    void draw(VertexConsumerProvider.Immediate buffers,MatrixStack matrices,float opacity){
        var entry=matrices.peek();var layer=RenderLayer.getEyes(texture);var consumer=buffers.getBuffer(layer);
        // Eyes uses additive ONE/ONE blending: premultiply vertex RGB as well
        // as alpha so a vanished afterglow actually fades on this layer.
        int r=Math.round((tint?18:255)*opacity),g=Math.round((tint?30:255)*opacity),b=Math.round(255*opacity),alpha=Math.round(255*opacity);
        for(int tri=0;tri<indices.length;tri+=3)for(int c:new int[]{0,1,2,2}){
            int i=indices[tri+c];consumer.vertex(entry.getPositionMatrix(),positions[i*3],positions[i*3+1],positions[i*3+2]).color(r,g,b,alpha)
                // Preserve 0 and 1 endpoints: fract(1)=0 collapses the entire
                // original sprite's UVs onto a transparent corner.
                .texture(uv[i*2],uv[i*2+1]).overlay(OverlayTexture.DEFAULT_UV).light(0x00f000f0)
                .normal(entry,normals[i*3],normals[i*3+1],normals[i*3+2]);
        }buffers.draw(layer);
    }
}
