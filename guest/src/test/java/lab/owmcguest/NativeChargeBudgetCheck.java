package lab.owmcguest;

public final class NativeChargeBudgetCheck {
    private static void check(boolean value,String message){if(!value)throw new AssertionError(message);}
    public static void main(String[] args){
        var budget=new NativeChargeBudget();var id=new NativeChargeScope.Identity(1,2,3,8,5,0);
        double charge=0;budget.observe(id,0,0,true);
        // Ten seconds of idle time retain integer-meter fractional points.
        for(int i=0;i<200;i++){
            budget.observe(id,0,.05,true);double offered=budget.offer(charge,1250,2);
            charge+=offered;budget.accepted(offered);
        }
        check(charge==50&&budget.pending()==0,"five native passive points/sec; integer fractions retained");
        // Two damage receipts while the meter is unavailable must not disappear.
        budget.observe(id,40,0,true);budget.observe(id,80,0,true);
        check(budget.offer(charge,1250,2)==80,"real damage survives missing meter reads");
        check(budget.offer(charge,1250,2)==80,"failed compare/write does not spend credit");
        budget.accepted(80);charge+=80;
        check(budget.offer(charge,1250,2)==0,"one accepted write spends once");
        budget.observe(id,100,0,true);
        check(budget.offer(1245,1250,2)==5,"native cost caps the actual write");
        budget.accepted(5);check(budget.offer(1250,1250,2)==0&&budget.pending()==0,"full meter banks no next ultimate");
        budget.observe(id,200,.1,false);budget.observe(id,200,.05,true);
        check(budget.offer(0,1250,2)==0&&Math.abs(budget.offer(0,1250,3)-.25)<1e-9,"active Q damage cannot recharge itself; float kind retains fractions");
        budget.observe(id,240,0,true);
        budget.observe(new NativeChargeScope.Identity(1,2,4,8,6,1),240,0,true);
        check(budget.pending()==0,"new model/world/session discards old pending credit");
        budget.observe(id,0,0,true);budget.observe(id,80,0,true);budget.observe(id,0,0,true);
        check(budget.pending()==0,"server counter reset has no inherited old damage");
        budget.observe(id,Double.NaN,.1,true);check(budget.pending()==0,"nonfinite refused");
        System.out.println("PASS: passive/damage charge, meter transport retries, integer/float/cost bounds and active/session reset");
    }
}
