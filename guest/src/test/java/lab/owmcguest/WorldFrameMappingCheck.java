package lab.owmcguest;

import com.sun.jna.Native;
import com.sun.jna.Pointer;
import com.sun.jna.WString;
import com.sun.jna.win32.StdCallLibrary;

/** Standalone Win64 transport regression; no Minecraft or OW client runs here. */
public final class WorldFrameMappingCheck {
    interface Reader extends StdCallLibrary {
        Pointer OpenFileMappingW(int access,boolean inherit,WString name);
        Pointer MapViewOfFile(Pointer handle,int access,int high,int low,long size);
        boolean UnmapViewOfFile(Pointer pointer);
        boolean CloseHandle(Pointer handle);
    }
    public static void main(String[] args) throws Exception {
        var pool=new FrameBufferPool(4);byte[][] held=new byte[4][];
        for(int i=0;i<4;i++){held[i]=pool.acquire(32);held[i][0]=(byte)(i+1);}
        if(pool.acquire(32)!=null)throw new AssertionError("unbounded frame allocation");
        pool.release(held[2]);var reused=pool.acquire(32);
        if(reused!=held[2]||pool.allocations()!=4)throw new AssertionError("frame was not recycled");
        reused[0]=99;for(int i:new int[]{0,1,3})if(held[i][0]!=(byte)(i+1))throw new AssertionError("in-flight pixels overwritten");
        pool.release(reused);boolean duplicateReturn=false;try{pool.release(reused);}catch(IllegalStateException expected){duplicateReturn=true;}
        if(!duplicateReturn)throw new AssertionError("duplicate return accepted");
        var resized=pool.acquire(64);if(resized==null||resized.length!=64||pool.acquire(64)!=null)throw new AssertionError("resize ignored in-flight ownership");
        pool.release(resized);for(int i:new int[]{0,1,3})pool.release(held[i]);
        try(var mapping=new WorldFrameMapping(WorldFrameMapping.NAME+"Test")) {
            float[] projection=new float[16];for(int i=0;i<4;i++) projection[i*5]=1;
            mapping.submit(new WorldFrameMapping.Capture(1,System.nanoTime(),17,23,2,2,.05f,256,70,.5,-58.4,.5,0,0,0,projection,mapping.acquireBytes(32),new NativeBossRuntime.State(1,125,200)));
            long limit=System.nanoTime()+1_000_000_000;
            while(mapping.published==0&&System.nanoTime()<limit) Thread.sleep(5);
            if(mapping.published!=1) throw new AssertionError("Windows mapping did not publish: "+mapping.failure);
            Reader reader=Native.load("kernel32",Reader.class);Pointer handle=reader.OpenFileMappingW(4,false,new WString(WorldFrameMapping.NAME+"Test"));
            if(handle==null) throw new AssertionError("Mapping reader unavailable");Pointer memory=reader.MapViewOfFile(handle,4,0,0,WorldFrameMapping.TOTAL);
            if(memory==null) throw new AssertionError("Mapping view unavailable");
            try {
                if(!new String(memory.getByteArray(0,8),java.nio.charset.StandardCharsets.US_ASCII).equals("OWMCFR01")) throw new AssertionError("Magic");
                if(memory.getLong(256)!=2||memory.getInt(48)!=0||memory.getInt(280)!=2||memory.getInt(284)!=2||memory.getLong(40)!=1) throw new AssertionError("Wire layout");
                if(memory.getLong(272)!=17||memory.getLong(432)!=23) throw new AssertionError("Paired host frame/generation");
                if(memory.getInt(300)!=2)throw new AssertionError("Real depth format flag");
                if(memory.getInt(440)!=0x31485342||memory.getFloat(444)!=125||memory.getFloat(448)!=200||memory.getInt(452)!=1)throw new AssertionError("Dragon health attached to captured frame");
                int hdBytes=1920*1080*4;var color=mapping.acquireBytes(hdBytes);color[0]=17;color[hdBytes-1]=79;
                mapping.submit(new WorldFrameMapping.Capture(2,System.nanoTime(),18,23,1920,1080,.05f,256,70,.5,-58.4,.5,0,0,0,projection,color));
                limit=System.nanoTime()+1_000_000_000;while(mapping.published<2&&System.nanoTime()<limit)Thread.sleep(5);
                if(mapping.published!=2||memory.getInt(556)!=1||memory.getInt(536)!=1920||memory.getInt(540)!=1080||memory.getByte(WorldFrameMapping.HEADER+WorldFrameMapping.STRIDE)!=17||memory.getByte(WorldFrameMapping.HEADER+WorldFrameMapping.STRIDE+hdBytes-1)!=79)throw new AssertionError("Full HD color-only wire publication");
                if(memory.getInt(708)!=0||memory.getFloat(704)!=0)throw new AssertionError("Absent boss clears previous health");
                int qhdBytes=2560*1440*4;var qhd=mapping.acquireBytes(qhdBytes);qhd[0]=31;qhd[qhdBytes-1]=91;
                mapping.submit(new WorldFrameMapping.Capture(3,System.nanoTime(),19,23,2560,1440,.05f,256,70,.5,-58.4,.5,0,0,0,projection,qhd));
                limit=System.nanoTime()+1_000_000_000;while(mapping.published<3&&System.nanoTime()<limit)Thread.sleep(5);
                long at=WorldFrameMapping.HEADER+2*WorldFrameMapping.STRIDE;
                if(memory.getInt(8)!=2||mapping.published!=3||memory.getInt(48)!=2||memory.getInt(792)!=2560||memory.getInt(796)!=1440||memory.getByte(at)!=31||memory.getByte(at+qhdBytes-1)!=91)throw new AssertionError("QHD pixels, stride or protocol");
                boolean refused=false;try(var duplicate=new WorldFrameMapping(WorldFrameMapping.NAME+"Test")) {}catch(IllegalStateException expected) {refused=true;}
                if(!refused) throw new AssertionError("A second live producer overwrote the mapping");
            } finally {reader.UnmapViewOfFile(memory);reader.CloseHandle(handle);}
        }
        System.out.println("Actual Win64 mapping creation, publication, wire layout, duplicate rejection and shutdown passed; synthetic pixels only.");
    }
}

