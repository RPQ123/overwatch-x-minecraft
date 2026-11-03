package lab.owmcguest;

import java.util.UUID;

/** 审查回归：cleanup 重放、真实 Begin/End、读失败恢复、完整身份负例。无需 MC 进程。 */
public final class NativeBuildersReviewCheck {
    private static int checks;
    private static void check(boolean ok){checks++;if(!ok)throw new AssertionError("check "+checks);}
    public static void main(String[] args){
        var owner=UUID.fromString("00000000-0000-0000-0000-000000000001");
        var other=UUID.fromString("00000000-0000-0000-0000-000000000002");
        var actor=new NativeTorbjornCoreAdmission.Actor(owner,11,22);
        var ledger=new NativeTorbjornCoreAdmission();var signal=new NativeTorbjornCoreBegin();
        check(signal.observe(0,false,false)==0);
        long begin=signal.observe(100,true,true);check(begin==100);check(ledger.admit(actor,begin));
        // 服务器效果已清理、客户端仍在报告同一激活：不能再发护甲。
        for(int i=0;i<20;i++)check(!ledger.admit(actor,signal.observe(100,true,true)));
        // 19的End或其他Core节点继续active，不能把End的tick当作新的Begin。
        long ending=signal.observe(110,false,true);check(ending==100);check(!ledger.admit(actor,ending));
        check(signal.observe(110,false,false)==0);
        check(signal.observe(200,true,true)==200);check(ledger.admit(actor,200));check(!ledger.admit(actor,100));
        // 读失败后正处active的首样本只作基线；直到实际观察到新的Begin。
        signal.missing();check(signal.observe(200,true,true)==0);check(signal.observe(200,true,true)==0);
        check(signal.observe(210,false,true)==0);check(signal.observe(300,true,true)==300);check(ledger.admit(actor,300));
        check(signal.observe(250,true,true)==0);check(signal.observe(300,true,true)==0);
        // MC世界不属于原版执行令牌：cleanup/换世界不能绕开同一actor的去重。
        check(!ledger.admit(new NativeTorbjornCoreAdmission.Actor(owner,11,22),300));
        check(ledger.admit(new NativeTorbjornCoreAdmission.Actor(owner,12,22),1));
        check(ledger.admit(new NativeTorbjornCoreAdmission.Actor(owner,11,23),1));
        check(!ledger.admit(new NativeTorbjornCoreAdmission.Actor(owner,0,22),1));
        check(!ledger.admit(actor,0));check(!ledger.admit(null,1));
        var bounded=new NativeTorbjornCoreAdmission(1);check(bounded.admit(actor,100));
        check(!bounded.admit(new NativeTorbjornCoreAdmission.Actor(other,12,23),100));
        check(!bounded.admit(actor,100));check(bounded.admit(actor,101));

        var identity=new NativeJunkratTireIdentity(owner,33,11,22);long junk=0x02e0000000000065L;
        check(identity.matches(owner,junk,33,11,22));
        check(!identity.matches(other,junk,33,11,22));check(!identity.matches(owner,0x02e0000000000006L,33,11,22));
        check(!identity.matches(owner,junk,34,11,22));check(!identity.matches(owner,junk,33,12,22));check(!identity.matches(owner,junk,33,11,23));
        check(!identity.matches(null,junk,33,11,22));check(!identity.matches(owner,junk,0,11,22));
        check(!new NativeJunkratTireIdentity(owner,0,11,22).matches(owner,junk,0,11,22));
        check(!new NativeJunkratTireIdentity(owner,33,0,22).matches(owner,junk,33,0,22));
        check(!new NativeJunkratTireIdentity(owner,33,11,0).matches(owner,junk,33,11,0));
        check(NativeJunkratTireIdentity.fresh(1000,10,1000,10,1100));
        check(NativeJunkratTireIdentity.fresh(1000,10,1000,11,1100)); // 同scope的原版新帧不能让控制锁闪断
        check(!NativeJunkratTireIdentity.fresh(1000,10,1000,9,1100));
        check(!NativeJunkratTireIdentity.fresh(800,10,1000,11,1100));
        check(!NativeJunkratTireIdentity.fresh(1000,10,900,11,1100));
        check(!NativeJunkratTireIdentity.fresh(1200,10,1000,11,1100));
        check(!NativeJunkratTireIdentity.fresh(1000,10,1200,11,1100));
        check(!NativeJunkratTireIdentity.fresh(1000,0,1000,11,1100));
        System.out.println("NativeBuildersReviewCheck passed: "+checks+" assertions");
    }
}
