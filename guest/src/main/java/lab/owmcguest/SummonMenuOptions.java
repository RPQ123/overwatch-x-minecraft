package lab.owmcguest;

import java.util.List;

/** Shared root mapping; 8 keeps the existing all-creatures entry, cleanup moves to page 2. */
public final class SummonMenuOptions {
    public record Option(String selection,String label){}
    public static final String ALL="catalog:all";
    // 用户要求（2026-10-27）：删除末影人/村民等测试目标，新增猫批次与随机原版动物。
    public static final List<Option> ROOT=List.of(
        new Option(RandomSummonPolicy.SELECTION,"random_monster"),
        new Option("batch:random8","random8"),
        new Option("batch:cats","cats"),
        new Option("batch:animals8","animals8"),
        new Option(ALL,"singles"));
    private SummonMenuOptions(){}
}
