"""Display lifecycle policy fixtures; no real screen/process mutations."""
from contextlib import ExitStack
import ctypes
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch,Mock
import native_display_mode as d


def mode(width,height=1080,hz=144,bits=32):
    m=d.Mode();m.size=ctypes.sizeof(m);m.width=width;m.height=height;m.hz=hz;m.bits=bits
    return m


class Display:
    def __init__(self):
        self.current=mode(2376);self.registered=mode(2376)
        self.modes=[mode(2376),mode(1920)]
        self.calls=[];self.fail=False
    def read(self,index):
        m=self.current if index==d.CURRENT else self.registered if index==d.REGISTERED else self.modes[index] if index<len(self.modes) else None
        return d.Mode.from_buffer_copy(bytes(m)) if m else None
    def change(self,m,flags):
        self.calls.append((d.signature(m),flags))
        if flags==d.TEST:return
        if self.fail:raise RuntimeError('simulated display refusal')
        if flags&d.REGISTRY:self.registered=d.Mode.from_buffer_copy(bytes(m))
        if not flags&d.NO_RESET:self.current=d.Mode.from_buffer_copy(bytes(m))


class LeaseChecks(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.path=Path(self.temp.name)/'receipt.json';self.screen=Display()
        self.lease=d.DisplayLease(self.path,self.screen)
        self.identity=dict(pid=123,created=100.25,executable=d.stored_executable())
        self.stack=ExitStack();self.addCleanup(self.stack.close)
        self.verify=self.stack.enter_context(patch.object(d,'verified_native',return_value=self.identity))
        self.prepare=self.stack.enter_context(patch.object(d,'verified_launch',return_value=self.identity))
        self.running=self.stack.enter_context(patch.object(d,'any_native_running',return_value=False))
        self.settings=dict(nativeFullscreen=True,width=1920,height=1080)
    def acquire(self):return self.lease.acquire(None,self.settings)
    def test_acquire_restore_repeat_preserves_full_original_modes(self):
        self.screen.registered=mode(2560,1440)
        old=(bytes(self.screen.current),bytes(self.screen.registered))
        self.assertTrue(self.acquire()['changed']);self.assertEqual(d.signature(self.screen.current),[1920,1080,144,32])
        record=self.lease.load();self.assertEqual(record['state'],'active')
        self.assertEqual(self.lease.backup_path(record['backups']['current']['path'],'current').read_bytes(),old[0])
        count=len(self.screen.calls);self.assertFalse(self.acquire()['changed'])
        self.assertEqual(len(self.screen.calls),count)
        self.assertTrue(self.lease.restore()['restored'])
        self.assertEqual((bytes(self.screen.current),bytes(self.screen.registered)),old)
        count=len(self.screen.calls);self.assertTrue(self.lease.restore()['restored'])
        self.assertEqual(len(self.screen.calls),count)
    def test_disabled_and_already_correct_do_not_take_ownership(self):
        self.settings['nativeFullscreen']=False
        self.assertFalse(self.acquire()['managed']);self.verify.assert_not_called();self.prepare.assert_not_called()
        self.settings['nativeFullscreen']=True;self.screen.current=self.screen.registered=mode(1920)
        self.assertFalse(self.acquire()['managed']);self.assertFalse(self.path.exists())
        self.assertEqual(self.screen.calls,[])
    def test_unknown_size_or_unavailable_refresh_refuses_before_mutation(self):
        self.settings['width']=999
        with self.assertRaises(ValueError):self.acquire()
        self.settings['width']=1920;self.screen.current.hz=120;self.screen.modes=[mode(2376)]
        with self.assertRaisesRegex(ValueError,'enumerated'):self.acquire()
        self.assertFalse(self.path.exists());self.assertEqual(self.screen.calls,[])
    def test_native_identity_change_during_prepare_refuses(self):
        self.prepare.side_effect=[self.identity,dict(self.identity,created=101)]
        with self.assertRaisesRegex(ValueError,'owner changed'):self.acquire()
        self.assertFalse(self.path.exists());self.assertEqual([f for _,f in self.screen.calls],[d.TEST])
    def test_restore_waits_for_every_native_to_exit(self):
        self.acquire();self.running.return_value=True;count=len(self.screen.calls)
        with self.assertRaisesRegex(ValueError,'still running'):self.lease.restore()
        self.assertEqual(len(self.screen.calls),count);self.assertEqual(self.lease.load()['state'],'active')
    def test_other_owner_cannot_adopt_old_lease(self):
        self.acquire();self.prepare.return_value=dict(self.identity,pid=456);count=len(self.screen.calls)
        with self.assertRaisesRegex(ValueError,'Another display lease'):self.acquire()
        self.assertEqual(len(self.screen.calls),count)
    def test_user_mode_change_is_preserved_at_acquire_and_restore(self):
        self.acquire();self.screen.current=mode(3840,2160);count=len(self.screen.calls)
        with self.assertRaisesRegex(ValueError,'not overriding'):self.acquire()
        with self.assertRaisesRegex(ValueError,'preserving'):self.lease.restore()
        self.assertEqual(len(self.screen.calls),count)
    def test_tampered_backup_never_reaches_display_api(self):
        self.acquire();record=self.lease.load();self.lease.backup_path(record['backups']['current']['path'],'current').write_bytes(b'bad')
        count=len(self.screen.calls)
        with self.assertRaisesRegex(ValueError,'checksum'):self.lease.restore()
        self.assertEqual(len(self.screen.calls),count)
    def test_failed_apply_retains_original_receipt_for_normal_stop(self):
        self.screen.fail=True
        with self.assertRaisesRegex(RuntimeError,'refusal'):self.acquire()
        self.assertEqual(self.lease.load()['state'],'preparing')
        self.screen.fail=False;self.assertTrue(self.lease.restore()['restored'])
        self.assertEqual(d.signature(self.screen.current),[2376,1080,144,32])
    def test_native_already_restored_desktop_is_idempotent(self):
        self.acquire();self.screen.current=self.screen.registered=mode(2376)
        count=len(self.screen.calls);self.assertTrue(self.lease.restore()['restored'])
        self.assertEqual(len(self.screen.calls),count)
    def test_actual_legacy_public_prefix_and_private_data_rejection(self):
        self.screen.current.size=self.screen.registered.size=188
        self.screen.modes[1].size=188
        self.assertTrue(self.acquire()['changed']);self.assertTrue(self.lease.restore()['restored'])
        self.screen.current.extra=4
        with self.assertRaisesRegex(ValueError,'driver-private'):self.acquire()
    def test_mismatched_existing_renderer_requires_normal_restart(self):
        with self.assertRaisesRegex(ValueError,'Normal restart required'):
            self.lease.acquire(123,self.settings)
        self.assertFalse(self.path.exists());self.assertEqual(self.screen.calls,[])
    def test_reservation_binds_only_to_its_own_verified_native(self):
        import psutil,os
        reservation=dict(kind='launch-reservation',pid=os.getpid(),created=psutil.Process().create_time(),executable=str(d.EXE))
        self.prepare.return_value=reservation;self.acquire()
        self.assertTrue(self.lease.bind(123,self.settings)['managed'])
        self.assertEqual(self.lease.load()['identity'],self.identity)
        self.verify.return_value=dict(self.identity,pid=456)
        with self.assertRaisesRegex(ValueError,'another native'):self.lease.bind(456,self.settings)

    def test_missing_post_change_registry_retries_reads_not_changes(self):
        self.acquire();count=len(self.screen.calls);read=self.screen.read;missed=[]
        def transient(index):
            if index==d.REGISTERED and len(self.screen.calls)==count+2 and not missed:
                missed.append(index);return None
            return read(index)
        self.screen.read=transient
        with patch.object(d.time,'sleep'):
            result=self.lease.restore()
        self.assertEqual(result['readbackRetries'],1)
        self.assertEqual(len(self.screen.calls),count+2)
        self.assertEqual(self.lease.load()['state'],'restored')

    def test_real_foreign_post_change_mode_is_not_retried(self):
        self.acquire();count=len(self.screen.calls);read=self.screen.read
        self.screen.read=lambda index: mode(2560,1440) if index==d.CURRENT and len(self.screen.calls)==count+2 else read(index)
        with patch.object(d.time,'sleep') as sleep:
            with self.assertRaisesRegex(RuntimeError,'readback differs'):self.lease.restore()
        sleep.assert_not_called();self.assertEqual(len(self.screen.calls),count+2)
        self.assertEqual(self.lease.load()['state'],'active')

    def test_native_appearing_during_final_readback_refuses(self):
        self.acquire();count=len(self.screen.calls)
        self.running.side_effect=[False,False,False,True]
        with self.assertRaisesRegex(ValueError,'Native started during desktop restoration readback'):self.lease.restore()
        self.assertEqual(len(self.screen.calls),count+2)
        self.assertEqual(self.lease.load()['state'],'active')

    def test_native_appearing_between_two_readback_queries_refuses(self):
        self.acquire();count=len(self.screen.calls)
        self.running.side_effect=[False,False,False,False,True]
        with self.assertRaisesRegex(ValueError,'Native started during desktop restoration readback'):self.lease.restore()
        self.assertEqual(len(self.screen.calls),count+2)
        self.assertEqual(self.lease.load()['state'],'active')

    def test_missing_post_change_readback_is_bounded_and_receipt_retained(self):
        self.acquire();count=len(self.screen.calls);read=self.screen.read
        self.screen.read=lambda index: None if index==d.REGISTERED and len(self.screen.calls)==count+2 else read(index)
        with patch.object(d.time,'monotonic',side_effect=[0,7]):
            with self.assertRaisesRegex(ValueError,'bounded restoration readback'):self.lease.restore()
        self.assertEqual(len(self.screen.calls),count+2)
        self.assertEqual(self.lease.load()['state'],'active')


class ApiCacheChecks(unittest.TestCase):
    def test_special_read_refreshes_documented_index_zero_cache(self):
        backend=d.WinDisplay.__new__(d.WinDisplay);backend.user=Mock();calls=[]
        def read(name,index,pointer):
            calls.append(index)
            if index==0:return True
            self.assertEqual(calls[-2],0)
            ctypes.memmove(pointer,ctypes.byref(mode(2376)),ctypes.sizeof(d.Mode))
            return True
        backend.user.EnumDisplaySettingsW.side_effect=read
        self.assertEqual(d.signature(backend.read(d.REGISTERED)),[2376,1080,144,32])
        self.assertEqual(calls,[0,d.REGISTERED])


if __name__=='__main__':unittest.main()
