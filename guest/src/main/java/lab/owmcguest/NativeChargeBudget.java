package lab.owmcguest;

/** Native-point credit retained across temporary meter transport failures only. */
public final class NativeChargeBudget {
    private NativeChargeScope.Identity identity;
    private double damage,pending;
    public void observe(NativeChargeScope.Identity next,double totalDamage,double dt,boolean idle){
        if(next==null||!Double.isFinite(totalDamage)||totalDamage<0||!Double.isFinite(dt)||dt<0){reset();return;}
        if(!next.equals(identity)||totalDamage<damage){identity=next;damage=totalDamage;pending=0;}
        double earned=Math.max(0,totalDamage-damage);damage=totalDamage;
        // Active/unknown original ultimate state never banks future charge.
        pending=idle?Math.min(100000,pending+Math.min(.1,dt)*5+earned):0;
    }
    public double offer(double charge,double cost,int kind){
        if(!Double.isFinite(charge)||!Double.isFinite(cost)||charge<0||cost<=0||charge>cost)return 0;
        if(charge==cost){pending=0;return 0;}
        return Math.min(cost-charge,kind==2?Math.floor(pending):kind==3?pending:0);
    }
    public void accepted(double amount){if(Double.isFinite(amount)&&amount>0&&amount<=pending)pending-=amount;}
    public double pending(){return pending;}
    public void reset(){identity=null;damage=pending=0;}
}
