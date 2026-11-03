package lab.owmcguest;

import com.google.gson.*;
import java.nio.file.*;
import java.security.MessageDigest;
import java.util.*;
import net.minecraft.client.render.*;
import net.minecraft.client.util.math.MatrixStack;

/** c3/02fe original geometry + BC4 mask + audited stage2 HDR color.
 * Native dynamic ramps, expansion/timing and HDR->MC LDR remain MC adaptation.
 * Does not select targets or control the existing red silhouettes. */
final class HanzoSonicPulseMesh {
    private static final Map<String,HanzoSonicPulseMesh> CACHE=new HashMap<>();
    private final OriginalMeshPack pack;
    private HanzoSonicPulseMesh(OriginalMeshPack pack){this.pack=pack;}
    static HanzoSonicPulseMesh get(String name)throws Exception{
        var cached=CACHE.get(name);if(cached!=null)return cached;
        if(!name.equals("hanzo-sonic-pulse")&&!name.equals("hanzo-sonic-sense"))throw new IllegalArgumentException("Sonic mesh name");
        var root=PrivateAssetPaths.meshes().resolve(name).toRealPath();
        var proof=JsonParser.parseString(Files.readString(root.resolve("provenance.json"))).getAsJsonObject();var files=proof.getAsJsonObject("files");
        if(!"0.8.0.24919".equals(proof.get("clientBuild").getAsString())||!files.has("pack.json")||!files.has("0c00000000001298.png"))throw new IllegalArgumentException("Sonic pack provenance");
        for(var e:files.entrySet()){
            var path=root.resolve(e.getKey()).toRealPath();
            if(!path.startsWith(root)||Files.size(path)>16*1024*1024)throw new IllegalArgumentException("Sonic path/size");
            String hash=HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(Files.readAllBytes(path)));
            if(!hash.equals(e.getValue().getAsString()))throw new IllegalArgumentException("Sonic asset hash");
        }
        var d=JsonParser.parseString(Files.readString(root.resolve("pack.json"))).getAsJsonObject();var gson=new Gson();
        var spec=HanzoSonicPackIdentity.validate(name,d,proof);
        float[] p=gson.fromJson(d.get("positions"),float[].class),n=gson.fromJson(d.get("normals"),float[].class),t=gson.fromJson(d.get("uv"),float[].class);
        int count=spec.vertices();if(p.length!=count*3||n.length!=p.length||t.length!=count*2)throw new IllegalArgumentException("Sonic mesh arrays");
        for(float[] array:new float[][]{p,n,t})for(float x:array)if(!Float.isFinite(x))throw new IllegalArgumentException("Sonic nonfinite array");
        for(float x:p)if(Math.abs(x)>4)throw new IllegalArgumentException("Sonic mesh bounds");
        var indices=new ArrayList<Integer>();for(var ge:d.getAsJsonArray("groups"))for(int i:gson.fromJson(ge.getAsJsonObject().get("indices"),int[].class)){
            if(i<0||i>=count)throw new IllegalArgumentException("Sonic index");indices.add(i);
        }
        if(indices.size()!=spec.triangles()*3)throw new IllegalArgumentException("Sonic triangles");
        var pack=OriginalMeshPack.get(name);if(pack==null)throw new IllegalArgumentException("Sonic pack load: "+OriginalMeshPack.ERRORS.get(name));
        var mesh=new HanzoSonicPulseMesh(pack);CACHE.put(name,mesh);return mesh;
    }
    void draw(VertexConsumerProvider.Immediate buffers,MatrixStack matrices,float radius,int alpha){
        matrices.scale(radius*2,radius*2,radius*2);matrices.translate(0,-.499487,0);
        pack.draw(buffers,matrices.peek(),LightmapTextureManager.MAX_LIGHT_COORDINATE,1,1,1,Math.max(0,Math.min(255,alpha))/255f);
    }
}
