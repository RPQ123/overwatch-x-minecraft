"""Offline real24919 declarations/mesh selections, plus script syntax. No game input."""
import ast
import hashlib
import json
from pathlib import Path
import unittest
import shutil
import subprocess

from inspect_hanzo_dragon_assets import FlatGraph
from prepare_native_builders_assets import LEVELS, selected_pack
from prepare_native_junkrat import GRAPHS as JUNK
from prepare_native_torb import GRAPHS as TORB

ROOT=Path(__file__).resolve().parents[1]
CACHE=ROOT/'research/asset-cache'


class BuildersOffline(unittest.TestCase):
    def graph(self,guid):
        path=CACHE/'builders-graphs'/(guid+'.raw')
        if not path.is_file():self.skipTest('requires SHA-guarded inspect_native_builders_archive.py cache')
        return FlatGraph(path.read_bytes())

    def test_live_binding_profiles_match_actual_native_types(self):
        for purpose,resource,count,states in JUNK+TORB:
            if purpose not in ('junkTire','torbHammer'):continue
            graph=self.graph(f'{resource:016x}')
            self.assertEqual(len(graph.nodes),count)
            for name,index,kind in states:
                with self.subTest(purpose=purpose,state=name):graph.node(index,kind)

    def test_tire_create_is_entity039c_and_not_unlabelled_node19(self):
        graph=self.graph('0580000000000232')
        create=graph.node(32,0x1bb99c36)
        entity=graph.typed(graph.q(create+0x88),0xe53c2921)
        self.assertEqual(graph.q(entity+24),0x040000000000039c)
        self.assertNotEqual(graph.kind(graph.nodes[19]),0x1bb99c36)

    def test_hammer_actual_health_declaration_is_75(self):
        graph=self.graph('05800000000000f3')
        strike=graph.node(24,0x619d9e95)
        self.assertEqual(graph.literal(graph.q(graph.q(strike+0x108)+0x38)),75)

    def test_death_bombs_are_six_original_volleys(self):
        graph=self.graph('058000000000022a')
        for node in (10,11,13,14,15,16):graph.node(node,0x860ee5fc)
        self.assertEqual(graph.raw.count((0x0400000000000515).to_bytes(8,'little')),6)

    def test_turret_levels_keep_real_vertices_and_exclude_other_level_parts(self):
        mesh_path=CACHE/'0400000000000143/0d0000000000092e.lod0.mesh.json'
        if not mesh_path.is_file():self.skipTest('original turret cache unavailable')
        mesh=json.loads(mesh_path.read_text())
        pack={key:[c for row in mesh[key] for c in row] for key in ('positions','normals','uv')}
        counts={}
        for level,parts in LEVELS.items():
            result=selected_pack(mesh,pack,parts)
            counts[level]=sum(len(g['indices'])//3 for g in result['groups'])
            self.assertEqual(counts[level],sum(s['triangleCount'] for s in mesh['submeshes'] if s['index'] in parts))
            self.assertEqual(len(result['positions']),result['vertices']*3)
            self.assertTrue(all(0<=i<result['vertices'] for group in result['groups'] for i in group['indices']))
        self.assertNotIn(19,LEVELS[2]);self.assertNotIn(15,LEVELS[2]);self.assertIn(15,LEVELS[3])
        self.assertEqual(counts,{1:5220,2:9434,3:10611})

    def test_private_prepared_pack_files_are_hash_guarded(self):
        for name in ('junk-tire','junk-death-bomb','torb-turret-1','torb-turret-2','torb-turret-3'):
            folder=CACHE/'builders-packs'/name
            if not folder.exists():self.skipTest('run prepare_native_builders_assets.py with local --out-root')
            proof=json.loads((folder/'provenance.json').read_text())
            self.assertFalse(proof['inGameVerified'])
            for filename,digest in proof['files'].items():self.assertEqual(hashlib.sha256((folder/filename).read_bytes()).hexdigest(),digest)

    def test_verification_scripts_parse_without_running_them(self):
        for filename in ('verify_junk_hanzo.py','verify_torb_kit.py','calibrate_torb_kit.py'):
            ast.parse((ROOT/'research/sprint-20261024'/filename).read_text(encoding='utf-8'))

    def test_child_tire_declarations_are_not_an_authenticated_local_binding(self):
        graph=self.graph('0580000000000233')
        self.assertEqual(len(graph.nodes),97)
        for node in (28,29,71):graph.node(node,0xff77458c)
        for node in (21,22,35,66,70):graph.node(node,0x619d9e95)
        self.assertNotIn(0x0580000000000233,{row[1] for row in JUNK})

    def test_review_cleanup_replay_new_begin_and_full_identity(self):
        javac=shutil.which('javac');java=shutil.which('java')
        self.assertIsNotNone(javac,'requires the existing JDK21');self.assertIsNotNone(java)
        folder=CACHE/'builders-review-check';folder.mkdir(exist_ok=True)
        source=ROOT/'guest/src/main/java/lab/owmcguest'
        files=[source/n for n in ('NativeTorbjornCoreAdmission.java','NativeTorbjornCoreBegin.java','NativeJunkratTireIdentity.java')]
        files.append(ROOT/'guest/src/test/java/lab/owmcguest/NativeBuildersReviewCheck.java')
        compiled=subprocess.run([javac,'--release','21','-encoding','UTF-8','-d',str(folder),*map(str,files)],capture_output=True,text=True,timeout=30)
        self.assertEqual(compiled.returncode,0,compiled.stderr)
        run=subprocess.run([java,'-cp',str(folder),'lab.owmcguest.NativeBuildersReviewCheck'],capture_output=True,text=True,timeout=15)
        self.assertEqual(run.returncode,0,run.stderr)
        (folder/'result.json').write_text(json.dumps(dict(passed=True,result=run.stdout.strip()))+'\n',encoding='utf-8')


if __name__=='__main__':unittest.main()
