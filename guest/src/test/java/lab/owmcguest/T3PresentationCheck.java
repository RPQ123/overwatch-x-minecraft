package lab.owmcguest;

import java.util.*;
import lab.owmcguest.NativeShotProtocol.Vec;

/** Verify input authority and close-contact invariants, not rendered counters. */
public final class T3PresentationCheck {
    private static void check(boolean ok,String label){if(!ok)throw new AssertionError(label);}
    private static void near(double a,double b){check(Math.abs(a-b)<1e-7,a+" != "+b);}
    private static void near(Vec a,Vec b){near(a.x(),b.x());near(a.y(),b.y());near(a.z(),b.z());}
    private static Vec at(String id,Vec p){return MuzzlePresentation.position(id,p,1000);}
    public static void main(String[] args){
        var p=new TorbPlacementInput();var none=TorbPlacementInput.Action.NONE;
        check(p.sample(true,false,false,0,0)==none,"baseline");
        check(p.sample(true,true,false,1,2)==none,"Shift starts preview, never deploys");
        check(p.sample(true,true,true,1,0)==none&&p.preview(),"animation end is not confirmation");
        check(p.sample(true,true,true,1,1)==TorbPlacementInput.Action.CONFIRM,"fresh LMB inside original preview");
        check(p.sample(true,true,true,1,1)==none,"held LMB never repeats");p.confirmed(true);
        check(p.sample(true,true,true,1,0)==none&&!p.preview(),"one placement per preview");
        p.sample(true,false,false,2,0);p.sample(true,true,true,3,2);p.sample(true,true,true,3,0);
        check(p.sample(true,true,true,3,2)==TorbPlacementInput.Action.CANCEL,"second Shift cancellation");
        p.sample(true,false,false,4,0);p.sample(true,true,true,5,2);p.sample(true,true,true,5,0);
        check(p.sample(true,true,true,5,4)==TorbPlacementInput.Action.CANCEL,"RMB cancellation");
        p.sample(false,false,false,0,0);check(p.sample(true,true,true,6,1)==none,"no held-button placement after scope loss");
        var origin=new Vec(0,0,0);var basis=new MuzzlePresentation.Basis(new Vec(0,0,1),new Vec(1,0,0),new Vec(0,1,0));
        var profile=MuzzlePresentation.profile(0x02e0000000000006L,0,0);double fov=70,aspect=16./9;
        var delta=MuzzlePresentation.offset(profile,basis,fov,aspect);near(delta.x()/delta.z()/Math.tan(Math.toRadians(fov)/2)/aspect,profile.x());near(delta.y()/delta.z()/Math.tan(Math.toRadians(fov)/2),profile.y());
        var scope=new MuzzlePresentation.Scope(UUID.randomUUID(),1,2,3);
        MuzzlePresentation.remember(scope,"rivet",0x02e0000000000006L,1000,origin,delta,profile);
        check(at("rivet",origin).equals(delta),"launch at calibrated gun aperture");
        var far=new Vec(0,0,10);check(at("rivet",far).equals(far),"far native ray exact");
        check(MuzzlePresentation.position("rivet",origin,1400).equals(origin),"a returning grenade must not regain its launch offset");
        // A wall closer than the physical muzzle depth still clips to the real
        // contact. The cosmetic path is monotonic, never beyond that wall.
        var hit=new Vec(0,0,.2);MuzzlePresentation.contact("rivet",hit);double previous=-1;
        for(double z=0;z<=.2000001;z+=.001){var at=at("rivet",new Vec(0,0,z));check(at.z()>=previous&&at.z()<=.2000001,"close wall/no overshoot");previous=at.z();}
        check(at("rivet",hit).equals(hit),"actual hit point unchanged");
        // Recorded tank factories start .793083552m below the eye. The first
        // render may already be 3m along the native ray: neither height nor
        // transport delay is allowed to displace the visual launch aperture.
        var first=new Vec(0,-.793083552,3);var aperture=new Vec(0,-.029,.8);
        MuzzlePresentation.remember(scope,"tank",0x02e0000000000015L,1000,new Vec(0,-.793083552,0),delta,profile);
        MuzzlePresentation.reanchorVisible("tank",first,aperture,new Vec(0,0,1),1000);
        near(at("tank",first),aperture);
        near(at("tank",new Vec(0,-.793083552,2)),aperture);
        var tankHit=new Vec(0,-.793083552,3.2);MuzzlePresentation.contact("tank",tankHit);previous=-1;
        for(double z=3;z<=3.2000001;z+=.001){var point=at("tank",new Vec(0,-.793083552,z));check(point.z()>=previous&&point.z()<=3.2000001,"delayed tank close wall monotonic/no overshoot");previous=point.z();}
        check(at("tank",tankHit).equals(tankHit),"delayed tank actual hit exact");
        var old=at("rivet",origin);MuzzlePresentation.remember(scope,"rivet",6,1001,origin,new Vec(-10,0,0),profile);
        check(at("rivet",origin).equals(old),"replay/turn cannot drag an existing launch");
        var other=new MuzzlePresentation.Scope(scope.owner(),9,2,3);MuzzlePresentation.remember(other,"other",6,1002,origin,delta,profile);
        check(at("rivet",origin).equals(origin),"departed world origin retired");
        MuzzlePresentation.retire(2000);MuzzlePresentation.remember(other,"old",6,1000,origin,delta,profile);
        check(at("old",origin).equals(origin),"pre-cleanup launch cannot return");
        for(long hero:new long[]{0x29,0x42,8,2,0x6e,3,0x15,5,0x65,0xdd,10,6})check(MuzzlePresentation.profile(0x02e0000000000000L+hero,0,0)!=null,"12 original hero profiles");
        near(MuzzlePresentation.profile(0x02e0000000000003L,0,0).x(),-MuzzlePresentation.profile(0x02e0000000000003L,0,1).x());
        var landed=TorbArmorPackMotion.pose(true,50,1000,1000);near(landed.yaw(),90);check(landed.lift()>=0&&landed.lift()<=.05,"no below-floor bob");
        check(TorbArmorPackMotion.pose(false,50,1000,1000).equals(new TorbArmorPackMotion.Pose(0,0)),"airborne physics unaffected");
        for(int level=1;level<=3;level++)near(TorbTurretGeometry.muzzle(origin,0,level).x(),0);
        var torb=MuzzleCalibration.at(0x02e0000000000006L,0x0400000000000157L,0,0);near((torb.x()+1)*960,1032);near((1-torb.y())*540,586);
        var tank=MuzzleCalibration.at(0x02e0000000000015L,0x04000000000003ceL,0,0);near((tank.x()+1)*960,960);near((1-tank.y())*540,568);
        String curve="{\"schema\":1,\"width\":1920,\"height\":1080,\"verified\":false,\"curves\":[{\"hero\":\"02e0000000000006\",\"resource\":\"0400000000000157\",\"points\":[{\"phaseMs\":0,\"x\":1032,\"y\":586},{\"phaseMs\":100,\"x\":1028,\"y\":580}]}]}";
        MuzzleCalibration.install(curve);var mid=MuzzleCalibration.at(0x02e0000000000006L,0x0400000000000157L,0,50);near((mid.x()+1)*960,1030);near((1-mid.y())*540,583);
        boolean rejected=false;try{MuzzleCalibration.install(curve.replace("\"x\":1028","\"x\":1e99"));}catch(IllegalArgumentException expected){rejected=true;}check(rejected,"unbounded pixel curve rejected atomically");
        near(MuzzleCalibration.at(0x02e0000000000006L,0x0400000000000157L,0,50).y(),mid.y());
        System.out.println("PASS: preview/LMB/cancel/freshness authority;12 visual muzzle profiles; frozen launch basis; close-wall monotonic convergence/exact contact; scope/replay retirement; pack spin and central turret apertures");
    }
}
