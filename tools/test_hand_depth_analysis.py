import struct
import tempfile
from pathlib import Path
import unittest
import json
import io
from contextlib import redirect_stdout
import numpy as np
from analyze_hand_depth import depth_delta, raw, analyze

class DepthObservationCheck(unittest.TestCase):
    def test_stencil_reuse_does_not_become_a_hand(self):
        before = (2, 2, 44, np.array([0x00123456]*4, '<u4').tobytes())
        after = (2, 2, 44, np.array([0x60123456, 0x00123457, 0x20123456, 0x00123456], '<u4').tobytes())
        mask, stencil = depth_delta(before, after)
        self.assertEqual(mask.tolist(), [[False, True], [False, False]])
        self.assertEqual(stencil.tolist(), [[True, False], [True, False]])
    def test_resource_mismatch_is_rejected(self):
        before = (2, 2, 44, bytes(16))
        with self.assertRaises(ValueError):depth_delta(before, (1, 4, 44, bytes(16)))
        with self.assertRaises(ValueError):depth_delta(before, (2, 2, 28, bytes(16)))
    def test_truncated_observation_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory)/'capture.raw'
            path.write_bytes(b'OWRAW001'+struct.pack('<4I', 2, 2, 44, 4)+bytes(15))
            with self.assertRaises(ValueError):raw(path)
            path.write_bytes(b'OWRAW001'+struct.pack('<4I', 2, 2, 44, 4)+bytes(16))
            self.assertEqual(raw(path)[:3], (2, 2, 44))
    def test_bounded_blend_preserves_exact_hand_and_alpha(self):
        with tempfile.TemporaryDirectory() as directory:
            directory = Path(directory);prefix = directory/'hand-depth-42'
            def save(name, fmt, data):
                Path(str(prefix)+'-'+name+'.raw').write_bytes(b'OWRAW001'+struct.pack('<4I', 2, 2, fmt, 4)+data)
            status = {k:True for k in ('restored','beforeHand','afterHand','beforeHud','final','worldBlended')}
            status.update(failures=0, handDraws=1, mcSourcePid=43, mcGeneration=1, mcFrame=7)
            prefix.with_suffix('.json').write_text(json.dumps(status))
            save('before-hand-depth', 44, np.zeros(4, '<u4').tobytes())
            save('after-hand-depth', 44, np.array([1,0,0,0], '<u4').tobytes())
            native = np.array([[255,0,0,123]]*4, np.uint8)
            fused = np.array([[255,0,0,123], [0,0,255,123], [0,0,255,123], [0,0,255,123]], np.uint8)
            save('before-hud', 28, native.tobytes());save('world-blended', 28, fused.tobytes());save('final', 28, fused.tobytes())
            with redirect_stdout(io.StringIO()):result = analyze(42, directory)
            self.assertTrue(result['handPixelsExact']);self.assertTrue(result['nativeAlphaExact'])
            self.assertEqual(result['changedBackgroundPixels'], 3)
            self.assertFalse(result['continuousGameplayVerified'])
            fused[0,0] = 254;save('world-blended', 28, fused.tobytes())
            with self.assertRaisesRegex(ValueError, 'Native hand or alpha'):analyze(42, directory)
            fused[0,0] = 255;fused[3,3] = 255;save('world-blended', 28, fused.tobytes())
            with self.assertRaisesRegex(ValueError, 'Native hand or alpha'):analyze(42, directory)

if __name__ == '__main__':unittest.main()
