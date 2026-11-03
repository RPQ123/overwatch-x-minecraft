"""Compile Widow sources and prove the shared melee correction without editing shared files.

Uses only the cached Java toolchain/dependencies and a Win64 memory fixture owned by
the test JVM. Starts no game, builds/deploys no JAR. Evidence is local and ignored.
"""
from __future__ import annotations

# Preserve stable tools imports when this script is invoked by its new path.
import sys as _tidy_sys
from pathlib import Path as _TidyPath
_tidy_tools = _TidyPath(__file__).resolve().parents[1]
if str(_tidy_tools) not in _tidy_sys.path:
    _tidy_sys.path.insert(0, str(_tidy_tools))


import json
import os
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[2]
EVIDENCE = ROOT / "research/sprint-20261027/widow-offline"
OLD = "if(spec==null&&!grapple&&!venom&&hero==NativeInfraSightState.HERO&&infraDuration()!=15)"
NEW = "if(spec==null&&!melee&&!grapple&&!venom&&hero==NativeInfraSightState.HERO&&infraDuration()!=15)"


def run(arguments: list[str], label: str, env: dict[str, str] | None = None) -> str:
    # The cached Fabric classpath exceeds Windows' CreateProcess command-line limit.
    # Java's native argument files keep the exact arguments without shell interpolation.
    if Path(arguments[0]).name in {"java.exe", "javac.exe"}:
        argument_file = EVIDENCE / f"{label}.args"
        argument_file.write_text("\n".join('"' + value.replace("\\", "\\\\").replace('"', '\\"') + '"'
                                          for value in arguments[1:]) + "\n", encoding="utf-8")
        arguments = [arguments[0], "@" + str(argument_file)]
    result = subprocess.run(arguments, cwd=ROOT, env=env, capture_output=True, text=True,
                            encoding="utf-8", errors="replace")
    output = result.stdout + result.stderr
    (EVIDENCE / f"{label}.log").write_text(output, encoding="utf-8")
    if result.returncode:
        raise RuntimeError(f"{label} failed ({result.returncode}): {output[-1800:]}")
    return output


def main() -> None:
    EVIDENCE.mkdir(parents=True, exist_ok=True)
    init = EVIDENCE / "classpath.init.gradle"
    init.write_text("""allprojects {
    afterEvaluate { project ->
        tasks.register('widowOfflineClasspath') {
            dependsOn tasks.named('compileClientJava')
            doLast { println('OWMC_WIDOW_CP=' + sourceSets.test.runtimeClasspath.asPath) }
        }
    }
}
""", encoding="utf-8")
    env = os.environ.copy()
    env["GRADLE_USER_HOME"] = str(ROOT / "tools/gradle-cache")
    output = run([str(ROOT / "tools/gradle/gradle-8.10.2/bin/gradle.bat"), "-p", "guest",
                  "--offline", "--console=plain", "--no-daemon", "-I", str(init),
                  "widowOfflineClasspath"], "compile-classpath", env)
    classpath = next(line.removeprefix("OWMC_WIDOW_CP=") for line in output.splitlines()
                     if line.startswith("OWMC_WIDOW_CP="))
    java_bin = ROOT / "minecraft-1.21.1/runtime/java-runtime-delta/windows-x64/java-runtime-delta/bin"
    reader_path = ROOT / "guest/src/client/java/lab/owmcguest/NativeSkillReader.java"
    original = reader_path.read_text(encoding="utf-8")
    already_fixed = OLD not in original and NEW in original
    if not already_fixed and original.count(OLD) != 1:
        raise RuntimeError("Shared reader changed; re-audit the correction before running this fixture")
    candidate = EVIDENCE / "candidate-src/lab/owmcguest/NativeSkillReader.java"
    candidate.parent.mkdir(parents=True, exist_ok=True)
    candidate.write_text(original.replace(OLD, NEW), encoding="utf-8")
    fixture = ROOT / "guest/src/test/java/lab/owmcguest/WidowMeleeReaderCheck.java"
    baseline_classes, candidate_classes = EVIDENCE / "baseline-classes", EVIDENCE / "candidate-classes"
    for path in (baseline_classes, candidate_classes):
        path.mkdir(exist_ok=True)
    run([str(java_bin / "javac.exe"), "-encoding", "UTF-8", "--release", "21", "-cp", classpath,
         "-d", str(baseline_classes), str(fixture)], "compile-fixture")
    baseline = run([str(java_bin / "java.exe"), "-cp", str(baseline_classes) + os.pathsep + classpath,
                    "lab.owmcguest.WidowMeleeReaderCheck"] + ([] if already_fixed else ["--expect-broken"]),
                   "melee-baseline")
    run([str(java_bin / "javac.exe"), "-encoding", "UTF-8", "--release", "21", "-cp", classpath,
         "-d", str(candidate_classes), str(candidate), str(fixture)], "compile-candidate")
    corrected = run([str(java_bin / "java.exe"), "-cp", str(candidate_classes) + os.pathsep + classpath,
                     "lab.owmcguest.WidowMeleeReaderCheck"], "melee-candidate")
    if reader_path.read_text(encoding="utf-8") != original:
        raise RuntimeError("Shared source changed concurrently; rerun against the integrated source")
    report = dict(compileClientJava=True, meleeBaseline=baseline.strip(), meleeCandidate=corrected.strip(),
                  baselineAlreadyFixed=already_fixed, sharedSourceUntouched=True, gameStarted=False,
                  jarBuilt=False, deployed=False, spiderLiveAcceptance=False)
    (EVIDENCE / "result.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False))


if __name__ == "__main__":
    main()
