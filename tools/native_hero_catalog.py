"""Read-only hero/weapon census for the exact supplied offline beta.

No resource loading, hero switching, hooks, or native getter calls. Resource
presence is deliberately separate from calibrated combat support.
"""
import argparse
import json
import struct
import zlib
from observe_overwatch import ROOT, ResearchProcess
from native_map_snapshot import snapshot_map
from native_weapon_binding import WeaponBindingReader
from provided_plugin_symbols import provided_plugin
from inspect_native_scripts import ScriptReader

CALIBRATED = {
    0x02e0000000000029: {"name": "Genji", "weaponKind": "projectile", "script": "0580000000000304"},
    0x02e0000000000042: {"name": "McCree", "weaponKind": "hitscan", "script": "05800000000001d2"},
    0x02e0000000000009: {"name": "Winston", "weaponKind": "beam", "script": "05800000000000fe"},
}


def capability(resource_id):
    value = int(resource_id, 16)
    profile = CALIBRATED.get(value)
    return {"nativeCombatCalibrated": profile is not None,
            "playableAcceptance": "not-established-by-catalog",
            "weaponKind": profile["weaponKind"] if profile else "unmeasured",
            "missing": [] if profile else ["weapon-event-binding", "damage-and-ammo-calibration",
                "viewmodel-lens", "abilities", "dimension-switch-regression"]}


def reference_field(reader, value, wanted):
    """Locate a declared 16-byte resource reference without decoding its getter."""
    info, _, size = reader.metadata(value)
    seen = set()
    while info:
        if info in seen or len(seen) >= 32:
            raise ValueError("Hero metadata inheritance bound")
        seen.add(info)
        parent, args = reader.unpack("<QQ", info + 0x20)
        count = reader.unpack("<i", info + 0x54)[0]
        if not 0 <= count <= 512:
            raise ValueError("Hero field count bound")
        for i in range(count):
            key, offset = reader.unpack("<Ii", args + i * 0xa0 + 8)
            if key == wanted:
                if offset % 8 or not 8 <= offset <= size - 16:
                    raise ValueError("Hero resource reference bounds")
                return value + offset
        info = parent
    raise ValueError("Hero resource reference absent")


def model_scripts(reader, model, loaded):
    _, kind, _ = reader.metadata(model)
    if kind != zlib.crc32(b"stuentitydefinition"):
        raise ValueError("Hero model is not STUEntityDefinition")
    header, flag = reader.unpack("<QQ", model + 0x28)
    if flag != 2:
        raise ValueError("Hero component-map format")
    buckets, ends, items = reader.unpack("<i4xQQ", header)
    if not 1 <= buckets <= 256:
        raise ValueError("Hero component-map bucket bound")
    count = reader.unpack("<i", ends + (buckets-1)*4)[0]
    if not 1 <= count <= 256:
        raise ValueError("Hero component-map size bound")
    result = []
    for kind, component in struct.iter_unpack("<I4xQ", reader.memory.read(items, count*16)):
        if kind != zlib.crc32(b"stustatescriptcomponent"):
            continue
        if reader.metadata(component)[1] != kind:
            raise ValueError("Hero script component type differs")
        info, _, _ = reader.metadata(component)
        args = reader.pointer(info + 0x28)
        fields = reader.unpack("<i", info + 0x54)[0]
        if not 1 <= fields <= 512:
            raise ValueError("Hero script component field count")
        declarations = [reader.unpack("<IiQ", args + i*0xa0 + 8) for i in range(fields)]
        declaration = [item for item in declarations if item[0] == 0x0175ad85]
        if len(declaration) != 1 or declaration[0][1] != 8:
            raise ValueError("Hero script instance-list field differs")
        constraint = declaration[0][2]
        if reader.constraint_identity(constraint) != ((5 << 32) | 0xb773e1d0):
            raise ValueError("Hero scripts are not measured inline instance data")
        stride = reader.unpack("<i", reader.pointer(constraint + 0x28) + 0x5c)[0]
        if stride != 32:
            raise ValueError("Hero script instance data size differs")
        storage, flag = reader.unpack("<QQ", component + 8)
        if not storage:
            continue
        first, second = reader.unpack("<QQ", storage)
        items, count = (first, second) if flag == 1 else (second, first)
        if flag not in (1,2) or not 0 <= count <= 512:
            raise ValueError("Hero script-list bound")
        raw = reader.memory.read(items, count*stride) if count else b""
        for i in range(count):
            entry, rid = struct.unpack_from("<QQ", raw, i*stride)
            row = {"resourceId": f"{rid:016x}"}
            graph = loaded.get(rid)
            row["loaded"] = graph is not None
            if graph is not None:
                _, graph_kind, _ = reader.metadata(graph)
                row["typeHash"] = f"{graph_kind:08x}"
                if graph_kind == zlib.crc32(b"stustatescriptgraph"):
                    nodes = ScriptReader(reader.memory).graph_nodes(graph)
                    row["volleyNodes"] = [n["index"] for n in nodes if n.get("hash") == "860ee5fc"]
                    row["nodeCount"] = len(nodes)
            result.append(row)
    return result


