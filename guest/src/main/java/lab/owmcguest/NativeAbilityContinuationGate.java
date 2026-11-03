package lab.owmcguest;

/** Initial cast requires gameplay input; an admitted native cinematic may lock
 * input while its same exact cast continues. Owner changes never continue it. */
public final class NativeAbilityContinuationGate {
    public record Scope(long source,long world,long model){}
    private Scope scope;private long last,admitted,inputWall;
    public boolean observe(Scope next,long begin,boolean active,boolean input,long now){
        if(next==null||next.source()==0||next.world()==0||next.model()==0||begin<0){reset();return false;}
        if(!next.equals(scope)){scope=next;last=begin;admitted=0;inputWall=input?now:0;return false;}
        if(input)inputWall=now;
        if(begin<last){last=begin;admitted=0;return false;}
        // Begin and the original input lock may be published in one frame.
        // A preceding fresh first-person frame is valid for only150ms and
        // only within this exact owner/world; it grants no event by itself.
        boolean freshInput=input||(inputWall!=0&&now>=inputWall&&now-inputWall<=150);
        if(begin>last){last=begin;admitted=active&&freshInput?begin:0;}
        if(!active){admitted=0;return false;}
        return admitted!=0&&begin==admitted;
    }
    public void reset(){scope=null;last=admitted=inputWall=0;}
}
