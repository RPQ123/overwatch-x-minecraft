package lab.owmcguest;

import java.util.UUID;

/** Offline lifecycle/cap scenarios; does not certify native damage or pixels. */
public final class NativeSustainPhaseCheck {
    private static int checks;
    private static void require(boolean ok,String why){checks++;if(!ok)throw new AssertionError(why);}
    private static NativeSustainPhase.Scope scope(long world,long source,long model,long hero){
        return new NativeSustainPhase.Scope(new UUID(0,1),world,source,model,hero);
    }
    public static void main(String[] args){
        var p=new NativeSustainPhase();var mei=scope(1,2,3,NativeSustainPhase.MEI);
        require(p.refresh(mei,100,true,150,3.9,1000),"actual Cryo phase accepted");
        double given=0;for(int i=0;i<20;i++)given+=p.consume();
        require(p.active(1150)&&!p.active(1151)&&!p.active(949),"freshness and future-clock bounds");
        require(p.refresh(mei,100,true,150,3.9,1200),"same execution resumes after gap");
        for(int i=0;i<100;i++)given+=p.consume();
        require(Math.abs(given-15)<1e-8&&p.remaining()==0,"gap/repeated snapshots cannot refill 150 native HP");
        require(!p.refresh(mei,99,true,150,3.9,1201),"older active snapshot cannot refill");
        require(!p.refresh(mei,100,true,150,3.9,1199),"older wall observation rejected");
        require(!p.refresh(mei,100,true,300,3.9,1202),"same execution cannot change its declared budget");
        require(p.refresh(mei,101,false,150,3.9,1250)&&!p.active(1250),"original End immediately stops");
        require(!p.refresh(mei,100,true,150,3.9,1251),"active before End cannot reopen protection");
        require(!p.refresh(mei,101,true,150,3.9,1251),"terminal timestamp cannot reopen protection");
        require(p.refresh(mei,102,true,150,3.9,1300)&&p.remaining()==15,"later real Begin gets a new cap");
        var replaced=scope(1,2,4,NativeSustainPhase.MEI);
        require(p.refresh(replaced,102,true,150,3.9,1400)&&p.remaining()==15,"new model with equal timestamp has its own cap");
        var restarted=scope(2,3,4,NativeSustainPhase.MEI);
        require(p.refresh(restarted,1,true,150,3.9,1500),"new world/source may restart native clock");
        p.clear();require(!p.active(1500)&&p.scope()==null,"session reset clears authority");
        var repair=scope(1,2,5,NativeSustainPhase.BASTION);
        require(p.refresh(repair,9,true,50,1,2000),"Bastion repair accepted");
        given=0;for(int i=0;i<200;i++)given+=p.consume();
        require(Math.abs(given-50)<1e-8,"held native repair remains 5 MC HP/s without Cryo cap");
        require(p.refresh(repair,10,false,50,1,2100)&&!p.active(2100),"repair release stops");
        require(!p.refresh(scope(1,0,5,NativeSustainPhase.MEI),11,true,150,3.9,2200),"zero generation rejected");
        require(!p.refresh(mei,11,true,Double.NaN,3.9,2200),"nonfinite amount rejected");
        require(!p.refresh(mei,11,true,150,0,2200),"zero interval rejected");
        System.out.println("NativeSustainPhaseCheck: "+checks+" checks passed");
    }
}
