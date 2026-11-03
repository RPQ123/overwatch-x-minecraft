"""Read-only Pulse Bomb calibration for the exact offline Tracer model.

Declarations and lossy logger snapshots do not implement a sticky MC projectile.
In particular, the anonymous explosion field is not a measured contact fuse.
No evaluator, input, hook, gameplay binding or native write is performed here.
"""
import argparse
import json
import math

from observe_overwatch import ROOT, ResearchProcess
from observe_native_weapon_states import WeaponStates
from inspect_native_control_skills import inline, literal, ref
from native_armory_binding import projectile_resources

HERO = 0x02e0000000000003
SCRIPT = 0x0580000000000034
PROJECTILE = 0x0400000000000045


def inspect(process):
    r = WeaponStates(process)
    sample = r.sample_weapon(False, True)
    b = r.bindings
    admin = r.pointer(process.base + 0x17b7f90)
    table = process.read(r.pointer(admin + 16), 65536)
    controller = r.entity(table, sample['localId'])
    reference = r.component(controller, 0x20)
    info = r.component(controller, 0x3f)
    if r.unpack('<Q', info + 0x98)[0] != HERO:
        raise ValueError('Select the original Tracer model')
    model = r.entity(table, sample['modelId'])
    matches = [key for key in r.graph_cache if key[2] == SCRIPT]
    if len(matches) != 1:
        raise ValueError('Current Pulse Bomb graph is not unique')
    script, graph, _ = matches[0]
    bag = r.pointer(script + 0x98)
    nodes = r.stu_list(graph + 0x50)
    if len(nodes) != 45 or b.metadata(nodes[1])[1] != 0x860ee5fc:
        raise ValueError('Pulse Bomb graph/Volley changed')
    volley = nodes[1]
    variants = projectile_resources(r, volley)
    if len(variants) != 1 or variants[0][0] != PROJECTILE:
        raise ValueError('Pulse Bomb projectile reference changed')

    def number(obj, field, owner):
        return literal(b, ref(b, obj, field, owner, 0xbfd9aadd))

    flight = dict(speed=number(volley, 0xac2f916a, 0x860ee5fc),
                  lifetime=number(volley, 0x5257be73, 0x860ee5fc),
                  range=number(volley, 0x308e35d5, 0x860ee5fc))
    owner, at, category, declared = b.field(volley, 0xb5d34136)
    if (owner, category, declared) != (0x860ee5fc, 3, 0x7f06bc91):
        raise ValueError('Pulse Bomb projectile motion declaration changed')
    motions = r.stu_list(at)
    if len(motions) != 1 or b.metadata(motions[0])[1] != 0xc2b6ce4b:
        raise ValueError('Pulse Bomb gravity motion changed')
    flight['gravity'] = number(motions[0], 0x005269ee, 0xc2b6ce4b)
    explosion = ref(b, volley, 0x5b97fa06, 0x860ee5fc, 0x66bd247b)
    rings = [[literal(b, value) for value in row] for row in
             inline(b, explosion, 0xee107893, 0x66bd247b, 0xf91c284f, 16)]
    explosion_health = ref(b, explosion, 0x89174668, 0x66bd247b, 0x06a06f4e)
    blast_amount = number(explosion_health, 0xc43222bc, 0x06a06f4e)
    impact = ref(b, volley, 0x3d131607, 0x860ee5fc, 0x4ef1dd7e)
    impact_health = ref(b, impact, 0x89174668, 0x4ef1dd7e, 0x06a06f4e)
    impact_amount = number(impact_health, 0xc43222bc, 0x06a06f4e)
    anonymous_explosion_field = number(explosion, 0xb3aef067, 0x66bd247b)
    # Preserve the exact beta declarations. Modern 350/5m rules are not an
    # oracle for this build; neither are these literals a physics trace.
    if (flight != dict(speed=15, lifetime=5, range=100, gravity=30)
            or len(rings) != 2 or rings[0] != [2, 1]
            or rings[1][0] != 4 or not math.isclose(rings[1][1], .2, abs_tol=1e-6)
            or blast_amount != 400 or impact_amount != 5
            or anonymous_explosion_field != 1):
        raise ValueError('Pulse Bomb values need separate version calibration')
    charge_destination = ref(b, nodes[2], 0xec9f34a6, 0x4698e4b6, 0xf8cc195d)
    if (b.dynamic_path(charge_destination) != ['0d80000000000004', '0d80000000000156']
            or number(nodes[2], 0x5180e750, 0x4698e4b6) != 0):
        raise ValueError('Pulse Bomb native charge-reset declaration changed')
    current = process.read(r.pointer(admin + 16), 65536)
    if (r.pointer(process.base + 0x17b7f90) != admin
            or r.unpack('<I', admin + 0x220)[0] != sample['localId']
            or r.entity(current, sample['localId']) != controller
            or r.entity(current, sample['modelId']) != model
            or r.component(controller, 0x20) != reference
            or r.component(controller, 0x3f) != info
            or r.unpack('<I', reference + 0x94)[0] != sample['modelId']
            or r.unpack('<Q', info + 0x98)[0] != HERO
            or r.pointer(script + 0x160) != graph
            or r.pointer(script + 0x98) != bag
            or r.unpack('<Q', script + 0x150)[0] != SCRIPT
            or r.pointer(r.pointer(r.pointer(script + 0x10) + 0x450) + 8) != model):
        raise ValueError('Pulse Bomb owner changed during calibration')
    return dict(version=1, hero='Tracer', heroId=f'{HERO:016x}', modelId=sample['modelId'],
                script=f'{SCRIPT:016x}', volleyNode=1, projectile=f'{PROJECTILE:016x}',
                declaredFlight=flight, declaredBlastRings=rings,
                declaredBlastHealthModifier=blast_amount, declaredImpactHealthModifier=impact_amount,
                anonymousExplosionFields={'b3aef067': anonymous_explosion_field},
                nativeChargeResetDeclaration=True,
                diagnosticStates=[v for v in sample['records'].values() if v['instanceAddress'] == script],
                stickyAttachmentVerified=False, fuseStartPolicyVerified=False,
                mcPulseBombImplemented=False, losslessProjectileChannel=False,
                readOnly=True, nativeCalls=False, newHooksInstalled=False)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--pid', type=int, required=True)
    parser.add_argument('--output', required=True)
    args = parser.parse_args()
    path = (ROOT / args.output).resolve()
    if ROOT / 'research' not in path.parents or path.suffix != '.json':
        parser.error('Output must be a private research JSON file')
    process = ResearchProcess(args.pid)
    try:
        result = inspect(process)
    finally:
        process.close()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({key: value for key, value in result.items() if key != 'diagnosticStates'}))


if __name__ == '__main__':
    main()
