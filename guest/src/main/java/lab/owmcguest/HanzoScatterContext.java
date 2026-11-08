package lab.owmcguest;

import com.google.gson.*;
import lab.owmcguest.NativeShotProtocol.Vec;

/** Parameters only for an ALREADY admitted b9:26 cast. No attack admission.
 * q is a typed native 2a5 read, never reconstructed from speed/hold time.
 * Expressions are used only after the read-only binding verifies their exact
 * bytecode/constants/variable paths. Child trajectory oracle is still pending.
 * MC 适配：用户要求，散射母/子箭伤害在原版读数通过校验后统一乘4。 */
public final class HanzoScatterContext {
    public static final long HERO=0x02e0000000000005L,STRONG=0x04000000000001a4L,WEAK=0x040000000000020cL;
    public static final double DAMAGE_MULTIPLIER=4,FALLBACK_DAMAGE=75*DAMAGE_MULTIPLIER;
    public static final String DAMAGE_ADAPTATION="MC 适配：用户要求";
    public record Expected(int pid,long creation,long generation,long model,long volleyKey,long nodeTick){}
    public record Numbers(double q,double direct1dc,double child980,long wall){}
    public record Parameters(boolean nativeValues,Double q,Vec velocity,double parentSpeed,double parentDamage,
                             double childSpeed,double childDamage,String identity,String reason){}
    private HanzoScatterContext(){}
    public static Parameters fallback(String reason){return new Parameters(false,null,null,90,FALLBACK_DAMAGE,52,FALLBACK_DAMAGE,"",reason+"; "+DAMAGE_ADAPTATION+"，散射伤害×4");}
    private static long n(JsonObject o,String key){return Long.parseUnsignedLong(o.get(key).getAsString());}
    private static double d(JsonObject o,String key){double x=o.get(key).getAsDouble();if(!Double.isFinite(x))throw new IllegalArgumentException("nonfinite "+key);return x;}
    private static void require(boolean b,String reason){if(!b)throw new IllegalArgumentException(reason);}
    public static Parameters resolve(JsonObject report,Expected e,Numbers values,long now){
        require(values!=null,"typed native q/1dc/980 unavailable");
        require(e.nodeTick()>0&&(e.nodeTick()&15)==0,"Scatter node/factory tick relation unavailable");
        require(n(report,"pid")==Integer.toUnsignedLong(e.pid())&&n(report,"creation")==e.creation()
            &&n(report,"hostGeneration")==e.generation()&&n(report,"modelId")==e.model()&&n(report,"hero")==HERO,"Scatter factory owner changed");
        require((n(report,"probeVersion")==16||n(report,"probeVersion")==17)&&n(report,"protocol")==3&&n(report,"epoch")>0
            &&report.get("enabled").getAsBoolean()&&!report.get("restored").getAsBoolean()
            &&!report.get("overflow").getAsBoolean()&&n(report,"failures")==0,"Scatter factory source invalid");
        require(report.get("factoryCalibration").getAsBoolean(),"factory parameter transport disabled; unchanged MC fallback");
        require(now-n(report,"heartbeat")<=150&&n(report,"heartbeat")<=now+50,"Scatter factory heartbeat stale");
        require(values.wall()<=now+50&&now-values.wall()<=150,"typed Scatter numbers stale");
        require(Double.isFinite(values.q())&&values.q()>=0&&values.q()<=1,"native charge2a5 outside [0,1]");
        require(Double.isFinite(values.direct1dc())&&values.direct1dc()>=25&&values.direct1dc()<=125,"native contextual1dc unavailable/bounds");
        require(Double.isFinite(values.child980())&&values.child980()>=15&&values.child980()<=75,"native contextual980 unavailable/bounds");
        var all=report.getAsJsonArray("factoryObservations");require(all!=null&&all.size()<=256,"Scatter factory snapshot bounds");
        JsonObject match=null;
        for(var value:all){var row=value.getAsJsonObject();long resource=n(row,"resource");
            if((resource!=STRONG&&resource!=WEAK)||n(row,"hero")!=HERO||n(row,"owner")!=e.model()
                ||n(row,"tick")!=e.nodeTick()/16||(n(row,"volley")&0xffffff00L)!=e.volleyKey())continue;
            long wall=n(row,"wallMs");if(wall>now+50||now-wall>150)continue;
            require(match==null,"ambiguous same-tick Scatter factories");match=row;
        }
        require(match!=null,"no fresh factory matching admitted Scatter node");
        require(n(match,"status")==8&&n(match,"type")==1&&n(match,"result")==0&&n(match,"shot")<=65535&&n(match,"pellet")==0,"Scatter factory status/type/result");
        require(d(match,"lifetime")==10&&d(match,"range")==300,"Scatter factory flight declaration changed");
        double speed=d(match,"speed");require(speed>=25-.001&&speed<=90+.001,"Scatter factory speed bounds");
        require(Math.abs(speed-(25+65*values.q()))<=.05,"native q does not match same-cast factory velocity");
        require(Math.abs(values.child980()-(15+60*values.q()))<=.02,"native980 does not match pinned b9:84 expression");
        var a=match.getAsJsonArray("direction");require(a!=null&&a.size()==3,"Scatter factory direction size");
        var direction=new Vec(a.get(0).getAsDouble(),a.get(1).getAsDouble(),a.get(2).getAsDouble());
        require(Double.isFinite(direction.x())&&Double.isFinite(direction.y())&&Double.isFinite(direction.z())
            &&Math.abs(direction.lengthSquared()-1)<.02,"Scatter factory direction invalid");
        // evaluatedDamage is deliberately NOT consumed: unbound Scatter rows
        // report zero there even when the real contextual bag contains damage.
        String identity=n(report,"epoch")+":"+e.model()+":"+n(match,"volley")+":"+n(match,"tick")+":"+n(match,"shot");
        double childSpeed=(double)0.800000011920929f*(20+65*values.q());
        // Authenticate raw original values above; adapt exactly once before the
        // parent/children carry their damage through all subsequent bounces.
        return new Parameters(true,values.q(),direction.multiply(speed),speed,values.direct1dc()*DAMAGE_MULTIPLIER,childSpeed,values.child980()*DAMAGE_MULTIPLIER,identity,
            "typed native 2a5/1dc/980 + matched factory; pinned child expression, trajectory oracle pending; "+DAMAGE_ADAPTATION+"，散射伤害×4");
    }
}
