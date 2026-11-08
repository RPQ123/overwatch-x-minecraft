package lab.owmcguest;

import java.util.*;
import com.google.gson.*;

/** Screen-pixel calibration, separate from native hit physics. The provisional
 * defaults use existing recorded native gun pixels, not live bone measurements.
 * A validated per-resource firing-phase curve can replace them without code or
 * asset repackaging. Its verification label is diagnostic, never an acceptance. */
public final class MuzzleCalibration {
    private record Point(long phase,double x,double y){}
    private record Key(long hero,long resource){}
    private record Curve(double width,double height,List<Point> points){}
    private static volatile Map<Key,Curve> curves=Map.of();
    private static volatile String provenance="historical-screen-reference/provisional",error="";
    private static volatile boolean verified;private static volatile long revision;
    private MuzzleCalibration(){}
    private static double finite(JsonObject o,String key){double v=o.get(key).getAsDouble();if(!Double.isFinite(v))throw new IllegalArgumentException("nonfinite calibration "+key);return v;}
    public static synchronized void install(String json){
        if(json.length()>32768)throw new IllegalArgumentException("calibration size");
        var root=JsonParser.parseString(json).getAsJsonObject();if(root.get("schema").getAsInt()!=1)throw new IllegalArgumentException("calibration schema");
        double width=finite(root,"width"),height=finite(root,"height");if(width<320||width>7680||height<180||height>4320||Math.abs(width/height-16./9)>.01)throw new IllegalArgumentException("calibration reference dimensions");
        var next=new HashMap<Key,Curve>();var list=root.getAsJsonArray("curves");if(list.size()>16)throw new IllegalArgumentException("calibration curve count");
        for(var value:list){var item=value.getAsJsonObject();long hero=Long.parseUnsignedLong(item.get("hero").getAsString(),16),resource=Long.parseUnsignedLong(item.get("resource").getAsString(),16);
            if(!(hero==0x02e0000000000006L&&(resource==0x0400000000000157L||resource==0x04000000000002d0L)||hero==0x02e0000000000015L&&resource==0x04000000000003ceL))throw new IllegalArgumentException("calibration weapon identity");
            var points=new ArrayList<Point>();long previous=-1;var samples=item.getAsJsonArray("points");if(samples.isEmpty()||samples.size()>64)throw new IllegalArgumentException("calibration samples");
            for(var row:samples){var p=row.getAsJsonObject();long phase=p.get("phaseMs").getAsLong();double x=finite(p,"x"),y=finite(p,"y");
                if(phase<0||phase>2000||phase<=previous||x<-.5*width||x>1.5*width||y<-.5*height||y>1.5*height)throw new IllegalArgumentException("calibration sample bounds/order");
                previous=phase;points.add(new Point(phase,x,y));}
            if(next.put(new Key(hero,resource),new Curve(width,height,List.copyOf(points)))!=null)throw new IllegalArgumentException("duplicate calibration weapon");
        }
        // Commit only a complete valid document. Invalid edits retain the last
        // working projection; they cannot produce a NaN or mutate a Shot.
        curves=Map.copyOf(next);verified=root.has("verified")&&root.get("verified").getAsBoolean();provenance=root.has("provenance")?root.get("provenance").getAsString():"manual-screen-reference";error="";revision++;
    }
    public static void failed(String message){error=message;}
    public static MuzzlePresentation.Profile at(long hero,long resource,long alternate,long phaseMs){
        var base=MuzzlePresentation.profile(hero,resource,alternate);if(base==null)return null;
        var curve=curves.get(new Key(hero,resource));
        if(curve!=null){var points=curve.points();Point a=points.getFirst(),b=a;
            for(var p:points){if(p.phase()<=phaseMs)a=p;if(p.phase()>=phaseMs){b=p;break;}b=p;}
            double t=a.phase()==b.phase()?0:Math.clamp((phaseMs-a.phase())/(double)(b.phase()-a.phase()),0,1),x=a.x()+(b.x()-a.x())*t,y=a.y()+(b.y()-a.y())*t;
            return new MuzzlePresentation.Profile(base.name()+"/screen",2*x/curve.width()-1,1-2*y/curve.height(),base.depth(),base.converge());
        }
        // Existing footage puts the original gun aperture ahead of the old
        // receiver-centred guesses. These are initial screen references only;
        // this code-only delivery does not claim a measured final pixel error.
        if(hero==0x02e0000000000006L&&(resource==0x0400000000000157L||resource==0x04000000000002d0L))return new MuzzlePresentation.Profile(base.name()+"/reference",.075,-.0851851851851852,base.depth(),base.converge());
        if(resource==0x04000000000003ceL)return new MuzzlePresentation.Profile(base.name()+"/reference",0,-.05185185185185185,base.depth(),base.converge());
        return base;
    }
    public static JsonObject diagnostics(){var o=new JsonObject();o.addProperty("revision",revision);o.addProperty("curves",curves.size());o.addProperty("provenance",provenance);o.addProperty("verified",verified);o.addProperty("error",error);return o;}
}
