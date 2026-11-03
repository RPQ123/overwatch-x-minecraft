package lab.owmcguest;

public final class NativeRecallHistoryCheck {
    private static void require(boolean ok,String message){if(!ok)throw new AssertionError(message);}
    public static void main(String[] args){
        var h=new NativeRecallHistory();require(h.previous(1000)==null&&h.candidates(1000).isEmpty(),"No invented pre-spawn history");
        for(int i=0;i<=100;i++)h.add(new NativeRecallHistory.Point(1000+i*50,i,0,0,i<60?20:2));
        var old=h.previous(6000);require(old.wall()==3000&&old.x()==40&&old.health()==20,"Three seconds returns actual older position and health");
        require(h.size()<=85&&h.candidates(6000).get(0).equals(old),"Bounded fallback candidates start at the rewind point");
        h.add(new NativeRecallHistory.Point(6000,101,0,0,2));require(h.size()<=85,"Duplicate timestamp replaces, never expands history");
        h.add(new NativeRecallHistory.Point(2000,5,0,0,15));require(h.size()==1&&h.previous(2000).x()==5,"Clock reversal cannot use future history");
        h.add(new NativeRecallHistory.Point(2100,Double.NaN,0,0,20));require(h.size()==1,"Invalid coordinates cannot become teleport destinations");
        h.clear();require(h.previous(8000)==null,"World/model reset removes all old destinations");
        h.add(new NativeRecallHistory.Point(8100,1,2,3,2));
        require(h.size()==1&&h.candidates(8099).isEmpty(),"Samples newer than native Begin cannot impersonate pre-cast history");
        require(h.candidates(8100).size()==1,"The first real sample is available at its actual timestamp");
        h.clear();require(h.candidates(8200).isEmpty(),"Empty test history remains an empty candidate list");
        System.out.println("PASS: real three-second Recall history, injured health, fallback, clock reversal, future-only refusal and world reset");
    }
}
