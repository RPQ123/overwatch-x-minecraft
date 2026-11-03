"""Launch the standalone Minecraft test window without attaching to Overwatch."""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PROFILE = ROOT / "guest-world-client"
WORLD = "Overwatch Minecraft World"
JAR = ROOT / "guest/build/libs/owmc-guest-0.1.0.jar"
SETTINGS = ROOT / "secondary-minecraft-settings.json"

sys.path.insert(0, str(ROOT / "tools"))
from launch_minecraft import build_command  # noqa: E402


def configure_profile() -> None:
    if not PROFILE.is_dir():
        raise FileNotFoundError(f"Missing standalone profile: {PROFILE}")
    if not (PROFILE / "saves" / WORLD / "level.dat").is_file():
        raise FileNotFoundError(f"Missing standalone save: {WORLD}")
    if not JAR.is_file():
        raise FileNotFoundError("Build guest first: tools\\build_guest.ps1 build")
    mods = PROFILE / "mods"
    mods.mkdir(parents=True, exist_ok=True)
    (mods / JAR.name).write_bytes(JAR.read_bytes())
    options = PROFILE / "options.txt"
    lines = options.read_text(encoding="utf-8").splitlines() if options.exists() else []
    values = {
        "renderDistance": "8",
        "fullscreen": "false",
        "pauseOnLostFocus": "false",
    }
    keys = set()
    output = []
    for line in lines:
        key = line.split(":", 1)[0]
        if key in values:
            if key not in keys:
                output.append(f"{key}:{values[key]}")
                keys.add(key)
        else:
            output.append(line)
    for key, value in values.items():
        if key not in keys:
            output.append(f"{key}:{value}")
    options.write_text("\n".join(output) + "\n", encoding="utf-8")


def command() -> list[str]:
    cmd = build_command()
    cmd[cmd.index("--gameDir") + 1] = str(PROFILE)
    # This is deliberately a standalone client: no frame exporter, host pose,
    # shared HTTP endpoint, or native callback owner is started.
    cmd[1:1] = ["-Dowmc.dayNightCycle=true"]
    cmd.extend(["--quickPlaySingleplayer", WORLD])
    return cmd


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    configure_profile()
    if args.check:
        print(json.dumps({
            "profile": str(PROFILE),
            "world": WORLD,
            "shaders": "off",
            "renderDistance": 8,
            "dayNightCycle": True,
            "overwatchAttached": False,
        }, ensure_ascii=False, indent=2))
        return 0
    log = PROFILE / "logs" / "secondary-launch.log"
    log.parent.mkdir(parents=True, exist_ok=True)
    process = subprocess.Popen(
        command(),
        cwd=PROFILE,
        stdout=log.open("w", encoding="utf-8"),
        stderr=subprocess.STDOUT,
        creationflags=subprocess.CREATE_NO_WINDOW,
    )
    print(json.dumps({"pid": process.pid, "profile": str(PROFILE), "world": WORLD}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
