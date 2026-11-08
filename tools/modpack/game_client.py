"""Local copy of the user's exact research client; no downloads or execution."""
from pathlib import Path

from .client import FOLDER
from .config import OW_SHA256, sha256

LICENSE='暴雪娱乐版权所有；专有客户端本地副本，再分发授权未核实'
COMPONENT='game-client'
OMIT_DIRS={'cache','logs','crash-reports','.git'}
OMIT_FILES={'.env','launcher_accounts.json','accounts.json','credentials.json'}


def stage(builder, configured) -> dict:
    executable=configured.get('owExecutable')
    if sha256(executable)!=OW_SHA256:
        raise ValueError('待复制的 OW 客户端 SHA256 不匹配，未打包。')
    source=executable.parent.resolve()
    builder.component(COMPONENT,LICENSE,'User-provided local offline research client; redistribution authorization not verified',version='0.8.0.24919')
    builder.components[COMPONENT].update(authorizationVerified=False,localCopyOnly=True)
    copied=0;size=0;omitted=0
    for path in sorted(source.rglob('*')):
        relative=path.relative_to(source)
        if (any(part.casefold() in OMIT_DIRS for part in relative.parts) or path.name.casefold() in OMIT_FILES
                or path.suffix.lower() in ('.log','.tmp','.dmp','.lnk')
                or relative.as_posix().casefold() == 'data/casc/data/shmem'):
            omitted+=int(path.is_file());continue
        if path.is_symlink() or path.is_junction():
            raise ValueError('客户端含链接，未跟随复制：'+str(relative))
        if not path.is_file():continue
        builder.copy(path,'game/'+FOLDER+'/'+relative.as_posix(),COMPONENT,source)
        copied+=1;size+=path.stat().st_size
    result=dict(files=copied,bytes=size,omittedRuntimeFiles=omitted,
                executable='game/'+FOLDER+'/'+executable.name,sha256=OW_SHA256,
                localCopyOnly=True,redistributionAuthorizationVerified=False)
    if sha256(builder.destination/result['executable'])!=OW_SHA256:
        raise ValueError('打包后 OW 客户端 SHA256 校验失败。')
    return result
