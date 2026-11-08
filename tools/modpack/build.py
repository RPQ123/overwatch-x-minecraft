"""Stage an auditable local bundle; never copy user profiles or credentials.

Run with the project Python: tools/modpack/build.py --version 1.0.0
There is deliberately no network access and no overwrite/recursive-delete option.
"""
from __future__ import annotations

import argparse
import ast
import hashlib
import importlib.metadata as metadata
import json
from pathlib import Path, PurePosixPath
import re
import shutil
import sys
import zipfile

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'tools'))
from modpack.config import PackPaths, OW_SHA256, local_path, sha256, write_json
from modpack.private_assets import LICENSE as PRIVATE_LICENSE
from modpack.private_assets import PROFILE_DIRECTORY
from modpack.game_client import LICENSE as CLIENT_LICENSE

INTERNAL = 'LicenseRef-OWMC-Internal-Only'
PYTHON_LICENSE = 'LicenseRef-CPython-Bundled-Licenses'
JAVA_LICENSE = 'GPL-2.0-only WITH Classpath-exception-2.0 AND LicenseRef-OpenJDK-Third-Party'
SEEDS = ('project_launcher', 'launch_passthrough_session', 'stop_passthrough_session',
         'launch_passthrough_guest', 'configure_passthrough', 'check_environment')
DEPENDENCIES = {
    'minecraft-launcher-lib': ('BSD-2-Clause', 'https://codeberg.org/JakobDev/minecraft-launcher-lib'),
    'psutil': ('BSD-3-Clause', 'https://github.com/giampaolo/psutil'),
    'numpy': ('BSD-3-Clause AND 0BSD AND MIT AND Zlib AND CC0-1.0', 'https://github.com/numpy/numpy'),
    'pillow': ('MIT-CMU', 'https://github.com/python-pillow/Pillow'),
    'websockets': ('BSD-3-Clause', 'https://github.com/python-websockets/websockets'),
    'pymongo': ('Apache-2.0', 'https://github.com/mongodb/mongo-python-driver'),
    'dnspython': ('ISC', 'https://github.com/rthalley/dnspython'),
    'requests': ('Apache-2.0', 'https://github.com/psf/requests'),
    'urllib3': ('MIT', 'https://github.com/urllib3/urllib3'),
    'certifi': ('MPL-2.0', 'https://github.com/certifi/python-certifi'),
    'charset-normalizer': ('MIT', 'https://github.com/jawah/charset_normalizer'),
    'idna': ('BSD-3-Clause', 'https://github.com/kjd/idna'),
}
FORBIDDEN_PARTS = {'.git', '.venv', '.universal-modder', 'private-assets', 'game', 'overwatch-2015', 'saves',
                   'resourcepacks', 'shaderpacks', 'logs', 'research', 'PrismLauncher'}
SECRET = re.compile(rb'(?<![A-Za-z0-9_])(?:AKIA[0-9A-Z]{16}|gh[pousr]_[A-Za-z0-9]{30,}|sk-(?:proj-|ant-)?[A-Za-z0-9_-]{40,})(?![A-Za-z0-9_-])')


def safe_source(path: Path, root: Path) -> None:
    if not path.is_file() or not path.resolve().is_relative_to(root.resolve()):
        raise ValueError(f'复制源不在允许目录内：{path.name}')
    for parent in (path, *path.parents):
        if parent == root.parent:
            break
        if parent.is_symlink() or parent.is_junction():
            raise ValueError(f'不打包符号链接或联接点：{path.name}')


