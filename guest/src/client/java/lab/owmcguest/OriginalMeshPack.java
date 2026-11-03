package lab.owmcguest;

import com.google.gson.*;
import java.nio.file.*;
import java.security.MessageDigest;
import java.util.*;
import java.util.concurrent.ConcurrentSkipListMap;
import net.minecraft.client.MinecraftClient;
import net.minecraft.client.render.*;
import net.minecraft.client.texture.*;
import net.minecraft.client.util.math.MatrixStack;
import net.minecraft.util.Identifier;
import org.joml.Vector3f;

/** 通用原版网格包（tools/build_mesh_pack.py 生成，私有目录 ~/.universal-modder/assets/owmc-mesh/<名称>/）。
 * 校验 provenance 后按材质绘制。原版 HDR/混合到 MC LDR 的转换是显式近似；不执行原版 shader。 */
final class OriginalMeshPack {
    private static final Map<String,OriginalMeshPack> CACHE=new HashMap<>();
    private static final Identifier GREY=Identifier.of("minecraft","textures/block/iron_block.png");
    // HTTP diagnostics iterate/toString while the render thread updates errors.
    // Keep sorted Map output, with weakly consistent concurrent iteration.
    static final Map<String,String> ERRORS=new ConcurrentSkipListMap<>();
    private final float[] positions,normals,uv;private final List<Identifier> textures=new ArrayList<>();private final List<int[]> groups=new ArrayList<>();
    private final List<Material> materials=new ArrayList<>();
    private Skin skin;
    private long drawCalls,drawnTriangles,lastDrawWall;

    private record Material(float[] tint,float emissive,String blend,Identifier emission,boolean resolved){
        static Material read(JsonObject o,Identifier emission){
            float[] tint={1,1,1,1};
            if(o.has("tint")){
                var a=o.getAsJsonArray("tint");if(a.size()!=4)throw new IllegalArgumentException("material tint");
                for(int i=0;i<4;i++){tint[i]=a.get(i).getAsFloat();if(!Float.isFinite(tint[i])||tint[i]<0||tint[i]>1)throw new IllegalArgumentException("material tint range");}
            }
            float e=o.has("emissive")?o.get("emissive").getAsFloat():0;
            String blend=o.has("blendMode")?o.get("blendMode").getAsString():"cutout";
            if(!Float.isFinite(e)||e<0||e>256||!Set.of("cutout","alpha","additive","skip").contains(blend))throw new IllegalArgumentException("material emission/blend");
            return new Material(tint,e,blend,emission,o.has("resolved")&&o.get("resolved").getAsBoolean());
        }
    }
    private record Skin(int[][] indices,int[][] weights,int[] palette,float[][] bind){ }

    private OriginalMeshPack(float[] p,float[] n,float[] t){positions=p;normals=n;uv=t;}

    /** Read-only diagnostics: never loads textures from the HTTP/server thread. */
    static JsonObject diagnostics(String name){
        var d=new JsonObject();var pack=CACHE.get(name);d.addProperty("loaded",pack!=null);
        String error=ERRORS.get(name);if(error!=null)d.addProperty("error",error);
        if(pack==null)return d;
        d.addProperty("skinBones",pack.boneCount());d.addProperty("drawCalls",pack.drawCalls);
        d.addProperty("drawnTriangles",pack.drawnTriangles);d.addProperty("lastDrawWall",pack.lastDrawWall);
        d.addProperty("additiveGroups",pack.materials.stream().filter(m->m.blend.equals("additive")).count());
        d.addProperty("emissionLayers",pack.materials.stream().filter(m->m.emission!=null).count());
        d.addProperty("skippedGroups",pack.materials.stream().filter(m->m.blend.equals("skip")).count());
        d.addProperty("nativeShaderEvaluated",false);return d;
    }

