"""Make an additive, verified private handoff snapshot; never removes source files."""
import hashlib,json,os,shutil,time
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
OUT=Path(os.environ.get('OWMC_TRANSFER_DIR', str(ROOT.parent/'OWMC-Transfer'))).expanduser().resolve()
STAGE=OUT/'OWMC'

def copy_tree(source,destination,records):
    total=0;count=0;last=time.monotonic()
    for base,dirs,files in os.walk(source,followlinks=True):
        relative=Path(base).relative_to(source);target=destination/relative;target.mkdir(parents=True,exist_ok=True)
        for directory in dirs:
            p=Path(base)/directory
            if p.is_symlink() or p.is_junction():
                resolved=p.resolve()
                if not resolved.is_relative_to(ROOT.resolve()) or resolved in p.parents:raise RuntimeError('External or cyclic linked directory: '+str(p))
                print(json.dumps({'materializedLink':str(p),'target':str(resolved)}),flush=True)
        for name in files:
            src=Path(base)/name;dst=target/name;before=src.stat();digest=hashlib.sha256()
            if dst.is_file() and dst.stat().st_size==before.st_size and dst.stat().st_mtime_ns==before.st_mtime_ns:
                with dst.open('rb') as existing:
                    while chunk:=existing.read(4*1024*1024):digest.update(chunk)
                records.append({'path':dst.relative_to(STAGE).as_posix(),'bytes':before.st_size,'sha256':digest.hexdigest()});total+=before.st_size;count+=1;continue
            with src.open('rb') as inp,dst.open('wb') as output:
                while chunk:=inp.read(4*1024*1024):output.write(chunk);digest.update(chunk)
            after=src.stat()
            if (before.st_size,before.st_mtime_ns)!=(after.st_size,after.st_mtime_ns):raise RuntimeError('Source changed while copied: '+str(src))
            shutil.copystat(src,dst);total+=before.st_size;count+=1
            records.append({'path':dst.relative_to(STAGE).as_posix(),'bytes':before.st_size,'sha256':digest.hexdigest()})
            if time.monotonic()-last>5:print(json.dumps({'copy':source.name,'files':count,'bytes':total}),flush=True);last=time.monotonic()
    print(json.dumps({'copied':str(source),'files':count,'bytes':total}),flush=True)

if __name__=='__main__':
    OUT.mkdir(exist_ok=True);STAGE.mkdir(exist_ok=True);records=[]
    if STAGE.resolve().is_relative_to(ROOT.resolve()):raise RuntimeError('Archive staging must be outside source')
    copy_tree(ROOT,STAGE,records)
    # Optional private handoff toolchains must be explicitly configured.
    for variable, destination in (('OWMC_MINGW_ROOT','mingw64'),
                                  ('OWMC_UNIVERSAL_MODDER_ROOT','universal-modder'),
                                  ('OWMC_GIT_ROOT','git')):
        configured=os.environ.get(variable)
        if configured:
            copy_tree(Path(configured).expanduser().resolve(),STAGE/'tools'/destination,records)
    (OUT/'source-copy-manifest.json').write_text(json.dumps(records,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'complete':True,'files':len(records),'bytes':sum(r['bytes'] for r in records)}),flush=True)
