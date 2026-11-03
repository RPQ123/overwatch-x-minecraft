"""Read-only crash evidence for one previously SHA-verified native process.

An offline client may catch its exception, launch BlizzardError and exit0.
Never equate its process exit code with successful or crash-free termination.
"""
import ctypes
import os
import re
import time
from pathlib import Path
import psutil


def documents_folder():
    if os.name!='nt':return Path.home()/'Documents'
    value=ctypes.create_unicode_buffer(32768)
    result=ctypes.windll.shell32.SHGetFolderPathW(None,5,None,0,value)
    if result or not value.value:raise OSError('Cannot resolve Windows Documents folder')
    return Path(value.value)


def find_native_crash_reports(pid,created,executable,*,documents=None,processes=None):
    """Match process, report filename, time and the report's actual Application.

    Reporter arguments are diagnostic paths only, never commands. A bounded
    Documents fallback retains evidence after a reporter has already closed.
    """
    executable=Path(executable).resolve();pid=int(pid)
    if pid<=0 or created<=0:raise ValueError('Verified process identity required')
    pattern=re.compile(r'Overwatch_24919_Retailx64_'+str(pid)+r'_\d{2}-\d{2}-\d{2}_\d{2}\.\d{2}\.\d{2}_ErrorLog\.txt\Z')
    reporters={executable.parent/'ErrorReporting'/arch/'BlizzardError.exe' for arch in ('x86','x64')}
    reporters={p.resolve() for p in reporters};candidates={}
    if processes is None:processes=psutil.process_iter(['pid','exe','cmdline','create_time'])
    for process in processes:
        try:
            info=dict(process.info or {})
            reporter_created=info.get('create_time')
            if (not info.get('exe') or Path(info.get('exe')).resolve() not in reporters
                    or not isinstance(reporter_created,(int,float)) or reporter_created<created):continue
            for argument in (info.get('cmdline') or [])[1:]:
                path=Path(argument)
                if path.is_absolute() and pattern.fullmatch(path.name):candidates[path.resolve()]=info.get('pid') or process.pid
        except (OSError,ValueError,psutil.Error):continue
    errors=Path(documents if documents is not None else documents_folder())/'Overwatch/Logs/Overwatch/errors'
    if errors.is_dir():
        for path in errors.glob(f'Overwatch_24919_Retailx64_{pid}_*_ErrorLog.txt'):
            if pattern.fullmatch(path.name):candidates.setdefault(path.resolve(),None)
    accepted=[]
    for path,reporter in candidates.items():
        try:
            before=path.stat()
            if not 0<before.st_size<=2*1024*1024 or before.st_mtime<created:continue
            text=path.read_text(encoding='utf-8-sig',errors='replace')
            application=re.search(r'^Application:\s*([^\r\n]+)',text,re.MULTILINE)
            after=path.stat()
            if (before.st_size,before.st_mtime_ns)!=(after.st_size,after.st_mtime_ns):continue
            if not application or Path(application.group(1).strip()).resolve()!=executable:continue
            if '<Inspector.Assertion:>' not in text:continue
            item={'path':str(path),'reporterPid':reporter,'size':after.st_size,'mtimeMs':round(after.st_mtime*1000)}
            dump=path.with_name(path.name.removesuffix('ErrorLog.txt')+'Minidump.dmp')
            if dump.is_file() and dump.stat().st_mtime>=created:item['minidump']=str(dump)
            accepted.append(item)
        except (OSError,ValueError):continue
    return sorted(accepted,key=lambda row:row['path'])


def wait_native_crash_reports(pid,created,executable,seconds=1):
    deadline=time.monotonic()+min(max(seconds,0),2)
    while True:
        rows=find_native_crash_reports(pid,created,executable)
        if rows or time.monotonic()>=deadline:return rows
        time.sleep(.1)
