package lab.owmcguest;

import java.util.UUID;

/** A confirmed new native pawn may initialize health once; reader gaps may not. */
public final class NativeSpawnHealthGate {
    private record Pawn(UUID player,long source,long hero,long model){}
    private Pawn initialized;
    public boolean claim(UUID player,long source,long hero,long model,boolean confirmed){
        if(!confirmed||player==null||source==0||hero==0||model==0)return false;
        var next=new Pawn(player,source,hero,model);
        if(next.equals(initialized))return false;initialized=next;return true;
    }
    public void reset(){initialized=null;}
}
