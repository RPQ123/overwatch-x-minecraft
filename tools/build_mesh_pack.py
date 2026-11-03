"""把已验证 LOD0 缓存打成私有网格包；--out-root 可先写 research/asset-cache。

多模型/效果材质必须显式选择，禁止按文件名取第一个或读取上次遗留网格。
用法：python tools/build_mesh_pack.py <名称> <实体GUID> [--model GUID --material GUID]
批量：python tools/build_mesh_pack.py --batch <jobs.json> [--out-root <目录>]
批量逐项记录并继续，最后输出 summary；任一失败退出1。pose 是来源元数据，
materials 沿用 models 的已验证静态材质配方，不得丢弃为普通灰色包。
"""
from modpack.config import paths
import argparse
import hashlib
import json
import math
from pathlib import Path
import re
import shutil
import tempfile

from ow_material_params import prepare as prepare_material
from ow_dragon_skin import extract as extract_dragon_skin

ROOT = Path(__file__).resolve().parents[1]
CACHE = ROOT/'research/asset-cache'
OUT = paths().get('meshAssets')


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def select_mesh(src, chain, model=None, material=None):
    exports = chain.get('meshExports')
    if exports is None:
        exports = [dict(model=g,material=None,file=r['model']['file'])
                   for g,r in chain['resources'].items()
                   if r.get('model',{}).get('status')=='parsed' and r['model'].get('lod')==0]
    if not exports:
        raise ValueError('没有 LOD0 网格（先运行 tools/ow_asset_chain.py）；这不证明纯粒子')
    if model:
        exports = [r for r in exports if r['model']==model]
    if material:
        exports = [r for r in exports if r.get('material')==material]
    else:
        direct = {r['guid'] for r in chain['resources'].get(chain['entity'],{}).get('refs',[])
                  if r['guid'].startswith('0d00')}
        bound = [r for r in exports if r['model'] in direct and r.get('material') is None]
        if bound:
            exports = bound
    if len(exports)!=1:
        raise ValueError('模型/材质不唯一或未声明；使用 --model 和 --material 明确选择')
    row = exports[0]
    path = (src/row['file']).resolve()
    if path.parent!=src.resolve() or not row['file'].endswith('.lod0.mesh.json'):
        raise ValueError('Invalid mesh export path')
    return path,row


def validate_mesh(mesh):
    count = len(mesh['positions'])
    if not count:
        raise ValueError('Empty mesh')
    for key,width in [('positions',3),('normals',3),('uv',2)]:
        rows = mesh[key]
        if len(rows)!=count or any(len(v)!=width or any(not math.isfinite(c) for c in v) for v in rows):
            raise ValueError('Invalid mesh array: '+key)
    indices = mesh['indices']
    if len(indices)%3 or any(not isinstance(i,int) or not 0<=i<count for i in indices):
        raise ValueError('Invalid triangle indices')
    if len(mesh['triangleTextureIds'])*3!=len(indices):
        raise ValueError('Triangle texture count mismatch')


