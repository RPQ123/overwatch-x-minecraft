package lab.owmcguest;
import java.nio.*;

/** Offline regression for missing server phases and native receipt ownership. */
public final class WinstonCastCheck {
    private static int checks;
    private static void check(boolean ok,String label){checks++;if(!ok)throw new AssertionError(label);}
    private static byte[] ack(PlacementActionProtocol.Request r,float duration){
        var b=ByteBuffer.allocate(80).order(ByteOrder.LITTLE_ENDIAN);b.put("OWPLAK01".getBytes(java.nio.charset.StandardCharsets.US_ASCII)).putInt(1).putInt(r.pid()).putLong(r.creation()).putLong(r.sequence()).putLong(r.wall()).putLong(r.generation()).putLong(r.world()).putLong(r.modelId()).putInt(r.kind()).putInt(1).putFloat(duration-.1f).putFloat(duration);return b.array();
    }
    public static void main(String[] args){
        var launch=new WinstonJumpLaunch();
        check(!launch.input(false,true,true,1000),"attach establishes input baseline");
        check(launch.input(true,true,true,1001)&&launch.needsLaunch(),"Shift predicts immediately before any native ACK");
        launch.launched();check(!launch.needsLaunch()&&launch.takeCommit()==0,"prediction grants no combat or audio receipt");
        check(!launch.nativeCast(100,1050)&&!launch.needsLaunch(),"native cast matches the existing leap");
        launch.confirm(1000,100,1300);check(!launch.needsLaunch()&&launch.takeCommit()==1000&&launch.takeCommit()==0,"300ms late ACK commits once without a second impulse");
        launch.confirm(1000,100,1400);check(!launch.needsLaunch()&&launch.takeCommit()==0,"duplicate ACK cannot replay movement/effects");
        launch.input(false,true,false,1500);check(!launch.input(true,true,false,1600),"original cooldown still rejects prediction");
        check(launch.nativeCast(200,1700)&&launch.needsLaunch(),"real native recast after a missed zero sample repairs blocked prediction");
        launch.revokeInput();check(launch.needsLaunch(),"focus change cannot erase a real pending cast");
        launch.launched();launch.confirm(2000,200,1750);check(launch.takeCommit()==2000,"every successful cast has an applied impulse before commit");
        launch.reset();launch.confirm(3000,300,2000);check(launch.needsLaunch()&&launch.takeCommit()==0,"ACK fallback cannot commit without launching");
        launch.launched();check(launch.takeCommit()==3000,"missed input/cast observation is repaired by successful ACK");
        launch.reset();launch.input(false,true,true,3000);check(launch.input(true,true,true,3001),"new prediction");launch.launched();
        check(launch.takeCommit()==0&&!launch.waiting(3802),"missing/rejected native ACK adds no cooldown/effects latch");
        launch.input(false,true,true,3803);check(launch.input(true,true,true,3804),"a later valid press is not swallowed by failed prediction");
        launch.reset();check(!launch.input(true,true,true,4000),"joining while Shift held never auto-jumps");
        launch.input(false,false,true,4001);check(!launch.input(true,true,true,4002),"focus return while held is a baseline");
        check(WinstonBarrierAppearance.BLUE>WinstonBarrierAppearance.GREEN&&WinstonBarrierAppearance.GREEN>WinstonBarrierAppearance.RED
            &&WinstonBarrierAppearance.ALPHA>0&&WinstonBarrierAppearance.ALPHA<.5f,"blue translucent dome with bounded opacity");
        var contact=new WinstonJumpContact();var landed=new NativeShotProtocol.Vec(4,8,12);
        contact.begin(1);contact.sample(false,new NativeShotProtocol.Vec(0,10,0),1000);contact.sample(true,landed,1100);
        check(contact.take(1200)==null,"predicted contact grants no impact before native ACK");
        contact.confirm(2,100);check(contact.take(1200)==null,"wrong prediction identity cannot authorize impact");
        contact.confirm(1,100);check(contact.take(1800).equals(landed)&&contact.take(1801)==null,"late ACK releases the actual earlier MC contact once");
        contact.begin(2);contact.confirm(2,200);contact.sample(false,landed,2000);contact.sample(true,landed,2050);
        check(contact.take(2050).equals(landed),"ordinary ACK-before-landing is unchanged");
        contact.begin(3);contact.sample(false,landed,3000);contact.sample(true,landed,3050);contact.confirm(3,300);
        check(contact.take(4051)==null,"stale landing can never become delayed damage");
        contact.begin(4);contact.sample(false,landed,5000);contact.sample(true,landed,5050);contact.begin(5);contact.confirm(4,400);
        check(contact.take(5100)==null,"a new leap retires the previous pending impact");
        var localCast=new WinstonCastPhase();var serverEffect=new WinstonCastPhase();
        check(localCast.observe(0)==0&&serverEffect.observe(0)==0,"initial sample baseline");
        check(localCast.observe(100)==100&&serverEffect.observe(0)==0,"local native cast survives absent movement14/Pet22");
        check(localCast.observe(100)==0,"holding phase cannot repeat");
        check(localCast.observe(120)==120,"short completed cast has a native logger edge");
        localCast.reset();check(localCast.observe(120)==0,"reconnect never replays an old cast");
        check(localCast.observe(10)==0,"clock rollback baseline");check(localCast.observe(20)==20,"next genuine cast after rollback");
        var attached=new WinstonCastPhase();check(attached.observe(500,true)==0,"attach during cast is baseline");
        check(attached.observe(520,false)==0,"End of an attached old cast cannot replay");
        check(attached.observe(600,true)==600,"new cast after release is admitted");
        for(int kind:new int[]{5,6})for(float duration:kind==5?new float[]{8,2}:new float[]{13}){
            var r=new PlacementActionProtocol.Request(11,12,13,1000,14,15,16,17,18,19,20,21,kind);
            check(PlacementActionProtocol.encode(r).length==112,"existing bounded mailbox contract");var bytes=ack(r,duration);
            check(PlacementActionProtocol.decode(bytes,r,1000).phase()==1,"only own native ACK authorizes MC");
            ByteBuffer.wrap(bytes).order(ByteOrder.LITTLE_ENDIAN).putLong(56,999);boolean refused=false;
            try{PlacementActionProtocol.decode(bytes,r,1000);}catch(IllegalArgumentException e){refused=true;}check(refused,"wrong model ACK refused");
        }
        var flight=new WinstonJumpFlight();check(!flight.owns(0,false,true),"ordinary movement still imports native walk speed");
        flight.launch(10);check(flight.owns(10,false,true)&&flight.owns(11,true,true)&&flight.owns(12,true,true),"initial onGround correction cannot erase the launch");
        check(!flight.owns(13,true,true),"ground grace is bounded and collision/landing wins");
        flight.launch(100);var v=WinstonRules.jump(new NativeShotProtocol.Vec(0,0,1));double y=0,z=0;int age=100;
        while(age<220&&flight.owns(age,y<0,true)){
            // Flat, unobstructed vanilla airborne step. Native keyboard input
            // can be zero: it must not zero the actual launch velocity.
            y+=v.y();z+=v.z();v=new NativeShotProtocol.Vec(v.x()*.91,(v.y()-.08)*.98,v.z()*.91);age++;
        }
        check(z>8&&age>110&&age<140,"actual momentum survives idle native walk import until landing");
        check(!flight.owns(age,false,true),"landing permanently releases flight ownership");
        flight.launch(200);check(!flight.owns(201,false,false)&&!flight.owns(202,false,true),"identity or dimension loss revokes old momentum");
        flight.launch(300);check(!flight.owns(421,false,true),"no unbounded flight lease");
        flight.launch(500);check(!flight.owns(1,false,true),"world/player age rollback cannot revive flight");
        System.out.println("PASS WinstonCast "+checks+" assertions; local-cast/missing-server and mailbox contract, no game");
    }
}
