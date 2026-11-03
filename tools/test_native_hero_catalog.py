"""Synthetic memory layout regressions; no game is opened."""
import unittest
import zlib
from unittest.mock import patch
from native_hero_catalog import capability, model_scripts
from native_weapon_binding import WeaponBindingReader
from test_native_weapon_binding import Memory


def fixture(stride=32):
    m=Memory();model=0x100100;component=0x100200;graph=0x100300
    m.meta(model,0x101000,0x101100,0x101200,zlib.crc32(b"stuentitydefinition"),64)
    m.meta(component,0x102000,0x102100,0x102200,zlib.crc32(b"stustatescriptcomponent"),32)
    m.meta(graph,0x103000,0x103100,0x103200,zlib.crc32(b"stustatescriptgraph"),128)
    m.put(model+0x28,"<QQ",0x104000,2)
    m.put(0x104000,"<i4xQQ",1,0x104100,0x104200)
    m.put(0x104100,"<i",1)
    m.put(0x104200,"<I4xQ",zlib.crc32(b"stustatescriptcomponent"),component)
    m.put(0x102200+0x28,"<Q",0x105000);m.put(0x102200+0x54,"<i",1)
    m.put(0x105000+8,"<IiQ",0x0175ad85,8,0x105100)
    m.put(0x105100,"<Q",0x105200);m.put(0x105100+0x28,"<Q",0x105400)
    m.put(0x105200+0x30,"<Q",0x105300)
    m.raw(0x105300,bytes.fromhex("488b412848b900000000050000008b4050480bc1c3")+b"\0"*11)
    m.put(0x105400+0x50,"<I",0xb773e1d0);m.put(0x105400+0x5c,"<i",stride)
    m.put(component+8,"<QQ",0x106000,2);m.put(0x106000,"<QQ",2,0x106100)
    # Inline resource+variable-list pairs, rather than two 16-byte references.
    m.put(0x106100,"<QQQQ",0,0x0580000000000033,0x107000,2)
    m.put(0x106120,"<QQQQ",0,0x0580000000000304,0x107020,2)
    return m,model,{0x0580000000000033:graph,0x0580000000000304:graph}


class HeroCatalogTests(unittest.TestCase):
    def test_inline_stride_keeps_last_weapon_reference(self):
        memory,model,loaded=fixture()
        with patch("native_hero_catalog.ScriptReader.graph_nodes",return_value=[]):
            rows=model_scripts(WeaponBindingReader(memory),model,loaded)
        self.assertEqual([r["resourceId"] for r in rows],["0580000000000033","0580000000000304"])

    def test_unknown_inline_size_is_refused(self):
        memory,model,loaded=fixture(48)
        with self.assertRaisesRegex(ValueError,"size differs"):
            model_scripts(WeaponBindingReader(memory),model,loaded)

    def test_resource_presence_does_not_grant_weapon_authority(self):
        self.assertFalse(capability("02e0000000000008")["nativeCombatCalibrated"])
        self.assertEqual(capability("02e0000000000029")["weaponKind"],"projectile")


if __name__=="__main__":
    unittest.main()
