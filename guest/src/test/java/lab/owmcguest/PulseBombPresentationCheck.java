package lab.owmcguest;

public final class PulseBombPresentationCheck {
    private static void close(double actual,double expected){if(Math.abs(actual-expected)>1e-9)throw new AssertionError(actual+" != "+expected);}
    public static void main(String[] args){
        double half=.050670683384;
        close(PulseBombPresentation.contactOffset(half,false,false),0);
        close(.04+PulseBombPresentation.contactOffset(half,true,true)-half,.003);
        close(PulseBombPresentation.contactOffset(half,true,false)-half,.003);
        close(PulseBombPresentation.spinDegrees(123450,123450,false),0);
        close(PulseBombPresentation.spinDegrees(123700,123450,false),90);
        close(PulseBombPresentation.spinDegrees(124700,123450,false),90);
        close(PulseBombPresentation.spinDegrees(123700,123450,true),0);
        close(PulseBombPresentation.spinDegrees(123400,123450,false),0);
        try{PulseBombPresentation.contactOffset(Double.NaN,true,true);throw new AssertionError("NaN accepted");}catch(IllegalArgumentException expected){}
        System.out.println("Pulse presentation: contact clearance and actual-launch phase passed");
    }
}
