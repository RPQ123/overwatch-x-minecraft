"""离线核对实测归档节点/时间与默认清单；不附加进程、不按键、不播放声音。"""
import json
from pathlib import Path
import unittest
import prepare_hero_hanzo_voice as begin
import prune_voice_defaults as prune

ROOT=Path(__file__).resolve().parents[1]


class VoiceBeginTests(unittest.TestCase):
    def test_archived_cast_message_precedes_release(self):
        trace=json.loads((ROOT/'research/sprint-20261024/hanzo-dragon-calibration1/result.json').read_text(encoding='utf-8'))
        rows={r['node']:r for r in trace['nativeAfterE']['records'].values() if r['script']=='05800000000000b9'}
        config=json.loads((ROOT/'research/sprint-20261024/hanzo-current-calibration1/sonic-config.json').read_text(encoding='utf-8'))
        graph=next(g for g in config['graphs'] if g['resource']=='05800000000000b9')
        self.assertEqual(len(graph['nodes']),117)
        for _,index,kind in begin.PROFILE:self.assertEqual(int(graph['nodes'][index]['data']['type'],16),kind)
        self.assertTrue(rows[79]['finished'])  # 瞬时消息已结束也必须消费tick，不能要求active。
        self.assertFalse(rows[79]['weaponVolleyNode']);self.assertTrue(rows[76]['weaponVolleyNode'])
        self.assertEqual(rows[76]['nativeTick']-rows[79]['nativeTick'],1400)
        self.assertEqual(rows[80]['nativeTick']-rows[76]['nativeTick'],200)
        wait=graph['nodes'][80]['data']['fields']['db0e39db']['literal']
        self.assertAlmostEqual(wait,.2,places=6)
        expected_advance=(rows[76]['nativeTick']-rows[79]['nativeTick'])*wait/(rows[80]['nativeTick']-rows[76]['nativeTick'])
        self.assertAlmostEqual(expected_advance,1.4,places=6)

    def test_current_catalog_has_no_movement_and_generator_cannot_restore_it(self):
        catalog=json.loads((ROOT/'research/voice-catalog-20261025/download.json').read_text(encoding='utf-8'))
        self.assertEqual(len(catalog),785)
        self.assertFalse(any(r['event'] in prune.MOVEMENT for r in catalog))
        for event in prune.MOVEMENT:
            self.assertEqual(prune.reason('hanzo',dict(event=event,hash='0'*32,text='【半藏】测试')), 'movement_voice')
        self.assertIn('ability:scatter_arrow',{r['event'] for r in catalog})
        self.assertEqual([r['hash'] for r in catalog if r['hero']=='hanzo' and r['event']=='ult_cast'],[prune.HANZO_ULT_HASH])


if __name__=='__main__':unittest.main()
