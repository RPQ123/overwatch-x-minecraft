package lab.owmcguest;

/** MC 近似：沿原版脊柱 +Z 的行进波；不是原版动画资源的解码或播放。 */
final class HanzoDragonSwim {
    static final double LENGTH=40.66034508,AMPLITUDE=.45,WAVE=2*Math.PI/16,PHASE_PER_TICK=.16;
    record Sample(double x,double y,double slopeX,double slopeY) { }
    static Sample sample(double sourceZ,double phase){
        double fraction=Math.max(0,Math.min(1,-sourceZ/LENGTH));
        double amplitude=AMPLITUDE*(.15+.85*fraction);
        double derivative=sourceZ<0&&sourceZ>-LENGTH?-AMPLITUDE*.85/LENGTH:0;
        double angle=sourceZ*WAVE+phase,sin=Math.sin(angle),cos=Math.cos(angle);
        return new Sample(amplitude*sin,.35*amplitude*cos,
            derivative*sin+amplitude*WAVE*cos,.35*(derivative*cos-amplitude*WAVE*sin));
    }
    private HanzoDragonSwim(){ }
}
