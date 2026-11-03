package lab.owmcguest;

/** Roster gate for the generic meter adapter; values still come from each native hero. */
final class NativeChargeEligibility {
    private static final long BASE=0x02e0000000000000L;
    private static final long GENJI=BASE|0x29;
    // Meter eligibility is independent of MC weapon/skill implementation.
    // Each actual current model must still expose the typed charge/cost pair.
    private static final long[] ROSTER={BASE|2,BASE|3,BASE|4,BASE|5,BASE|6,BASE|7,BASE|8,BASE|9,BASE|10,
        BASE|0x15,BASE|0x16,BASE|0x20,BASE|0x29,BASE|0x40,BASE|0x42,BASE|0x65,BASE|0x68,BASE|0x6e,BASE|0x79,BASE|0x7a,BASE|0xdd};

    private NativeChargeEligibility() {}

    static boolean supported(long hero) {
        for (long candidate: ROSTER) if (candidate==hero) return true;
        return false;
    }

    static boolean nativeUltimateOwner(long hero) { return hero==GENJI; }
}
