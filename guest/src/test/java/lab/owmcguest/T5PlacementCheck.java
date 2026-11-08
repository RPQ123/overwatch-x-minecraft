package lab.owmcguest;
import java.util.*;
import java.nio.*;
import lab.owmcguest.NativeShotProtocol.Vec;
/** Offline acceptance boundaries; does not open a game or drive input. */
public final class T5PlacementCheck {
    static void check(boolean b,String message){if(!b)throw new AssertionError(message);}
    static void near(double a,double b){check(Math.abs(a-b)<1e-6,a+" != "+b);}
    static void refused(Runnable r){try{r.run();}catch(IllegalArgumentException expected){return;}throw new AssertionError("must refuse invalid scope/value");}
    static byte[] ack(PlacementActionProtocol.Request r){var b=ByteBuffer.allocate(80).order(ByteOrder.LITTLE_ENDIAN);b.put("OWPLAK01".getBytes(java.nio.charset.StandardCharsets.US_ASCII)).putInt(1).putInt(r.pid());b.putLong(r.creation()).putLong(r.sequence()).putLong(r.wall()).putLong(r.generation()).putLong(r.world()).putLong(r.modelId()).putInt(r.kind()).putInt(1).putFloat(r.kind()==1?10:8).putFloat(r.kind()==1?10:8);return b.array();}
    public static void main(String[] args){
        var input=new TorbPlacementInput();check(input.sample(true,false,true,0,0)==TorbPlacementInput.Action.NONE,"baseline");
        check(input.sample(true,true,true,100,2)==TorbPlacementInput.Action.NONE&&input.preview(),"E enters preview only");
        input.sample(true,true,true,100,0);check(input.sample(true,true,true,100,1)==TorbPlacementInput.Action.CONFIRM,"new LMB confirms");input.confirmed(true);
        check(input.sample(true,true,true,100,1)==TorbPlacementInput.Action.NONE&&!input.preview(),"held LMB no repeat");
        input.sample(true,false,true,100,0);input.sample(true,true,true,200,0);check(input.sample(true,true,true,200,4)==TorbPlacementInput.Action.CANCEL,"RMB cancel");
        input.sample(true,false,true,200,0);input.sample(true,true,true,300,0);check(input.sample(true,true,true,300,2)==TorbPlacementInput.Action.CANCEL,"E cancel");
        input.sample(false,true,true,300,1);check(!input.preview(),"menu/focus/hero refusal resets");input.sample(true,true,true,400,1);check(input.sample(true,true,true,400,1)==TorbPlacementInput.Action.NONE,"reattach held click has no edge");
        for(boolean alongX:new boolean[]{true,false})for(double base:new double[]{0,.5,.9375}){
            var ground=new ArrayList<IceWallGeometry.Ground>();for(int i=0;i<IceWallGeometry.WIDTH;i++)for(int d=0;d<IceWallGeometry.THICKNESS;d++)ground.add(new IceWallGeometry.Ground(alongX?i:3+d,alongX?4+d:i,base));
            var p=new IceWallGeometry.Plan(alongX,ground);near(p.yaw(),alongX?0:-90);
            var cells=p.cells(1);near(cells.stream().mapToDouble(c->c.top()/16.-c.lower()).sum(),IceWallGeometry.WIDTH*IceWallGeometry.THICKNESS*4);
            for(int i=0;i<IceWallGeometry.WIDTH;i++){final int n=i;near(cells.stream().filter(c->alongX?c.x()==n:c.z()==n).mapToDouble(c->c.top()/16.-c.lower()).sum(),IceWallGeometry.THICKNESS*4);}
            check(p.pillars(1).size()==5,"original five pillars");for(var pillar:p.pillars(1))near(pillar.height(),4);
            check(IceWallGeometry.PILLAR_WIDTH-IceWallGeometry.PILLAR_SPACING>=.06,"original pillar silhouettes overlap without MC cubes");check(p.cells(0).isEmpty(),"no collision before rise");
            for(int step=1;step<=8;step++)near(p.cells(step/8.).stream().mapToDouble(c->c.top()/16.-c.lower()).sum(),IceWallGeometry.WIDTH*IceWallGeometry.THICKNESS*4*step/8.);
        }
        var stairs=new ArrayList<IceWallGeometry.Ground>();for(int i=0;i<IceWallGeometry.WIDTH;i++)for(int d=0;d<IceWallGeometry.THICKNESS;d++)stairs.add(new IceWallGeometry.Ground(i,d,(i/2)*.5));
        var slope=new IceWallGeometry.Plan(true,stairs);near(slope.cells(1).stream().mapToDouble(c->c.top()/16.-c.lower()).sum(),IceWallGeometry.WIDTH*IceWallGeometry.THICKNESS*4);
        for(var pillar:slope.pillars(1))check(pillar.height()>=4,"terrain-fitted pillar bridges height transitions");
        stairs.set(4,new IceWallGeometry.Ground(4,0,9));refused(()->new IceWallGeometry.Plan(true,stairs));
        var r=new PlacementActionProtocol.Request(33,44,1000,2000,55,66,0x400000,19,0x500000,0x600000,0x700000,300,1);
        var request=ByteBuffer.wrap(PlacementActionProtocol.encode(r)).order(ByteOrder.LITTLE_ENDIAN);check(request.capacity()==112&&request.getLong(96)==300&&request.getInt(104)==1,"native packet offsets");
        var a=ack(r);near(PlacementActionProtocol.decode(a,r,2000).duration(),10);refused(()->PlacementActionProtocol.decode(a,r,2251));a[48]^=1;refused(()->PlacementActionProtocol.decode(a,r,2000));a[48]^=1;
        ByteBuffer.wrap(a).order(ByteOrder.LITTLE_ENDIAN).putFloat(76,11);refused(()->PlacementActionProtocol.decode(a,r,2000));
        var velocity=GrappleCancelMomentum.release(new Vec(.8,.1,.2));near(velocity.x(),.8);near(velocity.z(),.2);near(velocity.y(),GrappleCancelMomentum.MIN_UP);
        velocity=GrappleCancelMomentum.release(new Vec(6,5,8));near(Math.hypot(velocity.x(),velocity.z()),GrappleCancelMomentum.MAX_HORIZONTAL);near(velocity.y(),GrappleCancelMomentum.MAX_UP);
        check(GrappleCancelMomentum.release(new Vec(0,0,0))==null,"no jump without actual pull momentum");
        check(GrappleCancelMomentum.release(new Vec(Double.NaN,1,0))==null,"nonfinite refusal");
        double y=0,dy=GrappleCancelMomentum.MAX_UP,peak=0;int landing=0;for(int t=1;t<100;t++){y+=dy;peak=Math.max(peak,y);dy=(dy-.08)*.98;if(y<0){landing=t;break;}}
        check(peak<14&&landing>20&&landing<50,"bounded vanilla gravity arc after T6 boost");
        System.out.println("PASS: placement edges/held/menu refusal;9 contiguous terrain columns/5 original meshes/8-step rise;112/80 scope/duration receipts;cancel momentum/caps/vanilla gravity peak="+peak+",flightTicks="+landing);
    }
}
