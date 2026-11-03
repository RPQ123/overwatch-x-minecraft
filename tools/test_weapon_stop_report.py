"""Gate11 restoration proof policy; no running game or process writes."""
from contextlib import ExitStack
import json,struct,tempfile,unittest
from pathlib import Path
from unittest.mock import Mock,patch
import stop_passthrough as s


class WeaponTerminalChecks(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name);self.build=self.root/'native-host/build';self.build.mkdir(parents=True)
        self.path=self.build/'weapon-gate-42.json';self.path.write_text('{"enabled":true}')
        self.pending=self.path.with_suffix('.json.tmp')
        self.terminal=dict(pid=42,probeVersion=11,enabled=False,restored=True,failures=0,
                           skillEntryInstalled=False,skillTickInstalled=False)
        self.pending.write_text(json.dumps(self.terminal))
        self.dll=self.build/'owmc-weapon-gate-v11.dll';self.dll.write_bytes(b'fixture')
        self.request=self.build/'weapon-gate-request-42.bin'
        self.fields=[b'OWGATE05',5,128,42,0,12345,0x20000,1,2,3,4,*([0]*7)]
        self.write_request();self.process=Mock(base=0x140000000)
        self.memory={self.process.base+0x17b7f90:0x20000}
        self.memory.update({self.process.base+0x15d2450+off:self.process.base+rva for off,rva in ((0x110,0xd44b50),(0x120,0xd44d60),(0x270,0xd456c0))})
        self.process.read.side_effect=lambda address,size:struct.pack('<Q',self.memory[address])
        self.stack=ExitStack();self.addCleanup(self.stack.close)
        self.stack.enter_context(patch.object(s,'ROOT',self.root))
        self.stack.enter_context(patch.object(s,'process_creation',return_value=12345))
        self.stack.enter_context(patch.object(s.psutil,'Process',return_value=Mock(create_time=Mock(return_value=0))))
        self.modules=self.stack.enter_context(patch('launch_passthrough_session.installed_modules',return_value={self.dll.name:self.dll.resolve()}))
        self.hash=self.stack.enter_context(patch.object(s.hashlib,'sha256',return_value=Mock(hexdigest=Mock(return_value='b53f738e2096ebb7043f8fffbb706a98de25e6e42c47be68365a544ef7a5ee51'))))
    def write_request(self):self.request.write_bytes(struct.pack('<8s4I13Q',*self.fields))
    def recover(self):return s.recover_weapon_terminal_report(self.process,42,self.path)
    def refused(self):
        self.assertIsNone(self.recover());self.assertTrue(self.pending.exists());self.assertEqual(self.path.read_text(),'{"enabled":true}')
    def test_terminal_and_all_original_slots_promote_exact_bytes(self):
        raw=self.pending.read_bytes();self.assertEqual(self.recover(),self.terminal)
        self.assertEqual(self.path.read_bytes(),raw);self.assertFalse(self.pending.exists())
    def test_each_unrestored_callback_refuses_terminal_claim(self):
        for offset in (0x110,0x120,0x270):
            address=self.process.base+0x15d2450+offset;old=self.memory[address]
            self.memory[address]=0x30000;self.refused();self.memory[address]=old
    def test_another_creation_or_lab_pointer_never_recovers(self):
        for index,value in ((5,12346),(11,0x30000),(16,0x40000),(17,1)):
            old=self.fields[index];self.fields[index]=value;self.write_request();self.refused()
            self.fields[index]=old;self.write_request()
    def test_another_build_or_duplicate_owner_is_refused(self):
        self.hash.return_value.hexdigest.return_value='unaccepted';self.refused()
        self.hash.return_value.hexdigest.return_value='b53f738e2096ebb7043f8fffbb706a98de25e6e42c47be68365a544ef7a5ee51'
        self.modules.return_value['owmc-weapon-gate-v10.dll']=self.dll
        self.refused()
    def test_request_change_during_native_read_is_refused(self):
        def read(address,size):
            self.request.write_bytes(bytes(128));return struct.pack('<Q',self.memory[address])
        self.process.read.side_effect=read;self.refused()
    def test_unknown_terminal_entry_state_is_refused(self):
        for value in (None,True,0):
            self.pending.write_text(json.dumps(dict(self.terminal,skillEntryInstalled=value)));self.refused()


if __name__=='__main__':unittest.main()