def build(name, entity, *, out_root=None, model=None, material=None, pose=None):
    if pose is not None and not isinstance(pose,dict):
        raise ValueError('pose must be a metadata object; it does not transform geometry')
    if not re.fullmatch('[a-z0-9][a-z0-9_-]*',name) or not re.fullmatch('(?:03|04)[0-9a-f]{14}',entity):
        raise ValueError('Invalid pack name/entity')
    src = CACHE/entity
    chain_path = src/'chain.json'
    chain = json.loads(chain_path.read_text(encoding='utf-8'))
    if chain['entity']!=entity or chain['build']!='0.8.0.24919':
        raise ValueError('Chain identity mismatch')
    mesh_path,selected = select_mesh(src,chain,model,material)
    mesh = json.loads(mesh_path.read_text(encoding='utf-8'))
    validate_mesh(mesh)
    bindings = [s.get('binding',{}) for s in mesh.get('submeshes',[])]
    triangle_materials = [None]*len(mesh['triangleTextureIds'])
    assigned = set()
    for submesh in mesh.get('submeshes',[]):
        # Older fixture caches have binding evidence without triangle ranges.
        if 'triangleStart' not in submesh:
            continue
        start,count = submesh['triangleStart'],submesh['triangleCount']
        if start<0 or count<0 or start+count>len(triangle_materials):
            raise ValueError('Material triangle range bounds')
        for triangle in range(start,start+count):
            if triangle in assigned:
                raise ValueError('Overlapping material triangle ranges')
            assigned.add(triangle)
            triangle_materials[triangle] = submesh.get('binding',{}).get('material')
    groups = {}
    for triangle,texture in enumerate(mesh['triangleTextureIds']):
        if texture is not None and not re.fullmatch('0c[0-9a-f]{14}',texture):
            raise ValueError('Invalid texture GUID')
        groups.setdefault((texture or 'grey',triangle_materials[triangle]),[]).extend(mesh['indices'][triangle*3:triangle*3+3])
    root = Path(OUT if out_root is None else out_root).resolve()
    out = root/name
    if out==src.resolve() or out.is_relative_to(src.resolve()) or src.resolve().is_relative_to(out):
        raise ValueError('Output overlaps source cache')
    root.mkdir(parents=True,exist_ok=True)
    # Finish validation/copying before replacing a previous pack.
    with tempfile.TemporaryDirectory(prefix='.'+name+'-',dir=root) as temporary:
        stage = Path(temporary)
        files = {}
        for texture in dict.fromkeys(t for t,m in groups):
            if texture=='grey':
                continue
            png = src/(texture+'.png')
            decoded = chain['resources'].get(texture,{}).get('texture',{})
            if decoded.get('status')!='decoded' or not png.is_file():
                raise ValueError('Referenced color PNG is missing: '+texture)
            shutil.copy2(png,stage/png.name)
            files[png.name] = sha(stage/png.name)
        # Effect shaders can use linear intensity maps and variable references
        # rather than a diffuse image. Preserve those samplers without falsely
        # assigning a BC4 mask/BC5 normal as the group's color texture.
        material_textures = {}
        for binding in bindings:
            for slot in binding.get('textureSlots',[]):
                if slot['refType']!=3:
                    continue
                texture = slot['guid']
                decoded = chain['resources'].get(texture,{}).get('texture',{})
                entry = {**slot,**decoded}
                material_textures[(binding['material'],slot['slot'])] = dict(material=binding['material'],**entry)
                if decoded.get('status')=='decoded':
                    png = src/decoded['file']
                    if png.name!=decoded['file'] or not png.is_file():
                        raise ValueError('Missing/invalid material texture PNG')
                    shutil.copy2(png,stage/png.name)
                    files[png.name] = sha(stage/png.name)
        parameters = {}
        for binding in bindings:
            material_guid = binding.get('material')
            if material_guid and material_guid not in parameters:
                parameters[material_guid],generated = prepare_material(material_guid,binding,src,chain,stage)
                files.update(generated)
        skin = None
        if selected['model']=='0d00000000000ee9' and mesh.get('skin'):
            resource = chain['resources'][selected['model']]
            raw = (src/resource['file']).read_bytes()
            if hashlib.sha256(raw).hexdigest()!=resource['sha256'] or hashlib.md5(raw).hexdigest()!=resource['ckey']:
                raise ValueError('Dragon model SHA256/CKey mismatch')
            skin = extract_dragon_skin(mesh,raw)
        pack = dict(schema=1,name=name,entity=entity,model=selected['model'],material=selected.get('material'),
                    units='meters',vertices=len(mesh['positions']),
                    positions=[c for v in mesh['positions'] for c in v],
                    normals=[c for v in mesh['normals'] for c in v],uv=[c for v in mesh['uv'] for c in v],
                    groups=[dict(texture=t,material=m,indices=v) for (t,m),v in groups.items()],height=mesh.get('height'),
                    materialParameters=parameters,skin=skin,
                    materialTextures=list(material_textures.values()),
                    materialBindingComplete=mesh.get('materialBindingComplete',False))
        (stage/'pack.json').write_text(json.dumps(pack,separators=(',',':'))+'\n',encoding='utf-8')
        files['pack.json'] = sha(stage/'pack.json')
        provenance = dict(clientBuild=chain['build'],entity=entity,source=str(mesh_path),sourceSha256=sha(mesh_path),
                          chainSha256=sha(chain_path),files=files,inGameVerified=False,
                          geometryOnly=mesh.get('geometryOnly',False),animationEvaluated=False,
                          effectRenderers=mesh.get('effectRenderers',[]),
                          materialBindings=bindings,
                          materialParameters=parameters,
                          limits='Original geometry and audited material data; MC layer/blend/HDR/ramp adaptation and procedural swim, not native shader/animation execution')
        if pose is not None:
            provenance['modelsPose'] = pose
        (stage/'provenance.json').write_text(json.dumps(provenance,indent=2)+'\n',encoding='utf-8')
        if out.is_symlink() or out.is_junction():
            raise ValueError('Refusing to replace a linked output directory')
        if out.exists():
            shutil.rmtree(out)
        stage.replace(out)
    counts = {}
    for group in pack['groups']:
        counts[group['texture']] = counts.get(group['texture'],0)+len(group['indices'])//3
    return dict(name=name,vertices=pack['vertices'],triangles=len(mesh['indices'])//3,
                groups=counts,materials=len(parameters),skinBones=len(skin['parents']) if skin else 0,output=str(out))


