"""Prepare an isolated, relocated acceptance copy. Never starts/stops games.

This copies only the clean preview into data/, backs up the existing profile in
ignored research/, then clones a test profile without private resource packs.
The explicit development flag preserves the existing offline research scope;
it is not an account login.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import shutil
import sys
import uuid
import zipfile

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from modpack.build import verify_manifest
from modpack.config import PackPaths, read_json, write_json
from modpack.first_run import verify_ow


def prepare(package: Path, reference: Path, output: Path, *, development_offline=False, without_sodium=False, bundled_private=False, backend=None) -> dict:
    if not development_offline:
        raise ValueError('此工具仅为已有离线研究环境准备实测副本，请明确传入 --development-offline。')
    package, reference, output = package.resolve(), reference.resolve(), output.resolve()
    data = (reference/'data').resolve()
    if output == data or not output.is_relative_to(data) or output.exists():
        raise ValueError('实测目录必须是参考工作区 data/ 下尚不存在的新子目录；不会覆盖或删除。')
    verified=verify_manifest(package)
    if bundled_private and not verified['privateFiles']:
        raise ValueError('--bundled-private 需要已审计的私有包。')
    configured = PackPaths(reference)
    verify_ow(configured.get('owExecutable'))
    if backend is None:
        from project_launcher import SessionBackend
        backend = SessionBackend(reference)
    if backend.supervisors() or backend.project_processes():
        raise ValueError('参考会话仍在运行；请先使用正常关闭流程保存并退出，再准备隔离副本。')
    source_profile = configured.get('profile')
    if not source_profile.is_dir():
        raise ValueError('参考 profile 不存在，未创建实测副本。')
    settings_file = reference/'passthrough-settings.json'
    settings = read_json(settings_file)
    backup = reference/'research/modpack-task-B2/claude-backups'/uuid.uuid4().hex
    backup.mkdir(parents=True, exist_ok=False)
    # Keep the original, complete profile backup outside the distribution tree.
    # Never follow linked folders or read launcher account stores.
    omitted = {'.env','launcher_accounts.json','accounts.json','credentials.json'}
    with zipfile.ZipFile(backup/'profile.zip','x',zipfile.ZIP_DEFLATED) as archive:
        for path in sorted(source_profile.rglob('*')):
            if path.is_symlink() or path.is_junction():
                raise ValueError('档案包含链接，请先人工核对；未跟随链接备份。')
            if path.is_file() and path.name not in omitted:
                archive.write(path,path.relative_to(source_profile).as_posix())
    shutil.copyfile(settings_file,backup/'passthrough-settings.json')
    output.parent.mkdir(parents=True,exist_ok=True)
    shutil.copytree(package,output)
    profile = output/'data/profile'
    from render_optimization import NAME as sodium_name
    excluded=['resourcepacks','logs','crash-reports','screenshots','session.lock',*omitted]
    if without_sodium:excluded.append(sodium_name)
    shutil.copytree(source_profile,profile,ignore=shutil.ignore_patterns(*excluded))
    options = profile/'options.txt'
    if options.is_file():
        lines=[line for line in options.read_text(encoding='utf-8').splitlines()
               if not line.startswith(('resourcePacks:','incompatibleResourcePacks:'))]
        options.write_text('\n'.join(lines+['resourcePacks:[]','incompatibleResourcePacks:[]'])+'\n',encoding='utf-8')
    private='private-assets' if bundled_private else 'data/absent-private-assets'
    factory=read_json(package/'manifest.json')
    client=(factory.get('clientSummary') or {}).get('executable') if verified.get('clientFiles') else None
    if client:
        verify_ow(output/client)
    write_json(output/'config/launcher.json',dict(schemaVersion=1,
        account={'mode':'development-offline'},rendererPolicy='optional-sodium' if without_sodium else 'required-sodium',
        paths=dict(owExecutable=client or str(configured.get('owExecutable')),minecraft=str(configured.get('minecraft')),
                   python='runtime/python/python.exe',java='runtime/java/bin/java.exe',profile='data/profile',
                   privateAssets=private,meshAssets=private+'/owmc-mesh',
                   heroVoiceAssets=private+'/ow1-zhcn-2016/thnu-full',ffmpeg='tools/ffmpeg/ffmpeg.exe')))
    write_json(output/'passthrough-settings.json',settings)
    result=dict(root=str(output),backup=str(backup),profile=str(profile),
                privateResourcesOmitted=not bundled_private,bundledPrivateAssetsUsed=bundled_private,
                bundledClientUsed=bool(client),
                sodiumOmitted=without_sodium,gameStarted=False,originalProfileModified=False)
    write_json(backup/'lab.json',result)
    return result


def main() -> int:
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--package',type=Path,required=True)
    parser.add_argument('--reference',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--development-offline',action='store_true')
    parser.add_argument('--without-sodium',action='store_true',help='Omit the exact pinned Sodium from the new copy only; delete nothing')
    parser.add_argument('--bundled-private',action='store_true',help='Use the audited private-assets in the local bundle; a bundled client is always preferred')
    args=parser.parse_args()
    print(json.dumps(prepare(args.package,args.reference,args.output,development_offline=args.development_offline,without_sodium=args.without_sodium,bundled_private=args.bundled_private),
                     ensure_ascii=False,indent=2))
    return 0


if __name__=='__main__':
    raise SystemExit(main())
