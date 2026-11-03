"""离线投射物/材质复核；生成证据、逐项 Claude 命令与批量 jobs，不开游戏。

默认只复核已有 chain；--refresh 用 SHA 防护的本地 Archive 重建全部链。
最终安装由 Claude 运行输出的 pack-commands.ps1 或 build_mesh_pack --batch。
"""
import argparse
from collections import deque
import json
from pathlib import Path

from PIL import Image, ImageStat

from ow_asset_chain import Archive, CACHE, collect, parse_effect
import build_mesh_pack as packer

# Exact24919 observed presentation effect/model/material pairs. A selected
# effect renderer is a static research artifact, never a complete effect player.
SPECS = [
    ('mercy-pistol','0158','01e1','0801','d6b19e91','粒子片（4三角形）及拖尾，无独立实体弹体模型'),
    ('zenyatta-primary','0236','0322','085b','e06922b3','effect 球形网格及粒子片；球体材质使用内建采样/变量'),
    ('zenyatta-secondary','0261','0345','085b','b815a1f6','effect 球形网格及粒子片；球体材质使用内建采样/变量'),
    ('reinhardt-fire','01ea','025f','0c1f','5781f72d','effect 火焰刃网格（另有0bd9/0b08/0c1e）'),
    ('zarya-grenade','03db','05b8','11c3','6b4d8661','effect 曲面网格及环片，遮罩/颜色变量着色'),
    ('zarya-graviton','08ce','064d','0dbf','115641cb','effect 球形网格及环片/粒子片'),
    ('roadhog-scrap','029a','057e','07f5','2f8f5991','粒子片及拖尾网格，无独立碎铁弹体模型'),
    ('roadhog-secondary','0295','057c','14c0','8caa7d7c','effect 碎铁球网格及粒子片'),
    ('roadhog-whole-hog','0405','058b','0801','2e4a449f','effect 通用双面粒子片，无独立弹体模型'),
    ('dva-pistol','1000','147c','0801','6ccc2cd2','粒子片及拖尾网格，无独立实体弹体模型'),
    ('torb-turret','0143',None,'092e',None,'实体网格；diffuse 1503，BC3 sRGB'),
    ('torb-armor','02a1',None,'0c40',None,'实体网格；diffuse 1500，BC1 sRGB'),
    ('junk-trap','11a9',None,'28cd',None,'实体网格；颜色52d7，BC1 sRGB'),
]


