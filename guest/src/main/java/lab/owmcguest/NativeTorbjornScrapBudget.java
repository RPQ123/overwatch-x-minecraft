package lab.owmcguest;

/** MC 适配资源账本：只在真实死亡拾取时入账，在原版投包事件时扣账。 */
public final class NativeTorbjornScrapBudget {
    private int amount,spent;
    public int amount(){return amount;}
    public int spent(){return spent;}
    public boolean collect(){if(amount>=200)return false;amount=Math.min(200,amount+25);return true;}
    public boolean spendArmor(){if(amount<50)return false;amount-=50;spent+=50;return true;}
    public void observeNative(int value){if(value<0||value>200)throw new IllegalArgumentException("native Scrap bounds");amount=value;}
    /** Real Volley5 already debited the native bag. Do not debit it twice. */
    public void nativeArmorAdmitted(){spent+=50;}
    public void clear(){amount=spent=0;}
}
