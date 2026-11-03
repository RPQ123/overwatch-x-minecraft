"""Read-only Soldier76 E declarations in the exact offline beta.

This is a calibration receipt, never a gameplay binding. A declared prefab or
SetVar value does not establish a spawned field, healing cadence, affiliation,
cover policy or lossless deployment event. No native evaluator is executed.
"""
import argparse
import json

from observe_overwatch import ROOT, ResearchProcess
from observe_native_weapon_states import WeaponStates
from provided_plugin_symbols import provided_plugin
from native_map_snapshot import lookup_map
from native_hero_catalog import model_scripts
from inspect_native_control_skills import literal, ref
from native_armory_binding import primitive, projectile_resources

HERO = 0x02e000000000006e
ABILITY = 0x0580000000000257
FIELD = 0x04000000000003dc
FIELD_SCRIPT = 0x0580000000000258


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
        raise ValueError('Select the original Soldier76 model')
    model = r.entity(table, sample['modelId'])
    matches = [key for key in r.graph_cache if key[2] == ABILITY]
    if len(matches) != 1:
        raise ValueError('Current Biotic Field ability graph is not unique')
    script, graph, _ = matches[0]
    bag = r.pointer(script + 0x98)
    nodes = r.stu_list(graph + 0x50)
    if len(nodes) != 26:
        raise ValueError('Uncalibrated Biotic Field ability graph')
    volley = nodes[6]
    if b.metadata(volley)[1] != 0x860ee5fc:
        raise ValueError('Biotic Field original Volley differs')
    variants = projectile_resources(r, volley)
    if len(variants) != 1 or variants[0][0] != 0x040000000000072d:
        raise ValueError('Biotic Field projectile visual differs')
    # This separate typed config reference is NOT the 072d projectile visual.
    # Its complete collision/deployment semantics have not been established.
    config = ref(b, volley, 0x3307a07b, 0x860ee5fc, 0x0dda5afc)
    entity_config = ref(b, config, 0x40877716, 0x0dda5afc, 0xbfd9aadd)
    if b.metadata(entity_config)[1] != 0xe53c2921:
        raise ValueError('Biotic Field entity config type differs')
    kind, at, category, target = b.field(entity_config, 0xb571fab4)
    if (kind, category, target) != (0xe53c2921, 12, 0xec23fffd):
        raise ValueError('Biotic Field entity reference declaration differs')
    entry, resource = r.unpack('<QQ', at)
    if resource != FIELD or not entry:
        raise ValueError('Biotic Field entity resource differs')
    base, image, pdb = provided_plugin(process)
    address = base + image.symbol_rva(pdb.exact('stu_resources::_constructed_stus'))
    def loaded_field_resources():
        values={rid:lookup_map(process,address,rid,'Q',20000) for rid in (FIELD,FIELD_SCRIPT)}
        if any(value is None for value in values.values()):raise ValueError('Biotic Field prefab/graph is not already loaded')
        return {rid:r.pointer(value) for rid,value in values.items()}
    loaded = loaded_field_resources()
    scripts = model_scripts(b, loaded[FIELD], loaded)
    if [s['resourceId'] for s in scripts] != [f'{FIELD_SCRIPT:016x}']:
        raise ValueError('Biotic Field prefab script differs')
    field_graph = loaded[FIELD_SCRIPT]
    field_nodes = r.stu_list(field_graph + 0x50)
    if len(field_nodes) != 14:
        raise ValueError('Biotic Field child graph differs')

    def assignment(index, identifier):
        node = field_nodes[index]
        destination = ref(b, node, 0xec9f34a6, 0x4698e4b6, 0xf8cc195d)
        if b.dynamic_path(destination) != [f'{identifier:016x}']:
            raise ValueError('Biotic Field SetVar destination differs')
        return literal(b, ref(b, node, 0x5180e750, 0x4698e4b6, 0xbfd9aadd))

    values = {
        'durationVariable': assignment(2, 0x0d80000000000237),
        'targetRangeVariable': assignment(3, 0x0d800000000001a6),
        'healAmountVariable': assignment(4, 0x0d800000000001a4),
    }
    target_node = field_nodes[1]
    range_config = ref(b, target_node, 0x71ef3ca4, 0x498b421a, 0xbfd9aadd)
    if b.metadata(range_config)[1] != 0xf8cc195d or b.dynamic_path(range_config) != ['0d800000000001a6']:
        raise ValueError('Biotic Field TrackTargets range differs')
    _, cooldown, _ = primitive(r, bag, 0x0d800000000001d8)
    if values != dict(durationVariable=5, targetRangeVariable=5, healAmountVariable=40) or cooldown != 15:
        raise ValueError('New Biotic Field values require separate calibration')
    volley_values = {key: literal(b, ref(b, volley, field, 0x860ee5fc, 0xbfd9aadd))
                     for key, field in [('speed', 0xac2f916a), ('lifetime', 0x5257be73), ('range', 0x308e35d5)]}
    if volley_values != dict(speed=10, lifetime=10, range=150):
        raise ValueError('New Biotic Field Volley values require calibration')
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
            or r.unpack('<Q', script + 0x150)[0] != ABILITY
            or r.pointer(r.pointer(r.pointer(script + 0x10) + 0x450) + 8) != model):
        raise ValueError('Biotic Field owner changed during calibration')
    live_resources = loaded_field_resources()
    if live_resources != loaded:
        raise ValueError('Biotic Field loaded resources changed during calibration')
    return dict(version=1, hero='Soldier76', heroId=f'{HERO:016x}', modelId=sample['modelId'],
                script=f'{ABILITY:016x}', volleyNode=6, projectileVisual='040000000000072d',
                fieldReference=f'{FIELD:016x}', fieldScript=f'{FIELD_SCRIPT:016x}',
                declaredInitialVariables=values, declaredCooldown=cooldown,
                declaredVolley=volley_values, fieldEntityObservation='not-performed',
                healingCadenceVerified=False, mcSkillImplemented=False,
                readOnly=True, newHooksInstalled=False, nativeCalls=False,
                losslessDeploymentChannel=False)


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
    print(json.dumps(result))


if __name__ == '__main__':
    main()
