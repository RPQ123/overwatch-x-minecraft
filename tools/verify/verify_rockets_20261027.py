"""Offline fixtures and compilation, including candidate shared edits; no game/JAR work."""
from __future__ import annotations

# Preserve stable tools imports when this script is invoked by its new path.
import sys as _tidy_sys
from pathlib import Path as _TidyPath
_tidy_tools = _TidyPath(__file__).resolve().parents[1]
if str(_tidy_tools) not in _tidy_sys.path:
    _tidy_sys.path.insert(0, str(_tidy_tools))

import difflib
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "research/rockets-20261027"


def replace_once(text: str, old: str, new: str) -> str:
    if new in text:
        return text
    if text.count(old) != 1:
        raise RuntimeError(f"Shared source anchor changed: {old[:85]!r}; review manually")
    return text.replace(old, new, 1)


def candidates() -> dict[str, bool]:
    """Write copies and a reviewable patch under research; never edit shared source."""
    folder = OUT / "integration-src/lab/owmcguest"
    folder.mkdir(parents=True, exist_ok=True)
    flight_path = ROOT / "guest/src/client/java/lab/owmcguest/NativeFlightController.java"
    flight = flight_original = flight_path.read_text("utf-8")
    legacy = '''        if(NativeRocketSelfImpulseClient.INSTANCE.useVanillaTravel(client)){
            previous=null;sequence=0;blocked=0;
            status="{\\"ready\\":true,\\"mcRocketJump\\":true}";
            return false;
        }
'''
    flight = flight.replace(legacy, "")
    if "useVanillaTravel(client)" in flight:
        raise RuntimeError("Legacy vanilla flight branch changed; review manually")
    flight = replace_once(flight, "        delta=delta.add(NativeConcussiveController.INSTANCE.motion(client));",
                         """        delta=delta.add(NativeConcussiveController.INSTANCE.motion(client));
        var rocketJump=NativeRocketSelfImpulseClient.INSTANCE.pharahMotion(client);
        delta=delta.add(rocketJump);""")
    anchor = "        var velocity=motion.velocity();p.setVelocity("
    flight = replace_once(flight, anchor,
                         "        NativeRocketSelfImpulseClient.INSTANCE.pharahBlocked(blocked);\n" + anchor)
    flight = replace_once(flight, "boosted?actual.y:velocity[1]/20",
                         "(boosted||rocketJump.lengthSquared()>1e-10)?actual.y:velocity[1]/20")
    (folder / flight_path.name).write_text(flight, encoding="utf-8")
    mixin_path = ROOT / "guest/src/client/java/lab/owmcguest/mixin/NativeDashTravelMixin.java"
    mixin = mixin_original = mixin_path.read_text("utf-8")
    old = "        return (Object)this==MinecraftClient.getInstance().player?NativeLocomotionController.INSTANCE.movement(movement):movement;"
    new = """        var client=MinecraftClient.getInstance();
        return (Object)this==client.player?lab.owmcguest.NativeRocketSelfImpulseClient.INSTANCE.vanillaMovement(
            client,NativeLocomotionController.INSTANCE.movement(movement)):movement;"""
    mixin = replace_once(mixin, old, new)
    (folder / "mixin").mkdir(exist_ok=True)
    (folder / "mixin" / mixin_path.name).write_text(mixin, encoding="utf-8")
    patch = []
    for path, before, after in [(flight_path, flight_original, flight), (mixin_path, mixin_original, mixin)]:
        relative = path.relative_to(ROOT).as_posix()
        patch.extend(difflib.unified_diff(before.splitlines(True), after.splitlines(True), fromfile="a/" + relative, tofile="b/" + relative))
    (OUT / "shared-integration.patch").write_text("".join(patch), encoding="utf-8")
    return {"nativeFlightOverlay": flight_original == flight, "normalHorizontalOverlay": mixin_original == mixin}


def main() -> int:
    if sys.version_info < (3, 13):
        raise RuntimeError("Use .venv/Scripts/python.exe")
    OUT.mkdir(parents=True, exist_ok=True)
    integration = candidates()
    asset_root = Path.home() / ".universal-modder/assets/owmc-pharah-projectile"
    manifest = json.loads((asset_root / "provenance.json").read_text("utf-8"))["files"]
    hashes = {name: hashlib.sha256((asset_root / name).read_bytes()).hexdigest() == manifest[name]
              for name in ["flare.png", "glow.png", "flame.png"]}
    init = OUT / "verify.init.gradle"
    init.write_text("""gradle.projectsEvaluated {
    rootProject.tasks.register('verifyRocketImpulseMotion20261027', JavaExec) {
        dependsOn rootProject.tasks.named('testClasses')
        classpath = rootProject.sourceSets.test.runtimeClasspath
        mainClass = 'lab.owmcguest.RocketImpulseMotionCheck'
    }
    rootProject.tasks.register('verifyRocketAdapters20261027', JavaExec) {
        dependsOn rootProject.tasks.named('testClasses')
        classpath = rootProject.sourceSets.test.runtimeClasspath
        mainClass = 'lab.owmcguest.RocketAdaptersCheck'
    }
    rootProject.tasks.register('compileRocketsIntegration20261027', JavaCompile) {
        dependsOn rootProject.tasks.named('compileClientJava')
        source = rootProject.fileTree('""" + (OUT / "integration-src").as_posix() + """') { include '**/*.java' }
        classpath = rootProject.sourceSets.client.compileClasspath + rootProject.sourceSets.client.output + rootProject.sourceSets.main.output
        destinationDirectory = rootProject.file('""" + (OUT / "integration-classes").as_posix() + """')
        options.compilerArgs.add('-proc:none')
        options.encoding = 'UTF-8'
    }
}
""", encoding="utf-8")
    command = [str(ROOT / "tools/gradle/gradle-8.10.2/bin/gradle.bat"), "-p", "guest", "--offline", "--console=plain",
               "--no-daemon", "--init-script", str(init), "compileClientJava", "compileRocketsIntegration20261027",
               "verifyRocketImpulseMotion20261027", "verifyRocketAdapters20261027", "verifyPharahRocketPresentation",
               "verifyPharahBarragePresentation", "verifyPharahConcussiveBursts", "verifyHelixPresentation"]
    env = dict(os.environ, GRADLE_USER_HOME=str(ROOT / "tools/gradle-cache"))
    with (OUT / "verify.log").open("w", encoding="utf-8") as log:
        result = subprocess.run(command, cwd=ROOT, env=env, stdout=log, stderr=subprocess.STDOUT, check=False)
    report = {"offlinePassed": result.returncode == 0 and all(hashes.values()), "gradleExit": result.returncode,
              "glowAssetHashes": hashes, "sharedIntegration": integration, "realGameTested": False, "jarBuiltOrDeployed": False}
    (OUT / "verification.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False))
    if result.returncode:
        print("\n".join((OUT / "verify.log").read_text("utf-8", errors="replace").splitlines()[-30:]))
    return 0 if report["offlinePassed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
