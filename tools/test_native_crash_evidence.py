"""Crash-report identity tests: no live game, UI or process termination."""
import os
import tempfile
import time
import unittest
from pathlib import Path
from types import SimpleNamespace
from native_crash_evidence import find_native_crash_reports


class EvidenceTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name);self.exe=self.root/'offline/GameClientApp.patched.exe';self.created=time.time()-10
        self.documents=self.root/'redirected-documents';self.errors=self.documents/'Overwatch/Logs/Overwatch/errors';self.errors.mkdir(parents=True)
        self.report=self.errors/'Overwatch_24919_Retailx64_42_10-21-26_08.24.10_ErrorLog.txt'
        self.report.write_text('<Inspector.Assertion:>\nApplication: '+str(self.exe)+'\n',encoding='utf-8')
    def find(self,processes=()):
        return find_native_crash_reports(42,self.created,self.exe,documents=self.documents,processes=processes)
    def reporter(self,exe=None,path=None,created=None):
        return SimpleNamespace(info={'pid':200,'exe':str(exe or self.exe.parent/'ErrorReporting/x86/BlizzardError.exe'),
                                     'cmdline':['BlizzardError.exe',str(path or self.report)],'create_time':created if created is not None else self.created+1})
    def test_redirected_documents_retains_report_after_reporter_closed(self):
        rows=self.find();self.assertEqual(len(rows),1);self.assertIsNone(rows[0]['reporterPid']);self.assertEqual(rows[0]['path'],str(self.report.resolve()))
    def test_exact_reporter_argument_retained_and_deduplicated(self):
        rows=self.find([self.reporter()]);self.assertEqual(len(rows),1);self.assertEqual(rows[0]['reporterPid'],200)
    def test_same_name_other_exe_cannot_supply_external_report(self):
        external=self.root/self.report.name;external.write_bytes(self.report.read_bytes());self.report.unlink()
        self.assertEqual(self.find([self.reporter(exe=self.root/'other/BlizzardError.exe',path=external)]),[])
    def test_earlier_reporter_cannot_supply_external_report(self):
        external=self.root/self.report.name;external.write_bytes(self.report.read_bytes());self.report.unlink()
        self.assertEqual(self.find([self.reporter(path=external,created=self.created-1)]),[])
    def test_pid_reuse_does_not_admit_old_report(self):
        os.utime(self.report,(self.created-1,self.created-1));self.assertEqual(self.find([self.reporter()]),[])
    def test_report_for_another_native_pid_is_not_admitted(self):
        other=self.report.with_name(self.report.name.replace('_42_','_43_'));self.report.rename(other)
        self.assertEqual(self.find([self.reporter(path=other)]),[])
    def test_application_must_match_the_verified_executable(self):
        self.report.write_text('<Inspector.Assertion:>\nApplication: '+str(self.root/'retail/GameClientApp.patched.exe')+'\n',encoding='utf-8')
        self.assertEqual(self.find([self.reporter()]),[])
    def test_incomplete_or_oversized_log_is_not_a_crash_proof(self):
        for text in ('','Application: '+str(self.exe),'x'*(2*1024*1024+1)):
            self.report.write_text(text,encoding='utf-8');self.assertEqual(self.find(),[])
    def test_corresponding_dump_only_is_attached(self):
        dump=self.report.with_name(self.report.name.replace('ErrorLog.txt','Minidump.dmp'));dump.write_bytes(b'fixture')
        self.assertEqual(self.find()[0]['minidump'],str(dump))
        os.utime(dump,(self.created-1,self.created-1));self.assertNotIn('minidump',self.find()[0])
    def test_missing_exe_or_argv_is_ignored(self):
        process=SimpleNamespace(info={'pid':200,'exe':None,'cmdline':None,'create_time':None})
        self.assertEqual(len(self.find([process])),1)
        process.info['exe']=str(self.exe.parent/'ErrorReporting/x86/BlizzardError.exe')
        self.assertIsNone(self.find([process])[0]['reporterPid'])


if __name__=='__main__':unittest.main()
