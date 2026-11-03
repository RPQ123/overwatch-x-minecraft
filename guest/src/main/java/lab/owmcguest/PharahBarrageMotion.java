package lab.owmcguest;

import lab.owmcguest.NativeShotProtocol.*;

/** Wave displacement traced in beta24919 1037b60. Server and renderer share it. */
final class PharahBarrageMotion {
    record Wave(double start,double fade,double phase,double frequency,double magnitude,double rotation,boolean spiral){}
    private static Vec cross(Vec a,Vec b){return new Vec(a.y()*b.z()-a.z()*b.y(),a.z()*b.x()-a.x()*b.z(),a.x()*b.y()-a.y()*b.x());}
    static Vec position(Shot shot,double age){
        var at=shot.start().add(shot.velocity().multiply(age));
        if(shot.waves().isEmpty())return at;
        var forward=shot.velocity().multiply(1/Math.sqrt(shot.velocity().lengthSquared()));
        // Emission vectors already use the common world axes; reproduce the
        // native forward x world-up side axis without a second reflection.
        var side=new Vec(-forward.z(),0,forward.x());double length=Math.sqrt(side.lengthSquared());
        side=length>1e-8?side.multiply(1/length):new Vec(1,0,0);
        var up=cross(side,forward);
        for(var wave:shot.waves()){
            double t=age-wave.start();if(t<=0)continue;
            double magnitude=wave.magnitude()*(wave.fade()>0?Math.min(1,t/wave.fade()):1);
            double angle=(t*wave.frequency()+wave.phase())*(double)(float)(2*Math.PI);
            if(!wave.spiral()){magnitude*=Math.sin(angle);angle=wave.rotation()*(double)(float)(Math.PI/180);}
            at=at.add(side.multiply(Math.sin(angle)*magnitude)).add(up.multiply(Math.cos(angle)*magnitude));
        }
        return at;
    }
    static Vec direction(Shot shot,double age){return position(shot,age+.001).subtract(position(shot,Math.max(0,age-.001)));}
}
