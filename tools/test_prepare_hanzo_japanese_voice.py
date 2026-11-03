"""只在系统Temp复制夹具，验证离线安装/回滚保护，不修改真实私有素材或游戏。"""
import json
from pathlib import Path
import shutil
import tempfile
import unittest
from unittest.mock import patch
import prepare_hanzo_japanese_voice as voice


class HanzoVoicePrepareTests(unittest.TestCase):
    def test_sha_provenance_install_idempotence_and_modified_file_guard(self):
        with tempfile.TemporaryDirectory(prefix='owmc-voice-fixture-') as temp:
            base=Path(temp);assets=base/'assets';full=assets/'thnu-full';full.mkdir(parents=True)
            for relative in ['bili-BV1Hs411q779/P10-audio.m4s','four-dps-20261023/actual-reference-audio-asr.json']:
                destination=assets/relative;destination.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(voice.ASSETS/relative,destination)
            original={'old-hanzo':dict(hero='hanzo',event='ult_cast'),'mei-wall':dict(hero='mei',event='ability:ice_wall')}
            manifest=full/'manifest.json';manifest.write_text(json.dumps(original),encoding='utf-8')
            with patch.object(voice,'ASSETS',assets),patch.object(voice,'OUTPUT',base/'review'),patch.object(voice,'ROOT',base/'repo'):
                result=voice.prepare(install=True,quiet=True)
                installed=json.loads(manifest.read_text(encoding='utf-8'))
                self.assertEqual(set(installed),{'mei-wall',voice.DERIVED_ID})
                self.assertEqual(installed['mei-wall'],original['mei-wall'])
                self.assertGreater(result['correlation'],.97)
                self.assertEqual(result['languageEvidence']['record']['language'],'ja')
                self.assertLess(len(result['listeningCandidates']),4)
                before=manifest.read_bytes();voice.prepare(install=True,quiet=True);self.assertEqual(before,manifest.read_bytes())
                self.assertEqual(json.loads((full/'manifest.before-hanzo-ja-20261027.json').read_text(encoding='utf-8')),original)
                target=full/'hanzo'/(voice.DERIVED_ID+'.mp3');target.write_bytes(b'user changed audio')
                with self.assertRaisesRegex(ValueError,'已有不同'):
                    voice.prepare(install=True,quiet=True)
                self.assertEqual(target.read_bytes(),b'user changed audio');self.assertEqual(before,manifest.read_bytes())
                custom=base/'custom/manifest.json';custom.parent.mkdir();custom.write_text(json.dumps(original),encoding='utf-8')
                voice.prepare(install=True,quiet=True,target_manifest=custom)
                self.assertIn(voice.DERIVED_ID,json.loads(custom.read_text(encoding='utf-8')))
                self.assertEqual(before,manifest.read_bytes()) # 自定义清单不写默认素材目录。


if __name__=='__main__':unittest.main()
