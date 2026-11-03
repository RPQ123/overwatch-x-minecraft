package lab.owmcguest;

import com.google.gson.*;

/** Pinned-context/fallback fixtures, not an actual native child-arrow oracle. */
public final class HanzoScatterContextCheck {
    private static void check(boolean b,String reason){if(!b)throw new AssertionError(reason);}
    private static final long KEY=0x12302100L,TICK=1286*16L,NOW=1000;
    private static final HanzoScatterContext.Expected EXPECTED=new HanzoScatterContext.Expected(10,20,30,40,KEY,TICK);
    private static JsonObject report(double q){
        var o=new JsonObject();for(var entry:new Object[][]{{"pid",10},{"creation",20},{"hostGeneration",30},{"modelId",40},{"hero",HanzoScatterContext.HERO},
            {"probeVersion",16},{"protocol",3},{"epoch",50},{"failures",0},{"heartbeat",NOW}})o.addProperty((String)entry[0],(Number)entry[1]);
        o.addProperty("enabled",true);o.addProperty("restored",false);o.addProperty("overflow",false);o.addProperty("factoryCalibration",true);
        var r=new JsonObject();r.addProperty("resource",HanzoScatterContext.STRONG);r.addProperty("hero",HanzoScatterContext.HERO);r.addProperty("owner",40);
        r.addProperty("tick",1286);r.addProperty("volley",Long.toUnsignedString(0x8000000000000000L|KEY|1));r.addProperty("wallMs",NOW);
        r.addProperty("status",8);r.addProperty("type",1);r.addProperty("result",0);r.addProperty("shot",0);r.addProperty("pellet",0);
        r.addProperty("lifetime",10);r.addProperty("range",300);r.addProperty("speed",25+65*q);r.addProperty("evaluatedDamage",0);
        r.add("direction",JsonParser.parseString("[0,0,-1]"));var all=new JsonArray();all.add(r);o.add("factoryObservations",all);return o;
    }
    private static HanzoScatterContext.Numbers numbers(double q){return new HanzoScatterContext.Numbers(q,25+100*q,15+60*q,NOW);}
    private static void rejected(JsonObject report,HanzoScatterContext.Expected expected,HanzoScatterContext.Numbers numbers,long now,String reason){
        try{HanzoScatterContext.resolve(report,expected,numbers,now);throw new AssertionError("accepted "+reason);}catch(IllegalArgumentException correct){}
    }
    public static void main(String[] args){
        for(double q:new double[]{0,.5,1}){
            var p=HanzoScatterContext.resolve(report(q),EXPECTED,numbers(q),NOW);
            check(p.nativeValues()&&p.q()==q,"uses the provided typed native q");
            check(Math.abs(p.childSpeed()-.8*(20+65*q))<.00001,"pinned original child speed expression");
            check(p.parentDamage()==4*(25+100*q)&&p.childDamage()==4*(15+60*q),"MC 适配：用户要求，separate original 1dc/980 damage x4");
            check(p.velocity().z()==-(25+65*q),"actual original factory velocity, no camera retarget");
        }
        var p=HanzoScatterContext.resolve(report(1),EXPECTED,numbers(1),NOW);check(p.parentDamage()==500&&p.childDamage()==300,"unbound evaluatedDamage=0 is ignored; adaptation applied once");
        rejected(report(1),EXPECTED,null,NOW,"missing typed numbers");
        rejected(report(1),EXPECTED,new HanzoScatterContext.Numbers(.5,125,45,NOW),NOW,"q/factory mismatch; no q derivation from speed");
        rejected(report(.5),EXPECTED,new HanzoScatterContext.Numbers(.5,75,75,NOW),NOW,"stale contextual980");
        rejected(report(1),EXPECTED,new HanzoScatterContext.Numbers(Double.NaN,125,75,NOW),NOW,"nonfinite q");
        rejected(report(1),EXPECTED,new HanzoScatterContext.Numbers(1,0,75,NOW),NOW,"zero damage placeholder");
        rejected(report(1),EXPECTED,new HanzoScatterContext.Numbers(1,500,300,NOW),NOW,"already quadrupled values are not raw original numbers");
        rejected(report(1),EXPECTED,numbers(1),NOW+151,"stale report/numbers");
        rejected(report(1),new HanzoScatterContext.Expected(10,20,31,40,KEY,TICK),numbers(1),NOW,"old host generation");
        rejected(report(1),new HanzoScatterContext.Expected(10,20,30,40,KEY,TICK+16),numbers(1),NOW,"another Scatter node tick");
        var disabled=report(1);disabled.addProperty("factoryCalibration",false);rejected(disabled,EXPECTED,numbers(1),NOW,"disabled diagnostic parameter transport");
        var ambiguous=report(1);ambiguous.getAsJsonArray("factoryObservations").add(ambiguous.getAsJsonArray("factoryObservations").get(0).deepCopy());rejected(ambiguous,EXPECTED,numbers(1),NOW,"ambiguous factories");
        var fallback=HanzoScatterContext.fallback("native q missing");check(!fallback.nativeValues()&&fallback.q()==null&&fallback.velocity()==null
            &&fallback.parentSpeed()==90&&fallback.childSpeed()==52&&fallback.parentDamage()==300&&fallback.childDamage()==300&&fallback.reason().contains("MC 适配：用户要求"),"atomic MC fallback damage x4 with unchanged speed");
        System.out.println("HanzoScatterContextCheck passed (context/fallback fixtures only)");
    }
}
