package lab.owmcguest;

/** MC-authored cosmetic shell. Restored silver shell, enlarged 33% (MC adaptation); center follows the admitted flight ray. */
final class BastionTankPresentation {
    static final double LENGTH=.60,RADIUS=.10,TRAIL_SECONDS=.035;
    static NativeShotProtocol.Vec center(NativeShotProtocol.Shot shot,double age){
        if(!shot.tankShell()||!Double.isFinite(age)||age<0||age>shot.lifetime()
            ||age*Math.sqrt(shot.velocity().lengthSquared())>shot.range()+1e-6)throw new IllegalArgumentException("Tank visual flight bounds");
        return shot.start().add(shot.velocity().multiply(age));
    }
}
