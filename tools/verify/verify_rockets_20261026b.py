"""Offline source/asset/compile fixtures only; never launches either game or builds a JAR."""
from __future__ import annotations

# Preserve stable tools imports when this script is invoked by its new path.
import sys as _tidy_sys
from pathlib import Path as _TidyPath
_tidy_tools = _TidyPath(__file__).resolve().parents[1]
if str(_tidy_tools) not in _tidy_sys.path:
    _tidy_sys.path.insert(0, str(_tidy_tools))

import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "research/rockets-20261026b"


def main() -> int:
    if sys.version_info < (3, 13):
        raise RuntimeError("Use .venv/Scripts/python.exe (3.13)")
    OUT.mkdir(exist_ok=True, parents=True)
    assets = {}
    for name, files in {
        "owmc-pharah-projectile": ["rocket.json", "body.png", "exhaust.png", "flame.png", "flare.png", "glow.png"],
        "owmc-pharah-barrage": ["barrage.json", "body.png", "trail.png", "flame.png", "flare.png", "glow.png"],
    }.items():
        folder = Path.home() / ".universal-modder/assets" / name
        manifest = json.loads((folder / "provenance.json").read_text("utf-8"))["files"]
        checks = {f: hashlib.sha256((folder / f).read_bytes()).hexdigest() == manifest[f] for f in files}
        assets[name] = checks
    init = OUT / "verify.init.gradle"
    init.write_text("""gradle.projectsEvaluated {
    rootProject.tasks.register('verifyRockets20261026b', JavaExec) {
        dependsOn rootProject.tasks.named('testClasses')
        classpath = rootProject.sourceSets.test.runtimeClasspath
        mainClass = 'lab.owmcguest.RocketAdaptersCheck'
    }
}
""", encoding="utf-8")
    env = dict(os.environ, GRADLE_USER_HOME=str(ROOT / "tools/gradle-cache"))
    command = [str(ROOT / "tools/gradle/gradle-8.10.2/bin/gradle.bat"), "-p", "guest", "--offline",
               "--console=plain", "--no-daemon", "--init-script", str(init), "compileClientJava",
               "verifyRockets20261026b", "verifyPharahRocketPresentation", "verifyPharahBarragePresentation",
               "verifyPharahConcussiveBursts", "verifyHelixPresentation"]
    with (OUT / "verify.log").open("w", encoding="utf-8") as log:
        result = subprocess.run(command, cwd=ROOT, env=env, stdout=log, stderr=subprocess.STDOUT, check=False)
    runtime = (ROOT / "guest/src/main/java/lab/owmcguest/NativeCombatRuntime.java").read_text("utf-8")
    flight = (ROOT / "guest/src/client/java/lab/owmcguest/NativeFlightController.java").read_text("utf-8")
    client = (ROOT / "guest/src/client/java/lab/owmcguest/HeroClientModules.java").read_text("utf-8")
    server = (ROOT / "guest/src/main/java/lab/owmcguest/HeroServerModules.java").read_text("utf-8")
    integration = {
        "flightTuning": "simulation.admit(RocketFlightTuning.adapt(batch))" in runtime,
        "selfImpact": "NativeRocketSelfImpulse.INSTANCE.impact(" in runtime,
        "pharahVanillaTravel": "NativeRocketSelfImpulseClient.INSTANCE.useVanillaTravel(client)" in flight,
        "clientRegistered": "NativeRocketSelfImpulseClient.INSTANCE" in client,
        "serverRegistered": "NativeRocketSelfImpulse.INSTANCE" in server,
    }
    report = {"offlinePassed": result.returncode == 0 and all(all(v.values()) for v in assets.values()),
              "gradleExit": result.returncode, "assetHashes": assets, "sharedIntegration": integration,
              "integrationPending": [k for k, v in integration.items() if not v], "realGameTested": False,
              "jarBuiltOrDeployed": False}
    (OUT / "verification.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps({k: v for k, v in report.items() if k != "assetHashes"}, ensure_ascii=False))
    if result.returncode:
        print("\n".join((OUT / "verify.log").read_text("utf-8", errors="replace").splitlines()[-24:]))
    return 0 if report["offlinePassed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
