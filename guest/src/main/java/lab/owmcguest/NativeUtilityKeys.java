package lab.owmcguest;

/** Release-to-arm edges: focus/session changes must not repeat world edits. */
public final class NativeUtilityKeys {
    private boolean armed;private int previous;
    public int poll(boolean active,int down){
        down&=7;
        if(!active){armed=false;previous=down;return 0;}
        if(!armed){previous=down;if(down==0)armed=true;return 0;}
        int rising=down&~previous;previous=down;return rising;
    }
    public void reset(){armed=false;previous=0;}
}
