"""Tracer first-use/sound lifecycle offline checks; never builds JARs or starts games."""

# Preserve stable tools imports when this script is invoked by its new path.
import sys as _tidy_sys
from pathlib import Path as _TidyPath
_tidy_tools = _TidyPath(__file__).resolve().parents[1]
if str(_tidy_tools) not in _tidy_sys.path:
    _tidy_sys.path.insert(0, str(_tidy_tools))

import ast
import json
import os
from pathlib import Path
import shutil
import subprocess

ROOT = Path(__file__).resolve().parents[2]


def require(ok, message):
    if not ok:
        raise ValueError(message)


def run():
    javac = shutil.which('javac')
    require(javac, 'JDK21 javac required')
    java = Path(javac).with_name('java.exe' if os.name == 'nt' else 'java')
    out = ROOT / 'research/asset-cache/tracer-lifecycle-typecheck'
    out.mkdir(parents=True, exist_ok=True)
    main = ROOT / 'guest/src/main/java/lab/owmcguest'
    client = ROOT / 'guest/src/client/java/lab/owmcguest'
    tests = ROOT / 'guest/src/test/java/lab/owmcguest'
    pure = [main / (n + '.java') for n in ('NativeDeploymentGate', 'NativePulseGate', 'RecallSoundGate')]
    checks = ['NativePulseGateCheck', 'RecallSoundGateCheck']
    pure += [tests / (name + '.java') for name in checks]
    result = subprocess.run([javac, '--release', '21', '-encoding', 'UTF-8', '-d', str(out),
                             *map(str, pure)], capture_output=True, text=True, cwd=ROOT, timeout=60)
    require(result.returncode == 0, result.stderr[-3000:])
    messages = []
    for name in checks:
        checked = subprocess.run([str(java), '-cp', str(out), 'lab.owmcguest.' + name],
                                 capture_output=True, text=True, cwd=ROOT, timeout=20)
        require(checked.returncode == 0, checked.stdout + checked.stderr)
        messages.append(checked.stdout.strip())
    jars = list((ROOT / 'guest/.gradle/loom-cache').glob('minecraftMaven/**/*.jar'))
    jars += list((ROOT / 'guest/.gradle/loom-cache').glob('remapped_mods/**/*.jar'))
    jars += list((ROOT / 'tools/gradle-cache/caches/modules-2/files-2.1').rglob('*.jar'))
    jars = [p for p in jars if not p.name.endswith('-sources.jar')]
    classes = [out, ROOT / 'guest/build/classes/java/main', ROOT / 'guest/build/classes/java/client']
    require(jars and all(p.is_dir() for p in classes), 'Existing named dependencies/classes required')
    sources = [main / (n + '.java') for n in ('NativePulseGate', 'RecallSoundGate', 'NativePulseRuntime', 'NativeRecallRuntime')]
    sources += [client / (n + '.java') for n in ('NativePulseController', 'NativeRecallController', 'RecallStartSound')]
    quote = lambda p: '"' + str(p).replace('\\', '/').replace('"', '\\"') + '"'
    args = ['--release', '21', '-encoding', 'UTF-8', '-proc:none', '-implicit:none', '-sourcepath', '""',
            '-d', quote(out), '-classpath', quote(os.pathsep.join(map(str, classes + jars)))]
    args += [quote(p) for p in sources]
    argfile = out / 'javac.args'
    argfile.write_text('\n'.join(args) + '\n', encoding='utf-8')
    typed = subprocess.run([javac, '@' + str(argfile)], cwd=ROOT, capture_output=True, text=True,
                           encoding='utf-8', errors='replace', timeout=60)
    (out / 'javac.log').write_text(typed.stdout + typed.stderr, encoding='utf-8')
    require(typed.returncode == 0, typed.stderr[-3000:])
    ast.parse(Path(__file__).read_text(encoding='utf-8'))
    live = ROOT / 'research/sprint-20261024/verify_tracer_first_use.py'
    if live.exists():
        ast.parse(live.read_text(encoding='utf-8'))
    proof = dict(passed=True, checks=messages, typedSources=len(sources), gamesStarted=False,
                 jarBuilt=False, liveAcceptance=False)
    (out / 'result.json').write_text(json.dumps(proof, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(proof))


if __name__ == '__main__':
    run()
