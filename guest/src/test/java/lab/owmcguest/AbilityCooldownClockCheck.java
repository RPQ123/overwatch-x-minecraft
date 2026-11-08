package lab.owmcguest;
public final class AbilityCooldownClockCheck {
    private static void eq(float a,float b){if(Math.abs(a-b)>.001)throw new AssertionError(a+" != "+b);}
    public static void main(String[] args){
        var c=new AbilityCooldownClock();eq(c.sample(1,1000,10,false),10);eq(c.sample(1,1250,10,false),9.75f);
        eq(c.sample(1,1500,9,false),9);eq(c.sample(1,1750,9,false),8.75f); // preserve faster native decay
        eq(c.sample(1,2000,10,false),10); // a genuinely newer counter cannot be shortened
        eq(c.sample(1,4000,10,false),10); // stale source lease never catches up blindly
        eq(c.sample(1,4250,10,true),10);eq(c.sample(1,4500,10,false),10); // ready flag is not a running timer
        eq(c.sample(2,1000,.1f,false),.1f);eq(c.sample(2,1250,.1f,false),0);
        c.clear();eq(c.sample(1,5000,10,false),10);boolean rejected=false;
        try{c.sample(3,5000,Float.NaN,false);}catch(IllegalArgumentException expected){rejected=true;}if(!rejected)throw new AssertionError();
        System.out.println("PASS: frozen offline timer, faster native clock, new cooldown, ready/refill, lease gap, scope clear and zero rearm");
    }
}
