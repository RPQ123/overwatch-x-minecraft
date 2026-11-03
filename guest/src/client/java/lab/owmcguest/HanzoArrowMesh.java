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

/** Hanzo-only reader of build_mesh_pack output. Shared OriginalMeshPack is unchanged.
 * b8d contains THREE overlapping heads: part0 normal, part2 scatter, part3 sonic;
 * part1 shaft and part4 fletching are common. This static selection is an MC
 * presentation adaptation inferred from extracted geometry, not native animation.
 * Never silently draw all heads together or use iron-block fallback for a mask. */
final class HanzoArrowMesh {
    enum Kind { PRIMARY, SONIC, SCATTER }
    private static final Map<Kind,HanzoArrowMesh> CACHE=new EnumMap<>(Kind.class);
    static final Map<String,Float> LENGTHS=new java.util.concurrent.ConcurrentHashMap<>();
    private final float[] positions,normals,uv;
    private final List<Identifier> textures=new ArrayList<>();
    private final List<int[]> groups=new ArrayList<>();
    private final float tip,axisY;
    private HanzoArrowMesh(float[] p,float[] n,float[] t,float z,float y){positions=p;normals=n;uv=t;tip=z;axisY=y;}
    static HanzoArrowMesh get(Kind kind)throws Exception{
        var mesh=CACHE.get(kind);if(mesh!=null)return mesh;
        String name=switch(kind){case PRIMARY->"hanzo-arrow-primary";case SONIC->"hanzo-arrow-sonic";case SCATTER->"hanzo-arrow-scatter";};
        var root=PrivateAssetPaths.meshes().resolve(name).toRealPath();
        var proof=JsonParser.parseString(Files.readString(root.resolve("provenance.json"))).getAsJsonObject();
        if(!"0.8.0.24919".equals(proof.get("clientBuild").getAsString()))throw new IllegalArgumentException("Hanzo build");
        var files=proof.getAsJsonObject("files");
        if(!files.has("pack.json"))throw new IllegalArgumentException("Hanzo pack hash missing");
        for(var e:files.entrySet()){
            var path=root.resolve(e.getKey()).toRealPath();
            if(!path.startsWith(root)||Files.size(path)>16*1024*1024)throw new IllegalArgumentException("Hanzo asset path/size");
            String hash=HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(Files.readAllBytes(path)));
            if(!hash.equals(e.getValue().getAsString()))throw new IllegalArgumentException("Hanzo asset hash "+e.getKey());
        }
        var d=JsonParser.parseString(Files.readString(root.resolve("pack.json"))).getAsJsonObject();var gson=new Gson();
        String entity=switch(kind){case PRIMARY->"0400000000000144";case SONIC->"0400000000000149";case SCATTER->"04000000000001a4";};
        if(d.get("schema").getAsInt()!=1||!"meters".equals(d.get("units").getAsString())
            ||!entity.equals(d.get("entity").getAsString())||!"0d00000000000b8d".equals(d.get("model").getAsString()))throw new IllegalArgumentException("Hanzo pack identity");
        float[] p=gson.fromJson(d.get("positions"),float[].class),n=gson.fromJson(d.get("normals"),float[].class),t=gson.fromJson(d.get("uv"),float[].class);
        if(p.length!=2304*3||n.length!=p.length||t.length!=2304*2)throw new IllegalArgumentException("Hanzo LOD0 layout");
        for(float[] values:new float[][]{p,n,t})for(float x:values)if(!Float.isFinite(x))throw new IllegalArgumentException("Hanzo nonfinite array");
        for(float x:p)if(Math.abs(x)>4)throw new IllegalArgumentException("Hanzo position bounds");
        int head=switch(kind){case PRIMARY->0;case SCATTER->2;case SONIC->3;};
        var selected=new ArrayList<int[]>();var selectedTextures=new ArrayList<String>();float tip=-Float.MAX_VALUE;
        float lowY=Float.MAX_VALUE,highY=-Float.MAX_VALUE,tail=Float.MAX_VALUE;int total=0,kept=0;
        for(var item:d.getAsJsonArray("groups")){
            var group=item.getAsJsonObject();int[] ids=gson.fromJson(group.get("indices"),int[].class);
            if(ids.length%3!=0)throw new IllegalArgumentException("Hanzo triangles");
            var filtered=new ArrayList<Integer>();
            for(int i=0;i<ids.length;i+=3){total++;
                int part=-1;boolean keep=true;
                for(int c=0;c<3;c++){int v=ids[i+c];if(v<0||v>=2304)throw new IllegalArgumentException("Hanzo index");
                    int s=v<536?0:v<837?1:v<1268?2:v<2079?3:4;
                    if(part!=-1&&s!=part)throw new IllegalArgumentException("Hanzo mixed submesh triangle");part=s;}
                keep=part==head||part==1||part==4;
                if(keep){kept++;for(int c=0;c<3;c++){int v=ids[i+c];filtered.add(v);tip=Math.max(tip,p[v*3+2]);tail=Math.min(tail,p[v*3+2]);lowY=Math.min(lowY,p[v*3+1]);highY=Math.max(highY,p[v*3+1]);}}
            }
            if(!filtered.isEmpty()){
                String tex=group.get("texture").getAsString();
                if(!tex.matches("0c[0-9a-f]{14}")||!files.has(tex+".png"))throw new IllegalArgumentException("Hanzo unbound color");
                selected.add(filtered.stream().mapToInt(Integer::intValue).toArray());selectedTextures.add(tex);
            }
        }
        int expected=switch(kind){case PRIMARY->1390;case SCATTER->1312;case SONIC->1748;};
        if(total!=2938||kept!=expected)throw new IllegalArgumentException("Hanzo selected geometry changed");
        mesh=new HanzoArrowMesh(p,n,t,tip,(lowY+highY)/2);
        for(int i=0;i<selected.size();i++){
            String tex=selectedTextures.get(i);var id=Identifier.of("owmcguest","private/hanzo/"+name+"/"+tex);
            try(var in=Files.newInputStream(root.resolve(tex+".png"))){MinecraftClient.getInstance().getTextureManager().registerTexture(id,new NativeImageBackedTexture(NativeImage.read(in)));}
            mesh.textures.add(id);mesh.groups.add(selected.get(i));
        }
        LENGTHS.put(kind.name(),tip-tail);CACHE.put(kind,mesh);return mesh;
    }
    void draw(VertexConsumerProvider.Immediate buffers,MatrixStack matrices,int light){
        // Sweep/contact positions represent the arrow tip; +Z is the original long axis.
        matrices.translate(0,-axisY,-tip);var entry=matrices.peek();
        for(int k=0;k<groups.size();k++){
            var layer=RenderLayer.getEntityCutoutNoCull(textures.get(k));var consumer=buffers.getBuffer(layer);int[] ids=groups.get(k);
            for(int tri=0;tri<ids.length;tri+=3)for(int c:new int[]{0,1,2,2}){
                int i=ids[tri+c];consumer.vertex(entry.getPositionMatrix(),positions[i*3],positions[i*3+1],positions[i*3+2]).color(255,255,255,255)
                    .texture(uv[i*2],uv[i*2+1]).overlay(OverlayTexture.DEFAULT_UV).light(light)
                    .normal(entry,normals[i*3],normals[i*3+1],normals[i*3+2]);
            }buffers.draw(layer);
        }
    }
}