def build_job(job, *, out_root=None):
    """Keep extended models recipes, rather than silently dropping job fields."""
    if not isinstance(job,dict):
        raise ValueError('Each batch job must be an object')
    unknown = set(job)-{'name','entity','model','material','pose','materials'}
    if unknown:
        raise ValueError('Unknown job fields: '+', '.join(sorted(unknown)))
    if 'pose' in job and not isinstance(job['pose'],dict):
        raise ValueError('pose must be a metadata object')
    if 'materials' in job and not isinstance(job['materials'],dict):
        raise ValueError('materials must be a material recipe object')
    if 'pose' in job or 'materials' in job:
        # Lazy import: that audited helper imports this module's core build(),
        # passing only name/entity/model/material, so it never re-enters here.
        # It also stages all overrides before replacing a previous output pack.
        from models_20261026_pack import pack as build_models_pack
        return build_models_pack(job,Path(OUT if out_root is None else out_root))
    return build(**job,out_root=out_root)


def run_batch(jobs, *, out_root=None):
    if not isinstance(jobs,list):
        raise ValueError('Batch JSON must be a list of jobs')
    successes,failures = [],[]
    for index,job in enumerate(jobs,1):
        name = job.get('name') if isinstance(job,dict) else None
        try:
            result = build_job(job,out_root=out_root)
        except Exception as error:
            failure = dict(index=index,name=name,errorType=type(error).__name__,error=str(error))
            failures.append(failure)
            print(json.dumps(dict(type='result',ok=False,**failure),ensure_ascii=False),flush=True)
        else:
            successes.append(result)
            print(json.dumps(dict(type='result',ok=True,index=index,**result),ensure_ascii=False),flush=True)
    summary = dict(type='summary',total=len(jobs),succeeded=len(successes),failed=len(failures),failures=failures)
    print(json.dumps(summary,ensure_ascii=False),flush=True)
    return summary


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('name',nargs='?')
    parser.add_argument('entity',nargs='?')
    parser.add_argument('--model')
    parser.add_argument('--material')
    parser.add_argument('--out-root',type=Path)
    parser.add_argument('--batch',type=Path,help='JSON jobs; pose/materials supported; continue on per-job failure')
    args = parser.parse_args()
    if args.batch:
        if any((args.name,args.entity,args.model,args.material)):
            parser.error('--batch cannot be combined with a single job')
        jobs = json.loads(args.batch.read_text(encoding='utf-8-sig'))
        summary = run_batch(jobs,out_root=args.out_root)
        return 1 if summary['failed'] else 0
    elif args.name and args.entity:
        print(json.dumps(build(args.name,args.entity,model=args.model,material=args.material,out_root=args.out_root),ensure_ascii=False))
        return 0
    else:
        parser.error('Provide name/entity or --batch')


if __name__=='__main__':
    raise SystemExit(main())
