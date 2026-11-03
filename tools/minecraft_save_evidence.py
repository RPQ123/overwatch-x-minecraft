"""Bounded, file-only save evidence for one already identified MC shutdown.

Only append bytes in the same log stream count. Old markers, a replaced log,
or a new client's rewritten stream cannot confirm this shutdown's save.
"""
import re
import time
from pathlib import Path


def capture(profile, world=None):
    result = dict(profile=str(Path(profile).resolve()), world=world, captured=time.time(), logs=[])
    for name in ('latest.log', 'launch.log'):
        path = Path(profile)/'logs'/name
        try:
            with path.open('rb') as stream:
                stat = path.stat()
                offset = max(0, stat.st_size-128)
                stream.seek(offset)
                anchor = stream.read(stat.st_size-offset)
            result['logs'].append(dict(path=str(path.resolve()), size=stat.st_size,
                                       inode=stat.st_ino, anchorOffset=offset, anchor=anchor.hex()))
        except OSError as error:
            result['logs'].append(dict(path=str(path.resolve()), unavailable=repr(error)))
    return result


def inspect(baseline):
    evidence = dict(complete=False, saveErrors=[], logs=[])
    for old in baseline['logs']:
        row = dict(path=old['path'], complete=False)
        evidence['logs'].append(row)
        if 'unavailable' in old:
            row['unavailableAtCapture'] = old['unavailable']
            continue
        path = Path(old['path'])
        try:
            before = path.stat()
            if before.st_ino != old['inode'] or before.st_size < old['size']:
                row['streamChanged'] = True
                continue
            with path.open('rb') as stream:
                stream.seek(old['anchorOffset'])
                if stream.read(len(bytes.fromhex(old['anchor']))) != bytes.fromhex(old['anchor']):
                    row['streamChanged'] = True
                    continue
                stream.seek(max(old['size'], before.st_size-2*1024*1024))
                tail = stream.read(2*1024*1024).decode('utf-8', errors='replace')
            after = path.stat()
            if (before.st_ino, before.st_size, before.st_mtime_ns) != (after.st_ino, after.st_size, after.st_mtime_ns):
                row['streamChangedDuringRead'] = True
                continue
            markers = ['Stopping server', 'Saving players', 'Saving worlds']
            if baseline.get('world'):
                markers.append("Saving chunks for level 'ServerLevel["+baseline['world']+"]'/")
            markers.append('All dimensions are saved')
            cursor = 0
            matched = []
            for marker in markers:
                found = tail.find(marker, cursor)
                if found < 0:
                    break
                matched.append(marker)
                cursor = found+len(marker)
            errors = [line[:500] for line in tail.splitlines()
                      if re.search(r"failed to save|exception saving|error saving|could(?:n't| not) save",line,re.I)
                      and re.search(r'chunk|level|world|player',line,re.I)]
            evidence['saveErrors'].extend(errors[:8])
            row.update(complete=len(matched)==len(markers) and not errors,
                       matched=matched, appendBytes=before.st_size-old['size'])
        except OSError as error:
            row['error'] = repr(error)
    evidence['complete'] = any(row['complete'] for row in evidence['logs']) and not evidence['saveErrors']
    return evidence
