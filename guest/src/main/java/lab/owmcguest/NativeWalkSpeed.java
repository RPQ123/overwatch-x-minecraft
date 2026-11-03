package lab.owmcguest;

/** Directional base locomotion in native metres per second; MC blocks are one metre. */
public final class NativeWalkSpeed {
    public static double[] local(int bits,double[] speeds){
        if(speeds==null||speeds.length!=6)return new double[]{0,0};
        int forward=((bits&1)!=0?1:0)-((bits&2)!=0?1:0);
        int right=((bits&8)!=0?1:0)-((bits&4)!=0?1:0);
        double length=Math.hypot(forward,right);if(length==0)return new double[]{0,0};
        int offset=(bits&32)!=0?3:0;
        return new double[]{right/length*speeds[offset+2]/20,forward/length*speeds[offset+(forward<0?1:0)]/20};
    }
}
