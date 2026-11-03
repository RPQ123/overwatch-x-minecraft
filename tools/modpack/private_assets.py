"""Curate a local personal-only asset bundle; never download or copy OW clients."""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path,PureWindowsPath
import re
import subprocess
import tempfile

from .config import PackPaths, local_path, read_json, sha256, write_json

LICENSE = '暴雪娱乐版权所有；非商业粉丝作品，按 Blizzard 粉丝内容政策使用，禁止商用'
COMPONENT = 'private'
VOICE_DIRECTORY = 'private-assets/ow1-zhcn-2016/thnu-full'
PROFILE_DIRECTORY = 'guest-passthrough-client'
RESOURCE_RECIPE = 1


def prebuild_profile_resources(builder) -> dict:
    """Rebuild runtime packs from this bundle's pinned assets, never a user pack."""
    import genji_voice_assets as genji
    import mccree_voice_assets as mccree
    import combat_feedback_assets as feedback
    import early_chinese_voice_assets as chinese
    import four_dps_voice_assets as skills
    from configure_passthrough import factory_options

    root=builder.destination;profile=root/PROFILE_DIRECTORY
    component='profile-private'
    builder.component(component,LICENSE,'Generated resource packs from the bundled SHA256-pinned assets')
    inputs={};active=[];statuses=[];outputs=[]

    def generated(relative, data):
        target=local_path(root,relative)
        if target.exists():raise ValueError('预制资源包路径重复：'+relative)
        target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(data)
        builder.record(relative,component);outputs.append(builder.rows[relative])

    def json_file(relative, data):
        generated(relative,(json.dumps(data,ensure_ascii=False,separators=(',',':'))+'\n').encode('utf-8'))

    def pack(name, label, module, specifications, *, full=False):
        # A whole legacy group must be valid before creating/enabling it.
        checked=[]
        for event, source, stem, pin in specifications:
            row=builder.rows.get(source)
            if not row or row['component']!=COMPONENT or row['sha256']!=pin:
                statuses.append(dict(component=module,label=label,ready=False,
                    warning=label+'缺失；继续启动，对应附加资源停用。'))
                return False
            data=local_path(root,source).read_bytes()
            if hashlib.sha256(data).hexdigest()!=pin or not data.startswith(b'OggS'):
                raise ValueError('预制音频哈希不匹配：'+source)
            checked.append((event,source,stem,pin))
        if not checked:return False
        relative=PROFILE_DIRECTORY+'/resourcepacks/'+name
        definitions={};proof={}
        for event,source,stem,pin in checked:
            destination=relative+'/assets/owmcguest/sounds/'+stem+'.ogg'
            if destination not in builder.rows:
                builder.copy(local_path(root,source),destination,component,root)
                outputs.append(builder.rows[destination])
            inputs[source]=dict(path=source,bytes=builder.rows[source]['bytes'],sha256=pin)
            definition=definitions.setdefault(event,dict(replace=True,sounds=[]))
            definition['sounds'].append(dict(name='owmcguest:'+stem,preload=not full))
            proof[stem]=dict(source=source,sha256=pin)
        description='Private OWMC hero voices; local manifest only' if full else 'OWMC bundled private audio'
        json_file(relative+'/pack.mcmeta',dict(pack=dict(pack_format=34,description=description)))
        json_file(relative+'/assets/owmcguest/sounds.json',definitions)
        json_file(relative+'/provenance.json',dict(schemaVersion=1,files=proof,license=LICENSE))
        if full:
            generated(relative+'/owmc-owned-v1',b'OWMC private full voice v1\n')
        active.append('file/'+name);statuses.append(dict(component=module,label=label,ready=True))
        return True

    genji_ready=pack('owmc-private-voice','源氏语音','genji_voice_assets',[
        ('genji.dragonblade','private-assets/ow-early-reference/genji-ow1-dragonblade.ogg',
         'private/genji_dragonblade',genji.SHA256)])
    pack('owmc-private-mccree','麦克雷语音','mccree_voice_assets',[
        ('mccree.'+name[:-4],'private-assets/owmc-mccree/'+mccree.SOURCES[name],
         'private/mccree/'+name[:-4],pin) for name,pin in mccree.FILES.items()])
    pack('owmc-private-combat-feedback','命中反馈','combat_feedback_assets',[
        ('combat.'+event,'private-assets/owmc-combat-feedback/'+name+'.ogg',
         'private/combat/'+name,feedback.FILES[name+'.ogg']) for event,name in (('hit','hit'),('elimination','kill'))])
    early=[(event,'private-assets/ow1-zhcn-2016/thnu-three/selected/'+name+'.ogg',
            'private/early_chinese/'+name,pin) for event,(name,pin) in chinese.CLIPS.items()]
    if genji_ready:early.append(('genji.dragonblade','private-assets/ow-early-reference/genji-ow1-dragonblade.ogg',
                                'private/genji_dragonblade',genji.SHA256))
    pack('owmc-private-early-chinese','中文选人语音','early_chinese_voice_assets',early)
    pack('owmc-private-four-dps','技能语音','four_dps_voice_assets',[
        (event,'private-assets/ow1-zhcn-2016/four-dps-20261023/'+name+'.ogg','private/four_dps/'+name,pin)
        for event,clips in skills.CLIPS.items() for name,pin in clips])
    barrage='private-assets/owmc-pharah-barrage/fire-loop.ogg'
    pack('owmc-private-pharah-barrage','法老之鹰语音','pack_pharah_barrage',[
        ('pharah.barrage.fire',barrage,'private/pharah/fire-loop',builder.rows.get(barrage,{}).get('sha256',''))])
    manifest=local_path(root,VOICE_DIRECTORY+'/manifest.json')
    full_entries=read_json(manifest).get('entries',{}) if manifest.is_file() else {}
    full_rows=[('hero_voice.'+identity,VOICE_DIRECTORY+'/'+entry['file'],'private/full/'+identity,entry['sha256'])
               for identity,entry in sorted(full_entries.items()) if not entry.get('unavailable')]
    full_ready=pack('owmc-private-full-voice','完整英雄语音','heroVoiceAssets',full_rows,full=True)
    if full_ready:
        for identity,entry in sorted(full_entries.items()):
            if entry.get('unavailable'):continue
            receipt=PROFILE_DIRECTORY+'/resourcepacks/owmc-private-full-voice/assets/owmcguest/sounds/private/full/'+identity+'.json'
            json_file(receipt,dict(sourceSha256=entry.get('originalMp3Sha256',entry['sha256']),oggSha256=entry['sha256']))
        inputs[VOICE_DIRECTORY+'/manifest.json']={k:builder.rows[VOICE_DIRECTORY+'/manifest.json'][k] for k in ('path','bytes','sha256')}
        if len(full_rows)!=785:
            statuses[-1].update(ready=False,warning=f'完整英雄语音仅预制 {len(full_rows)}/785 条；缺项保留告警。')
    else:
        statuses.append(dict(component='heroVoiceAssets',label='完整英雄语音',ready=False,warning='完整英雄语音缺失；继续启动。'))
    # Verify these sources too before bypassing the ordinary optional preparers.
    for relative,row in builder.rows.items():
        if row['component']==COMPONENT:
            inputs[relative]={k:row[k] for k in ('path','bytes','sha256')}
    for key,label,prefix in (('pulse_bomb_assets','脉冲炸弹模型','private-assets/owmc-pulse-bomb/'),
                             ('meshAssets','英雄附加模型','private-assets/owmc-mesh/')):
        ready=any(name.startswith(prefix) for name in inputs)
        row=dict(component=key,label=label,ready=ready)
        if not ready:row['warning']=label+'缺失；继续启动，对应附加资源停用。'
        statuses.append(row)
    modules=('genji_voice_assets','mccree_voice_assets','combat_feedback_assets','early_chinese_voice_assets',
             'four_dps_voice_assets','pack_pharah_barrage','pulse_bomb_assets')
    code=['tools/'+module+'.py' for module in modules]+['tools/modpack/resources.py','tools/modpack/private_assets.py']
    for relative in code:
        row=builder.rows.get(relative)
        if row:inputs[relative]={k:row[k] for k in ('path','bytes','sha256')}
    (profile/'options.txt').write_text(factory_options(active),encoding='utf-8')
    builder.record(PROFILE_DIRECTORY+'/options.txt','owmc')
    lock=dict(schemaVersion=RESOURCE_RECIPE,enabledPacks=active,components=statuses,
              sources=list(inputs.values()),files=[{k:row[k] for k in ('path','bytes','sha256')} for row in outputs])
    write_json(profile/'owmc-resource-lock.json',lock)
    builder.record(PROFILE_DIRECTORY+'/owmc-resource-lock.json','owmc')
    return dict(resourcePacks=active,files=len(outputs),warnings=[row['warning'] for row in statuses if 'warning' in row])


