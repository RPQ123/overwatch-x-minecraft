"""Run a separate original MC world solely to export its baked proof block."""
from pathlib import Path
import shutil
import subprocess
import argparse
from launch_minecraft import ROOT, GAME, build_command

PROFILE = ROOT / "guest-client"
if __name__ == "__main__":
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--patch",action="store_true")
    parser.add_argument("--creative",action="store_true")
    parser.add_argument("--new-world",action="store_true")
    args=parser.parse_args()
    if args.new_world:args.creative=True
    if args.creative: args.patch=True
    if args.patch: PROFILE=ROOT/"guest-patch-client"
    if args.creative: PROFILE=ROOT/"guest-creative-client"
    if args.new_world: PROFILE=ROOT/"guest-world-client"
    (PROFILE / "mods").mkdir(parents=True, exist_ok=True)
    jar = ROOT / "guest/build/libs/owmc-guest-0.1.0.jar"
    shutil.copy2(jar, PROFILE / "mods" / jar.name)
    api, = (GAME / "mods").glob("fabric-api-*.jar")
    shutil.copy2(api, PROFILE / "mods" / api.name)
    options = PROFILE / "options.txt"
    if not options.exists():
        options.write_text("onboardAccessibility:false\ntutorialStep:none\npauseOnLostFocus:false\n"
                           "renderDistance:4\nsimulationDistance:4\nguiScale:2\nfullscreen:false\nmaxFps:20\n", encoding="utf-8")
    world = PROFILE / ("saves/Overwatch Creative Flat" if args.creative else "saves/Overwatch Patch Lab" if args.patch else "saves/Overwatch Guest Export")
    if not args.new_world and not world.exists():
        world.parent.mkdir(parents=True, exist_ok=True)
        source=ROOT/"guest-client/saves/Overwatch Guest Export" if args.patch else ROOT/"combat/build/gametest-world/world"
        shutil.copytree(source,world)
    command = build_command()
    command[command.index("--gameDir") + 1] = str(PROFILE)
    command[1:1] = [("-Dowmc.exportPatch=true" if args.patch else "-Dowmc.exportProof=true"),
                   "-Dowmc.exportDirectory=" + str(ROOT / "native-host/build")]
    if args.patch: command[1:1]=["-Dowmc.backgroundExport=true"]
    if args.creative: command[1:1]=["-Dowmc.creativeFlat=true"]
    if args.new_world:command[1:1]=["-Dowmc.newWorld=true"]
    else:command.extend(["--quickPlaySingleplayer", world.name])
    (PROFILE / "logs").mkdir(exist_ok=True)
    with (PROFILE / "logs/launch.log").open("w", encoding="utf-8") as output:
        raise SystemExit(subprocess.call(command, cwd=PROFILE, stdout=output, stderr=subprocess.STDOUT))
