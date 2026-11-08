"""Replay the owned raw declarations through production Roadhog binding guards.

Requires ignored audit output from audit_roadhog.py; never attaches to a process.
"""
import hashlib
import json
from pathlib import Path
import struct
import unittest

from inspect_hanzo_dragon_assets import FlatGraph
from inspect_symmetra_graphs import schemas
from roadhog_profile import validate_weapon, RESOURCES

ROOT=Path(__file__).resolve().parents[1]

class FlatReader:
    def __init__(self,raw,schema):
        self.graph=FlatGraph(raw);self.schema=schema;self.bindings=self
    def pointer(self,at):
        # DUTS3 encodes an absent config as 0xffffffff; the loader resolves it
        # to nullptr. It is not a failed attempt to interpret native code.
        value=self.graph.q(at)
        return 0 if value==0xffffffff else value
    def unpack(self,fmt,at):
        value=struct.unpack_from(fmt,self.graph.raw,at)
        return (0,) if fmt=='<Q' and value==(0xffffffff,) else value
    def metadata(self,at):return 0,self.graph.kind(at),0
    def field(self,obj,key):
        kind=self.graph.kind(obj);f=self.schema[f'{kind:08x}'][f'{key:08x}']
        return kind,obj+f['offset'],f['category'],int(f['declared'],16)
    def literal_int(self,at):return self.graph.literal(at)
    def literal_float_expression(self,at):return {'value':self.graph.literal(at)}
    def impact_damage(self,node):
        amount=self.pointer(self.pointer(self.pointer(node+360)+56)+56)
        return {'configType':'STUConfigVarInt','value':self.graph.literal(amount),'valueAddress':amount}

class RoadhogProfileTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.raw=(ROOT/'research/asset-cache/roadhog-audit/05800000000001c6.raw').read_bytes()
        receipt=json.loads((ROOT/'research/roadhog/evidence/original-graphs.json').read_text(encoding='utf-8'))
        expected=receipt['graphs']['05800000000001c6']['sha256']
        if hashlib.sha256(cls.raw).hexdigest()!=expected:raise ValueError('original graph SHA mismatch')
        cls.schema=schemas()
    def test_original_all_three_guards(self):
        r=FlatReader(self.raw,self.schema)
        for index,(resource,damage,*_) in RESOURCES.items():
            with self.subTest(node=index):validate_weapon(r,0x05800000000001c6,index,r.graph.nodes[index],resource,0,damage)
    def test_altered_nested_count_refused(self):
        raw=bytearray(self.raw);r=FlatReader(self.raw,self.schema);parent=r.graph.nodes[34]
        child=r.pointer(r.pointer(parent+384)+144);count=r.pointer(child+400)
        struct.pack_into('<i',raw,count+16,24);bad=FlatReader(bytes(raw),self.schema)
        with self.assertRaises(ValueError):validate_weapon(bad,0x05800000000001c6,34,parent,0x0400000000000295,0,50)
    def test_wrong_graph_resource_damage_gravity_refused(self):
        r=FlatReader(self.raw,self.schema);node=r.graph.nodes[30]
        for graph,index,resource,gravity,damage in [(0x05800000000001c8,30,0x040000000000029a,0,9),(0x05800000000001c6,34,0x040000000000029a,0,9),
            (0x05800000000001c6,30,0x040000000000029a,9.8,9),(0x05800000000001c6,30,0x040000000000029a,0,50)]:
            with self.subTest(graph=graph,index=index,damage=damage),self.assertRaises(ValueError):validate_weapon(r,graph,index,node,resource,gravity,damage)

if __name__=='__main__':unittest.main()
