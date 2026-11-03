package lab.owmcguest;
public final class NativeUtilityKeysCheck {
    static void check(boolean value){if(!value)throw new AssertionError();}
    public static void main(String[] args){
        var key=new NativeUtilityKeys();check(key.poll(true,1)==0);check(key.poll(true,1)==0);check(key.poll(true,0)==0);
        check(key.poll(true,1)==1);check(key.poll(true,1)==0);check(key.poll(true,3)==2);check(key.poll(true,7)==4);
        check(key.poll(false,7)==0);check(key.poll(true,7)==0);check(key.poll(true,0)==0);check(key.poll(true,4)==4);
        key.reset();check(key.poll(true,4)==0);check(key.poll(true,0)==0);check(key.poll(true,7)==7);
        System.out.println("PASS: utility key single edges, holds, focus/session release-to-arm");
    }
}
