package lab.owmcguest;

import com.sun.jna.Native;
import com.sun.jna.Pointer;
import com.sun.jna.WString;
import com.sun.jna.win32.StdCallLibrary;
import java.lang.invoke.VarHandle;
import java.util.concurrent.atomic.AtomicReference;
import net.minecraft.client.MinecraftClient;
import java.nio.ByteBuffer;
import java.nio.ByteOrder;

/** Windows three-slot transport inspired by universal-modder's GTA/MC example.
 * Protocol is OWMCFR01, not the GTA example's wire identity. CPU publication only. */
final class WorldFrameMapping implements AutoCloseable {
    static final String NAME="Local\\OWMCPassthroughFrame";
    static final int MAX_W=2560,MAX_H=1440,HEADER=4096,DESC=256;
    static final long STRIDE=(long)MAX_W*MAX_H*8,TOTAL=HEADER+STRIDE*3;
    interface Kernel extends StdCallLibrary {
        Pointer CreateFileMappingW(Pointer file,Pointer security,int protection,int high,int low,WString name);
        Pointer MapViewOfFile(Pointer mapping,int access,int high,int low,long size);
        boolean UnmapViewOfFile(Pointer address);
        boolean CloseHandle(Pointer handle);
        int GetLastError();
    }
    record Capture(long frame,long captureNs,long hostFrame,long hostGeneration,int width,int height,float near,float far,float fov,
                   double x,double y,double z,float yaw,float pitch,float roll,float[] projection,byte[] bytes,NativeBossRuntime.State boss) {
        Capture(long frame,long captureNs,long hostFrame,long hostGeneration,int width,int height,float near,float far,float fov,
                double x,double y,double z,float yaw,float pitch,float roll,float[] projection,byte[] bytes){
            this(frame,captureNs,hostFrame,hostGeneration,width,height,near,far,fov,x,y,z,yaw,pitch,roll,projection,bytes,null);
        }
    }
    private final Kernel kernel=Native.load("kernel32",Kernel.class);
    private final Pointer handle,memory;
    private final AtomicReference<Capture> latest=new AtomicReference<>();
    private final FrameBufferPool buffers=new FrameBufferPool(4);
    final FrameTimings publishTime=new FrameTimings();
    private volatile boolean running=true;
    private final Thread writer;
    volatile long published,dropped;
    volatile String failure="";
    private int slot;
    WorldFrameMapping() {this(NAME);}
    WorldFrameMapping(String mappingName) {
        if(!mappingName.equals(NAME)&&!mappingName.equals(NAME+"Test")) throw new IllegalArgumentException("Mapping name");
        // The int overload zero-extends to 0x00000000ffffffff on Win64;
        // INVALID_HANDLE_VALUE must be the full 64-bit all-ones pointer.
        handle=kernel.CreateFileMappingW(Pointer.createConstant(-1L),null,4,0,(int)TOTAL,new WString(mappingName));
        if(handle==null) throw new IllegalStateException("CreateFileMapping: "+kernel.GetLastError());
        memory=kernel.MapViewOfFile(handle,0xF001F,0,0,TOTAL);
        if(memory==null) {kernel.CloseHandle(handle);throw new IllegalStateException("MapViewOfFile: "+kernel.GetLastError());}
        String existing=new String(memory.getByteArray(0,8),java.nio.charset.StandardCharsets.US_ASCII);
        if(existing.equals("OWMCFR01")) {
            long previousPid=Integer.toUnsignedLong(memory.getInt(52));
            if(ProcessHandle.of(previousPid).filter(ProcessHandle::isAlive).isPresent()) {
                kernel.UnmapViewOfFile(memory);kernel.CloseHandle(handle);throw new IllegalStateException("A live MC passthrough producer already owns the mapping");
            }
        } else if(memory.getLong(0)!=0) {kernel.UnmapViewOfFile(memory);kernel.CloseHandle(handle);throw new IllegalStateException("Unexpected mapping identity");}
        memory.clear(HEADER);
        memory.write(0,"OWMCFR01".getBytes(java.nio.charset.StandardCharsets.US_ASCII),0,8);
        memory.setInt(8,2);memory.setInt(12,HEADER);memory.setInt(16,3);memory.setInt(20,MAX_W);memory.setInt(24,MAX_H);
        memory.setLong(32,STRIDE);memory.setInt(48,-1);memory.setInt(52,(int)ProcessHandle.current().pid());
        memory.setLong(56,(new java.security.SecureRandom().nextLong()&Long.MAX_VALUE)|1);
        writer=new Thread(this::publishLoop,"owmc-frame-publisher");writer.setDaemon(true);writer.start();
    }
    byte[] acquireBytes(int size){return buffers.acquire(size);}
    void releaseBytes(byte[] bytes){buffers.release(bytes);}
    long bufferAllocations(){return buffers.allocations();}
    void submit(Capture frame) {
        int pixels=frame.width()*frame.height();
        if(frame.width()<1||frame.width()>MAX_W||frame.height()<1||frame.height()>MAX_H||frame.bytes()==null||
           (frame.bytes().length!=pixels*4&&frame.bytes().length!=pixels*8))throw new IllegalArgumentException("Frame payload format/dimensions");
        var replaced=latest.getAndSet(frame);if(replaced!=null){dropped++;buffers.release(replaced.bytes());}
        java.util.concurrent.locks.LockSupport.unpark(writer);
    }
    long generation(){return memory.getLong(56);}
    private long bodySequence;
    private final BodyMotionSample bodyMotion=new BodyMotionSample();
    /** Client tick result, independent of delayed GPU frame publication. */
    void publishBody(MinecraftClient client) {
        var p=client.player;var host=HostPoseReader.INSTANCE.latest();
        if(p==null||host==null||host.flags()!=1||!p.isAlive())return;
        var b=ByteBuffer.allocate(256).order(ByteOrder.LITTLE_ENDIAN);
        b.put("OWBODY01".getBytes(java.nio.charset.StandardCharsets.US_ASCII));
        b.putInt(1).putInt(256).putInt(host.pid()).putInt((int)ProcessHandle.current().pid());
        b.putLong(memory.getLong(56)).putLong(host.generation());
        bodySequence+=2;b.putLong(64,bodySequence);b.putLong(72,System.currentTimeMillis());b.putInt(80,p.isOnGround()?1:0);
        b.putDouble(96,p.getX());b.putDouble(104,p.getY());b.putDouble(112,p.getZ());
        var server=client.getServer();
        long world=server!=null&&client.world!=null?NativeWorldIdentity.of(server,client.world.getRegistryKey()):0;
        // Vanilla post-travel velocity has already been friction-damped and
        // does not describe our native-speed move(). Use actual completed MC
        // displacement so the original hands/body do not animate a slow glide.
        var v=bodyMotion.observe(p,world,NativeLocomotionController.INSTANCE.hero(),NativeLocomotionController.INSTANCE.modelId(),
            host.generation(),p.age,new double[]{p.getX(),p.getY(),p.getZ()},p.isOnGround());
        b.putFloat(120,(float)v[0]);b.putFloat(124,(float)v[1]);b.putFloat(128,(float)v[2]);
        long climbModel=WallClimbController.INSTANCE.nativeClimbModel(client);
        boolean climbing=climbModel!=0&&!p.isOnGround();
        b.putInt(144,0x324d4c43);b.putInt(148,climbing?1:0);b.putInt(152,climbing?(int)climbModel:0);
        // Ordinary heroes no longer consume the original motor accumulator.
        boolean nativeFlight=NativeFlightController.INSTANCE.requested(client)||NativeBlinkController.INSTANCE.requested(client);
        b.putInt(160,0x31594c46);b.putInt(164,nativeFlight?1:0);b.putInt(168,nativeFlight?(int)NativeLocomotionController.INSTANCE.modelId():0);b.putInt(172,nativeFlight?NativeFlightController.INSTANCE.blockedAxes():0);
        // Persisted save location and dimension identify a same-world guest
        // restart independently of the random process generation.
        if(server!=null&&client.world!=null) {
            b.putLong(136,world);
        }
        var deadeye=NativeDeadeyeController.INSTANCE.inputLock();
        if(deadeye!=null&&!deadeye.matches(host.generation(),NativeLocomotionController.INSTANCE.modelId(),world,System.currentTimeMillis()))deadeye=null;
        NativeDeadeyeInputLock.write(b,deadeye,host.deadeyeInputGuard()&&host.inputActive());
        HanzoControlProof.write(b,HanzoControlController.current(client,host));
        memory.setLong(1536+64,bodySequence-1);VarHandle.fullFence();
        memory.write(1536,b.array(),0,64);memory.write(1536+72,b.array(),72,256-72);
        VarHandle.fullFence();memory.setLong(1536+64,bodySequence);
    }
    private void publishLoop() {
        try {
            while(running) {
                Capture f=latest.getAndSet(null);
                // A permit survives submit-before-park, avoiding lost wakeups.
                // Polling at 5 ms dropped fresh frames at 165 FPS.
                if(f==null) {java.util.concurrent.locks.LockSupport.park();continue;}
                long begin=System.nanoTime();try {
                long d=256L+slot*DESC,sequence=(published+1)*2;
                memory.setLong(d,sequence-1);VarHandle.fullFence();
                memory.setLong(d+8,f.frame);memory.setLong(d+16,f.hostFrame);
                memory.setInt(d+24,f.width);memory.setInt(d+28,f.height);
                memory.setFloat(d+32,f.near);memory.setFloat(d+36,f.far);memory.setFloat(d+40,f.fov);memory.setInt(d+44,f.bytes.length/(f.width*f.height*4));
                memory.setDouble(d+48,f.x);memory.setDouble(d+56,f.y);memory.setDouble(d+64,f.z);
                memory.setFloat(d+72,f.yaw);memory.setFloat(d+76,f.pitch);memory.setFloat(d+80,f.roll);memory.setInt(d+84,1);
                memory.setLong(d+88,f.captureNs);memory.setLong(d+96,System.nanoTime());memory.setLong(d+104,System.currentTimeMillis());
                memory.setLong(d+176,f.hostGeneration);
                memory.setInt(d+184,0x31485342);memory.setFloat(d+188,f.boss==null?0:f.boss.health());
                memory.setFloat(d+192,f.boss==null?0:f.boss.maximum());memory.setInt(d+196,f.boss==null?0:1);
                memory.write(d+112,f.projection,0,16);memory.write(HEADER+slot*STRIDE,f.bytes,0,f.bytes.length);
                // Optional vanilla HUD lives in the unused color-only depth half.
                var hud=VanillaBossOverlay.latest;
                boolean overlay=f.bytes.length==f.width*f.height*4&&hud!=null;
                memory.setInt(d+200,overlay?0x31445548:0);memory.setInt(d+204,overlay?hud.width():0);memory.setInt(d+208,overlay?hud.height():0);
                if(overlay)memory.write(HEADER+slot*STRIDE+(long)MAX_W*MAX_H*4,hud.rgba(),0,hud.rgba().length);
                VarHandle.fullFence();memory.setLong(d,sequence);VarHandle.fullFence();memory.setInt(48,slot);
                memory.setLong(40,++published);slot=(slot+1)%3;
                }finally{buffers.release(f.bytes());publishTime.add(System.nanoTime()-begin);}
            }
        } catch(Exception error) {failure=error.toString();running=false;System.err.println("[OWMCFrames] Publication disabled: "+error);}
    }
    @Override public void close() {
        running=false;writer.interrupt();
        try {writer.join(1000);}catch(InterruptedException error) {Thread.currentThread().interrupt();}
        if(!writer.isAlive()) {var pending=latest.getAndSet(null);if(pending!=null)buffers.release(pending.bytes());kernel.UnmapViewOfFile(memory);kernel.CloseHandle(handle);}
    }
}
