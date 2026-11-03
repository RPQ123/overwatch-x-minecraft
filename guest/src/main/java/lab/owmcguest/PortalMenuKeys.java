package lab.owmcguest;

/** F8 toggle,1..8 choices,9 next page,0 previous page; held/focus-safe. */
public final class PortalMenuKeys {
    private final BossTravelMenuKeys edges=new BossTravelMenuKeys();
    private int page;
    public boolean open(){return edges.open();}
    public int page(){return page;}
    public void firstPage(){page=0;}
    public void close(){edges.close();}
    public void reset(){edges.reset();page=0;}
    public int poll(boolean valid,int down,boolean busy,int count){
        int selected=edges.poll(valid,down,busy);
        if(!valid)page=0;
        int pages=Math.max(1,(count+7)/8);page=Math.min(page,pages-1);
        if(selected==9){page=(page+1)%pages;return -1;}
        if(selected==10){page=(page+pages-1)%pages;return -1;}
        int index=page*8+selected-1;
        return selected>0&&index<count?index+1:0;
    }
}
