package lab.owmcguest;

import com.google.gson.*;

/** Pure manifest contract for the directly extracted 02fe effect packs. The
 * retired 0149 research bundle is intentionally NOT an accepted alternate root. */
public final class HanzoSonicPackIdentity {
    public static final String EFFECT="03000000000002fe";
    public record Spec(String model,String material,int offset,int vertices,int triangles){}
    private HanzoSonicPackIdentity(){}
    private static void require(boolean b,String why){if(!b)throw new IllegalArgumentException("Sonic "+why);}
    private static String string(JsonObject o,String key){require(o!=null&&o.has(key)&&!o.get(key).isJsonNull(),"manifest field "+key);return o.get(key).getAsString();}
    public static Spec validate(String name,JsonObject data,JsonObject proof){
        boolean pulse="hanzo-sonic-pulse".equals(name);require(pulse||"hanzo-sonic-sense".equals(name),"mesh name");
        var spec=pulse?new Spec("0d00000000001385","0e0000008a92fe7f",948,3354,6240)
            :new Spec("0d00000000000dbf","0e0000007b543afe",1284,1677,3120);
        require("0.8.0.24919".equals(string(proof,"clientBuild")),"client build");
        require(EFFECT.equals(string(data,"entity"))&&EFFECT.equals(string(proof,"entity")),"effect root; repack direct 02fe, legacy 0149 refused");
        require(data.get("schema").getAsInt()==1&&"meters".equals(string(data,"units"))&&name.equals(string(data,"name")),"schema/name/units");
        require(spec.model().equals(string(data,"model"))&&spec.material().equals(string(data,"material")),"model/material identity");
        String suffix=EFFECT+"/"+spec.model()+"."+spec.material()+".lod0.mesh.json";
        require(string(proof,"source").replace('\\','/').endsWith(suffix),"direct source manifest");
        var rows=proof.getAsJsonArray("effectRenderers");require(rows!=null&&rows.size()==1,"renderer provenance count");
        var row=rows.get(0).getAsJsonObject();require(EFFECT.equals(string(row,"effect"))&&"particle-renderer".equals(string(row,"kind"))
            &&spec.model().equals(string(row,"model"))&&spec.material().equals(string(row,"material"))
            &&row.get("offset").getAsInt()==spec.offset()&&row.get("modelOffset").getAsInt()==spec.offset()+184
            &&row.get("materialOffset").getAsInt()==spec.offset()+248,"original renderer/raw offset identity");
        var parameters=data.getAsJsonObject("materialParameters");var proofParameters=proof.getAsJsonObject("materialParameters");
        require(parameters!=null&&proofParameters!=null&&parameters.equals(proofParameters)&&parameters.has(spec.material()),"audited material manifest");
        var material=parameters.getAsJsonObject(spec.material());require(material.get("resolved").getAsBoolean()
            &&"additive".equals(string(material,"blendMode")),"audited additive material unresolved");
        var files=proof.getAsJsonObject("files");String render=string(material,"renderTexture");
        require(files!=null&&files.has("pack.json")&&files.has("0c00000000001298.png")&&render.matches("[a-z0-9_-]+\\.png")&&files.has(render),"hashed native mask/render texture missing");
        return spec;
    }
}
