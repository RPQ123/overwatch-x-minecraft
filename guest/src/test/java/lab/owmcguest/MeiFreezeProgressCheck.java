package lab.owmcguest;

public final class MeiFreezeProgressCheck {
    private static void require(boolean ok,String error){if(!ok)throw new AssertionError(error);}
    public static void main(String[] args){
        var p=new MeiFreezeProgress();
        require(p.hit("one",0)&&!p.hit("one",0)&&p.stacks()==1,"duplicate contact");
        p.advance(10);require(p.stacks()==1,"decay delay");p.advance(11);require(p.empty(),"decay after delay");
        for(int i=0;i<29;i++)require(p.hit("a"+i,20+i),"accepted hit");
        require(p.stacks()==29&&!p.frozen(48)&&Math.abs(p.slow(48)-.9)<1e-9,"pre-freeze slow");
        require(p.hit("last",49)&&p.frozen(49)&&p.remaining(49)==90,"threshold");
        require(!p.hit("during",60)&&p.remaining(60)==79,"no refreeze extension");
        p.advance(138);require(p.frozen(138),"last frozen tick");p.advance(139);require(p.empty()&&!p.frozen(139),"exact expiry");
        require(p.hit("again",140)&&p.stacks()==1,"rearm");require(!p.hit("past",139),"past hit rejected");
        var batch=new MeiFreezeProgress();for(int i=0;i<30;i++)batch.hit("b"+i,100);require(batch.frozen(100),"unique catchup contacts");
        batch.advance(10000);require(batch.empty(),"large tick gap cleanup");
        System.out.println("Mei contact/duplicate/decay/expiry/rearm/catchup checks passed");
    }
}
