package lab.owmcguest;

public final class NativeChargeEligibilityCheck {
    private static void require(boolean value,String message){if(!value)throw new AssertionError(message);}
    public static void main(String[] args){
        require(NativeChargeEligibility.supported(0x02e0000000000008L),"Pharah meter");
        require(NativeChargeEligibility.supported(0x02e0000000000042L),"McCree meter");
        require(NativeChargeEligibility.supported(0x02e0000000000009L),"Winston meter");
        require(NativeChargeEligibility.nativeUltimateOwner(0x02e0000000000029L),"Genji stays native owner");
        require(!NativeChargeEligibility.nativeUltimateOwner(0x02e0000000000042L),"McCree uses generic meter");
        require(!NativeChargeEligibility.supported(0),"Zero hero rejected");
        for(long id:new long[]{2,3,4,5,6,7,8,9,10,0x15,0x16,0x20,0x29,0x40,0x42,0x65,0x68,0x6e,0x79,0x7a,0xdd}){
            long hero=0x02e0000000000000L|id;
            require(NativeChargeEligibility.supported(hero),"Every original roster hero has a meter: "+id);
            require(NativeChargeEligibility.nativeUltimateOwner(hero)==(id==0x29),"One Genji charge writer only");
        }
        require(!NativeChargeEligibility.supported(0x02e00000000000ffL),"Unknown hero rejected");
        System.out.println("PASS: generic ultimate-meter roster gate and Genji ownership");
    }
}
