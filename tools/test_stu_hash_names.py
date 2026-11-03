import json
from pathlib import Path
import tempfile
import unittest
from stu_hash_names import HashNames

class HashNamesTests(unittest.TestCase):
    def table(self,text):
        folder=tempfile.TemporaryDirectory();self.addCleanup(folder.cleanup)
        path=Path(folder.name)/'names.csv';path.write_text(text,encoding='utf-8');return path
    def test_actual_observed_volley_hash_and_unknown_remain_distinct(self):
        names=HashNames(self.table('860EE5FC, STUStatescriptStateWeaponVolley\n'))
        self.assertEqual(names.get('860ee5fc'),'STUStatescriptStateWeaponVolley')
        self.assertIsNone(names.get('00000000'))
    def test_mismatched_claim_is_refused(self):
        with self.assertRaises(ValueError):HashNames(self.table('860EE5FC, STUStatescriptProjectileHit\n'))
    def test_malformed_and_unbounded_names(self):
        for row in ['12, Something\n','860EE5FC,\n','860EE5FC, A, B\n','860EE5FC, '+('X'*257)+'\n']:
            with self.subTest(row=row[:30]),self.assertRaises(ValueError):HashNames(self.table(row))
    def test_duplicate_identical_rows_allowed(self):
        names=HashNames(self.table('860EE5FC,STUStatescriptStateWeaponVolley\n860ee5fc,STUStatescriptStateWeaponVolley\n'))
        self.assertEqual(len(names.names),1)
    def test_upstream_omitted_leading_zero(self):
        names=HashNames(self.table('4E83493, STUConfigVarStatescriptGraph\n'))
        self.assertEqual(names.get('04e83493'),'STUConfigVarStatescriptGraph')
    def test_annotation_does_not_change_original_flags_or_claim_execution(self):
        names=HashNames(self.table('860EE5FC,STUStatescriptStateWeaponVolley\n'))
        original={'pid':7,'nativeCalls':False,'entities':[{'scripts':[{'resourceId':'0580000000000304','nodes':[{'index':6,'hash':'860ee5fc','name':'','serverOnly':0,'clientOnly':0},{'index':7,'hash':'00000000','serverOnly':1}]}]}]}
        before=json.dumps(original,sort_keys=True);result=names.annotate(original)
        self.assertEqual(json.dumps(original,sort_keys=True),before)
        node=result['entities'][0]['scripts'][0]['nodes'][0]
        self.assertEqual(node['serverOnly'],0);self.assertEqual(node['name'],'')
        self.assertEqual(result['typeNameResolution']['matchedNodes'],1)
        self.assertFalse(result['typeNameResolution']['nativeExecutionObserved'])

if __name__=='__main__':unittest.main()
