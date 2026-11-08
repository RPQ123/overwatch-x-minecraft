package lab.owmcguest;

import java.util.List;

/** The twelve Assault/Defense heroes from docs/HERO-SKILLS.md, in native picker order. */
public final class HeroNpcCatalog {
    public record Entry(String id,String name,int hero,float health){}
    public static final List<Entry> ENTRIES=List.of(
        new Entry("genji","源氏",0x29,200),new Entry("mccree","麦克雷",0x42,200),
        new Entry("pharah","法老之鹰",8,200),new Entry("reaper","死神",2,250),
        new Entry("soldier76","士兵：76",0x6e,200),new Entry("tracer","猎空",3,150),
        new Entry("bastion","堡垒",0x15,250),new Entry("hanzo","半藏",5,200),
        new Entry("junkrat","狂鼠",0x65,200),new Entry("mei","美",0xdd,250),
        new Entry("torbjorn","托比昂",6,200),new Entry("widowmaker","黑百合",10,200),
        new Entry("roadhog","路霸",0x40,600),new Entry("winston","温斯顿",9,500));
    private HeroNpcCatalog(){}
    public static Entry entry(int index){if(index<0||index>=ENTRIES.size())throw new IllegalArgumentException("hero NPC index");return ENTRIES.get(index);}
}