def prepared_profile_resources(profile: Path) -> bool:
    """A relocated pack can reuse prebuilt resources only after hash validation."""
    from .config import paths
    configured=paths()
    if not configured.packaged:return False
    try:
        profile=profile.resolve();root=configured.root
        if profile!=configured.get('profile'):return False
        lock=read_json(profile/'owmc-resource-lock.json')
        if lock.get('schemaVersion')!=RESOURCE_RECIPE:return False
        options=[line.split(':',1)[1] for line in (profile/'options.txt').read_text(encoding='utf-8').splitlines() if line.startswith('resourcePacks:')]
        if len(options)!=1 or not set(lock['enabledPacks'])<=set(json.loads(options[0])):return False
        for row in [*lock['sources'],*lock['files']]:
            path=local_path(root,row['path'])
            if not path.is_file() or path.stat().st_size!=row['bytes'] or sha256(path)!=row['sha256']:return False
        # The receipt is an optimization, never authority for different assets.
        expected={'privateAssets':root/'private-assets','meshAssets':root/'private-assets/owmc-mesh',
                  'heroVoiceAssets':root/VOICE_DIRECTORY}
        if any(configured.get(key)!=value for key,value in expected.items()):return False
        from .resources import REPORT
        write_json(root/REPORT,dict(schemaVersion=1,profile=str(profile),components=lock['components'],
            warnings=[row['warning'] for row in lock['components'] if 'warning' in row],prebuiltResourcesVerified=True))
        return True
    except (OSError,ValueError,KeyError,TypeError):
        return False


