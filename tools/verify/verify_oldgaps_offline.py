"""oldgaps 离线 Java21 类型检查/状态机测试；不启动游戏、不打包部署 JAR。"""

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
    compiler = shutil.which('javac')
    require(compiler, 'JDK21 javac required')
    java = Path(compiler).with_name('java.exe' if os.name == 'nt' else 'java')
    out = ROOT / 'research/asset-cache/oldgaps-typecheck'
    out.mkdir(parents=True, exist_ok=True)
    main = ROOT / 'guest/src/main/java/lab/owmcguest'
    test = ROOT / 'guest/src/test/java/lab/owmcguest/NativeSustainPhaseCheck.java'
    standalone = subprocess.run([compiler, '--release', '21', '-encoding', 'UTF-8', '-d', str(out),
                                 str(main / 'NativeSustainPhase.java'), str(test)],
                                cwd=ROOT, capture_output=True, text=True, timeout=60)
    require(standalone.returncode == 0, standalone.stderr[-3000:])
    checked = subprocess.run([str(java), '-cp', str(out), 'lab.owmcguest.NativeSustainPhaseCheck'],
                             cwd=ROOT, capture_output=True, text=True, timeout=20)
    require(checked.returncode == 0, checked.stdout + checked.stderr)
    jars = list((ROOT / 'guest/.gradle/loom-cache').glob('minecraftMaven/**/*.jar'))
    jars += list((ROOT / 'guest/.gradle/loom-cache').glob('remapped_mods/**/*.jar'))
    jars += list((ROOT / 'tools/gradle-cache/caches/modules-2/files-2.1').rglob('*.jar'))
    jars = [p for p in jars if not p.name.endswith('-sources.jar')]
    classes = [ROOT / 'guest/build/classes/java/main', ROOT / 'guest/build/classes/java/client']
    require(jars and all(p.is_dir() for p in classes), 'Existing named dependencies/classes required')
    sources = [main / 'NativeSustainPhase.java', main / 'NativeSustainRuntime.java']
    sources += [ROOT / 'guest/src/client/java/lab/owmcguest/NativeSustainController.java']
    quote = lambda p: '"' + str(p).replace('\\', '/').replace('"', '\\"') + '"'
    args = ['--release', '21', '-encoding', 'UTF-8', '-proc:none', '-implicit:none', '-sourcepath', '""',
            '-d', quote(out), '-classpath', quote(os.pathsep.join(str(p) for p in classes + jars))]
    args += [quote(p) for p in sources]
    argfile = out / 'javac.args'
    argfile.write_text('\n'.join(args) + '\n', encoding='utf-8')
    typed = subprocess.run([compiler, '@' + str(argfile)], cwd=ROOT, capture_output=True,
                           text=True, encoding='utf-8', errors='replace', timeout=60)
    (out / 'javac.log').write_text(typed.stdout + typed.stderr, encoding='utf-8')
    require(typed.returncode == 0, typed.stderr[-3000:])
    for path in [Path(__file__), ROOT / 'research/sprint-20261024/verify_oldgaps.py',
                 ROOT / 'tools/oldgaps_test_policy.py', ROOT / 'tools/test_oldgaps_test_policy.py']:
        ast.parse(path.read_text(encoding='utf-8'), filename=str(path))
    result = dict(passed=True, phaseChecks=checked.stdout.strip(), typedSources=len(sources),
                  pythonSyntax=True, gamesStarted=False, jarBuilt=False, liveAcceptance=False)
    (out / 'result.json').write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(result))


if __name__ == '__main__':
    run()
