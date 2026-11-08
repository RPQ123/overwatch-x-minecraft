package lab.owmcguest;

import java.util.EnumSet;
import java.util.UUID;
import static lab.owmcguest.WinstonAudioGate.Event.*;

/** Offline audio authorization/lifecycle regression. Never plays a sound. */
public final class WinstonAudioCheck {
    private static int checks;
    private static void check(boolean ok,String reason){checks++;if(!ok)throw new AssertionError(reason);}
    private static WinstonAudioGate.Sample sample(WinstonAudioGate.Scope s,long now,long jump,long barrier,long rage,long casts,long lands,long throws_,long opens,long rages){
        return new WinstonAudioGate.Sample(s,now,jump,barrier,rage,casts,lands,throws_,opens,rages);
    }
    public static void main(String[] args){
        var s=new WinstonAudioGate.Scope(new UUID(1,2),3,4,5);var gate=new WinstonAudioGate();long now=1000;
        var zero=sample(s,now,0,0,0,0,0,0,0,0);
        check(gate.observe(null,s,now).isEmpty(),"missing producer cannot trigger audio");
        check(gate.observe(zero,s,now).isEmpty(),"initial sample is baseline");
        check(gate.observe(sample(s,now,0,0,0,1,0,1,0,0),s,now).isEmpty(),"counters without actual native receipts do not authorize");
        check(gate.observe(sample(s,now,10,0,0,1,0,1,0,0),s,now).isEmpty(),"an ACK alone without a new committed action cannot trigger");
        var start=sample(s,now,11,21,0,2,0,2,0,0);
        check(gate.observe(start,s,now).equals(EnumSet.of(TAKEOFF,THROW)),"independent committed native casts authorize once");
        check(gate.observe(start,s,now).isEmpty(),"held state and retransmitted ACK never replay");
        var contact=sample(s,now,11,21,0,2,1,2,1,0);
        check(gate.observe(contact,s,now).equals(EnumSet.of(LANDING,DEPLOY)),"actual MC landing and deployment follow their admitted casts");
        check(gate.observe(contact,s,now).isEmpty(),"contact cannot repeat");
        check(gate.observe(sample(s,now,11,21,0,2,2,2,2,0),s,now).isEmpty(),"one cast owns at most one landing/open sound");
        check(gate.observe(sample(s,now,11,21,31,2,2,2,2,1),s,now).equals(EnumSet.of(PRIMAL)),"Q requires its real pool Begin and committed rage");
        check(gate.observe(sample(s,now,11,21,31,2,2,2,2,1),s,now).isEmpty(),"Q Begin cannot repeat");
        check(gate.observe(sample(s,now,0,0,0,0,0,0,0,0),s,now).isEmpty(),"counter rollback is baseline");
        var recovered=sample(s,now,12,22,0,1,0,1,0,0);
        check(gate.observe(recovered,s,now).equals(EnumSet.of(TAKEOFF,THROW)),"next genuine casts recover after rollback");
        check(gate.observe(recovered,s,now+201).isEmpty(),"stale state is revoked");
        check(gate.observe(sample(s,now+202,12,22,0,1,1,1,1,0),s,now+202).isEmpty(),"reconnect mid-cast does not replay landing/open");
        gate.reset();check(gate.observe(contact,s,now).isEmpty(),"attach to a completed old cast is baseline");
        for(var changed:new WinstonAudioGate.Scope[]{new WinstonAudioGate.Scope(new UUID(2,3),3,4,5),new WinstonAudioGate.Scope(s.owner(),6,4,5),
                new WinstonAudioGate.Scope(s.owner(),3,6,5),new WinstonAudioGate.Scope(s.owner(),3,4,6)}){
            check(gate.observe(start,changed,now).isEmpty(),"owner/world/generation/model mismatch cannot play");
        }
        check(gate.observe(start,s,now-1).isEmpty(),"future samples are rejected");
        check(HeroVoicePolicy.allowed("ability:jump_pack")&&HeroVoicePolicy.allowed("ability:barrier"),"explicit Winston callouts follow voice policy");
        check(!HeroVoicePolicy.allowed("jump")&&!HeroVoicePolicy.allowed("ability:jump_jet"),"generic movement grunts remain retired");
        check(!HeroVoicePolicy.interrupts("ability:barrier")&&!HeroVoicePolicy.interrupts("ability:jump_pack"),"skill callouts cannot interrupt the voice channel");
        var original=new WinstonAudioGate.NativeSample(s,now,11,100,101,0,21,200,0,0);
        check(WinstonAudioGate.owner(start,original,TAKEOFF,now)==WinstonAudioGate.Owner.NATIVE,"original Effect37 owns its own takeoff sound");
        check(WinstonAudioGate.owner(start,original,LANDING,now)==WinstonAudioGate.Owner.MINECRAFT,"certified missing Effect17 permits one supplement");
        check(WinstonAudioGate.owner(start,original,THROW,now)==WinstonAudioGate.Owner.MINECRAFT,"missing native throw is supplemented only after matching ACK");
        var nativePet=new WinstonAudioGate.NativeSample(s,now,11,100,101,0,21,200,201,202);
        check(WinstonAudioGate.owner(start,nativePet,THROW,now)==WinstonAudioGate.Owner.NATIVE&&WinstonAudioGate.owner(start,nativePet,DEPLOY,now)==WinstonAudioGate.Owner.NATIVE,"native Effect7/Pet own throw/deploy without an echo");
        check(WinstonAudioGate.owner(start,nativePet,DEPLOY,now+201)==WinstonAudioGate.Owner.UNKNOWN,"stale native audio ownership fails closed");
        var unknown=new WinstonAudioGate.NativeSample(s,now,11,100,-1,0,22,200,0,0);
        check(WinstonAudioGate.owner(start,unknown,TAKEOFF,now)==WinstonAudioGate.Owner.UNKNOWN,"failed optional audio read cannot create an echo");
        check(WinstonAudioGate.owner(start,unknown,THROW,now)==WinstonAudioGate.Owner.UNKNOWN,"wrong ACK cannot own a sound");
        for(var entry:WinstonAudioCatalog.SFX.entrySet()){
            check(WinstonAudioCatalog.allowed("winston",entry.getKey(),entry.getValue()),"only exact original media is whitelisted");
            check(!WinstonAudioCatalog.allowed("mei",entry.getKey(),entry.getValue()),"W3 cannot enable other heroes' supplemental SFX");
            check(!WinstonAudioCatalog.allowed("winston",entry.getKey(),"0".repeat(32)),"unknown sound files stay rejected");
            check(!HeroVoicePolicy.allowed(entry.getKey()),"SFX never enters the human voice arbiter");
        }
        check(HeroVoiceDefaultCatalog.allowed("winston","ability:jump_pack","eb2392f2a53913ad7f76076ed28bffd0"),"approved Chinese Jump Pack line is loadable");
        check(HeroVoiceDefaultCatalog.allowed("winston","ability:barrier","4af06c39dc6073d8b445602d2fbff18e"),"approved Chinese barrier line is loadable");
        check(HeroVoiceDefaultCatalog.allowed("winston","ult_cast","e3d1e1fbdbdd60922923f5aa44c12b92"),"approved Primal roar is loadable");
        check(Math.abs(WinstonAudioCatalog.gain(LANDING)-.70)<1e-6,"Landing is audible at the requested bounded gain");
        check(1.048*WinstonAudioCatalog.gain(LANDING)<.74,"Measured source overshoot retains digital headroom");
        for(var event:java.util.List.of(TAKEOFF,THROW,DEPLOY))check(WinstonAudioCatalog.gain(event)==.24f,"Other skill gains retain W3 levels");
        System.out.println("PASS WinstonAudio "+checks+" assertions; receipt/contact ownership, stale/rebind/replay refusal, no playback");
    }
}
