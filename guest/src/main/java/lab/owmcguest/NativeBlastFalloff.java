package lab.owmcguest;

/** Linear adaptation between actual native two-ring endpoints. */
public final class NativeBlastFalloff {
    public static double scale(double distance,double inner,double outer,double last){
        if(!Double.isFinite(distance)||!Double.isFinite(inner)||!Double.isFinite(outer)||!Double.isFinite(last)
            ||distance<0||inner<0||outer<=inner||outer>10||last<0||last>1||distance>outer)return 0;
        return distance<=inner?1:1-(distance-inner)/(outer-inner)*(1-last);
    }
}
