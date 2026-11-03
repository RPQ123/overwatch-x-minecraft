"""Download the pinned Minecraft lab from Mojang and Fabric; does not log in or launch."""
from modpack.config import paths
from pathlib import Path
import hashlib
import json
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools" / "python"))
import requests
import minecraft_launcher_lib as mc

GAME = paths().get('minecraft')
VERSION = "1.21.1"
LOADER = "0.19.5"
last_report = 0.0


def status(message):
    global last_report
    now = time.monotonic()
    if now - last_report > 15 or message in (
        "Download Libraries", "Download Assets", "Install java runtime", "Installation complete"
    ):
        print(message, flush=True)
        last_report = now


def sha1(path):
    with path.open("rb") as file:
        return hashlib.file_digest(file, "sha1").hexdigest()


if __name__ == "__main__":
    GAME.mkdir(exist_ok=True)
    for attempt in range(3):
        try:
            mc.install.install_minecraft_version(VERSION, GAME, callback={"setStatus": status})
            break
        except Exception as error:
            print(f"Install attempt {attempt + 1}: {error}", flush=True)
            if attempt == 2:
                raise
            time.sleep(3)

    # Fabric's official launcher profile avoids running a separate installer.
    url = f"https://meta.fabricmc.net/v2/versions/loader/{VERSION}/{LOADER}/profile/json"
    response = requests.get(url, timeout=30)
    response.raise_for_status()
    profile = response.json()
    profile_dir = GAME / "versions" / profile["id"]
    profile_dir.mkdir(parents=True, exist_ok=True)
    (profile_dir / f'{profile["id"]}.json').write_text(json.dumps(profile, indent=2), encoding="utf-8")
    mc.install.install_minecraft_version(profile["id"], GAME, callback={"setStatus": status})

    base = json.loads((GAME / "versions" / VERSION / f"{VERSION}.json").read_text())
    client = GAME / "versions" / VERSION / f"{VERSION}.jar"
    if sha1(client) != base["downloads"]["client"]["sha1"]:
        raise RuntimeError("Minecraft client checksum mismatch")
    index = json.loads((GAME / "assets" / "indexes" / f'{base["assets"]}.json').read_text())
    hashes = {asset["hash"] for asset in index["objects"].values()}
    invalid = [value for value in hashes if not (GAME / "assets" / "objects" / value[:2] / value).is_file()
               or sha1(GAME / "assets" / "objects" / value[:2] / value) != value]
    if invalid:
        raise RuntimeError(f"{len(invalid)} asset files missing or invalid")
    java = mc.runtime.get_executable_path(base["javaVersion"]["component"], GAME)
    if not java or not Path(java).is_file():
        raise RuntimeError("Java runtime missing")
    report = {"minecraft": VERSION, "fabric_loader": LOADER, "fabric_profile": profile["id"],
              "client_sha1": sha1(client), "verified_asset_objects": len(hashes), "java": java,
              "authentication": "Not performed; use an account-enabled launcher", "game_launched": False}
    (GAME / "installation-report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2), flush=True)
