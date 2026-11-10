"""Install/check the pinned official Sodium build in the private MC profile."""
from modpack.config import paths
import argparse, hashlib, json, urllib.request, zipfile
from pathlib import Path
from process_images import game_processes

ROOT = Path(__file__).resolve().parents[1]
PROFILE = paths().get('profile')
NAME = 'sodium-fabric-0.8.13+mc1.21.1.jar'
URL = 'https://cdn.modrinth.com/data/AANobbMI/versions/SMxNOGZ6/sodium-fabric-0.8.13%2Bmc1.21.1.jar'
SHA512 = '8614a374593698069a80ac74de8cd9c28f3928d16819a0e0d6320b538e823f7e54e8be06d5ea5a9c268beb0e02073209d1f831a02dede851588b972367680853'
SIZE = 1574609

def verify():
    target = PROFILE / 'mods' / NAME
    if not target.is_file():
        if paths().renderer_required():
            raise FileNotFoundError('Pinned renderer missing; run tools/render_optimization.py --install while the session is stopped')
    else:
        data = target.read_bytes()
        if len(data) != SIZE or hashlib.sha512(data).hexdigest() != SHA512:
            raise ValueError('Sodium artifact differs from the verified official build; refusing replacement')
    for path in target.parent.glob('*.jar'):
        if path == target:
            continue
        with zipfile.ZipFile(path) as jar:
            if 'fabric.mod.json' in jar.namelist():
                metadata = json.loads(jar.read('fabric.mod.json'))
                if metadata.get('id') in ('sodium', 'embeddium', 'optifabric', 'canvas', 'vulkanmod'):
                    raise ValueError('Conflicting renderer in private profile: ' + path.name)
    if not target.is_file():
        print('未安装可选 Sodium；将使用 Minecraft 原版渲染，性能仍需沙盒外实测。',flush=True)
        return None
    return target

def install():
    target = PROFILE / 'mods' / NAME
    if target.exists():
        return verify()
    if game_processes(profiles=(PROFILE,),java=paths().get('java')):
        raise RuntimeError('请先保存并结束游戏，再安装渲染器。')
    request = urllib.request.Request(URL, headers={'User-Agent': 'OWMC-local-lab/1.0'})
    with urllib.request.urlopen(request, timeout=30) as response:
        data = response.read(SIZE + 1)
    if len(data) != SIZE or hashlib.sha512(data).hexdigest() != SHA512:
        raise ValueError('Official renderer download failed size/SHA512 validation')
    target.parent.mkdir(parents=True, exist_ok=True)
    # Never overwrite another artifact, even if a concurrent installer won.
    with target.open('xb') as output:
        output.write(data)
    return verify()

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--install', action='store_true')
    arguments = parser.parse_args()
    print(install() if arguments.install else verify())
