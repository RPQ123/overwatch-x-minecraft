"""Offline tuning regression. Requires existing named jars and builders-only compile output."""
import json
from pathlib import Path
import shutil
import subprocess
import unittest

ROOT=Path(__file__).resolve().parents[1]


class BuildersTuningCheck(unittest.TestCase):
    def test_real_runtime_and_render_contracts(self):
        cache=ROOT/'research/asset-cache';out=cache/'builders-tuning-check';out.mkdir(exist_ok=True)
        asm=next((ROOT/'tools/gradle-cache/caches/modules-2/files-2.1/org.ow2.asm/asm').rglob('asm-*.jar'))
        compiled=cache/'builders-typecheck'
        self.assertTrue((compiled/'lab/owmcguest/NativeJunkratRuntime.class').is_file(),'run verify_native_builders_compile.py first')
        source=ROOT/'guest/src/main/java/lab/owmcguest'
        files=[source/'NativeJunkratGrenadeTuning.java',source/'NativeTorbjornTuning.java',ROOT/'guest/src/test/java/lab/owmcguest/NativeBuildersTuningCheck.java']
        cp=';'.join(map(str,[out,compiled,asm]))
        build=subprocess.run([shutil.which('javac'),'--release','21','-encoding','UTF-8','-cp',cp,'-d',str(out),*map(str,files)],capture_output=True,text=True,timeout=30)
        self.assertEqual(build.returncode,0,build.stderr)
        result=subprocess.run([shutil.which('java'),'-cp',cp,'lab.owmcguest.NativeBuildersTuningCheck'],capture_output=True,text=True,timeout=15)
        self.assertEqual(result.returncode,0,result.stderr)
        (out/'result.json').write_text(json.dumps(dict(passed=True,result=result.stdout.strip()))+'\n',encoding='utf-8')


if __name__=='__main__':unittest.main()