def voice_catalog(root: Path) -> list[tuple[str, str, str]]:
    text = (root/'guest/src/main/java/lab/owmcguest/HeroVoiceDefaultCatalog.java').read_text(encoding='utf-8')
    rows = re.findall(r'^([a-z0-9]+)\|([a-z_:]+)\|([0-9a-f]{32})$', text, re.M)
    if len(rows) != 785 or len({h for _, _, h in rows}) != 785:
        raise ValueError('语音白名单必须恰为 785 个不重复条目。')
    return rows


def model_references(root: Path, available: set[str]) -> set[str]:
    # Resolve static literals and the concatenated names used by renderers.
    texts = '\n'.join(p.read_text(encoding='utf-8') for folder in
                      ('guest/src/main/java','guest/src/client/java') for p in (root/folder).rglob('*.java'))
    # Strip comments before looking at literals, excluding retired/future jobs.
    texts = re.sub(r'/\*.*?\*/|//[^\n]*', '', texts, flags=re.S)
    literals = set(re.findall(r'"([^"\n]+)"', texts))
    selected = available & literals
    selected |= {name for name in available if any(name[:i] in literals and name[i:] in literals
                                                  for i in range(1, len(name)))}
    selected |= set(re.findall(r'OriginalMeshPack\.get\("([a-z0-9-]+)"\)', texts))
    # The turret's native level is bounded 1..3 by the server. The renderer
    # builds its name from that integer, so it is not a full string literal.
    if '"torb-turret-"+tv.level()' in texts:
        selected |= {f'torb-turret-{level}' for level in (1,2,3)}
    return {name for name in selected if not name.endswith('-')}


