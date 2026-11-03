package lab.owmcguest;
public final class BossTravelMenuKeysCheck {
    static void check(boolean b){if(!b)throw new AssertionError();}
    public static void main(String[] args){
        var k=new BossTravelMenuKeys();check(k.poll(true,1,false)==0&&!k.open());
        k.poll(true,0,false);check(k.poll(true,1,false)==0&&k.open());
        check(k.poll(true,1,false)==0&&k.open());k.poll(true,0,false);
        check(k.poll(true,2,false)==1);check(k.poll(true,2,false)==0);
        k.poll(true,0,false);check(k.poll(true,6,false)==0);
        k.poll(true,0,false);check(k.poll(true,256,true)==0);
        k.poll(true,0,false);check(k.poll(true,256,false)==8);
        check(k.poll(false,1,false)==0&&!k.open());check(k.poll(true,1,false)==0&&!k.open());
        k.poll(true,0,false);check(k.poll(true,3,false)==0&&k.open());
        k.close();k.poll(true,0,false);check(k.poll(true,2,false)==0&&!k.open());
        for(int i=0;i<10;i++){k.reset();k.poll(true,0,false);k.poll(true,1,false);k.poll(true,0,false);check(k.poll(true,2<<i,false)==i+1);}
        System.out.println("PASS: F12 single edges,1..8,held/focus/multiple-choice/busy rejection");
    }
}
