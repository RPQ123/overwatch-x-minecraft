package lab.owmcguest;

import java.nio.file.*;

/** Native local cast plus verified real counter ACK, never keyboard-only damage. */
final class WinstonNativeAction {
    private final int kind;private final String prefix;
    private PlacementActionProtocol.Request pending;private long began,lastWrite,lastToken,confirmedSequence,confirmedToken;private boolean cooling;
    private Path mailbox;String error="";
    WinstonNativeAction(int kind){if(kind!=5&&kind!=6)throw new IllegalArgumentException("Winston native role");this.kind=kind;prefix=kind==5?"jump":"barrier";}
    long tick(NativeSkillReader reader,HostPoseReader.Pose host,long world,long castToken){
        long now=System.currentTimeMillis();
        try{
            double remaining=reader.placementRemaining(kind);WinstonDiagnostics.value(prefix+"NativeRemaining",remaining);
            if(remaining<=0)cooling=false;
            if(pending==null&&castToken>lastToken){
                lastToken=castToken;
                // Jump now receives one genuine cast-window edge, not both
                // Anim Begin/End. A fresh native cast may already have restarted
                // its CD between polls; observing zero is not a prerequisite.
                if(kind==5||!cooling){pending=reader.placementRequest(kind,PlacementCooldowns.nextSequence(),world,castToken);began=now;lastWrite=0;error="";WinstonDiagnostics.value(prefix+"RequestToken",castToken);WinstonDiagnostics.increment(prefix+"Requests");}
                else WinstonDiagnostics.increment(prefix+"CoolingEdgesIgnored");
            }
            if(pending==null)return 0;
            if(now-began>800){pending=null;error="Winston native receipt timeout";WinstonDiagnostics.value(prefix+"ActionError",error);WinstonDiagnostics.increment(prefix+"Timeouts");return 0;}
            String dir=System.getProperty("owmc.nativeEventsDirectory","");if(dir.isBlank())throw new IllegalStateException("native directory missing");
            mailbox=Path.of(dir).resolve("native-placement-"+kind+"-request-"+host.pid()+".bin");
            if(now-lastWrite>=40){
                var refreshed=reader.placementRequest(kind,pending.sequence(),world,pending.token());var temp=mailbox.resolveSibling(mailbox.getFileName()+".tmp");
                Files.write(temp,PlacementActionProtocol.encode(refreshed));Files.move(temp,mailbox,StandardCopyOption.REPLACE_EXISTING,StandardCopyOption.ATOMIC_MOVE);lastWrite=now;
            }
            var file=mailbox.resolveSibling("native-placement-"+kind+"-ack-"+host.pid()+".bin");
            if(!Files.isRegularFile(file)||Files.size(file)!=80)return 0;
            PlacementActionProtocol.Receipt receipt;try{receipt=PlacementActionProtocol.decode(Files.readAllBytes(file),pending,System.currentTimeMillis());}catch(IllegalArgumentException stale){return 0;}
            long sequence=pending.sequence(),nativeToken=pending.token();pending=null;WinstonDiagnostics.value(prefix+"AckPhase",receipt.phase());WinstonDiagnostics.value(prefix+"AckSequence",sequence);
            if(receipt.phase()!=1){error="original Winston action/readback refused";WinstonDiagnostics.value(prefix+"ActionError",error);return 0;}
            cooling=true;confirmedSequence=sequence;confirmedToken=nativeToken;error="";WinstonDiagnostics.value(prefix+"ActionError","");WinstonDiagnostics.value(prefix+"AckLatencyMs",System.currentTimeMillis()-began);WinstonDiagnostics.increment(prefix+"Receipts");return sequence;
        }catch(Exception e){error=e.toString();WinstonDiagnostics.value(prefix+"ActionError",error);return 0;}
    }
    long confirmedSequence(){return confirmedSequence;}
    long confirmedToken(){return confirmedToken;}
    boolean pending(){return pending!=null;}
    void reset(){pending=null;lastToken=lastWrite=confirmedSequence=confirmedToken=0;cooling=false;error="";
        // Revoke our own scoped mailbox. No native call on the client thread.
        if(mailbox!=null){try{Files.write(mailbox,new byte[112]);}catch(java.io.IOException e){error=e.toString();}mailbox=null;}
    }
}
