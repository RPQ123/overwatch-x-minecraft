"""Extract the twelve original owned beta bodies into private MC mesh packs.

Only the gameplay entity's direct body model/Look are followed. Child weapons,
particles and first-person models are deliberately excluded from this NPC body.
All output defaults to the D: task lab, never the user's C: private cache.
"""
import argparse
import json
import hashlib
import struct
from pathlib import Path
import ow_asset_chain as chain
import build_mesh_pack as mesh_pack
from ow_model_submeshes import parse_model_submeshes

TRACER_SHA='6d783f0e384bd1a7ebc88f35e8ce7f597f599c21d9f4d165056058d3f689e6a3'

ROSTER=(('genji',0x29,'0225'),('mccree',0x42,'02a3'),('pharah',8,'0032'),('reaper',2,'0022'),
        ('soldier76',0x6e,'03cf'),('tracer',3,'0001'),('bastion',0x15,'01fd'),('hanzo',5,'0141'),
        ('junkrat',0x65,'0380'),('mei',0xdd,'08ba'),('torbjorn',6,'01a3'),('widowmaker',10,'001c'),('roadhog',0x40,'028f'),('winston',9,'01c0'))


def parse_body(raw):
    # Tracer's first LOD0 descriptor declares 12820 vertices although its
    # actual bounded index stream uses 12852 unique entries. Do not change the
    # archive or loosen the generic parser. Recompute that declaration in a
    # SHA-pinned, in-memory decoding view and retain both counts in provenance.
    digest=hashlib.sha256(raw).hexdigest()
    adjusted=False
    if len(raw)>392:
        sm=struct.unpack_from('<Q',raw,360)[0]
        if digest==TRACER_SHA:
            if struct.unpack_from('<H',raw,sm+60)[0]!=12820:raise ValueError('Tracer body declaration changed')
            view=bytearray(raw);struct.pack_into('<H',view,sm+60,12852);adjusted=True
        else:view=raw
    else:view=raw
    result=parse_model_submeshes(bytes(view),selected_lods_only=True)
    if adjusted:
        for row in result['sourceSubmeshes']+result['submeshes']:
            if row['descriptorOffset']==sm:row['originalDeclaredVertexCount']=12820;row['computedUniqueVertexCount']=12852
    return result


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out-root',type=Path,default=chain.ROOT/'research/survival/G-assets')
    parser.add_argument('--only',choices=[r[0] for r in ROSTER])
    args=parser.parse_args()
    output=args.out_root.resolve()
    if output.drive.upper()!='D:':raise ValueError('This task writes assets only to D:')
    cache=chain.ROOT/'research/survival/G-asset-cache';cache.mkdir(parents=True,exist_ok=True)
    chain.CACHE=cache;mesh_pack.CACHE=cache
    # Genji's unused LOD2 has a contradictory declared unique count. Read and
    # validate only the LOD0 geometry that is actually exported; production's
    # default all-LOD validation stays strict for every existing asset path.
    chain.parse_asset_model=parse_body
    scan=chain.scan_refs
    manifest=output.parent/'G-npc-assets.json'
    rows=json.loads(manifest.read_text(encoding='utf-8')) if args.only and manifest.exists() else []
    archive=None
    for name,hero,suffix in ROSTER:
        if args.only and args.only!=name:continue
        entity='040000000000'+suffix
        try:
            if archive is None:archive=chain.Archive(entity)
            archive.out=cache/entity;archive.out.mkdir(parents=True,exist_ok=True)
            archive.load_package(f'02e000000000{hero:04x}');archive.load_package(entity)
            def body_refs(raw,guid,records,**kwargs):
                refs=scan(raw,guid,records,**kwargs)
                if guid==entity:return [r for r in refs if r['guid'].startswith(('0d00','0980'))]
                return refs
            chain.scan_refs=body_refs
            report=chain.collect(entity,archive=archive)
            direct={r['guid'] for r in report['resources'][entity]['refs'] if r['guid'].startswith('0d00')}
            exports=[r for r in report['meshExports'] if r['model'] in direct and r.get('material') is None]
            if len(exports)!=1:raise ValueError('Exactly one direct original hero body required: '+str(exports))
            result=mesh_pack.build('hero-npc-'+name,entity,out_root=output,model=exports[0]['model'])
            result.update(hero=name,entity=entity,model=exports[0]['model'],geometry='original-stored-bind-pose',animation='MC head/body yaw only; no native skeleton animation')
            rows=[r for r in rows if r['hero']!=name];rows.append(dict(ok=True,**result));print(name,'OK',result['vertices'],flush=True)
        except Exception as error:
            rows=[r for r in rows if r['hero']!=name];rows.append(dict(ok=False,hero=name,error=str(error)));print(name,'FAILED',str(error)[:180],flush=True)
        finally:chain.scan_refs=scan
        manifest.write_text(json.dumps(rows,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    return 0 if rows and all(r['ok'] for r in rows) else 1


if __name__=='__main__':raise SystemExit(main())
