"""Bounded Windows report-read races must not abort normal restoration."""
import unittest,json,tempfile,struct
from pathlib import Path
from unittest.mock import Mock,patch
import stop_passthrough as stop

class ReportTests(unittest.TestCase):
    def test_compositor_vtable_restore_is_not_full_input_light_release(self):
        staged={'pid':42,'probeVersion':38,'enabled':False,'restored':True,
                'slotInputFilter':False,'slotInputRestored':False,
                'viewLightRestored':False,'nativeFrameLimitRestored':False}
        self.assertFalse(stop.restoration_complete(staged,42,compositor=True))
        for key in ('slotInputRestored','viewLightRestored','nativeFrameLimitRestored'):
            staged[key]=True
            self.assertEqual(stop.restoration_complete(staged,42,compositor=True),key=='nativeFrameLimitRestored')
        for key in ('slotInputRestored','viewLightRestored','nativeFrameLimitRestored'):
            with self.subTest(key=key):
                missing=dict(staged);missing.pop(key)
                self.assertFalse(stop.restoration_complete(missing,42,compositor=True))
        self.assertFalse(stop.restoration_complete(dict(staged,slotInputFilter=True),42,compositor=True))
        self.assertFalse(stop.restoration_complete(staged,43,compositor=True))
        self.assertTrue(stop.restoration_complete({'pid':42,'enabled':False,'restored':True,'probeVersion':34},42,compositor=True))
    def test_transient_replace_and_partial_json_are_retried(self):
        path=Mock();path.read_text.side_effect=[PermissionError(13,'sharing race'),'{','{"pid":42,"restored":true}']
        with patch.object(stop.time,'sleep') as sleep:
            self.assertEqual(stop.read_report(path),{'pid':42,'restored':True})
            self.assertEqual(sleep.call_count,2);self.assertEqual(path.read_text.call_count,3)
    def test_persistent_error_remains_fatal_after_finite_bound(self):
        path=Mock();failure=PermissionError(13,'still denied');path.read_text.side_effect=failure
        with patch.object(stop.time,'sleep') as sleep:
            with self.assertRaises(PermissionError) as raised:stop.read_report(path)
            self.assertIs(raised.exception,failure);self.assertEqual(path.read_text.call_count,8);self.assertEqual(sleep.call_count,7)
    def test_stable_report_is_read_without_delay(self):
        path=Mock();path.read_text.return_value='{"pid":42,"enabled":false}'
        with patch.object(stop.time,'sleep') as sleep:
            self.assertFalse(stop.read_report(path)['enabled']);sleep.assert_not_called()
            path.read_text.assert_called_once_with(encoding='utf-8')

class TerminalReportTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.path=Path(self.temp.name)/'body-sync-42.json';self.pending=self.path.with_suffix('.json.tmp')
        self.original=b'{"pid":42,"enabled":true,"restored":false}'
        self.path.write_bytes(self.original)
        self.terminal={'pid':42,'probeVersion':10,'enabled':False,'restored':True,'failures':0}
        self.raw=json.dumps(self.terminal).encode();self.pending.write_bytes(self.raw)
        self.process=Mock();self.process.base=0x140000000
        base=self.process.base;self.admin=0x20000000;self.items=0x30000000;self.component=0x40000000
        self.expected=tuple(base+v for v in (0xca0960,0xca0800,0xca09c0))
        self.memory={base+0x17b7f90:struct.pack('<Q',self.admin),self.admin+0xf0:struct.pack('<Qii',self.items,1,1),self.items:struct.pack('<Q',self.component),self.component:struct.pack('<Q',base+0x15c4e28),base+0x15c4e28:struct.pack('<3Q',*self.expected)}
        def read(address,size):
            raw=self.memory[address];self.assertEqual(len(raw),size);return raw
        self.process.read.side_effect=read
        self.identity=patch.object(stop.psutil,'Process');self.identity.start().return_value.create_time.return_value=0;self.addCleanup(self.identity.stop)
    def recover(self):return stop.recover_body_terminal_report(self.process,42,self.path)
    def unchanged(self):
        self.assertEqual(self.path.read_bytes(),self.original);self.assertTrue(self.pending.exists())
    def test_body13_requires_pinned_unique_owner_and_original_callbacks(self):
        root=Path(self.temp.name);dll=root/'native-host/build/owmc-guest-body-v13.dll';dll.parent.mkdir(parents=True);dll.write_bytes(b'fixture-only-dll')
        terminal=dict(self.terminal,probeVersion=13);self.pending.write_text(json.dumps(terminal))
        pin=Mock();pin.hexdigest.return_value='35208fc277cedca3e3f6b85497ce9b3249e9fd6a8811bb03fa8760add99b861d'
        with patch.object(stop,'ROOT',root),patch('launch_passthrough_session.installed_modules',return_value={dll.name:dll.resolve()}) as modules,patch.object(stop.hashlib,'sha256',return_value=pin):
            pin.hexdigest.return_value='bad-build';self.assertIsNone(self.recover());self.unchanged()
            pin.hexdigest.return_value='35208fc277cedca3e3f6b85497ce9b3249e9fd6a8811bb03fa8760add99b861d'
            modules.return_value={dll.name:dll.resolve(),'owmc-guest-body-v12.dll':dll.with_name('owmc-guest-body-v12.dll')}
            self.assertIsNone(self.recover());self.unchanged();modules.return_value={dll.name:dll.resolve()}
            self.memory[self.component]=struct.pack('<Q',0x50000000);self.memory[0x50000000]=struct.pack('<3Q',0x60000000,*self.expected[1:])
            self.assertIsNone(self.recover());self.unchanged()
            self.memory[self.component]=struct.pack('<Q',self.process.base+0x15c4e28)
            self.assertEqual(self.recover(),terminal);self.assertFalse(self.pending.exists())
    def test_actual_original_callbacks_promote_unchanged_bytes(self):
        self.assertEqual(self.recover(),self.terminal);self.assertEqual(self.path.read_bytes(),self.raw);self.assertFalse(self.pending.exists())
    def test_json_claim_does_not_override_active_body_callback(self):
        table=0x50000000;self.memory[self.component]=struct.pack('<Q',table);self.memory[table]=struct.pack('<3Q',0x60000000,*self.expected[1:])
        self.assertIsNone(self.recover());self.unchanged()
    def test_original_object_does_not_hide_another_active_body(self):
        self.memory[self.admin+0xf0]=struct.pack('<Qii',self.items,2,2)
        self.memory[self.items+8]=struct.pack('<Q',self.component+8)
        self.memory[self.component+8]=struct.pack('<Q',0x50000000)
        self.memory[0x50000000]=struct.pack('<3Q',0x60000000,*self.expected[1:])
        self.assertIsNone(self.recover());self.unchanged()
    def test_wrong_identity_type_version_or_incomplete_terminal_is_refused(self):
        for key,value in [('pid',43),('pid',42.0),('probeVersion',9),('enabled',True),('enabled',0),('restored',False),('restored',1),('failures',1),('failures',False)]:
            with self.subTest(key=key,value=value):
                self.pending.write_text(json.dumps(dict(self.terminal,**{key:value})),encoding='utf-8')
                self.assertIsNone(self.recover());self.unchanged()
        self.pending.write_text('{',encoding='utf-8');self.assertIsNone(self.recover());self.unchanged()
    def test_earlier_process_file_is_refused(self):
        stop.psutil.Process.return_value.create_time.return_value=self.pending.stat().st_mtime+1
        self.assertIsNone(self.recover());self.unchanged();self.process.read.assert_not_called()
    def test_changed_tmp_during_native_proof_is_refused(self):
        original_read=self.process.read.side_effect
        def read(address,size):
            if address==self.process.base+0x15c4e28:self.pending.write_bytes(b'changed')
            return original_read(address,size)
        self.process.read.side_effect=read
        self.assertIsNone(self.recover());self.unchanged()
    def test_transient_rename_error_rechecks_then_recovers(self):
        with patch.object(stop.os,'replace',side_effect=[PermissionError(13,'sharing race'),None]) as rename,patch.object(stop.time,'sleep') as sleep:
            self.assertEqual(self.recover(),self.terminal);self.assertEqual(rename.call_count,2);sleep.assert_called_once_with(.03)
        # Mocked second replace above did not mutate the filesystem.
        self.unchanged()
    def test_persistent_rename_error_keeps_both_files_and_stays_bounded(self):
        with patch.object(stop.os,'replace',side_effect=PermissionError(13,'denied')) as rename,patch.object(stop.time,'sleep') as sleep:
            self.assertIsNone(self.recover());self.assertEqual(rename.call_count,8);self.assertEqual(sleep.call_count,7)
        self.unchanged()
    def test_unknown_native_layout_never_promotes(self):
        self.memory[self.admin+0xf0]=struct.pack('<Qii',self.items,33,33)
        self.assertIsNone(self.recover());self.unchanged()

class EmissionTerminalTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.path=Path(self.temp.name)/'native-emissions-42.json';self.pending=self.path.with_suffix('.json.tmp')
        self.old=b'{"pid":42,"enabled":true,"restored":false}';self.path.write_bytes(self.old)
        self.terminal={'pid':42,'probeVersion':11,'protocol':3,'creation':12345,'enabled':False,'restored':True,'failures':0}
        self.raw=json.dumps(self.terminal).encode();self.pending.write_bytes(self.raw)
        self.process=Mock();self.process.base=0x140000000
        from prepare_native_emission import PREFIX,FACTORY_PREFIX
        b=self.process.base
        self.memory={b+0xd35c20:PREFIX,b+0xd354b0:FACTORY_PREFIX,
                     b+0x15c8e30+0x110:struct.pack('<Q',b+0xf531f0),b+0x15c8e30+0x158:struct.pack('<Q',b+0xf53270)}
        def read(at,size):
            self.assertEqual(len(self.memory[at]),size);return self.memory[at]
        self.process.read.side_effect=read
        for name,value in [('emission_owner_verified',True),('emission_owner_version',11),('process_creation',12345)]:
            patcher=patch.object(stop,name,return_value=value);patcher.start();self.addCleanup(patcher.stop)
        patcher=patch.object(stop.psutil,'Process');patcher.start().return_value.create_time.return_value=0;self.addCleanup(patcher.stop)
    def recover(self):return stop.recover_emission_terminal_report(self.process,42,self.path)
    def unchanged(self):self.assertEqual(self.path.read_bytes(),self.old);self.assertTrue(self.pending.exists())
    def test_both_original_patches_and_both_callbacks_are_required(self):
        for at,original in list(self.memory.items()):
            with self.subTest(at=at):
                self.memory[at]=bytes([original[0]^1])+original[1:]
                self.assertIsNone(self.recover());self.unchanged();self.memory[at]=original
        self.assertEqual(self.recover(),self.terminal);self.assertEqual(self.path.read_bytes(),self.raw);self.assertFalse(self.pending.exists())
    def test_reused_pid_wrong_module_protocol_and_incomplete_terminal_refuse(self):
        for key,value in [('pid',43),('probeVersion',12),('creation',12346),('creation',12345.0),('protocol',True),('protocol',2),('enabled',True),('restored',False),('failures',1)]:
            with self.subTest(key=key,value=value):
                self.pending.write_text(json.dumps(dict(self.terminal,**{key:value})),encoding='utf-8');self.assertIsNone(self.recover());self.unchanged()
        self.pending.write_bytes(self.raw);stop.emission_owner_verified.return_value=False
        self.assertIsNone(self.recover());self.unchanged()
    def test_rename_sharing_race_rechecks_original_callbacks(self):
        actual=stop.os.replace
        def rename(source,target):
            if rename.calls<2:rename.calls+=1;raise PermissionError(13,'file locked')
            return actual(source,target)
        rename.calls=0
        with patch.object(stop.os,'replace',side_effect=rename),patch.object(stop.time,'sleep'):
            self.assertEqual(self.recover(),self.terminal)
        self.assertEqual(self.path.read_bytes(),self.raw);self.assertEqual(self.process.read.call_count,12)
    def test_changed_terminal_is_not_promoted(self):
        original=self.process.read.side_effect
        def read(at,size):self.pending.write_bytes(b'changed');return original(at,size)
        self.process.read.side_effect=read
        self.assertIsNone(self.recover());self.unchanged()

