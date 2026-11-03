"""Inspect bounded original OW depth captures; a delta is a candidate mask, not fidelity proof."""
from pathlib import Path
import argparse
import json
import struct
import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]

def raw(path):
    data = Path(path).read_bytes()
    if len(data) < 24 or data[:8] != b'OWRAW001':
        raise ValueError('Observation image identity')
    w, h, fmt, bpp = struct.unpack_from('<4I', data, 8)
    if not 1 <= w <= 4096 or not 1 <= h <= 2160 or bpp != 4 or len(data) != 24 + w*h*4:
        raise ValueError('Observation dimensions/payload')
    if fmt not in (28, 29, 44, 87):
        raise ValueError('Unsupported native observation format')
    return w, h, fmt, data[24:]

def depth_delta(before, after):
    if before[:3] != after[:3] or before[2] != 44:
        raise ValueError('Depth resource dimensions/format changed')
    w, h = before[:2]
    a = np.frombuffer(before[3], '<u4').reshape(h, w)
    b = np.frombuffer(after[3], '<u4').reshape(h, w)
    # Stencil is shared by world geometry and hands; its value alone is no classifier.
    return (a & 0xffffff) != (b & 0xffffff), (a >> 24) != (b >> 24)

def analyze(pid, directory):
    prefix = directory / f'hand-depth-{pid}'
    status = json.loads(prefix.with_suffix('.json').read_text())
    if status['failures'] or not all(status[k] for k in ('restored', 'beforeHand', 'afterHand', 'beforeHud', 'final')):
        raise ValueError(f'Incomplete original capture: {status}')
    before = raw(str(prefix) + '-before-hand-depth.raw')
    after = raw(str(prefix) + '-after-hand-depth.raw')
    mask, stencil = depth_delta(before, after)
    color = raw(str(prefix) + '-before-hud.raw')
    if color[:2] != before[:2] or color[2] not in (28, 29, 87):
        raise ValueError('Pre-HUD color resource mismatch')
    rgba = np.frombuffer(color[3], np.uint8).reshape(color[1], color[0], 4).copy()
    if color[2] == 87:rgba = rgba[:, :, [2, 1, 0, 3]]
    rgba[:, :, 3] = mask.astype(np.uint8) * 255
    Image.fromarray(rgba).save(str(prefix) + '-candidate-hand.png')
    # Explicit opaque diagnostic background: some image viewers discard PNG
    # alpha and otherwise misleadingly show the excluded original world pixels.
    Image.alpha_composite(Image.new('RGBA', (color[0], color[1]), (96, 96, 96, 255)), Image.fromarray(rgba)).convert('RGB').save(str(prefix)+'-candidate-visible.png')
    Image.fromarray(mask.astype(np.uint8) * 255).save(str(prefix) + '-candidate-mask.png')
    ys, xs = np.nonzero(mask)
    result = {'kind':'original-depth-delta-candidate', 'pid':pid,
              'width':before[0], 'height':before[1], 'changedDepthPixels':int(mask.sum()),
              'changedStencilPixels':int(stencil.sum()), 'coverage':float(mask.mean()),
              'bbox':None if not len(xs) else [int(xs.min()), int(ys.min()), int(xs.max()), int(ys.max())],
              'handDraws':status['handDraws'], 'nativeReplay':False,
              'depthMaskVerified':False, 'owMcCompositionVerified':False}
    if status.get('worldBlended'):
        mixed = raw(str(prefix)+'-world-blended.raw')
        final = raw(str(prefix)+'-final.raw')
        if mixed[:3] != color[:3] or final[:3] != color[:3]:
            raise ValueError('Fused/native color surfaces differ')
        native = np.frombuffer(color[3], np.uint8).reshape(color[1], color[0], 4)
        fused = np.frombuffer(mixed[3], np.uint8).reshape(color[1], color[0], 4)
        final_rgba = np.frombuffer(final[3], np.uint8).reshape(color[1], color[0], 4).copy()
        hand_exact = bool(np.array_equal(fused[mask], native[mask]))
        alpha_exact = bool(np.array_equal(fused[:, :, 3], native[:, :, 3]))
        changed = np.any(fused[:, :, :3] != native[:, :, :3], axis=2)
        if not hand_exact or not alpha_exact:
            raise ValueError('Native hand or alpha changed during world blend')
        if color[2] == 87:final_rgba = final_rgba[:, :, [2, 1, 0, 3]]
        final_rgba[:, :, 3] = 255
        Image.fromarray(final_rgba).save(str(prefix)+'-final.png')
        result.update(boundedWorldFrameVerified=True, handPixelsExact=True, nativeAlphaExact=True,
                      changedBackgroundPixels=int(np.count_nonzero(changed & ~mask)),
                      mcSourcePid=status['mcSourcePid'], mcGeneration=status['mcGeneration'], mcFrame=status['mcFrame'],
                      hostPoseConnected=False, continuousGameplayVerified=False, movingHandMaskVerified=False)
    Path(str(prefix)+'-analysis.json').write_text(json.dumps(result, indent=2)+'\n')
    print(json.dumps(result, indent=2))
    return result

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--pid', type=int, required=True)
    parser.add_argument('--directory', type=Path, default=ROOT/'native-host/build')
    args = parser.parse_args();analyze(args.pid, args.directory)
