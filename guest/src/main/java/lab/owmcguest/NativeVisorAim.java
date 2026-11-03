package lab.owmcguest;

import lab.owmcguest.NativeShotProtocol.*;

/** Pure admission/math for the MC adapter; neither input nor a meter creates a shot. */
public final class NativeVisorAim {
    public static final long HERO=0x02e000000000006eL;
    public record Scope(long source,long model,long world,long wallMs,long begin,boolean active,double radius,double angle,long startedWallMs){}
    /** Conservatively timestamp the first observed native active window.
     * Factory tick is a different counter domain from the logger's clock. */
    public static final class Window {
        private long source,model,world,begin,started;
        public long observe(long nextSource,long nextModel,long nextWorld,long nextBegin,boolean active,long now){
            if(!active){reset();return 0;}
            if(started==0||source!=nextSource||model!=nextModel||world!=nextWorld||begin!=nextBegin){
                source=nextSource;model=nextModel;world=nextWorld;begin=nextBegin;started=now;
            }return started;
        }
        public void reset(){source=model=world=begin=started=0;}
    }
    public static boolean eligible(Scope s,Shot shot,long world,long source,long now){
        if(s==null||!s.active()||s.source()==0||s.model()<=0||s.model()>0xffffffffL||s.world()==0||s.begin()<=0||s.begin()>0xffffffffL
            ||now-s.wallMs()>150||s.wallMs()>now+50||now-shot.wallMs()>500||shot.wallMs()>now+100
            ||s.world()!=world||s.source()!=source||s.radius()!=45||s.angle()!=45
            ||s.startedWallMs()<=0||s.startedWallMs()>s.wallMs()||shot.wallMs()<s.startedWallMs()
            ||!shot.hitscan()||shot.effect()==null||shot.effect().hero()!=HERO||shot.effect().resource()!=0x04000000000003d4L)return false;
        // Compare wall times from the same machine. The bullet's native tick
        // and the state logger Begin are unrelated counters; comparing them
        // rejected every real Visor bullet despite passing synthetic fixtures.
        var identity=shot.identity().split(":",-1);
        if(identity.length!=7||!identity[0].equals("factory"))return false;
        try{return Long.parseLong(identity[1])==HERO&&Long.parseLong(identity[2])==s.model()
            &&Long.parseUnsignedLong(identity[3])!=0&&Long.parseLong(identity[4])>0&&Long.parseLong(identity[4])<=0xffffffffL;}
        catch(NumberFormatException invalid){return false;}
    }
    /** Negative means out of the original native range/cone. */
    public static double score(Vec forward,Vec delta,double range,double fullAngle){
        double distance=Math.sqrt(delta.lengthSquared()),length=Math.sqrt(forward.lengthSquared());
        if(!Double.isFinite(distance)||!Double.isFinite(length)||!Double.isFinite(range)||!Double.isFinite(fullAngle)
            ||distance<1e-6||distance>range||length<1e-6||range<=0||fullAngle<=0||fullAngle>=180)return -1;
        double cosine=(delta.x()*forward.x()+delta.y()*forward.y()+delta.z()*forward.z())/(distance*length);
        return cosine+1e-12<Math.cos(Math.toRadians(fullAngle/2))?-1:Math.min(1,cosine);
    }
}
