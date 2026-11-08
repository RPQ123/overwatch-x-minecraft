package lab.owmcguest;

/** Presentation only: ten-second turn and a positive lift above the real floor. */
public final class TorbArmorPackMotion {
    public record Pose(float yaw,double lift){}
    private TorbArmorPackMotion(){}
    public static Pose pose(boolean landed,int age,long published,long now){
        var pose=PickupKinematics.pose(landed,false,age,published,now);
        return new Pose((float)(pose.yaw()%360),pose.lift());
    }
}
