"""Fault injection only; no game input or live bridge calls."""
import unittest
from unittest.mock import patch
import verify_twilight_native_fire as target

class CleanupTests(unittest.TestCase):
    def run_cleanup(self,drive_error=None,boss_error=None,active=False,read_error=None):
        world={'probeActive':active,'mobGriefing':True,'nearby':[]}
        def read(route):
            if read_error:raise read_error
            return world if route=='world' else {'wallBlocks':0}
        with patch.object(target,'drive',side_effect=drive_error) as drive,patch.object(target,'trial',side_effect=boss_error) as boss,patch.object(target,'post') as combat,patch.object(target,'api',side_effect=read),patch.object(target.time,'sleep'):
            result=target.cleanup(True)
            boss.assert_called_once_with('native-cleanup');combat.assert_called_once_with('cleanup')
        return result

    def test_lost_focus_still_cleans_boss_blocks_and_rule(self):
        result=self.run_cleanup(drive_error=RuntimeError('foreground: ChatGPT'))
        self.assertTrue(result['cleaned']);self.assertIn('foreground',result['inputCleanupError'])
        self.assertNotIn('cleanupError',result)

    def test_failed_boss_route_still_runs_combat_cleanup(self):
        result=self.run_cleanup(boss_error=OSError('bridge unavailable'))
        self.assertIn('boss:',result['cleanupError'])

    def test_remaining_boss_cannot_pass(self):
        result=self.run_cleanup(active=True)
        self.assertFalse(result['cleaned']);self.assertIn('restoration',result['cleanupError'])

    def test_unreadable_cleanup_state_is_not_success(self):
        result=self.run_cleanup(read_error=OSError('connection refused'))
        self.assertFalse(result['cleaned']);self.assertIn('verification:',result['cleanupError'])

if __name__=='__main__':unittest.main()
