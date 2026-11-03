package lab.owmcguest;

public final class WallClimbCheck {
    private static void check(boolean value,String message){if(!value)throw new AssertionError(message);}
    public static void main(String[] args){
        check(WallClimbPhase.hero(0x02e0000000000029L)&&WallClimbPhase.hero(0x02e0000000000005L),"Genji and Hanzo wall-climb roster");
        check(!WallClimbPhase.hero(0x02e000000000006eL)&&!WallClimbPhase.hero(0x02e0000000000065L),"Other native heroes cannot acquire wall climb");
        check(!WallClimbPhase.wallAdmission(true,false,false),"one block ledge is not climbable");
        check(WallClimbPhase.wallAdmission(true,true,false),"tall wall admits climb");
        check(WallClimbPhase.wallAdmission(true,false,true),"active climb continues through wall top band");
        check(!WallClimbPhase.wallAdmission(false,true,true),"wall departure enters mantle transition");
        var p=new WallClimbPhase();long tick=0;double y=64;
        check(p.step(1,tick++,true,true,false,true,y)==0,"air is not a wall");
        check(p.step(1,tick++,true,false,true,true,y)==0,"wall alone supplies no input");
        double delta=p.step(1,tick++,true,true,true,true,y);check(delta>0,"wall plus jump and forward starts");y+=delta;
        check(p.step(1,tick-1,false,true,true,true,y)==0,"same MC tick cannot move twice");
        while(p.active()){delta=p.step(1,tick++,false,true,true,true,y);y+=delta;}
        check(Math.abs(y-70)<1e-5,"six block climb limit");
        check(p.step(1,tick++,false,true,true,true,y)==0,"airborne climb cannot restart");
        p.blocked();check(p.step(1,tick++,false,true,true,true,y)==0,"ceiling collision still stops movement");
        check(p.step(1,tick++,true,true,true,true,64)>0,"landing rearms");p.blocked();
        check(p.step(1,tick++,false,true,true,true,64)==0,"ceiling stops until landing");
        p.step(1,tick++,true,true,true,true,64);p.step(1,tick++,false,false,true,true,64.3);
        check(p.step(1,tick++,false,true,true,true,64.3)==0,"release cannot refill climb in air");
        p.step(1,tick++,true,true,true,true,64);check(p.step(2,tick++,false,true,true,true,64.3)==0,"new native session cannot continue old climb");
        check(p.step(2,tick++,true,true,true,false,64)==0,"unverified hero cannot climb");
        p.step(2,tick++,true,true,true,true,64);p.invalidate();check(!p.active(),"stale source stops immediately");
        System.out.println("PASS: bounded climb, wall/input admission, ceiling/release exhaustion, ground rearm and session loss");
    }
}
