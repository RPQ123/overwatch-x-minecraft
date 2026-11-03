package lab.owmcguest;

/** F12 toggle and one numeric choice, release-to-arm across native focus loss. */
public final class BossTravelMenuKeys {
    private boolean armed,open;
    private int previous;
    public boolean open(){return open;}
    public void close(){open=false;}
    public void reset(){armed=false;open=false;previous=0;}
    /** 0=no destination;1..9,0=one fresh choice. F12 always takes priority. */
    public int poll(boolean valid,int down,boolean busy){
        down&=2047;
        if(!valid){reset();previous=down;return 0;}
        if(!armed){previous=down;if(down==0)armed=true;return 0;}
        int rising=down&~previous;previous=down;
        if((rising&1)!=0){open=!open;return 0;}
        int choices=(rising>>>1)&1023;
        if(!open||busy||Integer.bitCount(choices)!=1)return 0;
        return Integer.numberOfTrailingZeros(choices)+1;
    }
}