def read_catalog(process, pid):
    module, image, pdb = provided_plugin(process)
    address = module + image.symbol_rva(pdb.exact("stu_resources::_constructed_stus"))
    reader = WeaponBindingReader(process)
    records = snapshot_map(process, address, "Q", 20000)
    loaded = {rid: reader.unpack("<Q", value)[0] for rid, value in records}
    heroes, errors = [], []
    for resource, value_address in records:
        # The early beta uses resource type 02e for heroes. Verify STU metadata
        # as well; a matching prefix alone is not proof of an actual hero.
        if resource >> 48 != 0x02e0:
            continue
        try:
            value = reader.pointer(value_address)
            _, kind, _ = reader.metadata(value)
            if kind != zlib.crc32(b"stuhero"):
                continue
            row = {"resourceId": f"{resource:016x}", **capability(f"{resource:016x}")}
            for label, key in (("gameplayEntity", zlib.crc32(b"m_gameplayentity")), ("displayString", 0x0cd16baa)):
                field = reference_field(reader, value, key)
                entry, rid = reader.unpack("<QQ", field)
                row[label] = f"{rid:016x}"
                if label == "gameplayEntity" and rid in loaded:
                    try:
                        row["modelScripts"] = model_scripts(reader, loaded[rid], loaded)
                    except (OSError, ValueError) as error:
                        row["modelScriptsError"] = str(error)
                if label == "displayString" and entry not in (0, 0xffffffffffffffff):
                    # Read the loaded UX string pointer, as the provided
                    # GetUXDisplayString does; never execute that getter.
                    aligned = entry & ~63
                    if reader.unpack("<Q", aligned + 0x10)[0] != rid:
                        raise ValueError("Hero display-string resource identity differs")
                    data = reader.pointer(aligned)
                    text = reader.pointer(data)
                    name = process.read(text, 128).split(b"\0", 1)[0].decode("utf-8")
                    if not name or not name.isprintable():
                        raise ValueError("Invalid hero display-string payload")
                    row["name"] = name
            heroes.append(row)
        except (OSError, ValueError) as error:
            errors.append({"resourceId": f"{resource:016x}", "error": str(error)})
    return {"pid": pid, "readOnly": True, "pdbDllIdentityMatched": True,
            "nativeCalls": False, "resourcesObserved": len(records),
            "heroes": sorted(heroes, key=lambda row: row["resourceId"]), "errors": errors}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pid", type=int)
    parser.add_argument("--snapshot", type=str, help="Inspect a saved private inventory instead of a process")
    parser.add_argument("--output", default="research/hero-capabilities.json")
    args = parser.parse_args()
    if bool(args.pid) == bool(args.snapshot):
        parser.error("Choose exactly one of --pid or --snapshot")
    output = (ROOT / args.output).resolve()
    if ROOT / "research" not in output.parents:
        parser.error("Output must stay in private research storage")
    if args.pid:
        process = ResearchProcess(args.pid)
        try:
            result = read_catalog(process, args.pid)
        finally:
            process.close()
    else:
        source = json.loads((ROOT / args.snapshot).read_text(encoding="utf-8"))
        result = {"historicalSnapshot": True, "source": args.snapshot,
            "heroes": [{"resourceId": row["resourceId"],
                "gameplayEntity": row.get("m_gameplayEntity"),
                **({"name": CALIBRATED[int(row["resourceId"],16)]["name"]} if int(row["resourceId"],16) in CALIBRATED else {}),
                **capability(row["resourceId"])} for row in source.get("heros", source.get("heroes", []))]}
    output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, ensure_ascii=True, indent=2))


if __name__ == "__main__":
    main()
