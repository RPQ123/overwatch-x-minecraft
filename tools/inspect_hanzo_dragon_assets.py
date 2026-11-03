"""SHA-guarded offline24919 dragon audit. No game, injection, JAR or deployment.

Extract with ow_asset_chain, inspect measured flat STU pointers, and optionally
validate private mesh packs inside ignored research/asset-cache only.
Claude installs with build_mesh_pack.py --batch tools/hanzo-dragon-pack-jobs.json.
"""
import argparse
import hashlib
import json
import struct
from pathlib import Path

from ow_asset_chain import Archive, CACHE, collect
from build_mesh_pack import build, select_mesh
from audit_ow_asset_chain import verify_pack

ROOT = Path(__file__).resolve().parents[1]
JOBS = ROOT/'tools/hanzo-dragon-pack-jobs.json'


class FlatGraph:
    """Only the measured DUTS3 arrays, node references and literal configs.

    Field offsets are the original reflected 24919 schemas recorded in
    research/hanzo-skills-20261021/graphs.json, not the newer OWLib layouts.
    Never evaluate an unknown opcode or attach meanings to unlabelled values.
    """
    def __init__(self, raw):
        self.raw = raw
        if raw[:8] != b'DUTS\x03\0\0\0' or self.kind(16) != 0x0df7e24f:
            raise ValueError('Not the measured24919 graph')
        stop = self.q(8)
        self.objects = set()
        at = 16
        while at < stop:
            self.objects.add(at)
            following = self.unpack('<I',at+4)
            if following == 0xffffffff:  # measured end-of-instance-chain marker
                break
            if not at < following <= stop:
                raise ValueError('Flat instance chain bounds')
            at = following
        self.nodes = [self.q(p) for p in self.array(16+0x50,8)]

    def unpack(self, fmt, at):
        if not 0 <= at <= len(self.raw)-struct.calcsize(fmt):
            raise ValueError('Flat read bounds')
        return struct.unpack_from(fmt,self.raw,at)[0]

    def q(self, at): return self.unpack('<Q',at)
    def kind(self, at): return self.unpack('<I',at)

    def array(self, at, stride):
        storage = self.q(at)
        if not storage: return []
        count,items = self.q(storage),self.q(storage+8)
        if count > 4096 or items+count*stride > len(self.raw):
            raise ValueError('Flat array bounds')
        return range(items,items+count*stride,stride)

    def typed(self, at, kind):
        if at not in self.objects or self.kind(at) != kind:
            raise ValueError('Flat instance type mismatch')
        return at

    def node(self, index, kind): return self.typed(self.nodes[index],kind)

    def dynamic(self, at):
        self.typed(at,0xf8cc195d)
        rows = list(self.array(at+16,16))
        if any(self.q(p) != 0xffffffffffffffff for p in rows):
            raise ValueError('Flat dynamic reference sentinel')
        return [f'{self.q(p+8):016x}' for p in rows]

    def literal(self, at):
        kind = self.kind(at)
        if kind == 0x3ae7427e:
            self.typed(at,kind);return self.unpack('<i',at+16)
        if kind == 0x7b13a0d4:
            self.typed(at,kind);return self.unpack('<f',at+16)
        self.typed(at,0xec502a81)
        code = bytes(self.raw[p] for p in self.array(at+32,1))
        values = [self.unpack('<f',p) for p in self.array(at+64,4)]
        if len(code)!=3 or code[0]!=70 or code[2]!=0 or code[1]>=len(values):
            raise ValueError('Not a measured single-float literal')
        return values[code[1]]


def definitions(archive):
    blobs = {}
    for suffix in ('00b9','0132'):
        guid = '058000000000'+suffix
        row = archive.resolve(guid)
        raw = archive.fetch(row['ckey'],guid+'.raw')
        if len(raw)!=row['bytes'] or hashlib.md5(raw).hexdigest()!=row['ckey']:
            raise ValueError('Graph content-key mismatch')
        blobs[suffix] = raw
    bow,dragon = (FlatGraph(blobs[s]) for s in ('00b9','0132'))
    if (len(bow.nodes),len(dragon.nodes))!=(117,52):
        raise ValueError('Original graph node counts changed')
    volley = bow.node(76,0x860ee5fc)
    arrow = {key:bow.literal(bow.q(volley+offset)) for key,offset in
             (('speedMps',320),('rangeM',304),('lifetimeSeconds',296))}
    radius_set = dragon.node(25,0x4698e4b6)
    radius_variable = dragon.dynamic(dragon.q(radius_set+144))
    radius = dragon.literal(dragon.q(radius_set+160))
    # Native m_radius CRC32=71ef3ca4, reflected offset0x140=320.
    radius_nodes = (1,7,10,20,36,38,44)
    for index in radius_nodes:
        track = dragon.node(index,0x498b421a)
        if dragon.dynamic(dragon.q(track+320)) != radius_variable:
            raise ValueError('TrackTargets radius binding differs')
    if (arrow,radius_variable,radius)!=({'speedMps':20.0,'rangeM':10,'lifetimeSeconds':5},['0d800000000001a6'],4):
        raise ValueError('Original dragon calibration changed')
    candidates = []
    for index in (3,4,29):
        node = dragon.node(index,0x4698e4b6)
        candidates.append(dict(node=index,variable=dragon.dynamic(dragon.q(node+144)),
                               value=dragon.literal(dragon.q(node+160)),semanticUseAuthenticated=False))
    return dict(graphSha256={s:hashlib.sha256(b).hexdigest() for s,b in blobs.items()},
                arrow=arrow,targetRadiusM=radius,radiusVariable=radius_variable,radiusNodes=radius_nodes,
                unclassifiedAssignments=candidates,
                unknown=['dragonSpeed','range/lifetime','damagePeriod/dps','wallOcclusion','coilRadius/frequency'],
                fixtureOnly=False,inGameVerified=False)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--validate-packs',action='store_true')
    args = parser.parse_args()
    archive = Archive('hanzo-dragon-audit')
    archive.load_package('02e0000000000005')
    jobs = json.loads(JOBS.read_text(encoding='utf-8'))
    chains = {}
    for entity in dict.fromkeys(j['entity'] for j in jobs):
        archive.out = CACHE/entity
        archive.out.mkdir(exist_ok=True)
        chains[entity] = collect(entity,archive=archive)
    archive.out = CACHE/'hanzo-dragon-audit'
    evidence = dict(definitions=definitions(archive),packs=[])
    for job in jobs:
        source = CACHE/job['entity']
        path,_ = select_mesh(source,chains[job['entity']],job['model'],job.get('material'))
        mesh = json.loads(path.read_text(encoding='utf-8'))
        entry = dict(job=job,vertices=len(mesh['positions']),triangles=len(mesh['indices'])//3,
                     sourceBounds=mesh['sourceBounds'],originTranslation=mesh['originTranslation'],
                     materialBindingComplete=mesh['materialBindingComplete'],
                     bindings=[s.get('binding') for s in mesh['submeshes']])
        if args.validate_packs:
            result = build(**job,out_root=CACHE/'hanzo-dragon-pack-validation')
            entry['verification'] = verify_pack(job,result)
        evidence['packs'].append(entry)
    (archive.out/'evidence.json').write_text(json.dumps(evidence,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(dict(packs=len(jobs),arrow=evidence['definitions']['arrow'],
                         targetRadiusM=evidence['definitions']['targetRadiusM'],
                         packsValidated=args.validate_packs,inGameVerified=False)))


if __name__=='__main__': main()
