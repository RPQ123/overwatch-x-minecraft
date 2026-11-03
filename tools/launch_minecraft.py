"""Launch the local Fabric client for this project's offline development tests."""
from modpack.config import paths
from pathlib import Path
import argparse
import json
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools" / "python"))
from minecraft_launcher_lib.command import get_minecraft_command
from modpack.account import launch_options

GAME = paths().get('minecraft')
VERSION = "fabric-loader-0.19.5-1.21.1"


def build_command(*, account_provider=None):
    if not (GAME / "versions" / VERSION / f"{VERSION}.json").is_file():
        raise FileNotFoundError("Local Fabric client missing; run tools/install_minecraft.py first.")
    configured = paths()
    java = str(configured.get('java'))
    if not Path(java).is_file():
        raise FileNotFoundError("The downloaded Java 21 runtime is missing.")
    identity, development = launch_options(configured, account_provider)
    options = {
        **identity,
        "executablePath": java,
        "launcherName": "Overwatch-Minecraft-Development-Lab",
        "launcherVersion": "0.1.0",
        "jvmArguments": [
            "-Xms1G", "-Xmx4G",
            *(["-Dminecraft.api.session.host=http://127.0.0.1:9",
               "-Dminecraft.api.services.host=http://127.0.0.1:9"] if development else []),
        ],
        "disableMultiplayer": True,
        "customResolution": True,
        "resolutionWidth": "1280",
        "resolutionHeight": "720",
    }
    command = get_minecraft_command(VERSION, GAME, options)
    # These optional account identifiers do not exist in a development session.
    for flag in (("--clientId", "--xuid") if development else ()):
        if flag in command:
            index = command.index(flag)
            del command[index:index + 2]
    classpath = command[command.index("-cp") + 1]
    missing = [item for item in classpath.split(";") if not Path(item).is_file()]
    if missing:
        raise FileNotFoundError("Missing local game libraries: " + ", ".join(missing))
    if any("${" in argument for argument in command):
        raise ValueError("Unresolved placeholder in launch command.")
    return command


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="Check local files without opening the game")
    args = parser.parse_args()
    try:
        command = build_command()
        if args.check:
            print(json.dumps({"version": VERSION, "mode": "offline-development",
                              "local_classpath_files": len(command[command.index("-cp") + 1].split(";")),
                              "java": command[0], "multiplayer_disabled": True}, indent=2))
        else:
            logs = GAME / "logs"
            logs.mkdir(exist_ok=True)
            print("Starting the offline development client. Online multiplayer is disabled.", flush=True)
            print(f"Launch log: {logs / 'offline-launch.log'}", flush=True)
            with (logs / "offline-launch.log").open("w", encoding="utf-8") as output:
                raise SystemExit(subprocess.call(command, cwd=GAME, stdout=output, stderr=subprocess.STDOUT))
    except (OSError, ValueError, KeyError) as error:
        print(f"Minecraft launch failed: {error}", file=sys.stderr)
        raise SystemExit(1)
