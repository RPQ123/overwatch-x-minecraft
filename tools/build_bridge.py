"""Build a Fabric diagnostic mod that needs no Minecraft class remapping."""
from pathlib import Path
import subprocess
import zipfile

ROOT = Path(__file__).resolve().parents[1]
GAME = ROOT / "minecraft-1.21.1"
JDK = GAME / "runtime/java-runtime-delta/windows-x64/java-runtime-delta/bin"
LOADER = GAME / "libraries/net/fabricmc/fabric-loader/0.19.5/fabric-loader-0.19.5.jar"
GSON = GAME / "libraries/com/google/code/gson/gson/2.10.1/gson-2.10.1.jar"
CLASSES = ROOT / "bridge/build/classes"

if __name__ == "__main__":
    CLASSES.mkdir(parents=True, exist_ok=True)
    sources = list((ROOT / "bridge/src").rglob("*.java"))
    subprocess.run([str(JDK / "javac.exe"), "--release", "21", "-encoding", "UTF-8", "-cp",
                    str(LOADER) + ";" + str(GSON), "-d", str(CLASSES), *map(str, sources)], check=True)
    output = ROOT / "bridge/build/owbridge-0.1.0.jar"
    with zipfile.ZipFile(output, "w", zipfile.ZIP_DEFLATED) as jar:
        for path in CLASSES.rglob("*.class"):
            jar.write(path, path.relative_to(CLASSES).as_posix())
        for path in (ROOT / "bridge/resources").rglob("*"):
            if path.is_file(): jar.write(path, path.relative_to(ROOT / "bridge/resources").as_posix())
    print(output)
