package lab.owmcguest;
public final class HelixPresentationCheck {
    public static void main(String[] args){
        for(double age=0;age<2;age+=.001){
            double x=0,y=0;for(int i=0;i<3;i++){var p=HelixPresentation.strand(age,i);x+=p.x();y+=p.y();if(p.lengthSquared()>HelixPresentation.RADIUS*HelixPresentation.RADIUS+1e-12)throw new AssertionError("unbounded visual orbit");}
            if(Math.abs(x)>1e-12||Math.abs(y)>1e-12)throw new AssertionError("visual strands shifted authoritative center");
            var m=HelixPresentation.launch(age,90,16./9);if(age*50+m.forward()<.9)throw new AssertionError("near camera discontinuity");
            if(age>=.12&&(m.forward()!=0||m.right()!=0||m.up()!=0))throw new AssertionError("distant damage ray displaced");
        }
        System.out.println("PASS: bounded three-strand centroid and unchanged distant projectile path");
    }
}
