"""Explicit first-run official installation, never called by checks or pack builds.

This module is exercised with offline fixtures in task B. No game download is
performed by the task. The UI requires a separate click to invoke installation.
Mojang publishes SHA1, not SHA256: authenticate against that official SHA1 first,
then retain a local SHA256 lock for subsequent checks; do not invent SHA256 pins.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import re
import shutil
import urllib.parse
import urllib.request

from .config import PackPaths, local_path, manifest_files, read_json, resolved_within, sha256, verify_files, write_json

MC = '1.21.1'
LOADER = '0.19.5'
PROFILE = f'fabric-loader-{LOADER}-{MC}'
VERSION_MANIFEST = 'https://piston-meta.mojang.com/mc/game/version_manifest_v2.json'
FABRIC_PROFILE = f'https://meta.fabricmc.net/v2/versions/loader/{MC}/{LOADER}/profile/json'
HOSTS = {'piston-meta.mojang.com', 'piston-data.mojang.com', 'launchermeta.mojang.com',
         'launcher.mojang.com', 'libraries.minecraft.net', 'resources.download.minecraft.net',
         'meta.fabricmc.net', 'maven.fabricmc.net'}


def official_url(value: str) -> str:
    url = urllib.parse.urlsplit(value)
    if url.scheme != 'https' or url.hostname not in HOSTS or url.username or url.password or url.port not in (None, 443):
        raise ValueError('下载元数据包含非官方来源，已停止。')
    return value


class _OfficialRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, request, fp, code, message, headers, newurl):
        return super().redirect_request(request, fp, code, message, headers, official_url(newurl))


def fetch(url: str, limit: int = 4 * 1024 * 1024) -> bytes:
    opener = urllib.request.build_opener(_OfficialRedirect())
    request = urllib.request.Request(official_url(url), headers={'User-Agent': 'OWMC-Setup/0.1'})
    with opener.open(request, timeout=30) as response:
        official_url(response.url)
        result = response.read(limit + 1)
    if len(result) > limit:
        raise ValueError('官方元数据超过大小上限。')
    return result


def official_json(url: str, expected_sha1: str | None = None) -> tuple[dict, bytes]:
    data = fetch(url)
    if expected_sha1 and hashlib.sha1(data).hexdigest() != expected_sha1:
        raise ValueError('官方元数据 SHA1 校验失败，未继续安装。')
    value = json.loads(data)
    if not isinstance(value, dict):
        raise ValueError('官方元数据格式错误。')
    return value, data


def download_plan() -> dict:
    return dict(schemaVersion=1, minecraft=MC, fabricLoader=LOADER,
                sources=[VERSION_MANIFEST, FABRIC_PROFILE, 'https://libraries.minecraft.net/',
                         'https://resources.download.minecraft.net/', 'https://maven.fabricmc.net/'],
                authentication='使用合法账号与官方来源；本向导不登录、不提供账号凭据。',
                upstreamIntegrity='Official HTTPS + SHA1 where provided; local SHA256 lock after verification',
                downloadsPerformed=False, worldCreated=False, gameLaunched=False)


def _windows_library(item: dict) -> bool:
    allowed = not item.get('rules')
    for rule in item.get('rules', []):
        os_rule = rule.get('os', {})
        if os_rule.get('name', 'windows') != 'windows' or os_rule.get('arch', 'x86_64') not in ('x86_64', 'amd64'):
            continue
        if rule.get('features') or os_rule.get('version'):
            # Do not guess special feature/version rules for this fixed release.
            continue
        allowed = rule.get('action') == 'allow'
    return allowed


def verify_official_files(game: Path, base: dict, fabric: dict) -> list[dict]:
    """Verify every required Windows artifact + all actual asset objects."""
    rows = {}
    def check(relative: str, digest: str, size: int | None = None):
        if not re.fullmatch('[0-9a-f]{40}', digest):
            raise ValueError('官方 SHA1 格式错误。')
        path = local_path(game, relative)
        if not path.is_file() or (size is not None and path.stat().st_size != size):
            raise ValueError(f'MC 文件缺少或大小错误：{relative}')
        with path.open('rb') as stream:
            actual = hashlib.file_digest(stream, 'sha1').hexdigest()
        if actual != digest:
            raise ValueError(f'MC 文件官方 SHA1 校验失败：{relative}')
        rows[relative] = dict(path=relative, bytes=path.stat().st_size, sha256=sha256(path), officialSha1=digest)
    client = base['downloads']['client']
    official_url(client['url'])
    check(f'versions/{MC}/{MC}.jar', client['sha1'], client['size'])
    client_id = fabric.get('jar', fabric.get('id', MC))
    if client_id not in (MC, PROFILE):
        raise ValueError('Fabric 客户端 JAR 指向未知版本。')
    if client_id == PROFILE:
        check(f'versions/{PROFILE}/{PROFILE}.jar', client['sha1'], client['size'])
    index = base['assetIndex']
    official_url(index['url'])
    index_path = f'assets/indexes/{index["id"]}.json'
    check(index_path, index['sha1'], index['size'])
    for item in read_json(local_path(game, index_path))['objects'].values():
        digest = item['hash']
        check(f'assets/objects/{digest[:2]}/{digest}', digest, item['size'])
    logging = base.get('logging', {}).get('client', {}).get('file')
    if logging:
        official_url(logging['url'])
        check('assets/log_configs/' + logging['id'], logging['sha1'], logging['size'])
    for item in base['libraries']:
        if not _windows_library(item):
            continue
        downloads = item.get('downloads', {})
        artifacts = [downloads['artifact']] if 'artifact' in downloads else []
        native = item.get('natives', {}).get('windows')
        if native:
            classifier = native.replace('${arch}', '64')
            artifacts.append(downloads['classifiers'][classifier])
        for artifact in artifacts:
            official_url(artifact['url'])
            check('libraries/' + artifact['path'], artifact['sha1'], artifact['size'])
    for item in fabric['libraries']:
        group, name, version = item['name'].split(':')
        relative = '/'.join((group.replace('.', '/'), name, version, f'{name}-{version}.jar'))
        url = official_url(item.get('url', 'https://libraries.minecraft.net/').rstrip('/') + '/' + relative)
        digest = (fetch(url + '.sha1', 256).decode('ascii').strip().split() or [''])[0]
        check('libraries/' + relative, digest)
    return sorted(rows.values(), key=lambda row: row['path'])


def install(root: Path, report=print) -> dict:
    """Download on explicit user action only; no account bypass or game process."""
    from minecraft_launcher_lib.install import install_minecraft_version
    from .first_run import environment, verify_ow
    if not environment(root, gpu=False)['ok']:
        raise ValueError('环境检查未通过，请先查看首次运行页。')
    game = PackPaths(root).get('minecraft')
    # Never repair or replace an existing player's tree without a verified lock.
    # The pack's sole pre-bundled MC subdirectory is mods/fabric-api-*.jar.
    if any((game / name).exists() for name in ('versions', 'assets', 'libraries', 'runtime')):
        raise ValueError('检测到已有或未完成的 MC 安装；请先使用“校验安装”或保留该目录后改用新解压目录。不会覆盖。')
    paths = PackPaths(root)
    if not paths.config_path.is_file():
        raise ValueError('请先在首次运行页校验 OW 并保存配置，再下载 MC/Fabric。')
    verify_ow(paths.get('owExecutable'))
    report('正在获取 Mojang 与 Fabric 官方元数据…')
    catalog, _ = official_json(VERSION_MANIFEST)
    version = next((v for v in catalog['versions'] if v.get('id') == MC), None)
    if version is None:
        raise ValueError('Mojang 版本目录中找不到 MC 1.21.1。')
    base, base_bytes = official_json(version['url'], version['sha1'])
    fabric, fabric_bytes = official_json(FABRIC_PROFILE)
    if base.get('id') != MC or fabric.get('inheritsFrom') != MC or fabric.get('id') != PROFILE:
        raise ValueError('官方版本身份与固定版本不符。')
    for item in fabric['libraries']:
        official_url(item.get('url', 'https://libraries.minecraft.net/'))
    for relative, data in ((f'versions/{MC}/{MC}.json', base_bytes),
                           (f'versions/{PROFILE}/{PROFILE}.json', fabric_bytes)):
        path = local_path(game, relative)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
    report('正在安装 MC 1.21.1 与 Fabric（不启动游戏）…')
    callback = {'setStatus': lambda _: None}
    install_minecraft_version(MC, game, callback=callback)
    install_minecraft_version(PROFILE, game, callback=callback)
    report('正在校验官方 SHA1 并保存本地 SHA256 清单…')
    rows = verify_official_files(game, base, fabric)
    for relative, data in ((f'versions/{MC}/{MC}.json', base_bytes),
                           (f'versions/{PROFILE}/{PROFILE}.json', fabric_bytes)):
        rows.append(dict(path=relative, bytes=len(data), sha256=hashlib.sha256(data).hexdigest()))
    # Own build output and the single reviewed API dependency are the only mods
    # copied. No existing user profile or private resource pack is traversed.
    profile = PackPaths(root).get('profile') / 'mods'
    profile.mkdir(parents=True, exist_ok=True)
    for source in [root / 'guest/build/libs/owmc-guest-0.1.0.jar',
                   game / 'mods/fabric-api-0.116.17+1.21.1.jar']:
        if not source.is_file():
            raise ValueError('整合包缺少 guest 或 Fabric API，请重新构建完整预览包。')
        destination = profile / source.name
        if destination.exists() and sha256(destination) != sha256(source):
            raise ValueError('现有模组与整合包不同，未覆盖。')
        if not destination.exists():
            shutil.copyfile(source, destination)
    result = dict(schemaVersion=1, minecraft=MC, fabricLoader=LOADER, files=rows,
                  integrity='official-https-and-sha1-then-local-sha256', gameLaunched=False)
    write_json(local_path(root, 'config/installation-sha256.json'), result)
    return dict(files=len(rows), gameLaunched=False,
                message='MC 文件已安装并校验；账号提供方与完整启动仍需沙盒外验收。')


def _required_minecraft_files(game: Path) -> set[Path]:
    """Walk the pinned local metadata, never Fabric's online .sha1 endpoints."""
    game = game.resolve()
    required = set()

    def need(relative: str) -> Path:
        path = local_path(game, relative, _resolved_root=True)
        if not path.is_file():
            raise ValueError(f'缺少 MC/Fabric 文件：{relative}，请重新解压完整包。')
        required.add(path)
        return path

    base = read_json(need(f'versions/{MC}/{MC}.json'))
    fabric = read_json(need(f'versions/{PROFILE}/{PROFILE}.json'))
    if base.get('id') != MC or fabric.get('id') != PROFILE or fabric.get('inheritsFrom') != MC:
        raise ValueError('包内 MC/Fabric 版本不匹配。')
    need(f'versions/{MC}/{MC}.jar')
    client_id = fabric.get('jar', PROFILE)
    if client_id not in (MC, PROFILE):
        raise ValueError('Fabric 客户端 JAR 指向未知版本。')
    if client_id == PROFILE:
        need(f'versions/{PROFILE}/{PROFILE}.jar')
    index = read_json(need(f'assets/indexes/{base["assetIndex"]["id"]}.json'))
    for item in index['objects'].values():
        digest = item['hash']
        if not isinstance(digest, str) or not re.fullmatch('[0-9a-f]{40}', digest):
            raise ValueError('包内 MC 资源索引格式错误。')
        need(f'assets/objects/{digest[:2]}/{digest}')
    for version in (base, fabric):
        for item in version['libraries']:
            if not _windows_library(item):
                continue
            downloads = item.get('downloads', {})
            artifact = downloads.get('artifact')
            if artifact:
                need('libraries/' + artifact['path'])
            elif version is fabric:
                coordinates = item['name'].split(':')
                if len(coordinates) not in (3, 4):
                    raise ValueError('包内 Fabric 库坐标格式错误。')
                group, name, release = coordinates[:3]
                classifier = '-' + coordinates[3] if len(coordinates) == 4 else ''
                need('/'.join(('libraries', group.replace('.', '/'), name, release,
                               f'{name}-{release}{classifier}.jar')))
            native = item.get('natives', {}).get('windows')
            if native:
                need('libraries/' + downloads['classifiers'][native.replace('${arch}', '64')]['path'])
    # Do not accept a fabricated Fabric profile that merely inherits vanilla.
    need(f'libraries/net/fabricmc/fabric-loader/{LOADER}/fabric-loader-{LOADER}.jar')
    logging = base.get('logging', {}).get('client', {}).get('file')
    if logging:
        need('assets/log_configs/' + logging['id'])
    return required


