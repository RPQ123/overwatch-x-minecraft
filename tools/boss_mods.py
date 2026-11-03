"""Validate optional pinned Fabric boss mods before any save is opened."""
import hashlib,json,zipfile
def verify(profile):
    path=profile/'owmc-boss-mods.json'
    if not path.exists():return []
    rows=json.loads(path.read_text(encoding='utf-8'));result=[]
    for row in rows:
        name=row['file']
        if '/' in name or '\\' in name or not name.endswith('.jar'):raise ValueError('Invalid optional mod manifest path')
        mod=profile/'mods'/name
        if not mod.is_file() or hashlib.sha256(mod.read_bytes()).hexdigest()!=row['sha256']:raise ValueError('Required world mod missing/changed: '+name)
        with zipfile.ZipFile(mod) as archive:meta=json.loads(archive.read('fabric.mod.json'))
        if meta['id']!=row['id'] or meta['version']!=row['version']:raise ValueError('Required world mod identity changed: '+name)
        result.append(row)
    return result
