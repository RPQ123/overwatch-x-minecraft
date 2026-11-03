"""Measured 24919 flat 0ee9 skeleton; no inferred/native animation tracks."""
import hashlib
import math
import struct


def extract(mesh, model_raw):
    skin = mesh.get('skin')
    if not skin:
        return None
    if mesh.get('sourceVertexLayout') or len(model_raw)<392:
        raise ValueError('Unsupported dragon skin layout')
    parents_at = struct.unpack_from('<Q',model_raw,80)[0]
    pose_at = struct.unpack_from('<Q',model_raw,104)[0]
    remap_at = struct.unpack_from('<Q',model_raw,152)[0]
    count, simple, cloth, remap_count, id_count = struct.unpack_from('<5H',model_raw,172)
    if (count,simple,cloth,remap_count,id_count)!=(67,67,0,64,67):
        raise ValueError('Dragon measured skeleton counts changed')
    for at,size in [(parents_at,count*6),(pose_at,count*48),(remap_at,remap_count*2)]:
        if at<392 or at+size>len(model_raw):
            raise ValueError('Dragon skeleton table bounds')
    parents = [struct.unpack_from('<h',model_raw,parents_at+i*6+4)[0] for i in range(count)]
    if any(p < -1 or p>=i for i,p in enumerate(parents)):
        raise ValueError('Dragon skeleton hierarchy cycle/order')
    poses = [list(struct.unpack_from('<12f',model_raw,pose_at+i*48)) for i in range(count)]
    if any(not math.isfinite(x) for p in poses for x in p):
        raise ValueError('Dragon nonfinite bind pose')
    if any(abs(sum(x*x for x in p[:4])-1)>.002 for p in poses):
        raise ValueError('Dragon invalid bind quaternion')
    remap = list(struct.unpack_from('<'+'H'*remap_count,model_raw,remap_at))
    if max(remap)>=count or len(set(remap))!=remap_count:
        raise ValueError('Dragon palette remap')
    if any(s['boneIdOffset']!=0 for s in mesh['submeshes']):
        raise ValueError('Unsupported per-submesh skin palette')
    bones, weights = skin['boneIndices'], skin['weightsUnorm8']
    if len(bones)!=len(mesh['positions']) or len(weights)!=len(bones):
        raise ValueError('Dragon skin vertex count')
    if any(len(b)!=4 or len(w)!=4 or sum(w)!=255 or min(w)<0 or max(w)>255
           or min(b)<0 or max(b)>=remap_count for b,w in zip(bones,weights)):
        raise ValueError('Dragon skin palette/weights')
    shift = mesh['originTranslation']
    return dict(mode='native-bind-pose-with-MC-swim', skeletonSha256=hashlib.sha256(model_raw).hexdigest(),
                parents=parents, palette=remap, bindPose=poses,
                bindPositions=[[p[8+j]+shift[j] for j in range(3)] for p in poses],
                boneIndices=bones, weightsUnorm8=weights, nativeAnimationEvaluated=False,
                limits='Native skeleton and weights; procedural bone rotations/translations are MC approximation, not native swim clip')