def verify_installation(root: Path, *, require_complete: bool = False, _inventory=None) -> dict:
    """Recognize a bundled installation or an explicit prior install, offline.

    The shipped manifest takes precedence over mutable setup-state/lock flags.
    Legacy locks remain usable for checking individual installed files; startup
    additionally requires the complete MC/Fabric dependency graph.
    """
    paths = PackPaths(root)
    game = paths.get('minecraft')
    rows = {}
    source = 'config/installation-sha256.json'
    if paths.packaged and local_path(root, 'manifest.json').is_file():
        inventory = manifest_files(root) if _inventory is None else _inventory
        bundled = {path: row for path, row in inventory.items() if resolved_within(path,game)}
        # Earlier minimal packs ship only mods/fabric-api. An explicit wizard
        # install adds its own verified lock; that is not a bundled MC tree.
        if any(path.relative_to(game).parts[0] in ('versions', 'assets', 'libraries') for path in bundled):
            rows = bundled
            source = 'manifest.json'
            require_complete = True
    if not rows:
        lock_path = local_path(root, source)
        if not lock_path.is_file():
            raise ValueError('缺少 MC/Fabric 的 SHA256 文件清单，请重新解压完整包或在排错页准备安装。')
        lock = read_json(lock_path)
        if lock.get('schemaVersion') != 1 or lock.get('minecraft') != MC or lock.get('fabricLoader') != LOADER:
            raise ValueError('安装清单版本不匹配。')
        entries = lock.get('files')
        if not isinstance(entries, list) or not entries:
            raise ValueError('安装清单为空，未确认安装完成。')
        for row in entries:
            if not isinstance(row, dict):
                raise ValueError('安装清单记录格式错误。')
            path = local_path(game, row.get('path', ''))
            size, digest = row.get('bytes'), row.get('sha256')
            if path in rows or type(size) is not int or size < 0 or not isinstance(digest, str) or not re.fullmatch('[0-9a-f]{64}', digest):
                raise ValueError('安装清单记录重复或 SHA256 格式错误。')
            rows[path] = row
    verify_files(rows)
    if require_complete:
        try:
            required = _required_minecraft_files(game)
        except (KeyError, TypeError, AttributeError) as error:
            raise ValueError('包内 MC/Fabric 元数据不完整，请重新解压完整包。') from error
        missing = required - rows.keys()
        if missing:
            first = sorted(missing)[0].relative_to(game).as_posix()
            raise ValueError(f'MC/Fabric 文件未列入 SHA256 清单：{first}')
    return dict(files=len(rows), installationVerified=True, gameLaunched=False,
                minecraftInstalled=True, source=source)
