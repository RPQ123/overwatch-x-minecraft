package lab.owmcguest;

/** Fresh equivalent tick publications may authorize one guarded meter operation. */
public final class NativeChargeScope {
    public record Identity(int pid,long source,long model,long hero,long world,long session) {}
    public record Sample(Identity identity,long wallMs) {}
    private NativeChargeScope() {}
    public static boolean current(Sample captured,Sample latest,long now){
        if(captured==null||latest==null||captured.identity()==null||!captured.identity().equals(latest.identity()))return false;
        var id=captured.identity();
        if(id.pid()<=0||id.source()==0||id.model()==0||id.hero()==0||id.world()==0)return false;
        return fresh(captured.wallMs(),now)&&fresh(latest.wallMs(),now);
    }
    private static boolean fresh(long wall,long now){return wall>0&&now>=wall-50&&now-wall<=150;}
}
