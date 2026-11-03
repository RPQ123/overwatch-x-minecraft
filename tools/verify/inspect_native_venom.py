"""Read-only Venom Mine declaration probe for the current offline Widowmaker model.

Reads graph0056 WeaponVolley1: projectile entity resource, flight and the impact/explosion
health declarations. Every field is tried independently and reported (no expected values yet:
this is the first calibration). No input, hook, evaluator or native write.
"""

# Preserve stable tools imports when this script is invoked by its new path.
import sys as _tidy_sys
from pathlib import Path as _TidyPath
_tidy_tools = _TidyPath(__file__).resolve().parents[1]
if str(_tidy_tools) not in _tidy_sys.path:
    _tidy_sys.path.insert(0, str(_tidy_tools))

import json
from observe_overwatch import ROOT, ResearchProcess
from observe_native_weapon_states import WeaponStates
from inspect_native_control_skills import inline, literal, ref
from native_armory_binding import projectile_resources

HERO = 0x02e000000000000a
SCRIPT = 0x0580000000000056


def inspect(process):
    r = WeaponStates(process); sample = r.sample_weapon(False, True); b = r.bindings
    admin = r.pointer(process.base + 0x17b7f90); table = process.read(r.pointer(admin + 16), 65536)
    info = r.component(r.entity(table, sample['localId']), 0x3f)
    if r.unpack('<Q', info + 0x98)[0] != HERO: raise ValueError('Select the original Widowmaker model')
    matches = [k for k in r.graph_cache if k[2] == SCRIPT]
    if len(matches) != 1: raise ValueError('Venom graph is not unique')
    script, graph, _ = matches[0]; nodes = r.stu_list(graph + 0x50)
    if len(nodes) != 27 or b.metadata(nodes[1])[1] != 0x860ee5fc: raise ValueError('Venom graph/Volley changed')
    volley = nodes[1]; out = {'projectiles': [hex(v[0]) for v in projectile_resources(r, volley)]}

    def attempt(name, fn):
        try: out[name] = fn()
        except Exception as error: out[name] = 'unavailable: ' + type(error).__name__ + ': ' + str(error)[:80]

    def number(obj, field, owner): return literal(b, ref(b, obj, field, owner, 0xbfd9aadd))
    for name, key in [('speed', 0xac2f916a), ('lifetime', 0x5257be73), ('range', 0x308e35d5)]:
        attempt(name, lambda key=key: number(volley, key, 0x860ee5fc))

    def motions():
        owner, at, category, declared = b.field(volley, 0xb5d34136)
        rows = []
        for m in r.stu_list(at):
            kind = b.metadata(m)[1]; row = {'type': hex(kind)}
            try: row['gravity'] = number(m, 0x005269ee, kind)
            except Exception as error: row['gravity'] = 'unavailable: ' + str(error)[:60]
            rows.append(row)
        return rows
    attempt('motions', motions)

    def health(field, decl):
        node = ref(b, volley, field, 0x860ee5fc, decl)
        hp = ref(b, node, 0x89174668, decl, 0x06a06f4e)
        return number(hp, 0xc43222bc, 0x06a06f4e)
    attempt('impactAmount', lambda: health(0x3d131607, 0x4ef1dd7e))
    attempt('explosionAmount', lambda: health(0x5b97fa06, 0x66bd247b))

    def rings():
        explosion = ref(b, volley, 0x5b97fa06, 0x860ee5fc, 0x66bd247b)
        return [[literal(b, v) for v in row] for row in inline(b, explosion, 0xee107893, 0x66bd247b, 0xf91c284f, 16)]
    attempt('explosionRings', rings)
    return out


if __name__ == '__main__':
    import argparse
    a = argparse.ArgumentParser(); a.add_argument('--pid', required=True, type=int); a.add_argument('--output', required=True)
    args = a.parse_args(); p = ResearchProcess(args.pid)
    try:
        result = inspect(p); path = ROOT / args.output; path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8'); print(json.dumps(result))
    finally: p.close()