class PrivateBundle:
    def __init__(self, builder, configured: PackPaths):
        self.builder, self.paths = builder, configured
        self.summary = dict(voiceCatalog=785, voiceClipsCopied=0, modelPacksCopied=0,
                            meshPacksCopied=0, specialModelPacksCopied=0, legacyAudioFiles=0,
                            ffmpegIncluded=False, runtimeTranscodingRequired=False,
                            buildConvertedVoices=0,
                            absoluteSourcePathsRedacted=0,
                            missingVoices=[], missingModels=[], optionalAudioWarnings=[])

    def copy(self, source: Path, relative: str, source_root: Path) -> None:
        sanitized=None;redacted=0
        if source.name=='provenance.json' or source.name.endswith('-source.json') or source.name in ('source.json','manifest.json'):
            def portable(value):
                nonlocal redacted
                if isinstance(value,dict):return {key:portable(item) for key,item in value.items()}
                if isinstance(value,list):return [portable(item) for item in value]
                if isinstance(value,str) and PureWindowsPath(value).is_absolute():
                    redacted+=1
                    return 'local-input:'+PureWindowsPath(value).name
                return value
            value=portable(json.loads(source.read_text(encoding='utf-8-sig')))
            if redacted:sanitized=(json.dumps(value,ensure_ascii=False,indent=2)+'\n').encode('utf-8')
        prior = self.builder.rows.get(relative)
        if prior:
            digest=hashlib.sha256(sanitized).hexdigest() if sanitized is not None else sha256(source)
            if prior['component'] != COMPONENT or prior['sha256'] != digest:
                raise ValueError('私有资源复制冲突：'+relative)
            return
        self.builder.copy(source, relative, COMPONENT, source_root)
        if sanitized is not None:
            local_path(self.builder.destination,relative).write_bytes(sanitized)
            self.builder.record(relative,COMPONENT)
            self.summary['absoluteSourcePathsRedacted']+=redacted

    def generated(self, relative: str, value: dict) -> None:
        path = local_path(self.builder.destination, relative)
        if path.exists():
            raise ValueError('私有元数据路径重复：'+relative)
        write_json(path, value)
        self.builder.record(relative, COMPONENT)

    def voices(self, catalog: list[tuple[str,str,str]]) -> None:
        root = self.paths.get('heroVoiceAssets')
        manifest = read_json(root/'manifest.json')
        entries = manifest.get('entries', manifest)
        cached = self.paths.get('profile')/'resourcepacks/owmc-private-full-voice/assets/owmcguest/sounds/private/full'
        packed = {}
        for hero, event, identity in catalog:
            entry = entries.get(identity, {})
            pin = str(entry.get('sha256', ''))
            row = dict(hero=hero, event=event, format='ogg', file=f'{hero}/{identity}.ogg', sha256=pin)
            packed[identity] = row
            try:
                if entry.get('hero') != hero or entry.get('event') != event or not re.fullmatch('[0-9a-f]{64}', pin):
                    raise ValueError('白名单与私有清单身份不同')
                # Reuse only hash-receipted OGGs for the exact pinned MP3 input.
                # This avoids copying raw MP3s or shipping a runtime converter.
                try:
                    ogg = cached/(identity+'.ogg')
                    proof = read_json(cached/(identity+'.json'))
                    if proof.get('sourceSha256') != pin or sha256(ogg) != proof.get('oggSha256'):
                        raise ValueError('OGG 缓存回执不匹配')
                    if not 0<ogg.stat().st_size<=5_000_000 or not ogg.read_bytes().startswith(b'OggS'):
                        raise ValueError('OGG 头不匹配')
                    self.copy(ogg, VOICE_DIRECTORY+'/'+row['file'], cached)
                    ogg_sha=proof['oggSha256']
                except (OSError,ValueError,KeyError,TypeError):
                    ogg_sha=self.convert_voice(root,hero,identity,pin,VOICE_DIRECTORY+'/'+row['file'])
                row.update(sha256=ogg_sha, originalMp3Sha256=pin)
                self.summary['voiceClipsCopied'] += 1
            except (OSError,ValueError,KeyError,TypeError,subprocess.SubprocessError) as error:
                # Keep an absent entry so Java reports incomplete assets rather
                # than treating a shortened catalog as fully installed.
                row['unavailable'] = True
                self.summary['missingVoices'].append(dict(hash=identity,hero=hero,event=event,reason=type(error).__name__))
        self.generated(VOICE_DIRECTORY+'/manifest.json', dict(schemaVersion=1, entries=packed,
                       encoding='preconverted-ogg', allowedCatalogCount=len(catalog)))

    def convert_voice(self, root: Path, hero: str, identity: str, pin: str, relative: str) -> str:
        source=local_path(root,f'{hero}/{identity}.mp3')
        data=source.read_bytes()
        if not 0<len(data)<=5_000_000 or hashlib.sha256(data).hexdigest()!=pin:
            raise ValueError('MP3 源哈希或大小不匹配')
        ffmpeg=self.paths.get('ffmpeg')
        if not ffmpeg.is_file():raise FileNotFoundError('构建转码工具缺失')
        temporary=self.builder.root/'data/tmp';temporary.mkdir(parents=True,exist_ok=True)
        with tempfile.TemporaryDirectory(prefix='owmc-private-audio-',dir=temporary) as directory:
            output=Path(directory)/'voice.ogg'
            result=subprocess.run([str(ffmpeg),'-nostdin','-hide_banner','-loglevel','error',
                '-f','mp3','-i','pipe:0','-vn','-c:a','libvorbis','-q:a','4',str(output)],
                input=data,capture_output=True,timeout=30,
                env={**os.environ,'TMP':directory,'TEMP':directory},
                creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
            if result.returncode or not output.is_file() or not output.read_bytes().startswith(b'OggS'):
                raise ValueError('构建阶段语音转码失败')
            digest=sha256(output);self.copy(output,relative,Path(directory))
        self.summary['buildConvertedVoices']+=1
        return digest

    def model(self, name: str, folder: Path, destination: str, *, mesh=False) -> None:
        try:
            proof = read_json(folder/'provenance.json')
            pins = proof.get('files')
            if not isinstance(pins, dict) or not pins:
                raise ValueError('模型缺少逐文件哈希')
            sources = []
            for relative, pin in pins.items():
                path = local_path(folder, relative)
                if path.suffix.lower() not in ('.json','.png','.ogg') or not re.fullmatch('[0-9a-f]{64}',str(pin)):
                    raise ValueError('模型包含非运行资源或无效哈希')
                if sha256(path) != pin:
                    raise ValueError('模型文件 SHA256 不匹配')
                sources.append((path, relative))
            # Validate the complete group before copying; partial models remain
            # absent and follow the existing renderers' graceful fallback.
            for path, relative in sources:
                self.copy(path, destination+'/'+relative, folder)
            self.copy(folder/'provenance.json', destination+'/provenance.json', folder)
            self.summary['modelPacksCopied'] += 1
            self.summary['meshPacksCopied' if mesh else 'specialModelPacksCopied'] += 1
        except (OSError,ValueError,KeyError,TypeError) as error:
            self.summary['missingModels'].append(dict(name=name,reason=type(error).__name__))

    def models(self) -> None:
        root = self.paths.get('meshAssets')
        try:
            available = {p.name for p in root.iterdir() if p.is_dir()}
        except OSError:
            available = set()
        selected = model_references(self.builder.root, available)
        self.summary['meshPacksReferenced'] = len(selected)
        for name in sorted(selected):
            self.model(name, root/name, 'private-assets/owmc-mesh/'+name, mesh=True)
        for name in ('owmc-pharah-projectile','owmc-pharah-barrage','owmc-pulse-bomb','owmc-venom-mine'):
            self.model(name, self.paths.get('privateAssets')/name, 'private-assets/'+name)

    def legacy_audio(self) -> None:
        # These are additional, explicitly referenced startup sounds/effects,
        # not extra rows added to the approved 785-entry hero voice catalog.
        import genji_voice_assets as genji
        import mccree_voice_assets as mccree
        import combat_feedback_assets as feedback
        import early_chinese_voice_assets as chinese
        import four_dps_voice_assets as skills
        base = self.paths.get('privateAssets')
        files = [('ow-early-reference/genji-ow1-dragonblade.ogg',genji.SHA256)]
        metadata = set()
        for name, pin in mccree.FILES.items():
            source=mccree.SOURCES[name]
            files.append(('owmc-mccree/'+source,pin))
            metadata.add('owmc-mccree/'+source[:-4]+'-source.json')
        files += [('owmc-combat-feedback/'+name,pin) for name,pin in feedback.FILES.items()]
        metadata.add('owmc-combat-feedback/source.json')
        files += [('ow1-zhcn-2016/thnu-three/selected/'+name+'.ogg',pin) for name,pin in chinese.CLIPS.values()]
        for clips in skills.CLIPS.values():
            files += [('ow1-zhcn-2016/four-dps-20261023/'+name+'.ogg',pin) for name,pin in clips]
        metadata |= {'ow1-zhcn-2016/thnu-three/manifest.json','ow1-zhcn-2016/four-dps-20261023/manifest.json'}
        for relative, pin in files:
            try:
                path=local_path(base,relative)
                if sha256(path)!=pin or not path.read_bytes().startswith(b'OggS'):
                    raise ValueError('启动音效 SHA256 不匹配')
                self.copy(path,'private-assets/'+relative,base)
                self.summary['legacyAudioFiles'] += 1
            except (OSError,ValueError) as error:
                self.summary['optionalAudioWarnings'].append(dict(file=relative,reason=type(error).__name__))
        for relative in sorted(metadata):
            try:
                self.copy(local_path(base,relative),'private-assets/'+relative,base)
            except (OSError,ValueError) as error:
                self.summary['optionalAudioWarnings'].append(dict(file=relative,reason=type(error).__name__))

    def stage(self) -> dict:
        self.builder.component(COMPONENT, LICENSE, 'User-supplied fan-content notice; asset redistribution authorization not verified')
        self.builder.components[COMPONENT].update(noticeIsUserSupplied=True,authorizationVerified=False)
        self.voices(voice_catalog(self.builder.root))
        self.models()
        self.legacy_audio()
        self.ffmpeg()
        self.summary['audioFiles']=sum(r['component']==COMPONENT and r['path'].endswith('.ogg') for r in self.builder.rows.values())
        self.summary['legacyAudioFiles']=self.summary['audioFiles']-self.summary['voiceClipsCopied']
        self.summary['privateFiles'] = sum(r['component']==COMPONENT for r in self.builder.rows.values()) + 1
        self.generated('private-assets/bundle-summary.json',self.summary)
        return self.summary

    def ffmpeg(self) -> None:
        source=self.paths.get('ffmpeg')
        # A user's OW installation is never a packaging source, including when
        # an unrelated tool happens to have been placed in that directory.
        if source.resolve().is_relative_to(self.paths.get('owExecutable').parent):
            raise ValueError('禁止从 OW 客户端安装目录打包文件。')
        license_file=source.parent.parent/'LICENSE.txt'
        text=license_file.read_text(encoding='utf-8-sig')
        if 'GNU GENERAL PUBLIC LICENSE' not in text.upper() or 'Version 3' not in text:
            raise ValueError('当前 ffmpeg 输入缺少预期的 GPLv3 许可文本。')
        self.builder.component('ffmpeg','GPL-3.0-or-later','https://ffmpeg.org/legal.html',version='local binary; corresponding source offer pending')
        self.builder.copy(source,'tools/ffmpeg/ffmpeg.exe','ffmpeg',source.parent.parent)
        self.builder.copy(license_file,'tools/ffmpeg/LICENSE.txt','ffmpeg',source.parent.parent)
        self.summary['ffmpegIncluded']=True
