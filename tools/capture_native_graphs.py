"""Bounded, read-only native graph sampling; no process opening on import.

Uses ResearchProcess and the same logger payload/owner checks as
NativeSkillReader. The original logger stores LAST state only, not an event
queue. Begin/End below are observed edges, never a lossless combat channel.
"""
from __future__ import annotations

import copy
import hashlib
import math
import struct
import time

SET_VAR = '4698e4b6'


def stream_key(sample):
    graphs = tuple(sorted((k, g['graph'], g['bag'], tuple(g['nodePointers']))
                          for k, g in sample['graphs'].items()))
    return sample['identity'], graphs


def variables_flat(value, prefix=''):
    """Keep the full dynamic RID path, raw bits and numeric type (no guessing)."""
    out = {}
    if isinstance(value, dict):
        for key, child in value.items():
            out.update(variables_flat(child, prefix + '/' + key))
    elif isinstance(value, list):
        for row in value:
            key = row.get('rid', '?')
            if 'children' in row:
                out.update(variables_flat(row['children'], prefix + '/' + key))
            else:
                out[prefix + '/' + key] = row
    return out


class Edges:
    """First sample, identity changes, failed reads and rollback rebaseline."""
    def __init__(self):
        self.previous = None
        self.segment = -1

    def gap(self):
        self.previous = None

    def add(self, sample, phase, elapsed):
        old = self.previous
        reason = 'first-or-after-gap' if old is None else None
        if old is not None:
            if stream_key(old) != stream_key(sample):
                reason = 'identity-or-graph-changed'
            elif any(row['tick'] < old['records'][key]['tick']
                     for key, row in sample['records'].items()
                     if key in old['records']):
                reason = 'tick-rollback'
        events, writes = [], []
        if reason:
            self.segment += 1
        else:
            for key, row in sample['records'].items():
                before = old['records'].get(key)
                if before == row:
                    continue
                # An absent logger row is unknown, not a synthetic End.
                event = 'Begin' if row['active'] else 'End'
                events.append(dict(**row, event=event, firstObserved=before is None,
                                   previous=before))
            before_vars, after_vars = map(variables_flat, (old['variables'], sample['variables']))
            for key in sorted(before_vars.keys() | after_vars.keys()):
                if before_vars.get(key) != after_vars.get(key):
                    writes.append(dict(path=key, before=before_vars.get(key),
                                       after=after_vars.get(key), writerVerified=False))
        self.previous = copy.deepcopy(sample)
        return dict(phase=phase, elapsed=round(elapsed, 6), segment=self.segment,
                    baseline=bool(reason), baselineReason=reason,
                    events=events, variableChanges=writes, **sample)


def collect(reader, seconds, phase, rows, edges, *, hz=100, origin=None,
            guard=lambda: None, clock=time.perf_counter, sleep=time.sleep):
    """Single bounded window, with measured cadence; never busy-waits/catches up."""
    start = clock()
    origin = start if origin is None else origin
    deadline = start + seconds
    attempts = 0
    while clock() < deadline-1e-9:
        tick = clock()
        guard()
        try:
            sample = reader.sample()
            row = edges.add(sample, phase, tick - origin)
            row['sampleMs'] = round((clock() - tick) * 1000, 3)
            rows.append(row)
        except (OSError, ValueError) as error:
            edges.gap()
            rows.append(dict(phase=phase, elapsed=round(tick-origin, 6),
                             readError=str(error), baseline=True))
        attempts += 1
        remaining = min(1 / hz - (clock()-tick), deadline-clock())
        if remaining > 0:
            sleep(remaining)
    return attempts


def cadence(rows, phase):
    times = [r['elapsed'] for r in rows if r['phase'] == phase and 'readError' not in r]
    gaps = sorted(b-a for a, b in zip(times, times[1:]))
    return dict(samples=len(times),
                measuredHz=round((len(times)-1)/(times[-1]-times[0]), 2) if gaps else 0,
                maxGapMs=round(max(gaps)*1000, 3) if gaps else None,
                p95GapMs=round(gaps[int((len(gaps)-1)*.95)]*1000, 3) if gaps else None,
                readFailures=sum('readError' in r for r in rows if r['phase'] == phase))


