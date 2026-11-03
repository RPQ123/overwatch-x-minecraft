package lab.owmcguest;

import java.util.Set;

/** Persisted against the Overworld's total server game time, never entity age/day time. */
public final class SummonedMobExpiry {
    public static final long LIFETIME_TICKS=3*60*20;
    public static final String OWNED="owmc-f9-summoned",PREFIX="owmc-f9-until:";
    private SummonedMobExpiry(){}
    public static long deadline(long now){return Math.addExact(now,LIFETIME_TICKS);}
    public static long read(Set<String> tags){
        long result=-1;boolean found=false;
        for(String tag:tags)if(tag.startsWith(PREFIX)){
            if(found)return -1;found=true;
            try{result=Long.parseLong(tag.substring(PREFIX.length()));}catch(NumberFormatException ignored){return -1;}
            if(result<0)return -1;
        }
        return result;
    }
    public static boolean expired(long now,long until){return until<0||now>=until;}
}
