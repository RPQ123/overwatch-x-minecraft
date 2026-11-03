"""Reproduce the private original Genji asset pack with the user's OWLib tool.

Example (PowerShell):
  .venv/Scripts/python.exe tools/assets/extract_original_projectiles.py --client <OW-dir> --datatool <DataTool.exe>
The retail game is read as files only. No process attachment or archive writes.
"""

# Preserve stable tools imports when this script is invoked by its new path.
import sys as _tidy_sys
from pathlib import Path as _TidyPath
_tidy_tools = _TidyPath(__file__).resolve().parents[1]
if str(_tidy_tools) not in _tidy_sys.path:
    _tidy_sys.path.insert(0, str(_tidy_tools))

import argparse
import hashlib
import json
from pathlib import Path
import subprocess
from owlib_projectile_assets import pack_projectile


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--client',type=Path,required=True)
    parser.add_argument('--datatool',type=Path,required=True)
    parser.add_argument('--output',type=Path,default=Path.home()/'.universal-modder/assets/owmc-original-projectiles')
    parser.add_argument('--extraction',type=Path,default=Path.home()/'.universal-modder/assets/ow-retail-154088/genji-projectile')
    args=parser.parse_args()
    client,tool,out,extraction=(p.resolve() for p in (args.client,args.datatool,args.output,args.extraction))
    repo=Path(__file__).resolve().parents[2]
    if any(p.is_relative_to(repo) or p.is_relative_to(client) for p in (out,extraction)):
        parser.error('Keep extracted assets outside the source tree and the game installation')
    build=(client/'.build.info').read_bytes()
    if b'2.25.0.0.154088' not in build:
        parser.error('This conversion is calibrated for local build 2.25.0.0.154088; recalibrate after a client update')
    if not tool.is_file(): parser.error('DataTool.exe does not exist')
    extraction.parent.mkdir(parents=True,exist_ok=True)
    command=[str(tool),str(client),'extract-anything',str(extraction),'0x04000000000007ca',
             '--online=false','--rcn','--language=zhCN','--skip-sound','--skip-animations']
    log=extraction.parent/'extract-projectile.log'
    with log.open('w',encoding='utf-8') as stream:
        subprocess.run(command,cwd=tool.parent,stdout=stream,stderr=subprocess.STDOUT,check=True)
    if (client/'.build.info').read_bytes()!=build: raise RuntimeError('Client build changed during extraction')
    provenance=pack_projectile(extraction,out)
    provenance.update(toolSha256=hashlib.sha256(tool.read_bytes()).hexdigest(),
                      buildInfoSha256=hashlib.sha256(build).hexdigest(),command=command)
    (out/'provenance.json').write_text(json.dumps(provenance,indent=2),encoding='utf-8')
    print(json.dumps(dict(pack=str(out),sourceModel=provenance['originalModel'],
                         fullEffectGraph=False,log=str(log)),indent=2))


if __name__=='__main__': main()
