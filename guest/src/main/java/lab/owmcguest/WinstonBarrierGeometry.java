package lab.owmcguest;

import lab.owmcguest.NativeShotProtocol.Vec;

/** Intersection with the real5m hemisphere; never fills/replaces world blocks. */
public final class WinstonBarrierGeometry {
    private WinstonBarrierGeometry(){}
    private static double dot(Vec a,Vec b){return a.x()*b.x()+a.y()*b.y()+a.z()*b.z();}
    public static double intersection(Vec a,Vec b,Vec center){
        if(a==null||b==null||center==null||!Double.isFinite(a.lengthSquared()+b.lengthSquared()+center.lengthSquared()))return Double.NaN;
        Vec d=b.subtract(a),v=a.subtract(center);double aa=dot(d,d);
        if(aa<1e-14)return Double.NaN;
        double bb=2*dot(v,d),cc=dot(v,v)-WinstonRules.BARRIER_RADIUS*WinstonRules.BARRIER_RADIUS;
        double discriminant=bb*bb-4*aa*cc;if(discriminant<0)return Double.NaN;
        double sqrt=Math.sqrt(discriminant);
        for(double t:new double[]{(-bb-sqrt)/(2*aa),(-bb+sqrt)/(2*aa)})
            if(t>=0&&t<=1&&a.y()+d.y()*t>=center.y()-.025)return t;
        return Double.NaN;
    }
}
