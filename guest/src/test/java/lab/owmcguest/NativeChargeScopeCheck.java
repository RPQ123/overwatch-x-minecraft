package lab.owmcguest;

public final class NativeChargeScopeCheck {
    private static void check(boolean value,String message){if(!value)throw new AssertionError(message);}
    private static NativeSkillReader.State forms(long source,long model,long hero,boolean recon,boolean sentry,boolean tank){
        return new NativeSkillReader.State(source,model,hero,java.util.Map.of("recon",new NativeSkillReader.Entry(10,recon),"sentry",new NativeSkillReader.Entry(11,sentry),"tank",new NativeSkillReader.Entry(12,tank)),null);
    }
    private static void tankCharge(){
        long hero=0x02e0000000000015L,source=21,model=31;var id=new NativeChargeScope.Identity(17,source,model,hero,-41,0);
        check(NativeChargeController.requiresSkills(hero),"Bastion must read its actual native skill states before credit");
        var recon=forms(source,model,hero,true,false,false);var tank=forms(source,model,hero,false,false,true);
        var reconGate=NativeChargeController.skillGate(hero,source,model,recon,null);var tankGate=NativeChargeController.skillGate(hero,source,model,tank,null);
        check(reconGate.ready()&&!reconGate.active(),"Unique original Recon permits ordinary natural charge");
        check(tankGate.ready()&&tankGate.active(),"Original Tank105 Begin suppresses credit");
        var budget=new NativeChargeBudget();budget.observe(id,0,0,true);budget.observe(id,10,.1,true);
        check(budget.pending()>10,"Before Begin, real idle passive/damage credit can be pending");
        budget.observe(id,110,.1,!tankGate.active()&&tankGate.ready());
        for(int i=0;i<100;i++)budget.observe(id,110+i*19,.05,!tankGate.active()&&tankGate.ready());
        check(budget.pending()==0&&budget.offer(0,1500,3)==0,"Tank active clears existing credit and cannot recharge itself from damage or time");
        var unknowns=java.util.List.of(
            forms(source,model,hero,false,false,false),forms(source,model,hero,true,false,true),forms(source,model,hero,true,true,false),
            forms(source+1,model,hero,true,false,false),forms(source,model+1,hero,true,false,false),forms(source,model,hero+1,true,false,false),
            new NativeSkillReader.State(source,model,hero,java.util.Map.of("recon",new NativeSkillReader.Entry(10,true)),null));
        for(var unknown:unknowns){
            var gate=NativeChargeController.skillGate(hero,source,model,unknown,null);check(!gate.ready(),"Empty/conflicting/missing/replaced native forms refuse credit");
            budget.observe(id,2100,.1,true);budget.observe(id,2200,.1,!gate.active()&&gate.ready());check(budget.pending()==0,"Unknown form discards pending credit instead of banking it for End");
        }
        check(!NativeChargeController.skillGate(hero,source,model,null,null).ready(),"Failed native state read cannot grant Bastion credit");
        // Native End restores a unique Recon state. Damage already observed in
        // Tank/unknown phases is not granted retroactively on this transition.
        budget.observe(id,2200,.05,!reconGate.active()&&reconGate.ready());
        check(Math.abs(budget.pending()-.25)<1e-9,"Actual native End resumes only new idle passive charge");
        var sentryGate=NativeChargeController.skillGate(hero,source,model,forms(source,model,hero,false,true,false),null);
        check(sentryGate.ready()&&!sentryGate.active(),"Original Sentry remains eligible outside Tank Q");
        for(var changed:new NativeChargeScope.Identity[]{new NativeChargeScope.Identity(17,source,model+1,hero,-41,0),new NativeChargeScope.Identity(17,source,model,hero,-42,0),new NativeChargeScope.Identity(17,source,model,hero,-41,1)}){
            budget.observe(changed,2200,0,true);check(budget.pending()==0,"Hero-model/world/session transition clears old Tank budget");
        }
        // Preserve the prior required geometry for Visor/Blossom, and the
        // existing Pharah/Deadeye active-state suppression policy.
        for(var profile:java.util.Map.of(0x02e0000000000008L,"barrage",NativeDeadeyeRuntime.HERO,"ultimate",NativeVisorRuntime.HERO,"visor",NativeReaperRuntime.HERO,"firing").entrySet()){
            var state=new NativeSkillReader.State(source,model,profile.getKey(),java.util.Map.of(profile.getValue(),new NativeSkillReader.Entry(10,true)),null);
            var gate=NativeChargeController.skillGate(profile.getKey(),source,model,state,new double[]{1,1});check(gate.ready()&&gate.active(),"Existing native ultimate active phases still suppress charge");
            check(!NativeChargeController.skillGate(profile.getKey(),source,model,null,null).ready(),"Existing required skill failure still refuses credit");
        }
        check(!NativeChargeController.skillGate(NativeVisorRuntime.HERO,source,model,new NativeSkillReader.State(source,model,NativeVisorRuntime.HERO,java.util.Map.of(),null),null).ready(),"Visor geometry requirement remains intact");
        check(NativeChargeController.skillGate(0x02e0000000000009L,source,model,null,null).ready(),"Other existing generic-charge heroes retain their prior policy");
    }
    public static void main(String[] args){
        long torb=0x02e0000000000006L;
        var coreIdle=new NativeSkillReader.State(21,31,torb,java.util.Map.of("ultimate",new NativeSkillReader.Entry(0,false),"coreAnimation",new NativeSkillReader.Entry(0,false),"coreArmor",new NativeSkillReader.Entry(0,false),"coreEffect",new NativeSkillReader.Entry(0,false),"coreTimer",new NativeSkillReader.Entry(0,false)),null);
        check(NativeChargeController.requiresSkills(torb)&&NativeChargeController.skillGate(torb,21,31,coreIdle,null).ready(),"Torb requires the exact original Core graph before charge");
        var coreBudget=new NativeChargeBudget();var coreId=new NativeChargeScope.Identity(17,21,31,torb,-41,0);
        coreBudget.observe(coreId,0,0,true);coreBudget.observe(coreId,10,.1,true);
        for(String phase:coreIdle.entries().keySet()){
            var entries=new java.util.HashMap<>(coreIdle.entries());entries.put(phase,new NativeSkillReader.Entry(10,true));
            var gate=NativeChargeController.skillGate(torb,21,31,new NativeSkillReader.State(21,31,torb,entries,null),null);
            check(gate.ready()&&gate.active(),"Every actual Core windup/armor/effect/timer phase suppresses credit");
            coreBudget.observe(coreId,100,.1,!gate.active()&&gate.ready());check(coreBudget.pending()==0,"Core cannot bank active damage for End");
        }
        check(!NativeChargeController.skillGate(torb,21,31,null,null).ready()&&!NativeChargeController.skillGate(torb,21,32,coreIdle,null).ready(),"Missing/replaced Core cannot charge");
        var missing=new java.util.HashMap<>(coreIdle.entries());missing.remove("coreTimer");
        check(!NativeChargeController.skillGate(torb,21,31,new NativeSkillReader.State(21,31,torb,missing,null),null).ready(),"Partial Core binding cannot charge");
        coreBudget.observe(coreId,100,.05,true);check(Math.abs(coreBudget.pending()-.25)<1e-9,"Core End accepts only new idle passive credit");
        long widow=NativeInfraSightState.HERO;
        var idle=new NativeSkillReader.State(21,31,widow,java.util.Map.of("ultimate",new NativeSkillReader.Entry(0,false),"infraAnimation",new NativeSkillReader.Entry(0,false),"infraEffect",new NativeSkillReader.Entry(0,false),"infraTimer",new NativeSkillReader.Entry(0,false)),null);
        check(NativeChargeController.requiresSkills(widow)&&NativeChargeController.skillGate(widow,21,31,idle,null).ready(),"Typed original Widow idle permits charge");
        for(String phase:idle.entries().keySet()){
            var entries=new java.util.HashMap<>(idle.entries());entries.put(phase,new NativeSkillReader.Entry(10,true));
            var state=new NativeSkillReader.State(21,31,widow,entries,null);
            check(NativeChargeController.skillGate(widow,21,31,state,null).active(),"Every original windup/reveal phase suppresses charge");
        }
        check(!NativeChargeController.skillGate(widow,21,31,null,null).ready()&&!NativeChargeController.skillGate(widow,21,32,idle,null).ready(),"Missing/stale Widow skill identity cannot bank charge");
        var id=new NativeChargeScope.Identity(17,21,31,0x02e0000000000008L,-41,0);
        // A 20Hz producer replaces its Context while a 75ms guarded read runs.
        // Object-reference equality starved every such iteration; identity does not.
        for(long start=1000;start<6000;start+=75){
            var captured=new NativeChargeScope.Sample(id,start);
            var latest=new NativeChargeScope.Sample(id,(start+75)/50*50);
            check(captured!=latest&&NativeChargeScope.current(captured,latest,start+75),"fresh equivalent producer refresh must not starve charge");
        }
        var captured=new NativeChargeScope.Sample(id,1000);
        check(!NativeChargeScope.current(captured,new NativeChargeScope.Sample(id,1200),1200),"fresh producer cannot extend old sample permissions");
        check(!NativeChargeScope.current(captured,new NativeChargeScope.Sample(id,800),1000),"stale producer");
        check(!NativeChargeScope.current(captured,new NativeChargeScope.Sample(id,1100),1000),"future producer");
        var changed=new NativeChargeScope.Identity[]{
            new NativeChargeScope.Identity(18,21,31,id.hero(),-41,0),
            new NativeChargeScope.Identity(17,22,31,id.hero(),-41,0),
            new NativeChargeScope.Identity(17,21,32,id.hero(),-41,0),
            new NativeChargeScope.Identity(17,21,31,0x02e0000000000042L,-41,0),
            new NativeChargeScope.Identity(17,21,31,id.hero(),-42,0),
            new NativeChargeScope.Identity(17,21,31,id.hero(),-41,1),
            new NativeChargeScope.Identity(17,21,0,id.hero(),-41,0)
        };
        for(var next:changed)check(!NativeChargeScope.current(captured,new NativeChargeScope.Sample(next,1050),1075),"changed process/source/model/hero/world/session refused");
        check(!NativeChargeScope.current(null,captured,1050)&&!NativeChargeScope.current(captured,null,1050),"missing context");
        tankCharge();
        System.out.println("PASS: 20Hz charge publication race, current native Tank credit suppression, bounded freshness and process/model/hero/world/session revocation");
    }
}
