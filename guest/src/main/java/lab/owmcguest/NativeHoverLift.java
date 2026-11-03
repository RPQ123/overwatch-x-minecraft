package lab.owmcguest;

/** User-requested faster held-Space ascent; the original positive thrust is required. */
final class NativeHoverLift {
    static double apply(double delta,double nativeSpeed,boolean heldSpace){
        if(!Double.isFinite(delta)||!Double.isFinite(nativeSpeed))throw new IllegalArgumentException("hover motion");
        if(!heldSpace||delta<=0||nativeSpeed<=0||nativeSpeed>=3)return delta;
        // The measured beta hover plateaus near1.835m/s. Boost that low-speed
        // ascent; smoothly withdraw the lift before the original20m/s Jump Jet.
        // This is an explicit requested adaptation, not a retail physics claim.
        double blend=Math.max(0,Math.min(1,3-nativeSpeed));blend=blend*blend*(3-2*blend);
        // Native frames arrive in batches (e.g. three vs four physics frames
        // per MC tick). Multiplying their cumulative displacement amplified
        // that batching into visible 5..7m/s pulses. Integrate the confirmed
        // native thrust velocity at MC's fixed20Hz instead. Jet/descent above
        // retain the native cumulative path, with no impulse made from a key.
        return Math.min(8.0/20,(nativeSpeed/20)*(1+3.4*blend));
    }
}
