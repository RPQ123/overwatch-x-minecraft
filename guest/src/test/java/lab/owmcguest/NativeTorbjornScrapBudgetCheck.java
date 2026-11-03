package lab.owmcguest;

/** Empty funds, exact cost, failed double spend, capacity, and session-reset negative controls. */
public final class NativeTorbjornScrapBudgetCheck {
    private static void check(boolean ok){if(!ok)throw new AssertionError();}
    public static void main(String[] args){
        var budget=new NativeTorbjornScrapBudget();check(!budget.spendArmor());check(budget.amount()==0&&budget.spent()==0);
        check(budget.collect());check(!budget.spendArmor());check(budget.amount()==25&&budget.spent()==0);
        check(budget.collect());check(budget.spendArmor());check(!budget.spendArmor());check(budget.amount()==0&&budget.spent()==50);
        for(int i=0;i<8;i++)check(budget.collect());check(!budget.collect());check(budget.amount()==200);
        for(int i=0;i<4;i++)check(budget.spendArmor());check(!budget.spendArmor());check(budget.spent()==250);
        budget.clear();check(budget.amount()==0&&budget.spent()==0&&!budget.spendArmor());
        System.out.println("NativeTorbjornScrapBudgetCheck passed");
    }
}
