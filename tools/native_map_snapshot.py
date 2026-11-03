"""Bounded read-only snapshot of the supplied plugin's measured MSVC x64 map ABI.

Values remain addresses; callers supply the measured payload layout. A live tree
can mutate without changing its header, so snapshots are observations, not locks
or a lossless event queue. Failed reads must be retried as a whole snapshot.
"""
import struct

def lookup_map(memory,address,wanted,key_format='Q',max_count=4096):
    """Bounded exact-key tree observation, rechecking every visited node.

    Not a full-tree snapshot or a lock. Caller must validate the returned value
    and repeat its identity check before publishing a native binding.
    """
    if key_format not in ('Q','i'):raise ValueError('Unmeasured map key ABI')
    original=memory.read(address,16);head,count=struct.unpack('<QQ',original)
    if count>max_count or head<0x10000:raise ValueError('Map header bounds')
    sentinel=memory.read(head,32)
    if sentinel[25]!=1:raise ValueError('Map sentinel identity')
    node=struct.unpack_from('<Q',sentinel,8)[0];parent=head;low=high=None;seen={};result=None
    if (node==head)!=(count==0):raise ValueError('Map empty/root mismatch')
    while node!=head:
        if node<0x10000 or node in seen or len(seen)>=min(count,64):raise ValueError('Map lookup path bound/cycle')
        raw=memory.read(node,40);left,owner,right=struct.unpack_from('<QQQ',raw)
        if owner!=parent or raw[25]!=0:raise ValueError('Map parent or node identity changed')
        key=struct.unpack_from('<'+key_format,raw,32)[0]
        if (low is not None and key<=low) or (high is not None and key>=high):raise ValueError('Map ordering changed')
        seen[node]=raw
        if key==wanted:result=node+40;break
        parent=node
        if wanted<key:node=left;high=key
        else:node=right;low=key
    if memory.read(address,16)!=original or memory.read(head,32)!=sentinel:raise ValueError('Map header/root changed during lookup')
    for node,raw in seen.items():
        if memory.read(node,40)!=raw:raise ValueError('Map path changed during lookup')
    return result

def snapshot_map(memory,address,key_format,max_count=4096):
    if key_format not in ('Q','i'):raise ValueError('Unmeasured map key ABI')
    original=memory.read(address,16);head,count=struct.unpack('<QQ',original)
    if count>max_count or head<0x10000:raise ValueError('Map header bounds')
    sentinel=memory.read(head,32)
    if sentinel[25]!=1:raise ValueError('Map sentinel identity')
    root=struct.unpack_from('<Q',sentinel,8)[0]
    pending=[(root,head,None,None)] if root!=head else []
    seen=set();result=[]
    while pending:
        node,parent,low,high=pending.pop()
        if node==head:continue
        if node<0x10000 or node in seen or len(seen)>=count:raise ValueError('Map cycle or count mismatch')
        seen.add(node);raw=memory.read(node,40);left,owner,right=struct.unpack_from('<QQQ',raw)
        if owner!=parent or raw[25]!=0:raise ValueError('Map parent or node identity changed')
        key=struct.unpack_from('<'+key_format,raw,32)[0]
        if (low is not None and key<=low) or (high is not None and key>=high):raise ValueError('Map ordering changed')
        result.append((key,node+40))
        pending.extend(((left,node,low,key),(right,node,key,high)))
    if len(seen)!=count or memory.read(address,16)!=original:raise ValueError('Map count/header changed during snapshot')
    return result
