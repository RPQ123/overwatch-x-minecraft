"""Java21 builders-only type check using existing named jars/classes; no Loom cache writes.

This is not a full Gradle/mixin-runtime acceptance. Useful while other threads
are editing unrelated sources or holding the shared Loom cache.
"""
import json
from pathlib import Path
import shutil
import subprocess

ROOT=Path(__file__).resolve().parents[1]


def run():
    compiler=shutil.which('javac')
    if compiler is None:raise ValueError('JDK21 javac is required')
    named=ROOT/'guest/.gradle/loom-cache'
    jars=list(named.glob('minecraftMaven/**/*.jar'))+list(named.glob('remapped_mods/**/*.jar'))
    jars=[p for p in jars if not p.name.endswith('-sources.jar')]
    jars+=list((ROOT/'tools/gradle-cache/caches/modules-2/files-2.1').rglob('*.jar'))
    roots=[ROOT/'guest/build/classes/java/main',ROOT/'guest/build/classes/java/client']
    if not jars or not all(p.is_dir() for p in roots):raise ValueError('Requires existing successful project compilation baseline and named jar caches')
    sources=[]
    for directory in ('guest/src/main/java/lab/owmcguest','guest/src/client/java/lab/owmcguest','guest/src/client/java/lab/owmcguest/mixin'):
        for pattern in ('NativeJunkrat*.java','NativeTorbjorn*.java','NativeBuilders*.java','JunkratRenderer.java'):
            sources.extend((ROOT/directory).glob(pattern))
    out=ROOT/'research/asset-cache/builders-typecheck';out.mkdir(parents=True,exist_ok=True)
    quote=lambda s:'"'+str(s).replace('\\','/').replace('"','\\"')+'"'
    args=['--release','21','-encoding','UTF-8','-proc:none','-implicit:none','-sourcepath','""','-d',quote(out),
          '-classpath',quote(';'.join(str(p) for p in roots+jars))]+[quote(p) for p in sources]
    argument_file=out/'javac.args';argument_file.write_text('\n'.join(args)+'\n',encoding='utf-8')
    result=subprocess.run([compiler,'@'+str(argument_file)],cwd=ROOT,capture_output=True,text=True,encoding='utf-8',errors='replace',timeout=120)
    (out/'javac.log').write_text(result.stdout+result.stderr,encoding='utf-8')
    proof=dict(passed=result.returncode==0,sources=len(sources),jarCount=len(jars),fullGradle=False,log=str(out/'javac.log'))
    (out/'result.json').write_text(json.dumps(proof,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(proof))
    if result.returncode:print(result.stderr[:3500])
    return result.returncode


if __name__=='__main__':raise SystemExit(run())
