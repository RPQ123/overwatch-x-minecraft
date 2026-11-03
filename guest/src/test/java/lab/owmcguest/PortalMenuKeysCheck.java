package lab.owmcguest;

public final class PortalMenuKeysCheck {
    static void require(boolean v){if(!v)throw new AssertionError();}
    public static void main(String[] args){
        var k=new PortalMenuKeys();
        require(k.poll(true,1,false,14)==0&&!k.open()); // held key on entry
        k.poll(true,0,false,14);k.poll(true,1,false,14);require(k.open());
        require(k.poll(true,1,false,14)==0);k.poll(true,0,false,14);
        require(k.poll(true,2,false,14)==1);require(k.poll(true,2,false,14)==0);
        k.poll(true,0,false,14);require(k.poll(true,1<<9,false,14)==-1&&k.page()==1);
        k.poll(true,0,false,14);require(k.poll(true,2,false,14)==9);
        k.poll(true,0,false,14);require(k.poll(true,1<<8,false,14)==0); // absent row
        k.poll(true,0,false,14);require(k.poll(true,1<<10,false,14)==-1&&k.page()==0);
        k.poll(true,0,false,14);require(k.poll(true,2,true,14)==0); // pending
        k.poll(false,2,false,14);require(!k.open());
        require(k.poll(true,2,false,14)==0);k.poll(true,0,false,14);
        k.poll(true,1,false,14);k.poll(true,0,false,14);
        require(k.poll(true,6,false,14)==0); // ambiguous multiple digits
        System.out.println("Portal menu key lifecycle passed");
    }
}
