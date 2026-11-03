import unittest
from unittest.mock import patch,Mock
import provided_plugin_symbols as symbols

class CacheTests(unittest.TestCase):
    def tearDown(self):symbols._metadata.cache_clear()
    def test_exact_content_reuse_and_same_size_changed_content_revalidation(self):
        image=Mock(identity=('guid',1));pdb=Mock(identity=('guid',1))
        with patch.object(symbols,'PeImage',return_value=image) as pe,patch.object(symbols,'PdbSymbols',return_value=pdb) as debug:
            a=symbols._metadata('a','b',b'PE1',b'PDB1')
            self.assertIs(a,symbols._metadata('a','b',b'PE1',b'PDB1'))
            self.assertEqual(pe.call_count,1);self.assertEqual(debug.call_count,1)
            symbols._metadata('a','b',b'PE2',b'PDB1');self.assertEqual(pe.call_count,2)
            symbols._metadata('a','b',b'PE2',b'PDB2');self.assertEqual(debug.call_count,3)
    def test_mismatched_guid_is_never_cached_as_valid(self):
        with patch.object(symbols,'PeImage',return_value=Mock(identity=('x',1))),patch.object(symbols,'PdbSymbols',return_value=Mock(identity=('y',1))):
            with self.assertRaises(ValueError):symbols._metadata('a','b',b'PE',b'PDB')
            self.assertEqual(symbols._metadata.cache_info().currsize,0)

if __name__=='__main__':unittest.main()
