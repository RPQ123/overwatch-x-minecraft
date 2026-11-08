package lab.owmcguest;
import java.nio.file.*;
import net.minecraft.client.MinecraftClient;
/** One mailbox per role; no native callbacks on this client/render thread. */
final class NativePlacementActionClient implements AutoCloseable {
    private static final java.util.Map<Integer,String> errors=new java.util.concurrent.ConcurrentHashMap<>();
    private final int kind;private Path lastPath;private long lastWrite,lastAck,cancelSequence,cancelToken,beginSequence,beginToken;
    record GrappleReceipt(long token,int kind,int phase,float remaining){}
    private GrappleReceipt grappleReceipt;
    String error="";
    NativePlacementActionClient(int kind){this.kind=kind;}
    void beginGrapple(long token){if(kind==3&&token>0){beginToken=token;beginSequence=PlacementCooldowns.nextSequence();}}
    void cancelGrapple(long token){if(kind==3&&token>0){cancelToken=token;cancelSequence=PlacementCooldowns.nextSequence();}}
    GrappleReceipt takeGrappleReceipt(){var result=grappleReceipt;grappleReceipt=null;return result;}
    void tick(MinecraftClient c,HostPoseReader.Pose host,NativeSkillReader reader,PlacementCooldowns.Scope scope){
        try{
            long now=System.currentTimeMillis();if(kind!=3){double remaining=reader.placementRemaining(kind);c.getServer().execute(()->PlacementCooldowns.observe(scope,remaining,now));}
            var pending=PlacementCooldowns.requests.stream().filter(p->p.scope().equals(scope)).findFirst().orElse(null);
            boolean beginning=kind==3&&beginSequence!=0;
            long sequence=kind==3?(beginning?beginSequence:cancelSequence):pending==null?0:pending.sequence(),token=kind==3?(beginning?beginToken:cancelToken):pending==null?0:pending.token();
            if(sequence==0){clear();return;}
            var request=reader.placementRequest(beginning?4:kind,sequence,scope.world(),token);String dir=System.getProperty("owmc.nativeEventsDirectory","");if(dir.isBlank())throw new IllegalStateException("native action directory missing");
            var path=Path.of(dir).resolve("native-placement-"+kind+"-request-"+host.pid()+".bin");
            if(now-lastWrite>=40){var temp=path.resolveSibling(path.getFileName()+".tmp");Files.write(temp,PlacementActionProtocol.encode(request));Files.move(temp,path,StandardCopyOption.REPLACE_EXISTING,StandardCopyOption.ATOMIC_MOVE);lastPath=path;lastWrite=now;}
            var ack=path.resolveSibling("native-placement-"+kind+"-ack-"+host.pid()+".bin");if(!Files.isRegularFile(ack)||Files.size(ack)!=80)return;
            PlacementActionProtocol.Receipt receipt;try{receipt=PlacementActionProtocol.decode(Files.readAllBytes(ack),request,now);}catch(IllegalArgumentException old){return;}
            if(receipt.sequence()==lastAck)return;lastAck=receipt.sequence();
            if(kind==3){grappleReceipt=new GrappleReceipt(token,request.kind(),receipt.phase(),receipt.remaining());if(beginning)beginSequence=beginToken=0;else cancelSequence=cancelToken=0;}else c.getServer().execute(()->PlacementCooldowns.receipt(scope,receipt));
            error=receipt.phase()==1?"":"original native action/readback failed";errors.put(kind,error);
        }catch(Exception e){error=e.toString();errors.put(kind,error);}
    }
    private void clear()throws java.io.IOException{if(lastPath!=null){Files.write(lastPath,new byte[112]);lastPath=null;lastWrite=0;}}
    @Override public void close(){beginSequence=beginToken=cancelSequence=cancelToken=0;grappleReceipt=null;try{clear();}catch(Exception e){error=e.toString();}}
    static String diagnostics(){return new com.google.gson.Gson().toJson(errors);}
}
