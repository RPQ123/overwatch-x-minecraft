"""Compile only Symmetra sources against existing named Loom caches (no JAR).

Fallback when parallel Gradle invocations cannot acquire the shared Loom cache.
No cache deletion, game launch, dependency downloads, or deployment.
"""

# Preserve stable tools imports when this script is invoked by its new path.
import sys as _tidy_sys
from pathlib import Path as _TidyPath
_tidy_tools = _TidyPath(__file__).resolve().parents[1]
if str(_tidy_tools) not in _tidy_sys.path:
    _tidy_sys.path.insert(0, str(_tidy_tools))

import json
from pathlib import Path
import shutil
import subprocess

ROOT = Path(__file__).resolve().parents[2]


def run():
    compiler = shutil.which('javac')
    if not compiler:
        raise ValueError('Existing JDK21 javac required')
    out = ROOT/'research/asset-cache/symmetra-20261026/source-check'
    out.mkdir(parents=True,exist_ok=True)
    classpath = [ROOT/'guest/build/classes/java/main',ROOT/'guest/build/classes/java/client']
    classpath += [p for p in (ROOT/'guest/.gradle/loom-cache').rglob('*.jar') if not p.name.endswith('-sources.jar')]
    classpath += list((ROOT/'tools/gradle-cache/caches/modules-2/files-2.1').rglob('*.jar'))
    sources = [ROOT/'guest/src/main/java/lab/owmcguest/SymmetraServer.java',
               ROOT/'guest/src/main/java/lab/owmcguest/SymmetraLab.java',
               ROOT/'guest/src/client/java/lab/owmcguest/SymmetraClient.java']
    values = ['--release','21','-encoding','UTF-8','-proc:none','-d',str(out/'classes'),
              '-sourcepath',str(ROOT/'guest/src/main/java')+';'+str(ROOT/'guest/src/client/java'),
              '-classpath',';'.join(map(str,classpath)),*map(str,sources)]
    args = out/'javac.args'
    args.write_text('\n'.join('"'+s.replace('\\','/')+'"' for s in values)+'\n',encoding='utf-8')
    result = subprocess.run([compiler,'@'+str(args)],cwd=ROOT,capture_output=True,text=True,encoding='utf-8',errors='replace',timeout=90)
    (out/'javac.log').write_text(result.stdout+result.stderr,encoding='utf-8')
    report = {'passed':result.returncode==0,'jarBuilt':False,'deployed':False,'command':[compiler,'@'+str(args)],
              'log':str(out/'javac.log'),'explicitSources':[str(p.relative_to(ROOT)) for p in sources]}
    (out/'result.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(report))
    if result.returncode:
        print(result.stderr[-2200:])
    return result.returncode


if __name__ == '__main__':
    raise SystemExit(run())