    static OriginalMeshPack get(String name){
        if(CACHE.containsKey(name))return CACHE.get(name);
        OriginalMeshPack pack=null;
        try{pack=load(name);ERRORS.remove(name);}catch(Exception e){ERRORS.put(name,e.toString());System.err.println("OWMC original mesh "+name+" unavailable: "+e);}
        CACHE.put(name,pack);return pack;
    }
    private static OriginalMeshPack load(String name)throws Exception{
        var root=PrivateAssetPaths.meshes().resolve(name).toRealPath();
        var proof=JsonParser.parseString(Files.readString(root.resolve("provenance.json"))).getAsJsonObject();
        if(!proof.get("clientBuild").getAsString().equals("0.8.0.24919"))throw new IllegalArgumentException("client build");
        var files=proof.getAsJsonObject("files");if(!files.has("pack.json"))throw new IllegalArgumentException("unhashed pack");
        for(var e:files.entrySet()){
            var path=root.resolve(e.getKey()).toRealPath();
            if(!path.startsWith(root)||Files.size(path)>16*1024*1024)throw new IllegalArgumentException("asset path/size "+e.getKey());
            var hash=HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(Files.readAllBytes(path)));
            if(!hash.equals(e.getValue().getAsString()))throw new IllegalArgumentException("asset hash "+e.getKey());
        }
        var d=JsonParser.parseString(Files.readString(root.resolve("pack.json"))).getAsJsonObject();var g=new Gson();
        if(d.get("schema").getAsInt()!=1||!d.get("units").getAsString().equals("meters"))throw new IllegalArgumentException("pack schema");
        if(name.equals("mei-pillar")&&(!d.has("entity")||!d.has("model")
            ||!d.get("entity").getAsString().equals("0400000000000932")
            ||!d.get("model").getAsString().equals("0d00000000002a64")))
            throw new IllegalArgumentException("ice pillar must use entity0932 direct model2a64");
        var p=g.fromJson(d.get("positions"),float[].class);var n=g.fromJson(d.get("normals"),float[].class);var t=g.fromJson(d.get("uv"),float[].class);
        int count=p.length/3;if(count==0||p.length%3!=0||n.length!=p.length||t.length!=count*2)throw new IllegalArgumentException("pack arrays");
        // The original Hanzo dragon is 40.66 m long (centered Z +/-20.34).
        for(float x:p)if(!Float.isFinite(x)||Math.abs(x)>64)throw new IllegalArgumentException("pack position");
        for(float[] a:new float[][]{n,t})for(float x:a)if(!Float.isFinite(x))throw new IllegalArgumentException("pack nonfinite");
        var pack=new OriginalMeshPack(p,n,t);
        if(d.has("skin")&&!d.get("skin").isJsonNull()){
            var s=d.getAsJsonObject("skin");int[][] bones=g.fromJson(s.get("boneIndices"),int[][].class),weights=g.fromJson(s.get("weightsUnorm8"),int[][].class);
            int[] palette=g.fromJson(s.get("palette"),int[].class);float[][] bind=g.fromJson(s.get("bindPositions"),float[][].class);
            int[] parents=g.fromJson(s.get("parents"),int[].class);
            if(bones.length!=count||weights.length!=count||bind.length!=67||palette.length!=64||parents.length!=bind.length)throw new IllegalArgumentException("skin arrays");
            for(int i=0;i<bind.length;i++){
                if(bind[i].length!=3||parents[i]<-1||parents[i]>=i)throw new IllegalArgumentException("skin hierarchy/bind");
                for(float x:bind[i])if(!Float.isFinite(x)||Math.abs(x)>64)throw new IllegalArgumentException("skin bind bounds");
            }
            for(int i:palette)if(i<0||i>=bind.length)throw new IllegalArgumentException("skin palette");
            for(int i=0;i<count;i++){
                if(bones[i].length!=4||weights[i].length!=4)throw new IllegalArgumentException("skin influence count");
                int sum=0;for(int j=0;j<4;j++){if(bones[i][j]<0||bones[i][j]>=palette.length||weights[i][j]<0||weights[i][j]>255)throw new IllegalArgumentException("skin influence");sum+=weights[i][j];}
                if(sum!=255)throw new IllegalArgumentException("skin weight sum");
            }
            pack.skin=new Skin(bones,weights,palette,bind);
        }
        var params=d.has("materialParameters")?d.getAsJsonObject("materialParameters"):new JsonObject();
        for(var ge:d.getAsJsonArray("groups")){
            var o=ge.getAsJsonObject();var ids=g.fromJson(o.get("indices"),int[].class);
            if(ids.length%3!=0)throw new IllegalArgumentException("pack triangles");
            for(int i:ids)if(i<0||i>=count)throw new IllegalArgumentException("pack index");
            String mat=o.has("material")&&!o.get("material").isJsonNull()?o.get("material").getAsString():"";
            var material=params.has(mat)?params.getAsJsonObject(mat):new JsonObject();
            String tex=o.get("texture").getAsString();String file=material.has("renderTexture")?material.get("renderTexture").getAsString():tex+".png";
            Identifier id=tex.equals("grey")&&!material.has("renderTexture")?GREY:loadTexture(root,files,name,file);
            Identifier emission=material.has("emissiveTexture")?loadTexture(root,files,name,material.get("emissiveTexture").getAsString()):null;
            pack.textures.add(id);pack.groups.add(ids);
            pack.materials.add(Material.read(material,emission));
        }
        return pack;
    }
    private static Identifier loadTexture(Path root,JsonObject files,String name,String file)throws Exception{
        if(!file.matches("[a-z0-9_-]+\\.png")||!files.has(file))throw new IllegalArgumentException("unhashed texture path");
        var path=root.resolve(file).toRealPath();if(!path.startsWith(root))throw new IllegalArgumentException("texture path");
        var id=Identifier.of("owmcguest","private/mesh/"+name+"/"+file);
        try(var in=Files.newInputStream(path)){MinecraftClient.getInstance().getTextureManager().registerTexture(id,new NativeImageBackedTexture(NativeImage.read(in)));}
        return id;
    }
    /** 用实体材质绘制；light 为光照坐标。 */
    void draw(VertexConsumerProvider.Immediate buffers,MatrixStack.Entry entry,int light){
        draw(buffers,entry,light,1,1,1,1);
    }
    /** Extra instance tint multiplies the audited material tint; alpha also fades additive RGB. */
    void draw(VertexConsumerProvider.Immediate buffers,MatrixStack.Entry entry,int light,float r,float g,float b,float alpha){
        for(float x:new float[]{r,g,b,alpha})if(!Float.isFinite(x)||x<0||x>1)throw new IllegalArgumentException("draw tint");
        drawMesh(buffers,entry,light,positions,normals,false,Float.NEGATIVE_INFINITY,new float[]{r,g,b,alpha});
    }
    /** 原版网格的呈现形变；调用方说明动画/着色近似，旧的刚性 draw 路径保持不变。 */
    @FunctionalInterface interface Deformation {void apply(Vector3f position,Vector3f normal);}
    void drawEffect(VertexConsumerProvider.Immediate buffers,MatrixStack.Entry entry,Deformation deformation,float minSourceZ){
        var p=positions.clone();var n=normals.clone();var at=new Vector3f();var normal=new Vector3f();
        for(int i=0;i<p.length;i+=3){
            at.set(p[i],p[i+1],p[i+2]);normal.set(n[i],n[i+1],n[i+2]);deformation.apply(at,normal);
            p[i]=at.x;p[i+1]=at.y;p[i+2]=at.z;n[i]=normal.x;n[i+1]=normal.y;n[i+2]=normal.z;
        }
        drawMesh(buffers,entry,LightmapTextureManager.MAX_LIGHT_COORDINATE,p,n,true,minSourceZ,new float[]{1,1,1,1});
    }
    @FunctionalInterface interface BoneAnimation {void apply(int bone,Vector3f position,Vector3f normal);}
    int boneCount(){return skin==null?0:skin.bind.length;}
    Vector3f boneBindPosition(int bone){return new Vector3f(skin.bind[bone]);}
    /** Native palette/UNORM8 weights, MC-authored bone delta poses, then world-path deformation. */
    boolean drawSkinnedEffect(VertexConsumerProvider.Immediate buffers,MatrixStack.Entry entry,BoneAnimation pose,Deformation path,float minSourceZ){
        if(skin==null){drawEffect(buffers,entry,path,minSourceZ);return false;}
        var p=positions.clone();var n=normals.clone();var v=new Vector3f();var normal=new Vector3f();var sum=new Vector3f();var ns=new Vector3f();
        for(int i=0;i<positions.length/3;i++){
            sum.zero();ns.zero();
            for(int j=0;j<4;j++){
                int weight=skin.weights[i][j];if(weight==0)continue;
                v.set(positions[i*3],positions[i*3+1],positions[i*3+2]);normal.set(normals[i*3],normals[i*3+1],normals[i*3+2]);
                pose.apply(skin.palette[skin.indices[i][j]],v,normal);sum.fma(weight/255f,v);ns.fma(weight/255f,normal);
            }
            if(ns.lengthSquared()<1e-12f)ns.set(normals[i*3],normals[i*3+1],normals[i*3+2]);else ns.normalize();
            path.apply(sum,ns);p[i*3]=sum.x;p[i*3+1]=sum.y;p[i*3+2]=sum.z;n[i*3]=ns.x;n[i*3+1]=ns.y;n[i*3+2]=ns.z;
        }
        drawMesh(buffers,entry,LightmapTextureManager.MAX_LIGHT_COORDINATE,p,n,true,minSourceZ,new float[]{1,1,1,1});return true;
    }
    private void drawMesh(VertexConsumerProvider.Immediate buffers,MatrixStack.Entry entry,int light,float[] p,float[] n,boolean effect,float minSourceZ,float[] tint){
        for(int k=0;k<groups.size();k++){
            var m=materials.get(k);if(m.blend.equals("skip"))continue;
            var layer=switch(m.blend){case "additive"->RenderLayer.getEyes(textures.get(k));case "alpha"->RenderLayer.getEntityTranslucentEmissive(textures.get(k));default->effect&&!m.resolved?RenderLayer.getEntityTranslucentEmissive(textures.get(k)):RenderLayer.getEntityCutoutNoCull(textures.get(k));};
            emit(buffers,entry,layer,m.emissive>0?LightmapTextureManager.MAX_LIGHT_COORDINATE:light,p,n,groups.get(k),minSourceZ,m.tint,tint,m.blend.equals("additive"));
            if(m.emission!=null)emit(buffers,entry,RenderLayer.getEyes(m.emission),LightmapTextureManager.MAX_LIGHT_COORDINATE,p,n,groups.get(k),minSourceZ,m.tint,tint,true);
        }
    }
    private void emit(VertexConsumerProvider.Immediate buffers,MatrixStack.Entry entry,RenderLayer layer,int light,float[] p,float[] n,int[] ids,float minSourceZ,float[] materialTint,float[] tint,boolean additive){
            var c=buffers.getBuffer(layer);
            long triangles=0;
            float alpha=materialTint[3]*tint[3],rgbFade=additive?alpha:1;
            int r=Math.round(255*materialTint[0]*tint[0]*rgbFade),g=Math.round(255*materialTint[1]*tint[1]*rgbFade),b=Math.round(255*materialTint[2]*tint[2]*rgbFade),a=Math.round(255*alpha);
            for(int tri=0;tri<ids.length;tri+=3){
                // Grow the long dragon out of its release point rather than
                // exposing its entire tail behind the caster on the first tick.
                if(positions[ids[tri]*3+2]<minSourceZ&&positions[ids[tri+1]*3+2]<minSourceZ&&positions[ids[tri+2]*3+2]<minSourceZ)continue;
                triangles++;
                for(int corner:new int[]{0,1,2,2}){
                int i=ids[tri+corner];
                c.vertex(entry.getPositionMatrix(),p[i*3],p[i*3+1],p[i*3+2]).color(r,g,b,a)
                    .texture(uv[i*2],uv[i*2+1]).overlay(OverlayTexture.DEFAULT_UV).light(light)
                    .normal(entry,n[i*3],n[i*3+1],n[i*3+2]);
                }
            }
            buffers.draw(layer);
            if(triangles>0){drawCalls++;drawnTriangles+=triangles;lastDrawWall=System.currentTimeMillis();}
    }
}
