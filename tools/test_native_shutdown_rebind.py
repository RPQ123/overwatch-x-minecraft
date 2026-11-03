"""Current-admin replacement shutdown proof, using only fake process memory."""
import hashlib
import json
from pathlib import Path
import struct
import tempfile
import unittest
from unittest.mock import Mock, patch

import native_normal_close as close
import diagnose_native_shutdown_readonly as diagnostic


class ReboundSystemTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.target = Path(self.temp.name)/'inject.dll'
        self.target.write_bytes(b'corrected-fixture')
        self.sha = hashlib.sha256(self.target.read_bytes()).hexdigest()
        self.base, self.plugin = 0x10000000, 0x20000000
        self.admin, self.old_admin = 0x30000000, 0x31000000
        self.cached, self.current, self.items = 0x32000000, 0x33000000, 0x34000000
        self.memory = {}
        self.q(self.base+0x17b7f90, self.admin)
        self.q(self.plugin+0x2d0338, self.cached)
        self.q(self.cached, self.plugin+close.VTABLE)
        self.q(self.cached+8, self.old_admin)
        self.q(self.current, self.plugin+close.VTABLE)
        self.q(self.current+8, self.admin)
        self.q(self.plugin+close.SLOT, self.plugin+close.ZERO)
        self.memory[(self.plugin+close.ZERO,3)] = b'\x33\xc0\xc3'
        self.registry([self.current])
        self.process = Mock(base=self.base)
        self.process.read.side_effect = self.read
        self.primitive = Mock()
        self.primitive.snapshot.side_effect = ValueError('System singleton does not belong to current admin')
        self.patches = [patch.object(close, 'provided_plugin', return_value=(self.plugin,None,None)),
                        patch.object(close, 'TARGET', self.target), patch.object(close, 'CORRECTED', self.sha)]
        for entry in self.patches:
            entry.start()
            self.addCleanup(entry.stop)

    def q(self, address, value):
        self.memory[(address,8)] = struct.pack('<Q',value)

    def registry(self, values):
        self.memory[(self.admin+0xd8,16)] = struct.pack('<Qii',self.items,len(values),len(values))
        self.memory[(self.items,len(values)*8)] = struct.pack('<'+'Q'*len(values),*values)

    def read(self, address, size):
        try:
            return self.memory[(address,size)]
        except KeyError:
            raise OSError('fixture unreadable memory')

    def snapshot(self):
        return close.shutdown_snapshot(self.process,self.primitive)

    def test_unique_current_admin_replacement_proves_correct_shared_abi(self):
        result = self.snapshot()
        self.assertEqual(result['verificationRoute'],'current-admin-registry')
        self.assertEqual(result['instance'],self.current)
        self.assertEqual(result['cachedSingleton'],self.cached)
        self.assertEqual(result['cachedSingletonAdmin'],self.old_admin)
        self.assertEqual(result['admin'],self.admin)
        self.assertTrue(result['mappedAbiValid'])
        self.primitive.close_window.assert_not_called()

    def test_original_snapshot_is_used_when_valid(self):
        self.primitive.snapshot.side_effect = None
        self.primitive.snapshot.return_value = {'accepted':'unchanged verifier'}
        with patch.object(close,'inspect_shutdown_system') as inspect:
            self.assertEqual(self.snapshot(),{'accepted':'unchanged verifier'})
        inspect.assert_not_called()

    def test_other_verifier_error_is_never_bypassed(self):
        self.primitive.snapshot.side_effect = ValueError('Mapped ASLR-adjusted interface differs')
        with patch.object(close,'inspect_shutdown_system') as inspect:
            with self.assertRaisesRegex(ValueError,'ASLR'):
                self.snapshot()
        inspect.assert_not_called()

    def test_singleton_owner_mismatch_alone_is_not_proof(self):
        self.registry([self.cached])
        with self.assertRaisesRegex(ValueError,'No proved current-admin replacement'):
            self.snapshot()

    def test_replacement_must_belong_to_current_admin(self):
        self.q(self.current+8,self.old_admin)
        with self.assertRaisesRegex(ValueError,'No proved'):
            self.snapshot()

    def test_duplicate_systems_are_refused(self):
        self.registry([self.current,self.cached])
        with self.assertRaisesRegex(ValueError,'No proved'):
            self.snapshot()

    def test_missing_or_destructed_singleton_is_not_a_safe_close_shortcut(self):
        for state in ('null','unreadable','changed-type'):
            with self.subTest(state=state):
                self.q(self.plugin+0x2d0338,self.cached if state!='null' else 0)
                self.q(self.cached,self.plugin+close.VTABLE if state!='changed-type' else self.plugin+0x1234)
                if state=='unreadable':self.memory.pop((self.cached,8))
                with self.assertRaisesRegex(ValueError,'No proved'):
                    self.snapshot()

    def test_mapped_slot_and_zero_code_are_required(self):
        self.q(self.plugin+close.SLOT,self.plugin+close.ZERO+8)
        with self.assertRaisesRegex(ValueError,'No proved'):
            self.snapshot()
        self.q(self.plugin+close.SLOT,self.plugin+close.ZERO)
        self.memory[(self.plugin+close.ZERO,3)] = b'\xc3\xcc\xcc'
        with self.assertRaisesRegex(ValueError,'No proved'):
            self.snapshot()

    def test_wrong_disk_hash_cannot_authorize_rebind(self):
        self.target.write_bytes(b'changed')
        with self.assertRaisesRegex(ValueError,'Corrected plugin'):
            self.snapshot()

    def test_admin_change_during_read_is_refused(self):
        read = self.read
        calls = 0
        def changing(address,size):
            nonlocal calls
            if address==self.base+0x17b7f90:
                calls+=1
                if calls>1:return struct.pack('<Q',self.admin+0x10000)
            return read(address,size)
        self.process.read.side_effect = changing
        with self.assertRaisesRegex(ValueError,'No proved'):
            self.snapshot()

    def test_unreadable_system_entry_cannot_be_skipped(self):
        self.registry([self.current,0x35000000])
        with self.assertRaises(OSError):
            self.snapshot()

    def normal_fixture(self):
        import test_native_normal_close as existing
        fixture=existing.NormalCloseTests('test_complete_restoration_before_original_close')
        fixture.setUp()
        self.addCleanup(fixture.tearDown)
        fixture.primitives.snapshot.side_effect=ValueError('System singleton does not belong to current admin')
        return fixture

    def test_rebind_still_restores_every_owner_before_wm_close(self):
        state=close.inspect_shutdown_system(self.process)
        fixture=self.normal_fixture()
        def window(pid):
            for prefix,_ in close.OWNERS:
                self.assertTrue(json.loads((fixture.reports/f'{prefix}-10.json').read_text())['restored'])
            return 20
        fixture.primitives.close_window.side_effect=window
        with patch.object(close,'inspect_shutdown_system',return_value=state) as inspect:
            result=fixture.run_close()
        self.assertTrue(result['normalClosePassed'])
        self.assertEqual(inspect.call_count,2)
        self.assertEqual(result['afterRestoration']['verificationRoute'],'current-admin-registry')
        fixture.primitives.close_window.assert_called_once_with(10)

    def test_lost_rebind_proof_after_restoration_never_posts_close(self):
        state=close.inspect_shutdown_system(self.process)
        fixture=self.normal_fixture()
        with patch.object(close,'inspect_shutdown_system',side_effect=[state,{**state,'stable':False}]):
            result=fixture.failed()
        self.assertIn('No proved current-admin replacement',result['error'])
        fixture.primitives.close_window.assert_not_called()


