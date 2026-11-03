package lab.owmcguest;

import java.lang.reflect.Proxy;
import java.util.*;

/** Pure Java fixtures: no Minecraft server, game, network or actual Boss-bar viewer. */
public final class F9SummonLifecycleCheck {
    private static int checks;
    private static void require(boolean value,String reason){checks++;if(!value)throw new AssertionError(reason);}
    public static void main(String[] args){
        require(BossBarEvidence.inspect(new PlainF9Creature())==BossBarEvidence.Verdict.CLEAR,"ordinary inspected mob");
        for(Object creature:List.of(new LazyF9Creature(),new InheritedF9Creature(),new WrappedF9Creature(),new LateHudF9Creature(),new CustomPacketF9Creature(),new ContractF9Creature(),new MarkerF9Creature(),new ObjectF9Creature(Map.of("main",new SampleCustomHealthBar())),new ObjectF9Creature(Optional.of(List.of(new SampleServerBossBar())))))
            require(BossBarEvidence.inspect(creature)==BossBarEvidence.Verdict.HAS_BAR,"lazy/inherited/generic/custom/protocol/interface metadata: "+creature.getClass().getSimpleName());
        Object proxy=Proxy.newProxyInstance(F9SummonLifecycleCheck.class.getClassLoader(),new Class<?>[]{PlainF9Contract.class},(p,m,a)->null);
        require(BossBarEvidence.inspect(proxy)==BossBarEvidence.Verdict.UNKNOWN,"unreadable generated type fails closed");
        require(BossBarEvidence.inspect(null)==BossBarEvidence.Verdict.UNKNOWN,"missing probe fails closed");
        var cycle=new ObjectF9Creature(null);cycle.hud=cycle;
        require(BossBarEvidence.inspect(cycle)==BossBarEvidence.Verdict.CLEAR,"opaque HUD cycle is bounded");
        require(BossBarEvidence.inspect(new ObjectF9Creature(Collections.nCopies(200,new Object())))==BossBarEvidence.Verdict.UNKNOWN,"opaque container budget fails closed");
        BossBarEvidence.registerBarType(OpaqueProgress.class);
        require(BossBarEvidence.inspect(new OpaqueProgressHolder())==BossBarEvidence.Verdict.HAS_BAR,"runtime Class identity detects a remapped/opaque BossBar type");
        require(BossBarEvidence.inspect(new OpaqueGenericHolder())==BossBarEvidence.Verdict.HAS_BAR,"generic containers preserve remapped BossBar identity");
        require(BossBarEvidence.bossTag("c:bosses")&&BossBarEvidence.bossTag("mod:raid_bosses"),"registered mod Boss tags");
        require(!BossBarEvidence.bossTag("c:monsters"),"ordinary monster tag is not a bar");
        long created=100,until=SummonedMobExpiry.deadline(created);
        require(until-created==3600,"three server minutes at 20 TPS");
        var saved=new HashSet<>(Set.of(SummonedMobExpiry.OWNED,SummonedMobExpiry.PREFIX+until,"unrelated-tag"));
        var reloaded=new HashSet<>(saved); // vanilla Tags NBT round trip preserves these strings.
        require(SummonedMobExpiry.read(reloaded)==until,"deadline survives serialized tag copy");
        require(!SummonedMobExpiry.expired(until-1,SummonedMobExpiry.read(reloaded)),"one tick before expiry");
        require(SummonedMobExpiry.expired(until,SummonedMobExpiry.read(reloaded)),"exact deadline expires");
        require(SummonedMobExpiry.expired(until+3600,SummonedMobExpiry.read(reloaded)),"unloaded across deadline expires immediately on reload");
        require(SummonedMobExpiry.read(new HashSet<>(reloaded))==until,"reload does not grant another 3 minutes");
        require(SummonedMobExpiry.expired(0,SummonedMobExpiry.read(Set.of(SummonedMobExpiry.OWNED))),"missing deadline fails closed");
        for(String suffix:List.of("bad","-1","9223372036854775808"))
            require(SummonedMobExpiry.expired(0,SummonedMobExpiry.read(Set.of(SummonedMobExpiry.PREFIX+suffix))),"invalid saved deadline: "+suffix);
        require(SummonedMobExpiry.read(Set.of(SummonedMobExpiry.PREFIX+10,SummonedMobExpiry.PREFIX+20))<0,"ambiguous deadlines fail closed");
        boolean overflow=false;try{SummonedMobExpiry.deadline(Long.MAX_VALUE-100);}catch(ArithmeticException expected){overflow=true;}
        require(overflow,"deadline arithmetic cannot wrap into immortality");
        require(RandomSummonPolicy.BATCH_SIZE==8,"random request is x8");
        for(String id:List.of("minecraft:ender_dragon","minecraft:wither","aether:slider","aether:valkyrie_queen","aether:sun_spirit","aoa3:smash","aoa3:elite_smash","twilightforest:lich"))
            require(RandomSummonPolicy.blacklisted(id),"known independent-bar owner excluded regardless of size: "+id);
        System.out.println("PASS: F9 Boss-bar evidence and persisted lifetime ("+checks+" checks); no game launched");
    }
}

final class PlainF9Creature { private int damage=2; }
final class SampleServerBossBar {}
final class SampleCustomHealthBar {}
class LazyF9Creature { private final SampleServerBossBar value=null; }
final class InheritedF9Creature extends LazyF9Creature {}
final class WrappedF9Creature { private final Map<UUID,SampleCustomHealthBar> holders=Map.of(); }
final class LateHudF9Creature { private final Object hud=new SampleCustomHealthBar(); }
final class CustomPacketF9Creature { String channel(){return "author:boss_bar_update";} }
interface HealthContractF9 { Object getCustomHealthBar(); }
interface NestedContractF9 extends HealthContractF9 {}
final class ContractF9Creature implements NestedContractF9 { public Object getCustomHealthBar(){return null;} }
interface PlainF9Contract { void tick(); }
interface CustomBossBarF9 {}
interface PlainChildF9 extends CustomBossBarF9 {}
final class MarkerF9Creature implements PlainChildF9 {}
final class ObjectF9Creature { Object hud;ObjectF9Creature(Object hud){this.hud=hud;} }
class OpaqueProgress {}
final class OpaqueProgressHolder { private OpaqueProgress progress; }
final class OpaqueGenericHolder { private Map<UUID,OpaqueProgress> progress; }