def verify_pack(job, result):
    """Read the actual written pack back and compare every geometry/group/hash."""
    out = Path(result['output'])
    provenance = json.loads((out/'provenance.json').read_text(encoding='utf-8'))
    source = Path(provenance['source'])
    mesh = json.loads(source.read_text(encoding='utf-8'))
    pack = json.loads((out/'pack.json').read_text(encoding='utf-8'))
    assert provenance['sourceSha256']==packer.sha(source)
    assert provenance['inGameVerified'] is False
    for key in ('positions','normals','uv'):
        assert pack[key]==[c for v in mesh[key] for c in v],key
    expected = {}
    for t,texture in enumerate(mesh['triangleTextureIds']):
        expected.setdefault(texture or 'grey',[]).extend(mesh['indices'][t*3:t*3+3])
    assert {g['texture']:g['indices'] for g in pack['groups']}==expected
    stats = {}
    for filename,digest in provenance['files'].items():
        assert packer.sha(out/filename)==digest
        if filename.endswith('.png'):
            assert packer.sha(out/filename)==packer.sha(CACHE/job['entity']/filename)
            with Image.open(out/filename) as image:
                rgb = image.convert('RGB')
                sample = rgb.copy();sample.thumbnail((128,128))
                values = list(sample.get_flattened_data())
                chromatic = sum(max(v)-min(v)>8 for v in values)/len(values)
                stats[filename] = dict(size=list(image.size),meanRGB=ImageStat.Stat(rgb).mean,
                                       extrema=rgb.getextrema(),chromaticFraction=chromatic)
    return dict(arraysEqual=True,groupIndicesEqual=True,allFileHashesEqual=True,pngs=stats,
                vertices=pack['vertices'],triangles=sum(len(g['indices'])//3 for g in pack['groups']),
                materialBindingComplete=pack['materialBindingComplete'],
                greyTriangles=len(expected.get('grey',[]))//3)


def reference_path(chain, target):
    queue = deque([(chain['entity'],[])])
    visited = set()
    while queue:
        source,path = queue.popleft()
        if source==target:
            return path
        if source in visited:
            continue
        visited.add(source)
        for ref in chain['resources'].get(source,{}).get('refs',[]):
            queue.append((ref['guid'],path+[dict(source=source,**ref)]))
    raise ValueError('Selected effect is not reachable from the entity: '+target)


def audit(refresh=False):
    out = CACHE/'projectile-audit'
    out.mkdir(exist_ok=True)
    archive = Archive('projectile-audit') if refresh else None
    evidence, jobs, commands = [], [], []
    for name,suffix,effect_suffix,model_suffix,material_suffix,conclusion in SPECS:
        entity = '040000000000'+suffix
        src = CACHE/entity
        if refresh:
            archive.out = src
            src.mkdir(exist_ok=True)
            collect(entity,archive=archive)
        chain = json.loads((src/'chain.json').read_text(encoding='utf-8'))
        model = '0d0000000000'+model_suffix
        job = dict(name=name,entity=entity,model=model)
        if material_suffix:
            job['material'] = '0e000000'+material_suffix.zfill(8)
        if effect_suffix:
            effect = '030000000000'+effect_suffix
            effect_row = chain['resources'][effect]
            measured = parse_effect((src/effect_row['file']).read_bytes())
            assert any(r['model']==model and r['material']==job['material'] for r in measured['renderers'])
            path = reference_path(chain,effect)
        else:
            effect,measured,path = None,None,reference_path(chain,model)
        result = packer.build(**job,out_root=CACHE/'mesh-pack-validation')
        checked = verify_pack(job,result)
        model_path,_ = packer.select_mesh(src,chain,job['model'],job.get('material'))
        mesh = json.loads(model_path.read_text(encoding='utf-8'))
        evidence.append(dict(name=name,entity=entity,conclusion='有网格：'+conclusion,pureParticlesWithoutMesh=False,
            presentationEffect=effect,effectLayout=measured,model=model,material=job.get('material'),
            presentationPath=path,
            entityModelRefs=[r for r in chain['resources'][entity]['refs'] if r['guid'].startswith('0d00')],
            meshFile=str(model_path),bindings=[s['binding'] for s in mesh['submeshes']],
            chainSha256=packer.sha(src/'chain.json'),pack=result,verification=checked,
            unresolved=[g for g,r in chain['resources'].items() if r['status']!='read'],
            limits='仅离线几何/材质证据；effect 变换、发射/混合/动态颜色未复现，未游戏验收'))
        jobs.append(job)
        command = '.venv/Scripts/python.exe tools/build_mesh_pack.py '+name+' '+entity+' --model '+model
        if job.get('material'):
            command += ' --material '+job['material']
        commands.append(command)
        print(json.dumps(dict(name=name,triangles=checked['triangles'],pngs=len(checked['pngs']),
                              colorBound=checked['materialBindingComplete'],verified=True),ensure_ascii=False),flush=True)
    (out/'evidence.json').write_text(json.dumps(evidence,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    (out/'pack-jobs.json').write_text(json.dumps(jobs,indent=2)+'\n',encoding='utf-8')
    (out/'pack-commands.ps1').write_text('\n'.join(commands)+'\n',encoding='utf-8')
    lines = ['# 离线网格链复核（未启动游戏）','',
             '主清单同 PrimaryGUID 多版本被命名路径覆盖；现按每条记录 CKey/bytes 校验。',
             '0300 是 effect，0320 才是图像 payload。槽 refType=2 是变量，不是纹理；单 payload 小贴图使用03200000。','']
    for row in evidence:
        v = row['verification']
        lines.append(f"- {row['name']} {row['entity']}：{row['conclusion']}；{v['vertices']}顶点/{v['triangles']}三角形，{len(v['pngs'])}张PNG，颜色绑定={v['materialBindingComplete']}。")
    lines += ['', '不能把通用粒子片/拖尾称为无网格；也不能把它们称为完整的独立弹体模型。',
              '颜色未绑定的 effect 保留原始贴图/内建采样/变量槽，pack 的 grey 是明确的不支持着色，未虚构颜色图。',
              '各命令独占一行：pack-commands.ps1；批量同名执行：',
              '.venv/Scripts/python.exe tools/build_mesh_pack.py --batch research/asset-cache/projectile-audit/pack-jobs.json',
              '本次所有 pack 在 research/asset-cache/mesh-pack-validation；证据见 evidence.json。']
    (out/'REPORT.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
    return evidence


if __name__=='__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--refresh',action='store_true')
    args = parser.parse_args()
    audit(args.refresh)
