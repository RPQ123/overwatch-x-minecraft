import unittest,struct,tempfile,json
from pathlib import Path
from unittest.mock import Mock,patch
from native_bootstrap_maps import MAPS,selected_map,read_loaded_map

class BootstrapMapTests(unittest.TestCase):
    def test_default_and_explicit_request(self):
        self.assertEqual(selected_map({}),MAPS['hollywood'])
        self.assertEqual(selected_map({'nativeMap':'kyoto-login'}),0x0800000000000664)
        for value in ['arena','kyoto',None,7,[],{}]:
            with self.subTest(value=value),self.assertRaises(ValueError):selected_map({'nativeMap':value})
    def world(self):
        process=Mock();process.base=0x140000000
        data={process.base+0x17b7f90:struct.pack('<Q',0x20000000),0x200000d8:struct.pack('<Qii',0x30000000,1,1),0x30000000:struct.pack('<Q',0x40000000),0x40000000:struct.pack('<Q',process.base+0x15c3118),0x40000008:struct.pack('<Q',0x20000000),0x40000010:struct.pack('<B',8),0x40000020:struct.pack('<Q',MAPS['kyoto-login'])}
        process.read.side_effect=lambda address,size:data[address]
        return process,data
    def test_actual_loaded_identity_is_read_not_queued_map(self):
        process,_=self.world();self.assertEqual(read_loaded_map(process),{'state':8,'mapId':MAPS['kyoto-login']})
    def test_changed_owner_or_ambiguous_world_is_refused(self):
        process,data=self.world();data[0x40000008]=struct.pack('<Q',0x20000008)
        with self.assertRaisesRegex(ValueError,'owner'):read_loaded_map(process)
        process,data=self.world();data[0x200000d8]=struct.pack('<Qii',0x30000000,2,2);data[0x30000000]=struct.pack('<QQ',0x40000000,0x40000000)
        with self.assertRaisesRegex(ValueError,'ambiguous'):read_loaded_map(process)
    def test_bootstrap_request_carries_v10_and_exact_kyoto_id(self):
        import prepare_session_bootstrap as bootstrap
        module=0x180000000;process=Mock();process.base=0x140000000;image=Mock();image.image_size=0x100000;image.timestamp=42;image.symbol_rva.return_value=0x1234
        prefix=bytes.fromhex('4c8bdc5341564883ec58488b058fc3a8004833c44889442440418b40704d8bf0')
        process.read.side_effect=lambda address,size:b'\0' if address==module+0x1234 else prefix
        reader=Mock();reader.pointer.return_value=0x20000000;reader.unpack.return_value=(0,)
        with tempfile.TemporaryDirectory() as folder,patch.object(bootstrap,'ROOT',Path(folder)),patch.object(bootstrap,'provided_plugin',return_value=(module,image,Mock())),patch.object(bootstrap,'PoseReader',return_value=reader):
            (Path(folder)/'native-host/build').mkdir(parents=True)
            path=bootstrap.prepare(process,42,123456,MAPS['kyoto-login']);raw=path.read_bytes()
            self.assertEqual(len(raw),96);self.assertEqual(struct.unpack_from('<I',raw,8)[0],10);self.assertEqual(struct.unpack_from('<Q',raw,88)[0],MAPS['kyoto-login'])
    def test_existing_other_map_is_not_silently_adopted_or_overlaid(self):
        import launch_passthrough_session as session
        from native_bootstrap_maps import DLL
        with tempfile.TemporaryDirectory() as folder,patch.object(session,'BUILD',Path(folder)),patch.object(session.psutil,'Process') as identity,patch.object(session,'attach') as attach:
            identity.return_value.create_time.return_value=123
            (Path(folder)/'session-bootstrap-42.json').write_text(json.dumps({'pid':42,'probeVersion':10,'phase':3,'restored':True,'failures':0,'mapId':MAPS['hollywood']}),encoding='utf-8')
            with patch.object(session,'installed_modules',return_value={DLL:Path(folder)/DLL}):
                with self.assertRaisesRegex(RuntimeError,'startup is pending/failed'):session.ensure_bootstrap(42,MAPS['kyoto-login'])
            attach.assert_not_called()

if __name__=='__main__':unittest.main()
