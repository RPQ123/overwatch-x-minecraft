package lab.owmcguest;
import java.util.List;

/** Swept local-frame MC intersection of the original native corner boxes. */
public final class NativeDeflectGeometry {
    public static double hit(double[] position,double[] velocity,List<double[]> boxes){
        if(position==null||velocity==null||position.length!=3||velocity.length!=3||boxes==null||boxes.size()!=3)return Double.NaN;
        for(int i=0;i<3;i++)if(!Double.isFinite(position[i])||!Double.isFinite(velocity[i]))return Double.NaN;
        double nearest=Double.POSITIVE_INFINITY;
        for(var box:boxes){
            if(box==null||box.length!=6)return Double.NaN;double lo=0,hi=1;boolean valid=true;
            for(int i=0;i<3;i++){
                if(!Double.isFinite(box[i])||!Double.isFinite(box[i+3])||box[i]>box[i+3]||Math.abs(box[i])>8||Math.abs(box[i+3])>8)return Double.NaN;
                if(Math.abs(velocity[i])<1e-12){if(position[i]<box[i]||position[i]>box[i+3]){valid=false;break;}}
                else{double a=(box[i]-position[i])/velocity[i],b=(box[i+3]-position[i])/velocity[i];lo=Math.max(lo,Math.min(a,b));hi=Math.min(hi,Math.max(a,b));if(lo>hi){valid=false;break;}}
            }
            if(valid)nearest=Math.min(nearest,lo);
        }
        return Double.isFinite(nearest)?nearest:Double.NaN;
    }
}
