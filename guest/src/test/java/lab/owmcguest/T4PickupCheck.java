package lab.owmcguest;

import java.nio.*;
import lab.owmcguest.NativeShotProtocol.Vec;

/** Cross-owner resource receipts and physical convergence are acceptance
 * boundaries. These tests do not claim a real MC/OW session was run. */
public final class T4PickupCheck {
    private static void check(boolean ok,String message){if(!ok)throw new AssertionError(message);}
    private static void near(double a,double b){check(Math.abs(a-b)<1e-7,a+" != "+b);}
    private static byte[] ack(ScrapCreditProtocol.Request r,int phase,int before,int after,int credited){
        var b=ByteBuffer.allocate(80).order(ByteOrder.LITTLE_ENDIAN);b.put("OWSCRA01".getBytes(java.nio.charset.StandardCharsets.US_ASCII)).putInt(1).putInt(r.pid());
        b.putLong(r.creation()).putLong(r.sequence()).putLong(r.wall()).putLong(r.generation()).putLong(r.world()).putLong(r.modelId()).putInt(phase).putInt(before).putInt(after).putInt(credited);return b.array();
    }
    private static void refused(Runnable run,String message){boolean refused=false;try{run.run();}catch(IllegalArgumentException expected){refused=true;}check(refused,message);}
    public static void main(String[] args){
        var from=new Vec(0,0,0);var target=new Vec(2.8,.5,.2);var current=from;double speed=0,last=Math.sqrt(target.subtract(from).lengthSquared());
        for(int i=0;i<40;i++){
            var step=PickupKinematics.toward(current,target,speed,true);double travel=Math.sqrt(step.at().subtract(current).lengthSquared());
            double distance=Math.sqrt(target.subtract(step.at()).lengthSquared());check(travel<=PickupKinematics.MAX_STEP+1e-8&&distance<=last+1e-8,"bounded monotonic attraction");
            current=step.at();speed=step.speed();last=distance;
        }
        near(last,0);check(PickupKinematics.toward(from,target,.2,false).at().equals(from),"block LOS cannot teleport a pickup");
        check(PickupKinematics.toward(from,new Vec(4,0,0),.2,true).at().equals(from),"outside magnet radius");
        refused(()->PickupKinematics.toward(from,new Vec(Double.NaN,0,0),0,true),"nonfinite motion rejected");
        var pose=PickupKinematics.pose(true,false,200,1000,1000);near(pose.yaw()%360,0);check(pose.lift()>=0&&pose.lift()<=.05,"ground bob stays above floor");
        check(PickupKinematics.pose(true,true,200,1000,1000).lift()==0,"magnet sample has no cosmetic bob offset");
        var request=new ScrapCreditProtocol.Request(11,22,33,1000,44,55,66,77);var packet=ByteBuffer.wrap(ScrapCreditProtocol.encode(request)).order(ByteOrder.LITTLE_ENDIAN);
        check(packet.capacity()==80&&packet.getLong(56)==66&&packet.getLong(64)==77&&packet.getInt(72)==25,"native request wire offsets");
        var receipt=ScrapCreditProtocol.decode(ack(request,1,100,125,25),request,1050);check(receipt.credited()==25&&receipt.after()==125,"confirmed native credit");
        check(ScrapCreditProtocol.decode(ack(request,1,190,200,10),request,1050).credited()==10,"cap preserves actual credited amount");
        check(ScrapCreditProtocol.decode(ack(request,2,200,200,0),request,1050).phase()==2,"full native wallet is not a pickup");
        refused(()->ScrapCreditProtocol.decode(ack(request,1,100,150,25),request,1050),"invented resource delta rejected");
        refused(()->ScrapCreditProtocol.decode(ack(request,1,100,125,25),request,1300),"stale ack cannot consume a drop");
        var other=new ScrapCreditProtocol.Request(11,22,34,1000,44,56,66,78);
        refused(()->ScrapCreditProtocol.decode(ack(request,1,100,125,25),other,1050),"cross-world/model/replay ack rejected");
        refused(()->ScrapCreditProtocol.decode(ack(request,3,100,125,25),request,1050),"failed native call is never credited");
        var budget=new NativeTorbjornScrapBudget();budget.observeNative(100);budget.nativeArmorAdmitted();check(budget.amount()==100&&budget.spent()==50,"native Volley must not debit the mirror a second time");budget.observeNative(50);check(budget.amount()==50,"actual native post-spend value mirrored");
        System.out.println("PASS: shared bounded pickup attraction/blocked LOS/no overshoot;spin/bob;80-byte native Scrap request/ack identity,freshness,cap and failed-credit refusal;no double armor debit");
    }
}
