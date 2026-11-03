package lab.owmcguest;

import java.util.ArrayDeque;
import java.util.IdentityHashMap;

/** A bounded ownership transfer: render -> pending slot -> publisher -> free.
 * Never recycle a buffer while the publisher can still read its pixels. */
final class FrameBufferPool {
    private final int limit;
    private final ArrayDeque<byte[]> free=new ArrayDeque<>();
    private final IdentityHashMap<byte[],Boolean> leased=new IdentityHashMap<>();
    private long allocations;
    FrameBufferPool(int limit){if(limit<1)throw new IllegalArgumentException();this.limit=limit;}
    synchronized byte[] acquire(int bytes){
        if(bytes<1||bytes>WorldFrameMapping.MAX_W*WorldFrameMapping.MAX_H*8)throw new IllegalArgumentException("pixel size");
        for(var it=free.iterator();it.hasNext();){var buffer=it.next();if(buffer.length==bytes){it.remove();leased.put(buffer,true);return buffer;}}
        if(leased.size()>=limit)return null;
        // A resize can discard free old-size buffers, never an in-flight buffer.
        free.clear();byte[] buffer=new byte[bytes];allocations++;leased.put(buffer,true);return buffer;
    }
    synchronized void release(byte[] buffer){
        if(leased.remove(buffer)==null)throw new IllegalStateException("pixel buffer released twice or not owned");
        if(free.size()+leased.size()<limit)free.addLast(buffer);
    }
    synchronized long allocations(){return allocations;}
}
