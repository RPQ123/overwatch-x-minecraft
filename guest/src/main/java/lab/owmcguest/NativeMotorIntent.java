package lab.owmcguest;

/** Current native form guards and retained legacy pure motion fixtures. */
public final class NativeMotorIntent {
    /** Only a unique original form can authorize movement; unknown/conflicting phases stay locked. */
    public static String bastionForm(boolean recon,boolean sentry,boolean tank){
        if((recon?1:0)+(sentry?1:0)+(tank?1:0)!=1)return "transition";
        return recon?"recon":sentry?"sentry":"tank";
    }
    public static boolean bastionRooted(boolean recon,boolean sentry,boolean tank){
        String form=bastionForm(recon,sentry,tank);return !form.equals("recon")&&!form.equals("tank");
    }
    public static boolean responsive(long hero){return hero==0x02e0000000000002L||hero==0x02e000000000006eL;}
    /** Current direction/base speed, retaining a measured native speed boost only. */
    public static double[] responsiveStep(double[] requested,double[] velocity,double base){
        if(requested==null||requested.length!=2||velocity==null||velocity.length!=3||!Double.isFinite(base)||base<=0)return new double[]{0,0};
        for(double v:requested)if(!Double.isFinite(v))return new double[]{0,0};
        for(double v:velocity)if(!Double.isFinite(v))return new double[]{0,0};
        double speed=Math.hypot(velocity[0],velocity[2]);
        if(speed>base*3)return new double[]{0,0};
        double boost=Math.max(1,speed/base);
        return new double[]{requested[0]*boost,requested[1]*boost};
    }
    public static boolean hero(long hero){return (hero&~0xffffL)==0x02e0000000000000L&&java.util.Set.of(2L,5L,6L,10L,0x15L,0xddL,0x6eL).contains(hero&0xffffL);}
    public static double[] horizontal(int bits,double[] velocity){
        int forward=((bits&1)!=0?1:0)-((bits&2)!=0?1:0),right=((bits&8)!=0?1:0)-((bits&4)!=0?1:0);
        if((forward==0&&right==0)||velocity==null||velocity.length!=3)return new double[]{0,0};
        double x=velocity[0],z=velocity[2];
        if(!Double.isFinite(x)||!Double.isFinite(z)||x*x+z*z>900)return new double[]{0,0};
        return new double[]{x,z};
    }
}
