"""第六次语音反馈：实际归档的变形提前、已验证中文素材唯一性/完整性。"""
import hashlib
import json
from pathlib import Path
import unittest
import prepare_hero_bastion_voice as bastion
from four_dps_voice_assets import CLIPS,SOURCE


class VoiceFeedback6Tests(unittest.TestCase):
    def test_real_bastion_transform_starts_1500_before_tank(self):
        root=Path(__file__).resolve().parents[1]
        d=json.loads((root/'research/bastion-tank-20261021/q-probe.json').read_text(encoding='utf-8'))
        rows=[r for f in d['action']['changes'] for r in f['changes'] if r['script']=='058000000000012f']
        first=next(r['nativeTick'] for r in rows if r['node']==123 and not r['finished'])
        tank=next(r['nativeTick'] for r in rows if r['node']==105 and not r['finished'])
        self.assertEqual(tank-first,1500)
        g=next(g for g in json.loads((root/'research/bastion-tank-20261021/graphs.json').read_text(encoding='utf-8'))['graphs'] if g['resource']=='058000000000012f')
        self.assertEqual(len(g['nodes']),192)
        for _,index,kind in bastion.PROFILE:self.assertEqual(int(g['nodes'][index]['type'],16),kind)

    def test_verified_existing_chinese_callout_is_single_and_intact(self):
        self.assertEqual(CLIPS['reaper.blossom'],[('reaper-blossom-ally','1d5aff1b7998a24aa681627cb26d21f4397d427b51f1c9a6524cb61523e031da')])
        sound=SOURCE/'reaper-blossom-ally.ogg'
        self.assertEqual(hashlib.sha256(sound.read_bytes()).hexdigest(),CLIPS['reaper.blossom'][0][1])
        root=Path(__file__).resolve().parents[1];rows=json.loads((root/'research/voice-catalog-20261025/download.json').read_text(encoding='utf-8'))
        self.assertFalse(any(r['hero']=='reaper' and r['event']=='ult_cast' for r in rows),'legacy owner must not duplicate the Q bank')


if __name__=='__main__':unittest.main()