class GraphSampler:
    """All controller/model graphs, logger states and nested entity/script bags.

    No ACK, request, callback, code call, calibration switch or VM_WRITE access.
    Definitions are decoded before/after timing windows. New graph nodes are
    resolved afterwards, so a form change does not hide the sampling gap.
    """
    def __init__(self, process, pid, created):
        from observe_native_weapon_states import WeaponStates
        import ctypes
        self.process, self.pid, self.created = process, pid, created
        self.r = WeaponStates(process)
        self.catalog, self.current = {}, {}
        times = [ctypes.create_string_buffer(8) for _ in range(4)]
        process.kernel.GetProcessTimes.argtypes = [ctypes.c_void_p, *([ctypes.c_void_p]*4)]
        if not process.kernel.GetProcessTimes(process.handle, *times):
            raise ctypes.WinError(ctypes.get_last_error())
        self.creation = struct.unpack('<Q', times[0].raw)[0]
        actual_created = self.creation / 10_000_000 - 11644473600
        if abs(actual_created-created) > .001:
            raise ValueError('Read handle creation identity differs from requested PID')

    def identity(self):
        r, p = self.r, self.process
        admin = r.pointer(p.base + 0x17b7f90)
        local = r.unpack('<I', admin+0x220)[0]
        table = p.read(r.pointer(admin+16), 65536)
        controller = r.entity(table, local)
        reference, info = r.component(controller, 0x20), r.component(controller, 0x3f)
        model_id = r.unpack('<I', reference+0x94)[0]
        model = r.entity(table, model_id)
        if r.unpack('<I', controller+0x94)[0] != local or r.pointer(model+0x28) != admin:
            raise ValueError('Native owner/admin changed')
        return dict(pid=self.pid, created=self.created, creationFileTime=self.creation,
                    admin=admin, localId=local, controller=controller,
                    reference=reference, heroInfo=info, modelId=model_id, model=model,
                    hero=r.unpack('<Q', info+0x98)[0])

    def inventory(self, identity):
        r, graphs, entity_bags = self.r, {}, {}
        for role in ('controller', 'model'):
            owner = identity[role]
            try:
                component = r.component(owner, 0x23)
            except ValueError as error:
                # Absence is allowed; an existing malformed component is not.
                if str(error) == 'Research component 0x23 is absent':
                    continue
                raise
            inner = component+0xc0
            entity_bags[role] = r.unpack('<Q', inner+0x2e0)[0]
            for instance, in struct.iter_unpack('<Q', r.vector(inner+0xf0, 8)):
                if not instance:
                    continue
                graph, resource, bag = (r.pointer(instance+0x160),
                                        r.unpack('<Q', instance+0x150)[0],
                                        r.unpack('<Q', instance+0x98)[0])
                if r.pointer(r.pointer(r.pointer(instance+0x10)+0x450)+8) != owner:
                    raise ValueError('Native script owner differs')
                pointers = r.stu_list(graph+0x50)
                key = f'{role}:{instance:x}'
                graphs[key] = dict(role=role, owner=owner, instance=instance,
                                   script=f'{resource:016x}', graph=graph, bag=bag,
                                   nodePointers=pointers)
        return graphs, entity_bags

    def sample(self):
        from native_map_snapshot import snapshot_map
        r, p = self.r, self.process
        identity = self.identity()
        graphs, entity_bags = self.inventory(identity)
        if not graphs:
            raise ValueError('No current controller/model graphs')
        if not r.unpack('<Q', r.logger_entry)[0]:
            raise ValueError('Existing original logger has no state-entry trampoline')
        by_instance = {g['instance']: (key, g) for key, g in graphs.items()}
        records, variables = {}, {}
        for role, bag in entity_bags.items():
            variables['entity:'+role] = r.varbag(bag)
        for key, g in graphs.items():
            variables[key+':'+g['script']] = r.varbag(g['bag'])
        for instance, inner_map in snapshot_map(p, r.logger, 'Q'):
            if instance not in by_instance:
                continue
            graph_key, g = by_instance[instance]
            for node, at in snapshot_map(p, inner_map, 'i'):
                raw = p.read(at, 9)
                if p.read(at, 9) != raw:
                    raise ValueError('Native logger payload changed during read')
                tick, finished = struct.unpack('<qB', raw)
                if not 0 <= node < len(g['nodePointers']) or tick < 0 or finished > 1:
                    raise ValueError('Native logger payload bounds')
                records[f'{graph_key}:{node}'] = dict(
                    graphKey=graph_key, instance=instance, script=g['script'],
                    node=node, tick=tick, active=finished == 0, finished=bool(finished))
        health = self.health(identity)
        # NativeSkillReader also verifies all owner/script/bag/node identities
        # after the reads. Do not publish a partly old, partly new batch.
        if self.identity() != identity or self.inventory(identity) != (graphs, entity_bags):
            raise ValueError('Hero/model/controller/graph changed during snapshot')
        for key, g in graphs.items():
            signature = (identity['modelId'], key, g['graph'], tuple(g['nodePointers']))
            self.catalog.setdefault(signature, dict(identity=identity, **g))
        self.current = graphs
        return dict(wallMs=int(time.time()*1000), identity=identity,
                    graphs=graphs, records=records, variables=variables, healthPools=health)

    def health(self, identity):
        """Measured HealthPool layout from native_health_binding; no config edits."""
        try:
            r, out = self.r, []
            at = r.component(identity['model'], 0x28)
            if r.pointer(at) != self.process.base+0x15c5aa0 or r.pointer(at+8) != identity['model']:
                raise ValueError('Native health component identity differs')
            for kind, offset in enumerate((0x98, 0x1d8, 0x318)):
                raw = self.process.read(at+offset, 320)
                for slot in range(16):
                    enabled, maximum, current = struct.unpack_from('<Iff', raw, slot*20)
                    if enabled not in (0, 1) or not all(math.isfinite(x) for x in (maximum, current)):
                        raise ValueError('Native health numeric bounds')
                    if enabled:
                        if not 0 <= current <= maximum <= 10000:
                            raise ValueError('Native health pool bounds')
                        out.append(dict(kind=kind, slot=slot, maximum=maximum, current=current))
            return dict(component=at, pools=out, ownerVerified=True)
        except (ValueError, OSError) as error:
            return dict(readError=str(error), ownerVerified=False)

    def definitions(self):
        from inspect_native_impact import describe
        from inspect_support_native import expression
        out = {}
        for signature, graph in self.catalog.items():
            pointer_hash = hashlib.sha256(struct.pack('<'+'Q'*len(signature[3]), *signature[3])).hexdigest()[:16]
            key = f'{signature[0]}:{signature[1]}:{signature[2]:x}:{pointer_hash}'
            if key in out:
                continue
            try:
                # Refuse to follow pointers recycled after a model transition.
                if self.identity() != graph['identity']:
                    raise ValueError('Previous owner retired; no late pointer traversal')
                current, _ = self.inventory(graph['identity'])
                live = current.get(signature[1])
                if live is None or live != {k: v for k, v in graph.items() if k != 'identity'}:
                    raise ValueError('Graph retired before definition inspection')
                nodes = self.r.graph_nodes(graph['graph'])
                for row in nodes:
                    if row.get('hash') == SET_VAR:
                        detail = describe(self.r.bindings, graph['nodePointers'][row['index']])
                        row['setVarDefinition'] = detail
                        for field in detail['fields']:
                            obj = field.get('object', {})
                            if obj.get('type') == 'ec502a81':
                                obj['unevaluatedExpression'] = expression(self.r.bindings, obj['address'])
                if self.identity() != graph['identity'] or self.inventory(graph['identity'])[0].get(signature[1]) != live:
                    raise ValueError('Graph owner changed during definition inspection')
                out[key] = dict(**graph, nodes=nodes)
            except (OSError, ValueError) as error:
                out[key] = dict(**graph, definitionError=str(error))
        return out
