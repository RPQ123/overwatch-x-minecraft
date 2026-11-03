"""Read-only migration checks. Does not launch games, change saves or attach modules."""
from modpack.config import paths
import hashlib
import importlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]


def main():
    checks = []

    def check(name, action):
        try:
            detail = action()
            checks.append({"name": name, "ok": True, "detail": detail})
        except Exception as error:
            checks.append({"name": name, "ok": False, "detail": str(error)})

    def require(condition, message):
        if not condition:
            raise RuntimeError(message)
        return message

    check("python", lambda: require(sys.version_info >= (3, 13),
          "Python 3.13+ required; current " + sys.version.split()[0]))
    for module in ("psutil", "numpy", "PIL", "minecraft_launcher_lib", "websockets", "bson"):
        check("import:" + module, lambda module=module: str(importlib.import_module(module).__file__))

    def minecraft():
        from launch_minecraft import build_command
        command = build_command()
        return {"java": command[0], "classpathFiles": len(command[command.index("-cp") + 1].split(";"))}

    # build_command writes an identity only when absent; refuse that case in this read-only check.
    if paths().account_mode() == 'development-offline' and (paths().get('minecraft') / 'development-identity.json').is_file():
        check("minecraft", minecraft)
    else:
        checks.append({"name": "minecraft", "ok": False, "detail": "离线开发身份缺失，或尚未接入外部账号提供方；未读取凭据。"})

    def native_executable():
        from observe_overwatch import PATCHED_SHA256
        executable = paths().get('owExecutable')
        digest = hashlib.sha256(executable.read_bytes()).hexdigest()
        require(digest == PATCHED_SHA256, "Research executable SHA256 must match the exact supported build")
        return digest

    check("researchExecutable", native_executable)

    def artifacts():
        from launch_passthrough_session import NATIVE_FILES,BOOTSTRAP_DLL
        paths = [ROOT / "native-host/build" / name for name in
                 [*NATIVE_FILES.values(), BOOTSTRAP_DLL, "owmc-local-hero-spawn-v1.dll"]]
        paths.append(ROOT / "guest/build/libs/owmc-guest-0.1.0.jar")
        missing = [str(path.relative_to(ROOT)) for path in paths if not path.is_file()]
        require(not missing, "Missing artifacts: " + ", ".join(missing))
        return {str(path.relative_to(ROOT)): hashlib.sha256(path.read_bytes()).hexdigest() for path in paths}

    check("launchArtifacts", artifacts)
    from render_optimization import verify as verify_renderer
    check("minecraftRenderer", lambda: str(verify_renderer()))

    def compiler():
        local = ROOT / "tools/mingw64/bin/g++.exe"
        user = Path(os.environ.get("LOCALAPPDATA", "")) / "OWMC/toolchains/mingw64/bin/g++.exe"
        executable = os.environ.get("OWMC_CXX") or next(
            (str(path) for path in (local, user) if path.is_file()), shutil.which("g++"))
        require(bool(executable), "MinGW-w64 missing: tools/mingw64 or OWMC_CXX")
        target = subprocess.check_output([executable, "-dumpmachine"], text=True).strip()
        require(target == "x86_64-w64-mingw32", "Unsupported compiler target: " + target)
        return {"path": executable, "target": target}

    if paths().packaged:
        checks.append({"name":"nativeCompiler","ok":True,"detail":"预构建运行包不需要本机编译器。"})
    else:
        check("nativeCompiler", compiler)
    result = {"root": str(ROOT), "python": sys.executable, "ok": all(c["ok"] for c in checks), "checks": checks}
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
