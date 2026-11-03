"""Verified, optional community STU names for private native observations.

CSV rows are accepted only if the name's lowercase CRC32 equals the hash. A
matching name identifies the type, not its behavior, authority or runtime state.
No downloads, game calls, or process writes happen in this module.
"""
import csv
import re
from pathlib import Path
import zlib

class HashNames:
    def __init__(self,path=None):
        self.names={}
        if path is None:return
        path=Path(path)
        if path.stat().st_size>1024*1024:raise ValueError('Name table exceeds research bound')
        with path.open(encoding='utf-8-sig',newline='') as source:
            for line,row in enumerate(csv.reader(source),1):
                if not row:continue
                if len(row)!=2:raise ValueError(f'Name table row {line}: expected hash,name')
                raw,name=(part.strip() for part in row)
                if not re.fullmatch(r'[0-9a-fA-F]{1,8}',raw) or not name or len(name)>256:raise ValueError(f'Name table row {line}: field bounds')
                key=int(raw,16)
                if zlib.crc32(name.lower().encode('utf-8'))!=key:raise ValueError(f'Name table row {line}: hash mismatch')
                if key in self.names and self.names[key]!=name:raise ValueError(f'Name table row {line}: ambiguous hash')
                self.names[key]=name
        if len(self.names)>16384:raise ValueError('Name table count bound')

    def get(self,key):return self.names.get(int(key,16) if isinstance(key,str) else key)

    def annotate(self,inventory):
        """Return a copy; keep recorded native names, flags and provenance intact."""
        import copy
        result=copy.deepcopy(inventory);matched=total=0
        for entity in result.get('entities',[]):
            for script in entity.get('scripts',[]):
                for node in script.get('nodes',[]):
                    total+=1;name=self.get(node['hash']) if node.get('hash') else None
                    if name:node['resolvedTypeName']=name;matched+=1
        result['typeNameResolution']={'method':'lowercase-crc32-verified-csv','knownTypes':len(self.names),'matchedNodes':matched,'totalNodes':total,'nativeExecutionObserved':False}
        return result
