package lab.owmcguest;
import java.util.List;
public final class NativeDeflectGeometryCheck {
    static void require(boolean ok,String message){if(!ok)throw new AssertionError(message);}
    public static void main(String[] args){
        var boxes=List.of(new double[]{-1,-2,0,1,.75,2},new double[]{.5,-2,-1,1,.75,0},new double[]{-1,-2,-1,-.5,.75,0});
        require(NativeDeflectGeometry.hit(new double[]{0,0,5},new double[]{0,0,-4},boxes)==.75,"Fast incoming sweep reaches original frontal box");
        require(NativeDeflectGeometry.hit(new double[]{0,0,1},new double[]{0,0,-1},boxes)==0,"Already inside original box");
        require(Double.isNaN(NativeDeflectGeometry.hit(new double[]{0,1,5},new double[]{0,0,-4},boxes)),"Above original box rejected");
        require(Double.isNaN(NativeDeflectGeometry.hit(new double[]{2,0,5},new double[]{0,0,-4},boxes)),"Side miss rejected");
        require(Double.isNaN(NativeDeflectGeometry.hit(new double[]{0,0,-2},new double[]{0,0,-2},boxes)),"Departing behind box rejected");
        require(Double.isFinite(NativeDeflectGeometry.hit(new double[]{.75,0,-2},new double[]{0,0,2},boxes)),"Original side box uses normalized native corner pair");
        require(Double.isNaN(NativeDeflectGeometry.hit(new double[]{Double.NaN,0,5},new double[]{0,0,-4},boxes)),"Nonfinite projectile refused");
        require(Double.isNaN(NativeDeflectGeometry.hit(new double[]{0,0,5},new double[]{0,0,-4},List.of(new double[]{1,0,0,-1,1,1},boxes.get(1),boxes.get(2)))),"Corrupt native bounds refused");
        System.out.println("PASS: actual native Deflect corner-box sweeps, fast projectiles, misses and numeric guards");
    }
}
