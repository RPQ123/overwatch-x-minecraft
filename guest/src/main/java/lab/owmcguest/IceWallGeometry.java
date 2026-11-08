package lab.owmcguest;
import java.util.*;
/** One snapped, terrain-following wall for preview, native meshes and MC
 * collision. Fractional terrain/top surfaces are quantized to1/16 block. */
public final class IceWallGeometry {
    public static final int WIDTH=11,THICKNESS=3,HEIGHT=4;
    public static final double PILLAR_WIDTH=3.65,PILLAR_SPACING=WIDTH/5.;
    public static final double SOURCE_X=2.7266159057617188,SOURCE_Y=4.944886207580566,SOURCE_Z=2.6735048294067383;
    public record Ground(int x,int z,double y){}
    public record Cell(int x,int y,int z,int top,double lower){}
    public record Pillar(double x,double y,double z,double height){}
    public record Plan(boolean alongX,List<Ground> ground){
        public Plan{ground=List.copyOf(ground);if(ground.size()!=WIDTH*THICKNESS)throw new IllegalArgumentException("wall footprint");
            var start=ground.getFirst();
            for(int i=0;i<WIDTH;i++)for(int d=0;d<THICKNESS;d++){
                var g=ground.get(i*THICKNESS+d);
                if(!Double.isFinite(g.y())||Math.abs(g.y()*16-Math.rint(g.y()*16))>1e-6)throw new IllegalArgumentException("wall surface quantization");
                if(g.x()!=start.x()+(alongX?i:d)||g.z()!=start.z()+(alongX?d:i))throw new IllegalArgumentException("wall discontinuity");
                if(i>0&&Math.abs(g.y()-ground.get((i-1)*THICKNESS+d).y())>1.000001
                    ||d>0&&Math.abs(g.y()-ground.get(i*THICKNESS+d-1).y())>1.000001)throw new IllegalArgumentException("wall terrain step");
            }
        }
        public float yaw(){return alongX?0:-90;}
        public double sourceMinX(Pillar p){double at=alongX?p.x():p.z(),begin=alongX?ground.getFirst().x():ground.getFirst().z();return Math.max(-SOURCE_X/2,(begin-at)/(PILLAR_WIDTH/SOURCE_X));}
        public double sourceMaxX(Pillar p){double at=alongX?p.x():p.z(),end=(alongX?ground.getLast().x():ground.getLast().z())+1;return Math.min(SOURCE_X/2,(end-at)/(PILLAR_WIDTH/SOURCE_X));}
        public List<Cell> cells(double progress){
            var result=new ArrayList<Cell>();double height=HEIGHT*Math.clamp(progress,0,1);if(height<=0)return result;
            for(var g:ground){int first=(int)Math.floor(g.y()+1e-8),last=(int)Math.ceil(g.y()+height-1e-8)-1;
                for(int y=first;y<=last;y++){int top=(int)Math.round(Math.min(1,g.y()+height-y)*16);if(top>0)result.add(new Cell(g.x(),y,g.z(),top,Math.max(0,g.y()-y)));}}
            return List.copyOf(result);
        }
        public List<Pillar> pillars(double progress){
            var result=new ArrayList<Pillar>();var middle=ground.get((WIDTH/2)*THICKNESS+THICKNESS/2);
            for(int i=0;i<5;i++){double offset=(i-2)*PILLAR_SPACING,low=Double.POSITIVE_INFINITY,high=Double.NEGATIVE_INFINITY;
                for(int j=0;j<WIDTH;j++)if(Math.abs(j-WIDTH/2-offset)<=PILLAR_WIDTH/2+.500001)for(int d=0;d<THICKNESS;d++){
                    var g=ground.get(j*THICKNESS+d);low=Math.min(low,g.y());high=Math.max(high,g.y());}
                result.add(new Pillar(middle.x()+.5+(alongX?offset:0),low,middle.z()+.5+(alongX?0:offset),high-low+HEIGHT*Math.clamp(progress,0,1)));}
            return List.copyOf(result);
        }
    }
    private IceWallGeometry(){}
}
