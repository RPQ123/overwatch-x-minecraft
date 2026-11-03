"""Offline event-attribution regressions; does not build or launch either game."""
import json
from pathlib import Path
import unittest

import classify_voice_catalog as voices


class VoiceClassificationTests(unittest.TestCase):
    def event(self, hero, text):
        return voices.classify(hero, {"hash": "0" * 32, "text": text})["event"]

    def test_ready_and_progress_never_become_cast(self):
        for hero, text in [
            ("mccree", "【麦克雷】（大招）终极技能准备好了，你们准备和我一起来吗？"),
            ("mercy", "【天使】（重生）我准备好复活你们了"),
            ("mei", "【美】我准备好释放暴雪了。"),
            ("dva", "【D.VA】自毁程序已经就绪。"),
            ("genji", "【源氏】我的终级技能准备好了"),
        ]:
            with self.subTest(text=text):
                self.assertEqual("ult_ready", self.event(hero, text))
        for text in ["我的终极技能快准备好了", "我的终极技能还在充能", "我的终极技能还没准备好"]:
            self.assertEqual("ult_charge", self.event("genji", "【源氏】" + text))

    def test_context_exclusions_precede_keywords(self):
        for hero, text in [
            ("hanzo", "【半藏】【怪鼠复仇】（开大）让巨龙吞噬你"),
            ("mercy", "【天使】（女巫）（重生）英雄不朽"),
            ("mercy", "【天使】（重生E）英雄不朽"),
            ("genji", "【源氏】（对安娜）谢谢"),
            ("genji", "【源氏】（击杀半藏）目标倒下了"),
            ("genji", "【半藏】你好"),
            ("symmetra", "【秩序之光】光子屏障准备就绪"),
            ("winston", "【温斯顿】发现刺杀者"),
            ("genji", "【源氏】正在转移目标"),
            ("mccree", "【麦克雷】（队友击杀敌人）打得很准"),
            ("junkrat", "【狂鼠】（目击路霸被击杀）嘿，只有我才能杀了那个猪脑袋"),
        ]:
            with self.subTest(text=text):
                self.assertEqual("skip", self.event(hero, text))

    def test_nonverbal_is_not_invented(self):
        for text in ["【堡垒】", "【堡垒】。", "【堡垒】（音效）"]:
            self.assertIn(self.event("bastion", text), {"skip", "uncertain"})
        self.assertEqual("jump", self.event("genji", "【源氏】【跃】"))
        self.assertEqual("pain", self.event("genji", "【源氏】【受伤】"))
        self.assertEqual("low_health", self.event("widowmaker", "【黑百合】【受伤】（低血量音效）嘶~啊~。"))
        self.assertEqual("death", self.event("genji", "【源氏】（死亡）"))
        self.assertEqual("death", self.event("mei", "【美】被击杀。"))
        self.assertNotEqual("kill", self.event("junkrat", "【狂鼠】继续加油，我们就要干掉目标了。"))
        self.assertEqual("effort", self.event("genji", "【源氏】喝！"))
        self.assertEqual("skip", self.event("genji", "【源氏】（近战音效）"))
        self.assertEqual("uncertain", self.event("tracer", "【猎空】我回来了"))

    def test_distinctive_shouts_and_comm(self):
        for hero, text, event in [
            ("hanzo", "【半藏】（爆裂箭）散！", "ability:scatter_arrow"),
            ("hanzo", "【半藏】未知，不再神秘。（音）", "ability:sonic_arrow"),
            ("pharah", "【法老之鹰】天降正义。", "ult_cast"),
            ("mei", "【美】哼哼，冰墙升起来吧。", "ability:ice_wall"),
            ("genji", "【源氏】你好。", "comm"),
            ("genji", "【源氏】我需要治疗。", "healing_request"),
            ("genji", "【源氏】（击杀）目标已消灭", "kill"),
            ("genji", "【源氏】双杀", "multikill"),
        ]:
            with self.subTest(text=text):
                self.assertEqual(event, self.event(hero, text))

    def test_catalogue_conservation_and_download_guards(self):
        original = json.loads((voices.DEFAULT / "catalog.json").read_text(encoding="utf-8"))
        original_copy = json.dumps(original, ensure_ascii=False)
        result = voices.classify_catalog(original)
        self.assertEqual(11361, sum(map(len, result.values())))
        self.assertEqual(original_copy, json.dumps(original, ensure_ascii=False))
        for hero, rows in result.items():
            for before, row in zip(original[hero], rows):
                self.assertEqual(before, {key: row[key] for key in before})
                self.assertIn(row["event"].split(":")[0], {*voices.BASE_EVENTS, "ability"})
                self.assertFalse(row["deployment_allowed"])
                if row["download_recommended"]:
                    self.assertGreaterEqual(row["confidence"], .88)
                    self.assertNotIn(row["event"], {"skip", "uncertain", "effort", "idle"})
        h = voices.SELECT_HASHES["genji"]
        result = voices.classify_catalog(original, {h: {"stem": "genji-select"}})
        row = next(x for x in result["genji"] if x["hash"] == h)
        self.assertTrue(row["local_asset_verified"])
        self.assertFalse(row["download_recommended"])


if __name__ == "__main__":
    unittest.main()
