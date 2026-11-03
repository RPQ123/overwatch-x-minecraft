"""Launch an isolated real Minecraft combat profile; keep existing worlds separate."""
from pathlib import Path
import argparse
import json
import shutil
import subprocess
from launch_minecraft import build_command, GAME, ROOT

PROFILE = ROOT / "combat-client"
WORLD = PROFILE / "saves/Overwatch Combat Lab"

def prepare(showcase=False,minecraft_world=False):
    PROFILE.mkdir(exist_ok=True)
    (PROFILE / "mods").mkdir(exist_ok=True)
    jar = ROOT / "combat/build/libs/owcombat-0.2.0.jar"
    if not jar.is_file():
        raise FileNotFoundError("Build the combat mod with tools/build_combat.ps1 first")
    shutil.copy2(jar, PROFILE / "mods" / jar.name)
    apis = list((GAME / "mods").glob("fabric-api-*.jar"))
    if len(apis) != 1:
        raise ValueError("Expected one verified Fabric API in the original lab")
    shutil.copy2(apis[0], PROFILE / "mods" / apis[0].name)
    options = PROFILE / "options.txt"
    if not options.exists():
        options.write_text("lang:zh_cn\nonboardAccessibility:false\ntutorialStep:none\nguiScale:2\n"
                           "fullscreen:false\npauseOnLostFocus:false\nrenderDistance:8\nsimulationDistance:5\n", encoding="utf-8")
    if not minecraft_world and not WORLD.exists():
        source = ROOT / "combat/build/gametest-world/world"
        if not (source / "level.dat").is_file():
            raise FileNotFoundError("Run the isolated Minecraft GameTests to prepare the lab world first")
        WORLD.parent.mkdir(exist_ok=True)
        shutil.copytree(source, WORLD)
    command = build_command()
    command[command.index("--gameDir") + 1] = str(PROFILE)
    if minecraft_world:command.insert(1,'-Dowcombat.minecraftWorld=true')
    else:command.extend(["--quickPlaySingleplayer", WORLD.name])
    if showcase:
        command.insert(1, "-Dowcombat.showcase=true")
    return command

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--showcase", action="store_true", help="Run the isolated Genji/Pharah demo arena")
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--minecraft-world",action="store_true",help="Visible Minecraft with a genuinely new superflat world and hero controls")
    args = parser.parse_args()
    if args.minecraft_world:
        PROFILE=ROOT/'minecraft-overwatch-client';WORLD=PROFILE/'saves/Overwatch Superflat'
    command = prepare(args.showcase,args.minecraft_world)
    if args.check:
        print(json.dumps({"profile": str(PROFILE), "world": WORLD.name, "showcase": args.showcase}))
    else:
        (PROFILE / "logs").mkdir(exist_ok=True)
        with (PROFILE / "logs/launch.log").open("w", encoding="utf-8") as output:
            raise SystemExit(subprocess.call(command, cwd=PROFILE, stdout=output, stderr=subprocess.STDOUT))
