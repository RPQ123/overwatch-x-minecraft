package lab.owmcguest;

/** Immutable identity travels with work already in flight across a session reset. */
public final class NativeUltimateEventGate {
    public record Scope(long session,long world,long source,long model) {}
    private NativeUltimateEventGate() {}
    public static boolean accepts(Scope event,Scope current,long wallMs,long now){
        return event!=null&&event.equals(current)&&event.session()>=0&&event.world()!=0
            &&event.source()!=0&&event.model()>0&&event.model()<=0xffffffffL
            &&now-wallMs<=200&&wallMs-now<=50;
    }
}
