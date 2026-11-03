"""离线语音恢复清单、逐事件白名单、下载域名及拒绝跳转检查；不联网。"""
import json
import hashlib
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import restore_voice_ultimates as restored
import voice_download as download


class UltimateVoicesTests(unittest.TestCase):
    def test_archived_earlier_windup_timestamps(self):
        for name,graph,first,later,delta in [
            ('mei-blizzard-calibration2','058000000000064a',1,10,500),
            ('widow-infra-calibration1','0580000000000067',18,6,650),
            ('generic2-Lucio','058000000000073a',9,0,660),
        ]:
            result=json.loads((restored.ROOT/'research/sprint-20261024'/name/'result.json').read_text(encoding='utf-8'))
            ticks={}
            for frame in result['trace']:
                if 'Q' not in frame.get('label',''):continue
                for row in frame['changes']:
                    if row['script']==graph and row['node'] in [first,later] and (not row['finished'] or row['node']==10 and first==1):
                        ticks.setdefault(row['node'],row['nativeTick'])
            self.assertEqual(ticks[later]-ticks[first],delta)
        result=json.loads((restored.ROOT/'research/pulse-bomb-20261021/q-probe.json').read_text(encoding='utf-8'))
        rows=[r for f in result['samples'] for r in f['changes'] if r['script']=='0580000000000034']
        cast=next(r['nativeTick'] for r in rows if r['node']==3 and not r['finished'])
        deploy=next(r['nativeTick'] for r in rows if r['node']==1)
        self.assertEqual(deploy-cast,150)

    def test_exact_roster_and_event_scopes(self):
        rows=restored.additions()
        self.assertEqual(len(rows),24);self.assertEqual(len(restored.READY),21)
        self.assertEqual(len({r['hero'] for r in rows if r['event']=='ult_ready'}),21)
        self.assertTrue(all(download.approved_url(r) for r in rows))
        for row in rows:
            self.assertTrue(restored.selected(row['hero'],row['event'],row['hash']))
            self.assertFalse(restored.selected(row['hero'],'jump',row['hash']))
        catalog=json.loads((restored.ROOT/'research/voice-catalog-20261025/download.json').read_text(encoding='utf-8'))
        self.assertEqual(len(catalog),785)
        self.assertEqual(sum(r['event']=='ult_ready' for r in catalog),21)
        self.assertTrue(all(r in catalog for r in rows))

    def test_only_approved_host_hash_and_no_cross_host_redirect(self):
        row=restored.additions()[0]
        for url in ['https://evil.example/'+row['hash']+'.mp3',row['url'].replace(row['hash'],'0'*32),
                    row['url'].replace('://','://user:pass@'),'file:///tmp/'+row['hash']+'.mp3']:
            self.assertFalse(download.approved_url(dict(row,url=url)))
        with self.assertRaisesRegex(ValueError,'Unapproved redirect'):
            download.ApprovedRedirect(row).redirect_request(None,None,302,'redirect',{},'https://evil.example/audio.mp3')

    def test_dry_run_never_writes_or_opens_network(self):
        row=restored.additions()[0]
        with tempfile.TemporaryDirectory(prefix='owmc-voice-ready-') as temp:
            root=Path(temp);listing=root/'list.json';listing.write_text(json.dumps([row]),encoding='utf-8')
            target=root/'absent-private'
            with patch.object(download,'DEST',target),patch('sys.argv',['voice_download.py','--list',str(listing),'--dry-run']),patch('urllib.request.build_opener',side_effect=AssertionError('must not access network')):
                download.main()
            self.assertFalse(target.exists())

    def test_pruned_local_mp3_restores_manifest_without_network(self):
        row=restored.additions()[0];audio=b'ID3'+bytes(700)
        with tempfile.TemporaryDirectory(prefix='owmc-voice-reuse-') as temp:
            root=Path(temp);listing=root/'list.json';listing.write_text(json.dumps([row]),encoding='utf-8')
            target=root/'private';clip=target/row['hero']/(row['hash']+'.mp3');clip.parent.mkdir(parents=True);clip.write_bytes(audio)
            with patch.object(download,'DEST',target),patch('sys.argv',['voice_download.py','--list',str(listing)]),patch('urllib.request.build_opener',side_effect=AssertionError('existing MP3 must not download')):
                self.assertEqual(download.main(),0)
            manifest=json.loads((target/'manifest.json').read_text(encoding='utf-8'))
            entry=manifest[row['hash']]
            self.assertEqual((entry['hero'],entry['event']),(row['hero'],row['event']))
            self.assertEqual(entry['sha256'],hashlib.sha256(audio).hexdigest());self.assertTrue(entry['reusedLocal'])
            self.assertEqual(clip.read_bytes(),audio)


if __name__=='__main__':unittest.main()
