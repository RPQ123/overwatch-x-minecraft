"""Compile only colors sources against existing named MC caches, no Gradle/JAR.

Fallback for this machine's Loom mapping/temp failure; not a full Gradle check.
"""

# Preserve stable tools imports when this script is invoked by its new path.
import sys as _tidy_sys
from pathlib import Path as _TidyPath
_tidy_tools = _TidyPath(__file__).resolve().parents[1]
if str(_tidy_tools) not in _tidy_sys.path:
    _tidy_sys.path.insert(0, str(_tidy_tools))

import json
from pathlib import Path
import subprocess

ROOT=Path(__file__).resolve().parents[2]


def main():
    out=ROOT/'research/asset-cache/colors-20261026/javac'
    out.mkdir(parents=True,exist_ok=True)
    java=ROOT/'minecraft-1.21.1/runtime/java-runtime-delta/windows-x64/java-runtime-delta/bin'
    named=list((ROOT/'guest/.gradle/loom-cache/minecraftMaven').rglob('*.jar'))
    named=[p for p in named if '-sources' not in p.name]
    if len(named)!=2:
        raise ValueError('Expected existing two named Minecraft cache jars')
    jars=named+list((ROOT/'guest/.gradle/loom-cache/remapped_mods').rglob('*.jar'))
    jars+=list((ROOT/'tools/gradle-cache/caches/modules-2/files-2.1').rglob('*.jar'))
    jars=[p for p in jars if not any(s in p.name for s in ('-sources','-javadoc'))]
    cp=[ROOT/'guest/build/classes/java/main',ROOT/'guest/build/classes/java/client',*jars]
    sources=[ROOT/'guest/src/client/java/lab/owmcguest'/name for name in
             ('OriginalMeshPack.java','HanzoDragonSwim.java','HanzoDragonRenderer.java','HanzoSonicPulseMesh.java')]
    sources.append(ROOT/'guest/src/test/java/lab/owmcguest/HanzoDragonSwimCheck.java')
    args=['-proc:none','-encoding','UTF-8','-d',str(out),'-classpath',';'.join(map(str,cp)),
          '-sourcepath',';'.join(str(ROOT/p) for p in ('guest/src/main/java','guest/src/client/java')),*map(str,sources)]
    argfile=out/'args.txt'
    argfile.write_text('\n'.join('"'+a.replace('\\','/')+'"' for a in args)+'\n',encoding='utf-8')
    run=subprocess.run([str(java/'javac.exe'),'@'+str(argfile)],cwd=ROOT,capture_output=True)
    (out/'compile.log').write_bytes(run.stdout+run.stderr)
    result=dict(javacExit=run.returncode,gradleVerified=False,explicitSources=[p.name for p in sources])
    if run.returncode==0:
        check=subprocess.run([str(java/'java.exe'),'-cp',str(out),'lab.owmcguest.HanzoDragonSwimCheck'],capture_output=True)
        result.update(swimExit=check.returncode,swimOutput=check.stdout.decode('utf-8',errors='replace').strip())
    else:
        result['errors']=(run.stdout+run.stderr).decode('utf-8',errors='replace').splitlines()[:24]
    (out/'result.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(result,ensure_ascii=True))
    if run.returncode:
        raise SystemExit(run.returncode)


if __name__=='__main__':main()
