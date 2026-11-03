package lab.owmcguest;

import java.util.HashMap;
import java.util.Map;
import java.util.List;
import java.util.Random;

/** 语音挂接：无游戏依赖的优先级、旧所有者与边沿规则。 */
public final class HeroVoicePolicy {
    private HeroVoicePolicy() {}
    // 语音挂接：P10已有日语ASR证据，取0..2.65秒；该ID是裁剪配方派生标识，非站点hash。
    public static final String HANZO_ULT_HASH="ea38b68ebfa92aaa527c958f81edcb31";
    // 语音挂接：用户接受中文后固定已验证的本人友方大招“正在肃清敌人”，不选未确认英文。
    public static final String REAPER_ULT_HASH="a81b42c757722f46f7e007d3916caa1f";
    public static String fixedHash(String hero,String event){return !event.equals("ult_cast")?"":hero.equals("hanzo")?HANZO_ULT_HASH:hero.equals("reaper")?REAPER_ULT_HASH:"";}
    public static boolean clipAllowed(String hero,String event,String hash){
        if(hero.equals("reaper")&&event.equals("ult_cast"))return false; // 用户要求：死神不要大招语音。
        String fixed=fixedHash(hero,event);return allowed(event)&&(fixed.isEmpty()||fixed.equals(hash));
    }
    /** 语音挂接：全英雄只保留明确台词；位移、状态、语气声不能借旧清单复活。 */
    public static boolean allowed(String event){if(movementEvent(event))return false;return event.equals("select")||event.equals("ult_cast")||event.equals("ult_ready")||event.equals("kill")||event.equals("multikill")
        ||event.startsWith("ability:")&&!MUTED_ABILITIES.contains(event);}
    /** 语音挂接：仅开大/充满提示可抢占；所有其他语音到达忙声道时丢弃。 */
    public static boolean interrupts(String event){return event.equals("ult_cast")||event.equals("ult_ready");}
    /** 语音挂接：起跳/落地/攀爬语气事件永久移除，不因换事件前缀而恢复。 */
    public static boolean movementEvent(String event){
        return java.util.Set.of("jump","land","landing","takeoff","effort","movement:jump","movement:land",
            "ability:jump","ability:double_jump","ability:super_jump","ability:jump_jet","ability:rocket_jump","ability:leap","ability:wall_climb","ability:landing").contains(event);
    }
    public static boolean movementSound(String namespace,String path,String category){
        if(!category.equals("PLAYERS")&&!category.equals("VOICE"))return false;
        if(namespace.equals("minecraft"))return path.equals("entity.player.small_fall")||path.equals("entity.player.big_fall");
        return namespace.equals("owmcguest")&&path.matches(".*(?:^|[./_])(jump|jumpjet|landing|land|takeoff|effort|exertion|grunt)(?:[./_]|$).*");
    }
    private static final java.util.Set<String> MUTED_ABILITIES=java.util.Set.of("ability:blink","ability:recall","ability:grappling_hook");
    public static boolean selectionAllowed(String hero){return !hero.isBlank()&&!hero.equals("tracer")&&!hero.equals("bastion");}
    public static boolean optional(String event){return event.equals("reload")||event.equals("idle")||event.startsWith("status:");}
    public static int priority(String event) {
        if (event.startsWith("ability:")) return 90;
        if (event.startsWith("status:")) return 45; // 语音挂接：状态反应优先于普通痛叫。
        return switch (event) {
            case "select" -> 95;
            case "ult_cast" -> 101;
            case "kill", "multikill" -> 80;
            case "death" -> 70;
            case "respawn" -> 60;
            case "ult_ready" -> 100;
            case "pain" -> 40;
            case "healing_request" -> 30;
            case "jump" -> 20;
            case "reload" -> 32;
            case "idle" -> 10;
            default -> 0;
        };
    }
    public static long cooldownMs(String event) {
        if(HeroVoiceSkillCooldowns.applies(event))return HeroVoiceSkillCooldowns.COOLDOWN_MS;
        if(event.startsWith("status:"))return event.equals("status:healed")?30000:20000;
        return switch (event) {
            case "ult_ready" -> 0; // 语音挂接：只按充满边沿去重，每轮充满可说一次，不设时间冷却。
            case "healing_request" -> 20000;
            case "kill", "multikill" -> HeroVoiceKillGate.COOLDOWN_MS;
            case "pain" -> 2500;
            case "jump" -> 4000;
            case "reload" -> 8000;
            case "idle" -> 120000;
            default -> 1000;
        };
    }
    public static boolean legacyOwned(long hero, String event) {
        if (event.equals("select")) return true;
        int id = (int)(hero & 0xffff);
        if (event.equals("ult_cast")) return id==0x29||id==0x42||id==8||id==2||id==0x6e||id==3;
        return id==0x42&&event.equals("ability:flashbang")
            || id==0x6e&&event.equals("ability:biotic_field")
            || id==2&&event.equals("ability:shadow_step");
    }
    public static String nextHash(List<String> hashes,String previous,Random random){
        if(hashes.isEmpty())throw new IllegalArgumentException("empty voice bank");
        var choices=hashes.size()>1?hashes.stream().filter(h->!h.equals(previous)).toList():hashes;
        return choices.get(random.nextInt(choices.size()));
    }
    public static String heroName(long hero) {
        return switch ((int)(hero & 0xffff)) {
            case 0x29->"genji";case 0x42->"mccree";case 8->"pharah";case 2->"reaper";
            case 0x6e->"soldier76";case 3->"tracer";case 0x15->"bastion";case 5->"hanzo";
            case 0x65->"junkrat";case 0xdd->"mei";case 6->"torbjorn";case 10->"widowmaker";
            case 0x7a->"dva";case 7->"reinhardt";case 0x40->"roadhog";case 9->"winston";
            case 0x68->"zarya";case 0x79->"lucio";case 4->"mercy";case 0x16->"symmetra";
            case 0x20->"zenyatta";default->"";
        };
    }
    public static final class Edges {
        private final Map<String,Long> counters = new HashMap<>();
        /** 语音挂接：仅已知初始空报告可建立零基线；失败读数不能覆盖已有基线。 */
        public boolean newer(String key,Long value,boolean initiallyZero){
            if(value==null){if(initiallyZero)counters.putIfAbsent(key,0L);return false;}
            return newer(key,value.longValue());
        }
        /** Initial samples/regressions establish a baseline, not an event. */
        public boolean newer(String key,long value) {
            Long old=counters.put(key,value);
            return old!=null&&value>old;
        }
        public void clear(){counters.clear();}
    }
    /** 语音挂接：低弹药、回满、新原版赋值tick三者同时成立；初读满/回填无提交不说。 */
    public static final class Reload {
        private boolean baseline,spent,pendingFull,sawCommit;
        private int maximum;
        private long commit,fullAt,commitAt;
        public boolean observe(int ammo,int capacity,long tick,long now,boolean blocked){
            if(ammo<0||capacity<1||ammo>capacity||tick<0){reset();return false;}
            if(!baseline||capacity!=maximum||tick<commit||blocked){
                baseline=true;maximum=capacity;commit=tick;spent=!blocked&&ammo<capacity;pendingFull=sawCommit=false;return false;
            }
            boolean newCommit=tick>commit;commit=tick;
            if(newCommit&&spent){sawCommit=true;commitAt=now;}
            if(sawCommit&&now-commitAt>500_000_000L)sawCommit=false;
            if(ammo<capacity){spent=true;pendingFull=false;return false;}
            if(spent&&!pendingFull){pendingFull=true;fullAt=now;}
            if(pendingFull&&now-fullAt<=500_000_000L&&sawCommit){spent=pendingFull=sawCommit=false;return true;}
            if(pendingFull&&now-fullAt>500_000_000L)spent=pendingFull=false;
            return false;
        }
        public void reset(){baseline=spent=pendingFull=sawCommit=false;maximum=0;commit=fullAt=commitAt=0;}
    }
    /** 语音挂接：每个新预览周期只认一次MC实际放置；确认请求和旧墙都不发声。 */
    public static final class IceWall {
        private boolean baseline,armed;
        private long lastBuild,lastPreview,buildFloor,pendingBuild,lastOfferedBuild;
        public long observe(long builds,long previews,boolean placed,boolean selectionPending){
            if(builds<0||previews<0){reset();return 0;}
            if(!baseline||builds<lastBuild||previews<lastPreview||selectionPending){
                baseline=true;lastBuild=builds;lastPreview=previews;armed=false;pendingBuild=0;return 0;
            }
            // 语音挂接：确认先于实际放置时锁存本轮，重复预览不能抬高floor吞掉待建墙。
            if(previews>lastPreview&&!armed){armed=true;buildFloor=lastBuild;}
            lastBuild=builds;lastPreview=previews;
            if(armed&&builds>buildFloor)pendingBuild=builds;
            if(armed&&pendingBuild>0&&placed){armed=false;lastOfferedBuild=pendingBuild;pendingBuild=0;return lastOfferedBuild;}
            return 0;
        }
        public boolean armed(){return armed;}
        public long pendingBuild(){return pendingBuild;}
        public long lastOfferedBuild(){return lastOfferedBuild;}
        public void reset(){baseline=armed=false;lastBuild=lastPreview=buildFloor=pendingBuild=lastOfferedBuild=0;}
    }
    public static final class Meter {
        private boolean baseline,armed;
        private double lastCost;
        public boolean observe(double charge,double cost) {
            if(!Double.isFinite(charge)||!Double.isFinite(cost)||cost<=0||charge<0||charge>cost+Math.max(.001,cost*1e-6)) {reset();return false;}
            boolean full=charge>=cost-Math.max(1e-6,cost*1e-7);
            if(!baseline||cost!=lastCost){baseline=true;lastCost=cost;armed=!full;return false;}
            if(!full)armed=true; // 语音挂接：99%→100%也是新一次充满，不要求先下降到90%。
            if(full&&armed){armed=false;return true;}
            return false;
        }
        public void reset(){baseline=armed=false;lastCost=0;}
    }
}