class StopRecoveryScopeTests(unittest.TestCase):
    def test_missing_event_only_allows_calibrated_terminal_recovery(self):
        for options in ({},{'body':True},{'weapon':True},{'emissions':True}):
            with self.subTest(options=options):
                process=Mock();process.kernel.OpenEventW.return_value=0
                terminal={'pid':42,'enabled':False,'restored':True}
                with patch.object(stop,'ResearchProcess',return_value=process),patch.object(stop,'recover_body_terminal_report',return_value=terminal) as recovery,patch.object(stop,'recover_emission_terminal_report',return_value=terminal) as emission,patch.object(stop,'recover_compositor_terminal_report',return_value=terminal) as compositor,patch('builtins.print'):
                    if options.get('body'):
                        self.assertEqual(stop.stop(42,**options),terminal);recovery.assert_called_once()
                    elif options.get('emissions'):
                        self.assertEqual(stop.stop(42,**options),terminal);emission.assert_called_once();recovery.assert_not_called()
                    elif not options:
                        self.assertEqual(stop.stop(42),terminal);compositor.assert_called_once();recovery.assert_not_called();emission.assert_not_called()
                    else:
                        with self.assertRaisesRegex(ValueError,'No active'):stop.stop(42,**options)
                        recovery.assert_not_called()
                        emission.assert_not_called()
                        compositor.assert_not_called()
                process.close.assert_called_once()

class CompositorReadbackTests(unittest.TestCase):
    def setUp(self):
        self.p=Mock();self.p.base=0x140000000;self.b=0x180000000
        b=self.b;q=lambda v:struct.pack('<Q',v)
        self.memory={b+0x1514ed:b'\x01\x01\x00',b+0x151510:q(0),b+0x151518:q(0),
            b+0x151340+40:b'\x00\x01',b+0x151340:struct.pack('<2Q',0x20000000,0x20000018),
            0x20000000:q(0x30000000),0x20000008:bytes(range(16)),0x30000000:bytes(range(16)),
            b+0x144240:q(0),b+0x144240+60:b'\x00\x01',b+0x108020:q(0),
            b+0x108020+16:b'\x00\x01',b+0x108020+12:struct.pack('<f',100),self.p.base+0x179f130:struct.pack('<f',100)}
        def read(at,size):
            value=self.memory[at];self.assertEqual(len(value),size);return value
        self.p.read.side_effect=read
    def test_fully_released_actual_state_passes(self):self.assertTrue(stop.original_compositor40_restored(self.p,self.b))
    def test_staged_flags_and_each_actual_hook_refuse(self):
        for at,value in list(self.memory.items()):
            if at in (self.b+0x151340,0x20000000):continue
            with self.subTest(address=at):
                self.memory[at]=bytes([value[0]^1])+value[1:]
                self.assertFalse(stop.original_compositor40_restored(self.p,self.b));self.memory[at]=value
    def test_corrupt_hook_vector_refuses(self):
        for end in (0x1ffffff0,0x20000019,0x20000000,0x20000000+10*24):
            self.memory[self.b+0x151340]=struct.pack('<2Q',0x20000000,end)
            self.assertFalse(stop.original_compositor40_restored(self.p,self.b))

if __name__=='__main__':unittest.main()
