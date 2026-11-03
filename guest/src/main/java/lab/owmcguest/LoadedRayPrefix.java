package lab.owmcguest;

import java.util.function.BiPredicate;
import lab.owmcguest.NativeShotProtocol.Vec;

/** Clip at the first unavailable chunk, preserving every earlier possible hit. */
public final class LoadedRayPrefix {
    public record Clip(double fraction,boolean complete){}
    public static Clip clip(Vec a,Vec b,BiPredicate<Integer,Integer> loaded){
        double dx=b.x()-a.x(),dz=b.z()-a.z();
        if(!Double.isFinite(dx)||!Double.isFinite(dz)||Math.abs(dx)>1024||Math.abs(dz)>1024)throw new IllegalArgumentException("ray bounds");
        int x=(int)Math.floor(a.x()/16),z=(int)Math.floor(a.z()/16);
        if(!loaded.test(x,z))return new Clip(0,false);
        int sx=Double.compare(dx,0),sz=Double.compare(dz,0);
        double tx=dx==0?Double.POSITIVE_INFINITY:((sx>0?(x+1)*16.:x*16.)-a.x())/dx;
        double tz=dz==0?Double.POSITIVE_INFINITY:((sz>0?(z+1)*16.:z*16.)-a.z())/dz;
        double stepx=dx==0?Double.POSITIVE_INFINITY:16/Math.abs(dx),stepz=dz==0?Double.POSITIVE_INFINITY:16/Math.abs(dz);
        for(int count=0;count<256;count++){
            double t=Math.min(tx,tz);if(t>1)return new Clip(1,true);
            boolean crossX=tx<=tz,crossZ=tz<=tx;
            // Conservative corner guard: MC's block DDA may inspect either
            // side cell before the diagonal cell at an exact corner.
            if((crossX&&!loaded.test(x+sx,z))||(crossZ&&!loaded.test(x,z+sz))
               ||(crossX&&crossZ&&!loaded.test(x+sx,z+sz)))
                return new Clip(Math.max(0,t-1e-6/Math.max(1,Math.hypot(dx,dz))),false);
            if(crossX){x+=sx;tx+=stepx;}
            if(crossZ){z+=sz;tz+=stepz;}
        }
        throw new IllegalArgumentException("ray traversal bounds");
    }
}
