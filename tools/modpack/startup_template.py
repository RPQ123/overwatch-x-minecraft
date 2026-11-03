"""Pinned, player-free default terrain and reproducible Fabric startup inputs."""
from __future__ import annotations
import hashlib
import gzip
import os
from pathlib import Path, PurePosixPath
import shutil
import stat
import uuid
import zipfile
from .config import PackPaths, local_path, manifest_files, read_json, sha256

METADATA='config/startup-template.json'
PAYLOAD='data/startup-template/payload.zip'
WORLD='Overwatch World'


def checked(metadata, archive):
    if (metadata.get('schemaVersion')!=1 or metadata.get('worldName')!=WORLD
            or metadata.get('worldSeed')!=20261014 or metadata.get('dataVersion')!=3955
            or metadata.get('playerDataRemoved') is not True):
        raise ValueError('Unsupported clean startup template')
    rows=metadata.get('files',[])
    names=[r['path'] for r in rows]
    if len(names)!=len(set(names)) or not 1<len(names)<4096:
        raise ValueError('Invalid startup template inventory')
    if 'world/level.dat' not in names:raise ValueError('Template has no real vanilla level.dat')
    total=0
    with zipfile.ZipFile(archive) as z:
        if set(z.namelist())!=set(names):raise ValueError('Startup template member inventory differs')
        for row in rows:
            name=row['path'];path=PurePosixPath(name)
            world=(len(path.parts)>1 and path.parts[0]=='world' and path.suffix in ('.dat','.mca','.mcc')
                   and not {'playerdata','stats','advancements','players'}&set(path.parts)
                   and path.name not in ('level.dat_old','session.lock'))
            cache=(name.startswith('cache/.fabric/processedMods/') or name.startswith('cache/.fabric/remappedJars/')) and path.suffix=='.jar'
            if path.is_absolute() or '..' in path.parts or '\\' in name or not(world or cache):
                raise ValueError('Unapproved startup template path: '+name)
            info=z.getinfo(name)
            if stat.S_ISLNK(info.external_attr>>16) or info.file_size!=row['bytes'] or info.file_size>128*1024**2:
                raise ValueError('Invalid startup template member')
            total+=info.file_size
            if total>256*1024**2:raise ValueError('Startup template exceeds size budget')
            with z.open(info) as stream:digest=hashlib.file_digest(stream,'sha256').hexdigest()
            if digest!=row['sha256']:raise ValueError('Startup template hash differs: '+name)
        from pve_map_catalog import _NBT
        compressed=z.read('world/level.dat')
        import io
        with gzip.GzipFile(fileobj=io.BytesIO(compressed)) as stream:raw=stream.read(16*1024**2+1)
        if len(raw)>16*1024**2:raise ValueError('Template level.dat exceeds metadata budget')
        nbt=_NBT(raw)
        if nbt.number('B')!=10:raise ValueError('Template level.dat is not vanilla NBT')
        nbt.string();data=nbt.payload(10).get('Data',{})
        if (nbt.pos!=len(raw) or data.get('LevelName')!=WORLD or data.get('DataVersion')!=3955
                or data.get('WorldGenSettings',{}).get('seed')!=20261014 or 'Player' in data):
            raise ValueError('Template world identity/seed/player privacy differs')
    return rows


def stage(builder, directory):
    directory=Path(directory).resolve()
    # This is an explicit generated build input, never a developer save path.
    if not directory.is_relative_to((builder.root/'data').resolve()):
        raise ValueError('Startup templates must be explicit generated inputs under project data/')
    metadata=read_json(directory/'template.json')
    archive=directory/'payload.zip'
    rows=checked(metadata,archive)
    mods={p.name:sha256(p) for p in (builder.destination/'guest-passthrough-client/mods').glob('*.jar')}
    if mods!=metadata.get('mods'):raise ValueError('Startup template does not match the exact bundled mods')
    builder.component('startup-template','LicenseRef-Minecraft-Generated-World AND LicenseRef-Bundled-Mod-Notices',
                      'New project-generated seed 20261014 terrain; reproducible Fabric products from exactly bundled mods; no developer saves or player data')
    builder.copy(archive,PAYLOAD,'startup-template',directory)
    builder.copy(directory/'template.json',METADATA,'startup-template',directory)
    with zipfile.ZipFile(archive) as z:
        for row in rows:
            name=row['path']
            relative=('guest-passthrough-client/saves/'+WORLD+'/'+name[len('world/'):]) if name.startswith('world/') else 'guest-passthrough-client/'+name[len('cache/'):]
            target=local_path(builder.destination,relative)
            if target.exists():raise ValueError('Startup template would overwrite an existing factory file')
            target.parent.mkdir(parents=True,exist_ok=True)
            with z.open(name) as source,target.open('xb') as output:shutil.copyfileobj(source,output)
            if sha256(target)!=row['sha256']:raise ValueError('Factory startup template hash differs')
            builder.record(relative,'startup-template')
    return dict(worldCreated=True,worldCreation='clean-generated-startup-template',
                startupTemplate=True,templateFiles=len(rows),playerDataCopied=False)


def install(root,profile,settings):
    paths=PackPaths(root)
    if not paths.packaged or not (root/METADATA).is_file():return dict(installed=False,source='normal-world-creation')
    if settings.get('worldName')!=WORLD or int(settings.get('worldSeed',20261014))!=20261014:
        return dict(installed=False,source='different-selected-world')
    metadata=read_json(root/METADATA)
    destination=local_path(profile,'saves/'+WORLD)
    if destination.exists():
        return dict(installed=False,source='existing-world-preserved')
    inventory=manifest_files(root)
    for name in (METADATA,PAYLOAD):
        path=local_path(root,name)
        if path not in inventory or path.stat().st_size!=inventory[path]['bytes'] or sha256(path)!=inventory[path]['sha256']:
            raise ValueError('Startup template is not the pinned factory input')
    mods={p.name:sha256(p) for p in (profile/'mods').glob('*.jar')}
    if mods!=metadata.get('mods'):
        return dict(installed=False,source='changed-mod-set-preserved')
    archive=root/PAYLOAD
    rows=checked(metadata,archive)
    # Existing worlds, including partially created ones, are never replaced.
    create_world=not destination.exists()
    staging=profile/'saves'/('.owmc-default-'+uuid.uuid4().hex)
    if create_world:staging.mkdir(parents=True,exist_ok=False)
    caches=0
    with zipfile.ZipFile(archive) as z:
        for entry in rows:
            name=entry['path']
            if name.startswith('world/'):
                if not create_world:continue
                target=local_path(staging,name[len('world/'):])
            else:
                target=local_path(profile,name[len('cache/'):])
                if target.exists():continue  # Fabric owns an existing cache.
            target.parent.mkdir(parents=True,exist_ok=True)
            temporary=target.with_name(target.name+'.'+uuid.uuid4().hex+'.tmp')
            with z.open(name) as source,temporary.open('xb') as output:shutil.copyfileobj(source,output)
            if sha256(temporary)!=entry['sha256']:raise ValueError('Startup extraction hash differs')
            if target.exists():
                # Preserve a concurrent writer; leave our own temporary as evidence.
                continue
            temporary.rename(target)
            if name.startswith('cache/'):caches+=1
    if create_world:
        # Windows rename refuses to replace an existing world created concurrently.
        staging.rename(destination)
    return dict(installed=create_world,cachesPrepared=caches,source='pinned-clean-generated-template')
