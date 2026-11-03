package lab.owmcguest;

/** 只有实际观察到 coreArmor19 的新 active tick 才生成执行令牌。首样本/读失败恢复只作基线。 */
final class NativeTorbjornCoreBegin {
    private long last=-1,begin;
    private boolean suppressed;
    long observe(long armorTick,boolean armorActive,boolean windowActive){
        if(armorTick<0||last>=0&&armorTick<last){missing();return 0;}
        if(last<0){last=armorTick;suppressed=windowActive;return 0;}
        if(armorActive&&armorTick>last){begin=armorTick;suppressed=false;}
        last=armorTick;
        if(!windowActive){begin=0;suppressed=false;}
        return suppressed?0:begin;
    }
    void missing(){last=-1;begin=0;suppressed=true;}
}