class DiagnosticDenialTests(unittest.TestCase):
    def test_read_denial_is_recorded_without_a_guess_or_close(self):
        with tempfile.TemporaryDirectory() as name:
            root=Path(name);exe=root/'native.exe';exe.write_bytes(b'fixture')
            native=Mock();native.exe.return_value=str(exe);native.create_time.return_value=100.;native.is_running.return_value=True
            denied=PermissionError(5,'access denied');denied.winerror=5
            output=root/'diagnostic.json'
            with patch.object(diagnostic,'EXE',exe),patch.object(diagnostic,'PATCHED_SHA256',hashlib.sha256(b'fixture').hexdigest()),patch.object(diagnostic.psutil,'Process',return_value=native),patch.object(diagnostic,'ResearchProcess',side_effect=denied),patch.object(diagnostic,'inspect_shutdown_system') as inspect:
                result=diagnostic.diagnose(123,100.,output)
            self.assertFalse(result['memoryReadSucceeded'])
            self.assertIsNone(result['admin']);self.assertIsNone(result['cachedSingleton'])
            self.assertEqual(result['winerror'],5)
            self.assertTrue(result['readOnly'])
            self.assertEqual(json.loads(output.read_text()),result)
            inspect.assert_not_called()


if __name__=='__main__':
    unittest.main()
