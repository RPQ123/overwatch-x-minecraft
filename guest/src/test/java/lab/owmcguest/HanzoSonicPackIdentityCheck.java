package lab.owmcguest;

import com.google.gson.*;
import java.nio.file.*;
import java.security.MessageDigest;
import java.util.HexFormat;

/** Offline manifest/hash regression; no renderer, GL context or game launch. */
public final class HanzoSonicPackIdentityCheck {
    private static void rejected(String name,JsonObject d,JsonObject p,String reason){
        try{HanzoSonicPackIdentity.validate(name,d,p);throw new AssertionError("accepted "+reason);}catch(IllegalArgumentException expected){}
    }
    public static void main(String[] args)throws Exception{
        if(args.length!=1)throw new IllegalArgumentException("validation pack root required");
        for(String name:new String[]{"hanzo-sonic-pulse","hanzo-sonic-sense"}){
            var root=Path.of(args[0],name);var d=JsonParser.parseString(Files.readString(root.resolve("pack.json"))).getAsJsonObject();
            var p=JsonParser.parseString(Files.readString(root.resolve("provenance.json"))).getAsJsonObject();
            HanzoSonicPackIdentity.validate(name,d,p);
            for(var e:p.getAsJsonObject("files").entrySet()){
                var hash=HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(Files.readAllBytes(root.resolve(e.getKey()))));
                if(!hash.equals(e.getValue().getAsString()))throw new AssertionError("file hash "+e.getKey());
            }
            var old=d.deepCopy();var oldProof=p.deepCopy();old.addProperty("entity","0400000000000149");oldProof.addProperty("entity","0400000000000149");rejected(name,old,oldProof,"legacy 0149 root");
            rejected(name,d,oldProof,"mixed root manifests");
            var raw=p.deepCopy();raw.getAsJsonArray("effectRenderers").get(0).getAsJsonObject().addProperty("offset",0);rejected(name,d,raw,"wrong original raw offset");
            var wrong=d.deepCopy();wrong.addProperty("material","0e00000000000000");rejected(name,wrong,p,"other material");
            var source=p.deepCopy();source.addProperty("source",source.get("source").getAsString().replace("03000000000002fe","0400000000000149"));rejected(name,d,source,"derived legacy source");
            var parameters=d.deepCopy();var parameterProof=p.deepCopy();String mat=d.get("material").getAsString();
            parameters.getAsJsonObject("materialParameters").getAsJsonObject(mat).addProperty("resolved",false);
            parameterProof.add("materialParameters",parameters.get("materialParameters").deepCopy());rejected(name,parameters,parameterProof,"unaudited material");
            var missing=p.deepCopy();String tex=d.getAsJsonObject("materialParameters").getAsJsonObject(mat).get("renderTexture").getAsString();
            missing.getAsJsonObject("files").remove(tex);rejected(name,d,missing,"unhashed audited texture");
        }
        System.out.println("HanzoSonicPackIdentityCheck passed (direct 02fe packs, hashes, legacy refusal)");
    }
}