def source_closure(root: Path) -> list[Path]:
    """Local Python imports + literal subprocess scripts + dynamic hero plugins."""
    pending = [root / 'tools' / f'{name}.py' for name in SEEDS]
    pending += list((root / 'tools').glob('prepare_hero_*.py'))
    pending += [p for p in (root / 'tools/modpack').glob('*.py') if not p.name.startswith('test_')]
    seen = set()
    while pending:
        path = pending.pop()
        if path in seen:
            continue
        safe_source(path, root)
        seen.add(path)
        tree = ast.parse(path.read_text(encoding='utf-8-sig'))
        names = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                names.update(alias.name.split('.')[0] for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module and not node.level:
                names.add(node.module.split('.')[0])
            elif isinstance(node, ast.Constant) and isinstance(node.value, str):
                for relative in re.findall(r'(?:tools|bridge)/[\w.-]+\.py', node.value):
                    candidate = root / relative
                    if candidate.is_file():
                        pending.append(candidate)
        for name in names:
            for folder in ('tools', 'bridge'):
                candidate = root / folder / f'{name}.py'
                if candidate.is_file():
                    pending.append(candidate)
    return sorted(seen)


def native_artifacts(root: Path) -> list[str]:
    result = ['owmc-local-hero-spawn-v1.dll']
    for module, prefix in (
        ('native_bootstrap_maps', 'owmc-session-bootstrap'),
        ('native_compositor_version', 'owmc-live-passthrough'),
        ('native_body_version', 'owmc-guest-body'),
        ('native_weapon_gate_version', 'owmc-weapon-gate'),
        ('native_emission_version', 'owmc-native-emission'),
    ):
        # Parse the constant, never import modules that can touch native state.
        tree = ast.parse((root / 'tools' / f'{module}.py').read_text(encoding='utf-8'))
        versions = [n.value.value for n in tree.body if isinstance(n, ast.Assign)
                    and any(isinstance(t, ast.Name) and t.id == 'VERSION' for t in n.targets)
                    and isinstance(n.value, ast.Constant) and type(n.value.value) is int]
        if len(versions) != 1:
            raise ValueError(f'无法确定构建版本：{module}')
        result.append(f'{prefix}-v{versions[0]}.dll')
    return result


def validate_guest(path: Path) -> None:
    with zipfile.ZipFile(path) as archive:
        meta = json.loads(archive.read('fabric.mod.json'))
        if meta.get('id') != 'owmcguest':
            raise ValueError('guest JAR 身份不匹配。')
        for name in archive.namelist():
            if PurePosixPath(name).is_absolute() or '..' in PurePosixPath(name).parts:
                raise ValueError('guest JAR 包含非法路径。')
            if name.lower().endswith(('.ogg', '.wav', '.png', '.jpg', '.owmesh', '.obj', '.glb', '.zip')):
                raise ValueError('guest JAR 含媒体/模型，需单独确认来源后才能打包。')


class Builder:
    def __init__(self, root: Path, destination: Path, version: str):
        self.root, self.destination, self.version = root.resolve(), destination.resolve(), version
        self.ow_directory=PackPaths(self.root).get('owExecutable').parent
        self.rows: dict[str, dict] = {}
        self.components: dict[str, dict] = {}

    def component(self, name: str, license: str, source: str, *, version: str = '') -> None:
        self.components[name] = dict(license=license, source=source, version=version)

    def copy(self, source: Path, relative: str, component: str, source_root: Path | None = None) -> None:
        if source.resolve().is_relative_to(self.ow_directory) and component!='game-client':
            raise ValueError('禁止从 OW 客户端安装目录打包文件：'+source.name)
        safe_source(source, source_root or self.root)
        target = local_path(self.destination, relative)
        if relative in self.rows or target.exists():
            raise ValueError(f'打包路径重复：{relative}')
        target.parent.mkdir(parents=True, exist_ok=True)
        before = source.stat()
        shutil.copyfile(source, target)
        shutil.copystat(source, target)
        after = source.stat()
        if (before.st_size, before.st_mtime_ns) != (after.st_size, after.st_mtime_ns):
            raise ValueError(f'复制期间源文件被更新，请重新构建：{source.name}')
        self.record(relative, component)

    def record(self, relative: str, component: str) -> None:
        path = local_path(self.destination, relative)
        self.rows[relative] = dict(path=relative, bytes=path.stat().st_size,
                                   sha256=sha256(path), component=component,
                                   license=self.components[component]['license'])

    def tree(self, source: Path, relative: str, component: str, *, exclude=()) -> None:
        for path in sorted(source.rglob('*')):
            parts = path.relative_to(source).parts
            if any(part in {'__pycache__', *exclude} for part in parts) or path.suffix in ('.pyc', '.pyo'):
                continue
            if path.is_symlink() or path.is_junction():
                raise ValueError(f'运行时包含链接：{path.name}')
            if path.is_file():
                self.copy(path, (PurePosixPath(relative) / path.relative_to(source).as_posix()).as_posix(), component, source)

    def python(self, source: Path) -> None:
        source = source.resolve()
        self.component('cpython', PYTHON_LICENSE, 'https://github.com/astral-sh/python-build-standalone',
                       version='3.13 (local preview input; provenance not release-approved)')
        for name in ('python.exe', 'pythonw.exe', 'python3.dll', 'python313.dll', 'LICENSE.txt'):
            self.copy(source / name, f'runtime/python/{name}', 'cpython', source)
        for name in ('vcruntime140.dll', 'vcruntime140_1.dll', 'BUILD'):
            if (source / name).is_file():
                self.copy(source / name, f'runtime/python/{name}', 'cpython', source)
        for folder in ('DLLs', 'Lib', 'tcl'):
            self.tree(source / folder, f'runtime/python/{folder}', 'cpython', exclude=('site-packages', 'test', 'tests', 'ensurepip', 'idlelib'))
        # Only named distributions, never the whole development venv or .pth files.
        for name, (license, url) in DEPENDENCIES.items():
            dist = metadata.distribution(name)
            self.component(name, license, url, version=dist.version)
            origin = Path(dist.locate_file('')).resolve()
            files = dist.files or []
            notices = [str(f) for f in files if any(w in str(f).lower() for w in ('license', 'copying', 'notice'))]
            if not notices:
                if name == 'dnspython' and dist.version == '2.9.0':
                    self.copy(self.root / 'tools/modpack/licenses/dnspython-2.9.0-LICENSE.txt',
                              'licenses/dnspython/LICENSE', name)
                else:
                    raise ValueError(f'Python 依赖缺少许可证文件：{name}')
            for item in files:
                relative = PurePosixPath(str(item).replace('\\', '/'))
                if relative.is_absolute() or '..' in relative.parts:
                    continue  # installed command scripts outside site-packages
                if '__pycache__' in relative.parts or relative.suffix in ('.pyc', '.pyo'):
                    continue
                if relative.suffix == '.pth':
                    raise ValueError('不允许隐式执行 .pth 文件。')
                if relative.suffix == '.pyd':
                    abi=re.search(r'\.cp([0-9]+)(?:t)?-',relative.name)
                    if abi and abi.group(1)!='313':continue
                self.copy(Path(dist.locate_file(item)), 'runtime/python/Lib/site-packages/' + relative.as_posix(), name, origin)
        # A developer's inherited PYTHONHOME/PYTHONPATH must never redirect the
        # portable interpreter back to the build machine. CPython's relative
        # DLL path file also disables registry/user-site discovery. Keep the
        # two project module roots available to every existing helper entry.
        portable_paths = self.destination / 'runtime/python/python313._pth'
        portable_paths.write_text('.\nLib\nDLLs\nLib/site-packages\n../../tools\n../../bridge\n../..\nimport site\n', encoding='utf-8')
        self.record('runtime/python/python313._pth', 'cpython')
        io_bootstrap = self.destination / 'runtime/python/Lib/sitecustomize.py'
        io_bootstrap.write_text('import sys\nsys.dont_write_bytecode = True\nfor name in ("stdin", "stdout", "stderr"):\n    stream = getattr(sys, name, None)\n    if stream is not None and hasattr(stream, "reconfigure"):\n        stream.reconfigure(encoding="utf-8", errors="backslashreplace")\n', encoding='utf-8')
        self.record('runtime/python/Lib/sitecustomize.py', 'owmc')

    def java(self, source: Path) -> None:
        if not (source / 'bin/java.exe').is_file() or not (source / 'lib/modules').is_file():
            raise ValueError('Java 运行时缺少 java.exe 或模块映像。')
        release = (source / 'release').read_text(encoding='utf-8')
        if not re.search(r'JAVA_VERSION="21\.', release):
            raise ValueError('需要带 legal/ 目录的 OpenJDK 21 运行时。')
        text = (source / 'legal/java.base/LICENSE').read_text(encoding='utf-8')
        exception = (source / 'legal/java.base/ADDITIONAL_LICENSE_INFO').read_text(encoding='utf-8')
        if ('gnu general public license' not in text.lower() or 'Version 2' not in text
                or 'Classpath Exception' not in exception):
            raise ValueError('Java 许可证不是预期的 GPLv2 + Classpath Exception。')
        self.component('openjdk', JAVA_LICENSE, 'https://openjdk.org/', version='21 (local preview input; source offer pending)')
        for folder in ('bin', 'conf', 'legal', 'lib'):
            self.tree(source / folder, f'runtime/java/{folder}', 'openjdk')
        self.copy(source / 'release', 'runtime/java/release', 'openjdk', source)

    def native(self, source: Path | None = None) -> dict:
        from modpack.runtime import pe_linkage
        source=source or self.root/'native-host/build'
        source=source if source.is_absolute() else self.root/source
        # Resolve versions from the Python files actually copied into the pack.
        names=native_artifacts(self.destination)
        result=[]
        for name in names:
            relative='native-host/build/'+name
            self.copy(source/name,relative,'owmc',source)
            pe_linkage(self.destination/relative)
            image=(self.destination/relative).read_bytes();pe=int.from_bytes(image[0x3c:0x40],'little')
            if not int.from_bytes(image[pe+22:pe+24],'little')&0x2000:raise ValueError('原生产物必须是 x64 DLL：'+name)
            result.append({key:self.rows[relative][key] for key in ('path','bytes','sha256')})
        return dict(files=result,selection='exact versions referenced by bundled Python',sourceBuild='local build directory')

    def player_documents(self) -> None:
        self.copy(self.root/'tools/modpack/README.template.md','README.md','owmc')
        self.copy(self.root/'docs/PLAYER-README.md','docs/PLAYER-README.md','owmc')

    def setup_receipt(self, *, minecraft: bool, client: dict | None, python: bool, java: bool) -> None:
        ready=minecraft and bool(client) and python and java
        value=dict(schemaVersion=1,configured=ready,minecraftInstalled=minecraft,worldName='Overwatch World',
                   worldCreated=False,gameLaunched=False,integritySource='manifest.json',
                   runtimeIncluded=dict(python=python,java=java))
        if client:value['ow']=dict(path=client['executable'],sha256=client['sha256'],verified=True)
        write_json(self.destination/'config/setup-state.json',value);self.record('config/setup-state.json','owmc')

    def minecraft(self) -> dict:
        """Copy only the fixed local Fabric install, without downloads or natives/cache."""
        from modpack.config import read_json
        from modpack.install import MC,PROFILE,LOADER,_windows_library
        game=PackPaths(self.root).get('minecraft')
        base_path=f'versions/{MC}/{MC}.json';fabric_path=f'versions/{PROFILE}/{PROFILE}.json'
        base=read_json(local_path(game,base_path));fabric=read_json(local_path(game,fabric_path))
        if base.get('id')!=MC or fabric.get('id')!=PROFILE or fabric.get('inheritsFrom')!=MC:
            raise ValueError('本地 MC/Fabric 版本不匹配。')
        plan={base_path:None,fabric_path:None}
        def add(relative, artifact):
            parts=PurePosixPath(relative).parts
            if (not parts or parts[0] not in ('versions','assets','libraries') or '\\' in relative
                    or PurePosixPath(relative).is_absolute() or '..' in parts or ':' in relative):
                raise ValueError('MC 元数据文件路径无效。')
            digest=artifact.get('sha1')
            if digest and not re.fullmatch('[0-9a-f]{40}',digest):raise ValueError('本地 MC 元数据 SHA1 无效。')
            plan[relative]=dict(sha1=digest,size=artifact.get('size'))
        add(f'versions/{MC}/{MC}.jar',base['downloads']['client'])
        # launcher-lib resolves the merged profile's id as the client JAR.
        # Fabric's local installation keeps this byte-identical base-client alias.
        jar_version=fabric.get('jar',PROFILE)
        if jar_version not in (MC,PROFILE):raise ValueError('Fabric 客户端 JAR 指向未知版本。')
        if jar_version==PROFILE:add(f'versions/{PROFILE}/{PROFILE}.jar',base['downloads']['client'])
        index=base['assetIndex'];index_path=f'assets/indexes/{index["id"]}.json'
        add(index_path,index)
        for item in read_json(local_path(game,index_path))['objects'].values():
            digest=item['hash']
            if not re.fullmatch('[0-9a-f]{40}',digest):raise ValueError('MC 资源对象标识无效。')
            add(f'assets/objects/{digest[:2]}/{digest}',dict(sha1=digest,size=item['size']))
        for item in base.get('libraries',[]):
            if not _windows_library(item):continue
            downloads=item.get('downloads',{})
            if 'artifact' in downloads:add('libraries/'+downloads['artifact']['path'],downloads['artifact'])
            native=item.get('natives',{}).get('windows')
            if native:
                artifact=downloads['classifiers'][native.replace('${arch}','64')]
                add('libraries/'+artifact['path'],artifact)
        for item in fabric.get('libraries',[]):
            coordinate=item['name'].split(':')
            if len(coordinate)!=3:raise ValueError('不支持的 Fabric 库坐标。')
            group,name,version=coordinate
            artifact=item.get('downloads',{}).get('artifact',{})
            relative=artifact.get('path','/'.join((group.replace('.','/'),name,version,f'{name}-{version}.jar')))
            add('libraries/'+relative,artifact)
        logging=base.get('logging',{}).get('client',{}).get('file')
        if logging:add('assets/log_configs/'+logging['id'],logging)
        self.component('minecraft-local','LicenseRef-Minecraft-Proprietary AND Apache-2.0',
            'Existing local Minecraft/Fabric files; Mojang SHA1 where present; Fabric locally hashed, no downloads',version=MC+'/'+LOADER)
        rows=[]
        for relative,expected in sorted(plan.items()):
            source=local_path(game,relative);safe_source(source,game)
            if expected:
                if expected['size'] is not None and source.stat().st_size!=expected['size']:
                    raise ValueError('MC 文件大小不匹配：'+relative)
                if expected['sha1']:
                    with source.open('rb') as stream:digest=hashlib.file_digest(stream,'sha1').hexdigest()
                    if digest!=expected['sha1']:raise ValueError('MC 文件元数据 SHA1 不匹配：'+relative)
            self.copy(source,'minecraft-1.21.1/'+relative,'minecraft-local',game)
            row=self.rows['minecraft-1.21.1/'+relative]
            rows.append(dict(path=relative,bytes=row['bytes'],sha256=row['sha256'],
                             **({'officialSha1':expected['sha1']} if expected and expected['sha1'] else {})))
        write_json(self.destination/'config/installation-sha256.json',dict(schemaVersion=1,minecraft=MC,
            fabricLoader=LOADER,files=rows,integrity='local-files-sha256; Mojang metadata SHA1 where available; Fabric upstream provenance not reauthenticated',gameLaunched=False))
        self.record('config/installation-sha256.json','owmc')
        return dict(minecraft=MC,fabricLoader=LOADER,files=len(rows),downloadsPerformed=False)

    def profile(self) -> dict:
        """Fresh settings + exact current mods, excluding every personal profile file."""
        from configure_passthrough import factory_options,factory_settings
        from modpack.config import read_json
        source=PackPaths(self.root).get('profile');mods=[];identities=set()
        for path in sorted((source/'mods').glob('*.jar')):
            safe_source(path,source)
            with zipfile.ZipFile(path) as archive:meta=json.loads(archive.read('fabric.mod.json'))
            identity=meta.get('id');version=meta.get('version')
            if not isinstance(identity,str) or not re.fullmatch('[a-z][a-z0-9_-]*',identity) or identity in identities or not isinstance(version,str):
                raise ValueError('当前模组身份重复或无效：'+path.name)
            identities.add(identity)
            if identity=='owmcguest':
                installed_sha=sha256(path)
                staged=self.destination/'guest/build/libs/owmc-guest-0.1.0.jar'
                path=staged if staged.is_file() else self.root/'guest/build/libs/owmc-guest-0.1.0.jar'
                validate_guest(path)
                with zipfile.ZipFile(path) as archive:meta=json.loads(archive.read('fabric.mod.json'))
                version=meta['version']
                component='owmc'
            else:
                license=meta.get('license') or 'LicenseRef-Local-Mod-License-Unspecified'
                if isinstance(license,list):license=' AND '.join(license)
                component='mc-mod-'+identity
                self.component(component,license,'Current local Fabric profile; original JAR retained',version=version)
            relative=PROFILE_DIRECTORY+'/mods/'+path.name
            self.copy(path,relative,component,self.destination if path.is_relative_to(self.destination) else self.root if identity=='owmcguest' else source)
            mods.append(dict(file=path.name,id=identity,version=version,sha256=self.rows[relative]['sha256'],
                             license=self.components[component]['license']))
            if identity=='owmcguest':mods[-1].update(source='rebuilt-guest',installedSha256=installed_sha)
        required={'owmcguest','fabric-api','laowu_meme','sodium','owo','aether','twilightforest'}
        if not required<=identities:raise ValueError('完整档案缺少当前功能模组：'+', '.join(sorted(required-identities)))
        # Do not copy options, config, saves, hardware fingerprints or Fabric caches.
        generated={
            PROFILE_DIRECTORY+'/options.txt':factory_options(),
            PROFILE_DIRECTORY+'/config/iris.properties':'enableShaders=false\nshaderPack=\nmaxShadowRenderDistance=8\n',
            PROFILE_DIRECTORY+'/config/cumulus_menus-client.toml':'[Gui]\n"Enables random trivia" = false\n[Menu]\n"Enable Menu API" = false\n"Enables menu selection button" = false\n["World Preview"]\n"Enables world preview" = false\n"Enables toggle world button" = false\n"Enables quick load button" = false\n',
            PROFILE_DIRECTORY+'/config/twilightforest-client.toml':'disableOptifineNagScreen = true\ngiantSkinUUIDs = []\n',
        }
        for relative,text in generated.items():
            target=local_path(self.destination,relative);target.parent.mkdir(parents=True,exist_ok=True)
            target.write_text(text,encoding='utf-8');self.record(relative,'owmc')
        write_json(self.destination/'passthrough-settings.json',factory_settings());self.record('passthrough-settings.json','owmc')
        write_json(self.destination/PROFILE_DIRECTORY/'owmc-mods.json',dict(schemaVersion=1,loader='fabric',mods=mods))
        self.record(PROFILE_DIRECTORY+'/owmc-mods.json','owmc')
        write_json(self.destination/PROFILE_DIRECTORY/'owmc-boss-mods.json',mods)
        self.record(PROFILE_DIRECTORY+'/owmc-boss-mods.json','owmc')
        configuration=read_json(self.destination/'config/launcher.json') if (self.destination/'config/launcher.json').is_file() else dict(schemaVersion=1)
        configuration.setdefault('account',dict(mode='development-offline'))
        configuration['rendererPolicy']='required-sodium'
        configuration.setdefault('paths',{}).update(profile=PROFILE_DIRECTORY,minecraft='minecraft-1.21.1')
        write_json(self.destination/'config/launcher.json',configuration);self.record('config/launcher.json','owmc')
        return dict(directory=PROFILE_DIRECTORY,mods=mods,personalFilesCopied=False,worldCreated=False,
                    worldCreation='first normal guest launch',worldName='Overwatch World',worldSeed=20261014)

    def stage(self, python_source: Path | None, java_source: Path | None, include_api: bool, *, include_private: bool = True, include_client: bool | None = None, native_source: Path | None = None, startup_template: Path | None = None, defer_startup_template: bool = False) -> dict:
        if include_client is None:include_client=include_private
        if include_client and not include_private:
            raise ValueError('--public 不能包含客户端。')
        if startup_template is not None and not include_private:raise ValueError('Startup terrain requires the complete local bundle')
        if defer_startup_template and startup_template is None:raise ValueError('Deferred startup terrain requires a template')
        if self.destination.exists():
            raise FileExistsError('输出目录已存在；请使用新版本号。不会覆盖或删除现有目录。')
        self.destination.mkdir(parents=True)
        (self.destination/'game').mkdir()
        self.component('owmc', INTERNAL, 'Project-authored source and build outputs; public license not selected')
        # Mark the directory before copying anything. A partial build must
        # never be mistaken for a development checkout by the launch entry.
        distribution='fan-content-preview' if include_private else 'internal-preview'
        write_json(self.destination / 'modpack.json', dict(schemaVersion=1, version=self.version,
                   distribution=distribution, includesPrivate=include_private,
                   includesClient=include_client,
                   includesMinecraft=include_private,includesProfile=include_private,
                   backendIntegration='configured-paths-unverified', gameFilesIncluded=include_client or include_private))
        self.record('modpack.json', 'owmc')
        for source in source_closure(self.root):
            self.copy(source, source.relative_to(self.root).as_posix(), 'owmc')
        for name in ('assets/launcher/owmc.ico', 'assets/launcher/owmc.png', 'docs/MODPACK.md',
                     'tools/requirements-dev.txt', 'tools/open_project_launcher.ps1', 'launchers/Launch-Overwatch-Minecraft.cmd', 'ow x mc 启动器.exe',
                     'tools/modpack/launcher.example.json'):
            self.copy(self.root / name, name, 'owmc')
        guest = self.root / 'guest/build/libs/owmc-guest-0.1.0.jar'
        validate_guest(guest)
        self.copy(guest, guest.relative_to(self.root).as_posix(), 'owmc')
        native_summary=self.native(native_source)
        if include_api or include_private:
            self.fabric_api()
        if python_source:
            self.python(python_source)
        if java_source:
            self.java(java_source)
        minecraft_summary=self.minecraft() if include_private else None
        private_summary=None
        if include_private:
            from modpack.private_assets import PrivateBundle
            private_summary=PrivateBundle(self,PackPaths(self.root)).stage()
            write_json(self.destination/'config/launcher.json',dict(schemaVersion=1,
                account={'mode':'development-offline'},rendererPolicy='optional-sodium',paths=dict(
                    privateAssets='private-assets',meshAssets='private-assets/owmc-mesh',
                    heroVoiceAssets='private-assets/ow1-zhcn-2016/thnu-full',ffmpeg='tools/ffmpeg/ffmpeg.exe')))
            self.record('config/launcher.json','owmc')
        profile_summary=self.profile() if include_private else None
        if include_private:
            from modpack.private_assets import prebuild_profile_resources
            profile_summary.update(prebuild_profile_resources(self))
            if startup_template is not None:
                from modpack.startup_template import stage as stage_startup_template
                profile_summary.update(stage_startup_template(self,startup_template,expand=not defer_startup_template))
        client_summary=None
        if include_client:
            from modpack.game_client import stage as stage_client
            from modpack.config import read_json
            client_summary=stage_client(self,PackPaths(self.root))
            configuration=read_json(self.destination/'config/launcher.json') if (self.destination/'config/launcher.json').is_file() else dict(schemaVersion=1)
            configuration.setdefault('paths',{})['owExecutable']=client_summary['executable']
            write_json(self.destination/'config/launcher.json',configuration)
            self.record('config/launcher.json','owmc')
        self.setup_receipt(minecraft=bool(minecraft_summary),client=client_summary,python=bool(python_source),java=bool(java_source))
        self.player_documents()
        manifest = dict(schemaVersion=1, version=self.version, distribution=distribution, includesPrivate=include_private,includesClient=include_client,
                        includesMinecraft=include_private,includesProfile=include_private,
                        files=sorted(self.rows.values(), key=lambda row: row['path']),
                        components=self.components,
                        manifestSelfExcluded=True,
                        privateSummary=private_summary,
                        clientSummary=client_summary,
                        nativeSummary=native_summary,
                        minecraftSummary=minecraft_summary,profileSummary=profile_summary,
                        releaseBlockers=['项目代码/图标尚未选定发布许可证', 'Python 完整构建来源和第三方许可需发布审计',
                                         'OpenJDK/FFmpeg 对应源码提供方案尚未记录', '外部 MC 账号提供方未接入；搬迁与资源降级的实际启动待沙盒外验收',
                                          *(['完整 OW 客户端仅为用户已有安装的本地副本；再分发授权未核实'] if include_client else []),
                                         *(['暴雪资产再分发授权未核实；声明不等于版权许可'] if include_private else [])])
        write_json(self.destination / 'manifest.json', manifest)
        try:
            if include_client and java_source:
                from modpack.runtime import native_runtime
                manifest['nativeRuntimeSummary']=native_runtime(PackPaths(self.destination))
                write_json(self.destination/'manifest.json',manifest)
            verify_manifest(self.destination)
        except Exception:
            (self.destination / 'manifest.json').replace(self.destination / 'manifest.failed.json')
            raise
        return manifest

    def fabric_api(self) -> None:
        source = self.root / 'guest-passthrough-client/mods/fabric-api-0.116.17+1.21.1.jar'
        self.component('fabric-api', 'Apache-2.0', 'https://github.com/FabricMC/fabric/tree/1.21.1', version='0.116.17+1.21.1')
        with zipfile.ZipFile(source) as archive:
            value = json.loads(archive.read('fabric.mod.json'))
            if value.get('id') != 'fabric-api' or value.get('version') != '0.116.17+1.21.1' or value.get('license') != 'Apache-2.0':
                raise ValueError('Fabric API 元数据与打包白名单不匹配。')
            license = archive.read('LICENSE-fabric-api')
        self.copy(source, 'minecraft-1.21.1/mods/' + source.name, 'fabric-api')
        target = self.destination / 'licenses/fabric-api/LICENSE'
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(license)
        self.record('licenses/fabric-api/LICENSE', 'fabric-api')


def verify_manifest(root: Path) -> dict:
    root = root.resolve()
    manifest = json.loads((root / 'manifest.json').read_text(encoding='utf-8'))
    marker=json.loads((root/'modpack.json').read_text(encoding='utf-8')) if (root/'modpack.json').is_file() else {}
    allow_private=(manifest.get('includesPrivate') is True
                   and manifest.get('distribution')=='fan-content-preview' and marker.get('includesPrivate') is True)
    allow_client=(manifest.get('includesClient') is True and marker.get('includesClient') is True
                  and allow_private
                  and manifest.get('components',{}).get('game-client',{}).get('license')==CLIENT_LICENSE)
    allow_profile=allow_private and manifest.get('includesProfile') is True and marker.get('includesProfile') is True
    allow_minecraft=allow_private and manifest.get('includesMinecraft') is True and marker.get('includesMinecraft') is True
    installation_rows={}
    startup_rows={}
    profile_summary=manifest.get('profileSummary') or {}
    if allow_profile and profile_summary.get('startupTemplate'):
        from modpack.startup_template import checked,METADATA,PAYLOAD,WORLD
        metadata=json.loads((root/METADATA).read_text(encoding='utf-8'))
        rows=checked(metadata,root/PAYLOAD)
        if metadata.get('mods')!={row['file']:row['sha256'] for row in profile_summary['mods']}:
            raise ValueError('启动模板与整合包模组 SHA256 不一致。')
        if profile_summary.get('startupTemplateExpanded',True):
            for entry in rows:
                name=entry['path']
                relative=(PROFILE_DIRECTORY+'/saves/'+WORLD+'/'+name[len('world/'):]) if name.startswith('world/') else PROFILE_DIRECTORY+'/'+name[len('cache/'):]
                startup_rows[relative]=entry
    if allow_minecraft:
        lock=json.loads((root/'config/installation-sha256.json').read_text(encoding='utf-8'))
        if lock.get('minecraft')!='1.21.1' or lock.get('fabricLoader')!='0.19.5':raise ValueError('整合包 MC/Fabric 安装清单版本不匹配。')
        installation_rows={row['path']:row for row in lock['files']}
        if not installation_rows or len(installation_rows)!=len(lock['files']):raise ValueError('MC 安装清单为空或重复。')
    listed = set()
    total = 0
    private_count=0
    for row in manifest['files']:
        name = row['path']
        path = local_path(root, name)
        parts = PurePosixPath(name).parts
        private=row.get('component')=='private'
        profile_private=row.get('component')=='profile-private'
        client=row.get('component')=='game-client'
        if client and (not allow_client or row.get('license')!=CLIENT_LICENSE or not name.startswith('game/Overwatch Beta 0.8.0.24919/')):
            raise ValueError('客户端仅允许在明确标记的本地完整副本中出现：'+name)
        if private:
            if (not allow_private or row.get('license')!=PRIVATE_LICENSE
                    or manifest['components'].get('private',{}).get('license')!=PRIVATE_LICENSE
                    or not (name.startswith('private-assets/') or name.startswith('tools/ffmpeg/'))):
                raise ValueError('私有资源仅允许存在于已明确标记的带资源包：'+name)
            if name.startswith('private-assets/') and path.suffix.lower() not in ('.json','.png','.ogg','.mp3'):
                raise ValueError('私有包包含非运行资源：'+name)
            private_count+=1
        if profile_private:
            if (not allow_profile or row.get('license')!=PRIVATE_LICENSE
                    or manifest['components'].get('profile-private',{}).get('license')!=PRIVATE_LICENSE
                    or not name.startswith(PROFILE_DIRECTORY+'/resourcepacks/')
                    or path.suffix.lower() not in ('.json','.ogg','.mcmeta','')):
                raise ValueError('预制私有资源包仅允许在完整包的干净档案中出现：'+name)
            private_count+=1
        if name.startswith('private-assets/') and not private:
            raise ValueError('私有目录必须使用 private 组件标记。')
        if name.startswith('game/') and not client:
            raise ValueError('客户端目录必须使用 game-client 组件标记。')
        if row.get('component')=='minecraft-local' and not name.startswith('minecraft-1.21.1/'):
            raise ValueError('MC 本地组件不能写到安装目录之外。')
        if (row.get('component')=='ffmpeg' or name.startswith('tools/ffmpeg/')) and not allow_private:
            raise ValueError('公开精简包不能包含 ffmpeg。')
        owned_startup=row.get('component')=='startup-template' and name in startup_rows
        if owned_startup and any(row[k]!=startup_rows[name][k] for k in ('bytes','sha256')):
            raise ValueError('预生成世界/缓存与已审查模板不一致。')
        forbidden=FORBIDDEN_PARTS-({'game'} if client else {'private-assets'} if private else {'resourcepacks'} if profile_private else {'saves'} if owned_startup else set())
        forbidden_suffixes=('.lnk','.log','.env') if client else ('.lnk','.log','.env','.owmesh') if private or profile_private else ('.lnk','.log','.env','.owmesh','.ogg','.wav')
        if (name in listed or any(part in forbidden for part in parts)
                or path.name.lower() in ('.env', 'development-identity.json', 'launcher_accounts.json','accounts.json','credentials.json')
                or (not client and (path.name.lower() in ('inject.dll','prometheus.pdb')
                    or (path.name.casefold().startswith('gameclientapp') and path.suffix.casefold()=='.exe') or row['sha256']==OW_SHA256))
                or path.suffix.lower() in forbidden_suffixes):
            raise ValueError(f'清单包含重复或私有文件：{name}')
        safe_source(path, root)
        if path.stat().st_size != row['bytes'] or sha256(path) != row['sha256']:
            raise ValueError(f'文件完整性校验失败：{name}')
        if not row.get('license') or row['component'] not in manifest['components']:
            raise ValueError(f'清单缺少许可证：{name}')
        if path.suffix.lower() in ('.py', '.json', '.ps1', '.cmd', '.md', '.txt') and SECRET.search(path.read_bytes()):
            raise ValueError(f'检测到疑似密钥：{name}')
        # Full local bundles require a separately locked MC component. Public
        # previews retain the original API-only rule; personal files stay banned.
        if parts[0] == 'minecraft-1.21.1' and name != 'minecraft-1.21.1/mods/fabric-api-0.116.17+1.21.1.jar':
            expected=installation_rows.get('/'.join(parts[1:]))
            if (not allow_minecraft or row.get('component')!='minecraft-local' or not expected
                    or expected.get('sha256')!=row['sha256'] or expected.get('bytes')!=row['bytes']):
                raise ValueError(f'MC 文件没有完整本地包标记或安装清单：{name}')
        listed.add(name)
        total += row['bytes']
    actual = {p.relative_to(root).as_posix() for p in root.rglob('*') if p.is_file()}
    if actual != listed | {'manifest.json'}:
        raise ValueError('实际文件与清单不一致，可能混入未审核文件。')
    if startup_rows:
        actual_startup={r['path'] for r in manifest['files'] if r.get('component')=='startup-template' and r['path'].startswith(PROFILE_DIRECTORY+'/')}
        if actual_startup!=startup_rows.keys():raise ValueError('预生成世界/缓存的出厂清单不完整。')
    native=manifest.get('nativeSummary')
    if native:
        expected={'native-host/build/'+name for name in native_artifacts(root)}
        snapshots={row['path']:row for row in native['files']}
        rows={row['path']:row for row in manifest['files'] if row['path'].startswith('native-host/build/') and row['path'].endswith('.dll')}
        if set(snapshots)!=expected or set(rows)!=expected or len(snapshots)!=len(native['files']):raise ValueError('原生 DLL 快照与包内版本常量不一致。')
        if any(any(rows[name][key]!=snapshots[name][key] for key in ('bytes','sha256')) for name in rows):raise ValueError('原生 DLL 快照哈希不一致。')
    if allow_minecraft:
        expected={'minecraft-1.21.1/'+name for name in installation_rows}
        actual_install={row['path'] for row in manifest['files'] if row.get('component')=='minecraft-local'}
        if expected!=actual_install:raise ValueError('MC 安装锁与出厂清单不一致。')
    if allow_profile:
        mods=(manifest.get('profileSummary') or {}).get('mods',[])
        if not mods:raise ValueError('完整档案没有模组清单。')
        expected={PROFILE_DIRECTORY+'/mods/'+row['file']:row['sha256'] for row in mods}
        actual_mods={row['path']:row['sha256'] for row in manifest['files'] if row['path'].startswith(PROFILE_DIRECTORY+'/mods/')}
        if expected!=actual_mods:raise ValueError('档案模组与出厂清单不一致。')
    if allow_client:
        summary=manifest.get('clientSummary') or {}
        executable=local_path(root,summary.get('executable','game/missing.exe'))
        row=next((r for r in manifest['files'] if r['path']==summary.get('executable')),None)
        if (not row or row.get('component')!='game-client' or row.get('sha256')!=OW_SHA256
                or summary.get('sha256')!=OW_SHA256 or sha256(executable)!=OW_SHA256):
            raise ValueError('包内 OW 主程序不在精确 SHA256 白名单内。')
    return dict(files=len(listed), bytes=total, privateFiles=private_count,clientFiles=sum(r.get('component')=='game-client' for r in manifest['files']), manifestVerified=True)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--version', default='1.0.0')
    parser.add_argument('--output', help='New workspace-relative destination; existing output is never overwritten')
    parser.add_argument('--native-build-dir', type=Path, help='Completed rebuilt DLL directory; only the six versions referenced by bundled Python are used')
    parser.add_argument('--startup-template', type=Path, help='Explicit new player-free world/Fabric inputs generated under data/; never a developer profile')
    parser.add_argument('--defer-startup-template', action='store_true', help='Keep the pinned template archived until first launch')
    parser.add_argument('--python-runtime', type=Path, help='Existing clean Python 3.13 + Tk root; never a venv')
    parser.add_argument('--java-runtime', type=Path, help='Existing OpenJDK 21 root, with legal/')
    parser.add_argument('--include-fabric-api', action='store_true')
    parser.add_argument('--without-client',action='store_true',help='不复制本地 OW 客户端；--public 也会排除客户端')
    resource_mode=parser.add_mutually_exclusive_group()
    resource_mode.add_argument('--include-private',dest='include_private',action='store_true',help='默认：裁剪私有语音/模型并携带 ffmpeg')
    resource_mode.add_argument('--public',dest='include_private',action='store_false',help='不含私有语音、模型、ffmpeg 或 OW 客户端的精简包')
    parser.set_defaults(include_private=True)
    parser.add_argument('--verify', type=Path, help='Read-only verification of an existing pack')
    args = parser.parse_args()
    if args.verify:
        print(json.dumps(verify_manifest(args.verify), ensure_ascii=False))
        return 0
    if not re.fullmatch(r'[0-9][0-9A-Za-z.-]{0,63}', args.version):
        parser.error('版本号只能含数字、英文字母、点或连字符。')
    destination = local_path(ROOT, args.output or 'dist/OWMC-' + args.version)
    try:
        manifest = Builder(ROOT, destination, args.version).stage(args.python_runtime, args.java_runtime, args.include_fabric_api,include_private=args.include_private,
                    include_client=args.include_private and not args.without_client,native_source=args.native_build_dir,startup_template=args.startup_template,
                    defer_startup_template=args.defer_startup_template)
    except Exception:
        # Leave partial output intact for diagnosis; the entry requires a
        # completed manifest before opening a packaged launcher.
        raise
    print(json.dumps(dict(output=str(destination.relative_to(ROOT)), files=len(manifest['files']),
                          privateFiles=sum(r['component'] in ('private','profile-private') for r in manifest['files']), distribution=manifest['distribution']), ensure_ascii=False))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
