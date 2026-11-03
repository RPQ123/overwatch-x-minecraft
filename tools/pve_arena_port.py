"""Create a private, deliberately INCOMPLETE Arena 1.21.1 migration candidate.

Only three active datapacks receive exact path/schema edits. World NBT, command
blocks, resources and disabled packs stay byte-identical. This is not installable
until unresolved commands/resources and actual isolated play have been checked.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import io
import json
from pathlib import Path, PurePosixPath
import stat
import zipfile

from pve_map_catalog import EXECUTABLE, preflight, safe_member

SOURCE_SHA256 = "624c63961ac4610e42a77d9ab4552e84f6a9a3f6e925693e910aa25a2a3ef5c9"
PRIVATE_ROOT = Path.home() / ".universal-modder" / "maps"
PACKS = (
    "datapacks/ArenaOfDarknessDatapack_10_15.zip",
    "datapacks/PlayerRaycastLaser11_18.zip",
    "datapacks/VillagerRaycastLaser_11_18.zip",
)
SOURCES = {
    "components": "https://www.minecraft.net/en-us/article/minecraft-java-edition-1-20-5",
    "directories_attributes_loot": "https://www.minecraft.net/en-us/article/minecraft-java-edition-1-21",
}
SINGULAR = {"structures": "structure", "advancements": "advancement",
    "recipes": "recipe", "loot_tables": "loot_table", "predicates": "predicate",
    "item_modifiers": "item_modifier", "functions": "function"}
TAG_SINGULAR = {"functions": "function", "items": "item", "blocks": "block",
    "entity_types": "entity_type", "fluids": "fluid", "game_events": "game_event"}


def digest(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def renamed_path(name: str) -> str:
    parts = safe_member(name).split("/")
    if len(parts) >= 3 and parts[0] == "data":
        if parts[2] in SINGULAR:
            parts[2] = SINGULAR[parts[2]]
        elif parts[2] == "tags" and len(parts) >= 4 and parts[3] in TAG_SINGULAR:
            parts[3] = TAG_SINGULAR[parts[3]]
    return "/".join(parts)


def migrate_json(name: str, original: dict) -> tuple[dict, list[str], list[str]]:
    """Context-specific rules only. Unknown NBT is retained and marked blocked."""
    value = copy.deepcopy(original)
    changes, blockers = [], []
    if name == "pack.mcmeta":
        pack = value.get("pack")
        if not isinstance(pack, dict) or type(pack.get("pack_format")) is not int:
            raise ValueError("Expected integer datapack format")
        if pack["pack_format"] != 10:
            raise ValueError("Pinned active pack no longer has expected source format 10")
        if "supported_formats" in pack or "overlays" in value:
            raise ValueError("Ambiguous source format ranges/overlays require separate review")
        pack["pack_format"] = 48
        changes.append("pack_format_10_to_48")
        for block in value.get("filter", {}).get("block", []):
            if block.get("path") == "advancements/.*":
                block["path"] = "advancement/.*"
                changes.append("exact_vanilla_advancement_filter_path")
    elif "/recipe/" in name:
        if value.get("type") in {"minecraft:crafting_shaped", "minecraft:crafting_shapeless"}:
            result = value.get("result")
            if isinstance(result, dict) and set(result) <= {"item", "count"} and isinstance(result.get("item"), str):
                if "count" in result and (type(result["count"]) is not int or not 1 <= result["count"] <= 64):
                    raise ValueError("Recipe result count outside reviewed subset")
                result["id"] = result.pop("item")
                changes.append("recipe_result_item_to_id")
            else:
                blockers.append("recipe_result_outside_reviewed_subset")
    elif "/advancement/" in name:
        icon = value.get("display", {}).get("icon")
        if isinstance(icon, dict) and set(icon) == {"item"} and isinstance(icon["item"], str):
            icon["id"] = icon.pop("item")
            changes.append("simple_advancement_icon_item_to_id")
        elif isinstance(icon, dict) and ("item" in icon or "nbt" in icon):
            # In particular, do not discard the author's custom head NBT.
            blockers.append("advancement_icon_nbt_requires_components_conversion")
    elif "/loot_table/" in name:
        def visit(node):
            if isinstance(node, list):
                for child in node:
                    visit(child)
            elif isinstance(node, dict):
                if node.get("function") == "minecraft:looting_enchant":
                    if set(node) != {"function", "count"} or not isinstance(node["count"], dict) or set(node["count"]) != {"min", "max"}:
                        blockers.append("looting_enchant_outside_reviewed_subset")
                    else:
                        node["function"] = "minecraft:enchanted_count_increase"
                        node["enchantment"] = "minecraft:looting"
                        node["count"]["type"] = "minecraft:uniform"
                        changes.append("loot_looting_to_explicit_enchanted_count_increase")
                for child in node.values():
                    visit(child)
        visit(value)
    return value, changes, blockers


def deterministic_zip(entries: dict[str, bytes]) -> bytes:
    output = io.BytesIO()
    with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=6) as z:
        for name, raw in sorted(entries.items()):
            info = zipfile.ZipInfo(name, date_time=(1980, 1, 1, 0, 0, 0))
            info.create_system = 3
            info.external_attr = 0o100644 << 16
            info.compress_type = zipfile.ZIP_DEFLATED
            z.writestr(info, raw, compresslevel=6)
    return output.getvalue()


def transform_pack(raw: bytes) -> tuple[bytes, dict]:
    entries, seen, details = {}, set(), []
    with zipfile.ZipFile(io.BytesIO(raw)) as pack:
        infos = pack.infolist()
        if len(infos) > 20_000 or sum(i.file_size for i in infos) > 256 * 1024 ** 2:
            raise ValueError("Active datapack exceeds bounded conversion scope")
        for info in infos:
            old = safe_member(info.filename)
            new = renamed_path(old)
            if old.casefold() in seen:
                raise ValueError("Duplicate/case-alias active pack input")
            seen.add(old.casefold())
            if info.is_dir():
                continue
            if (stat.S_ISLNK(info.external_attr >> 16) or info.flag_bits & 1
                    or PurePosixPath(old).suffix.casefold() in EXECUTABLE
                    or info.file_size > 16 * 1024 ** 2):
                raise ValueError("Unsafe active datapack member")
            if new.casefold() in {n.casefold() for n in entries}:
                raise ValueError("Renamed datapack paths collide")
            content = pack.read(info)
            converted, changes, blockers = content, [], []
            if new.endswith(".json") or new == "pack.mcmeta":
                obj = json.loads(content.decode("utf-8-sig"))
                if not isinstance(obj, dict):
                    raise ValueError("Active pack JSON root must be object")
                obj, changes, blockers = migrate_json(new, obj)
                if changes:
                    converted = (json.dumps(obj, ensure_ascii=False, indent=2) + "\n").encode("utf-8")
            entries[new] = converted
            if old != new or content != converted or blockers:
                details.append({"source_path": old, "output_path": new,
                    "source_sha256": digest(content), "output_sha256": digest(converted),
                    "rules": (["exact_registry_directory_rename"] if old != new else []) + changes,
                    "unresolved": blockers})
    if "pack.mcmeta" not in entries:
        raise ValueError("Active datapack has no root pack.mcmeta")
    result = deterministic_zip(entries)
    return result, {"source_sha256": digest(raw), "output_sha256": digest(result),
                    "entries": details, "file_count": len(entries)}


def build_candidate(source: Path, output: Path, *, expected_sha256: str = SOURCE_SHA256,
                    private_root: Path = PRIVATE_ROOT) -> dict:
    root = private_root.resolve()
    target = output.resolve()
    if not target.is_relative_to(root) or target == root or target.suffix.lower() != ".zip":
        raise ValueError("Candidate must be a new ZIP inside the private map cache")
    if output.exists():
        raise FileExistsError("Never replace an existing map artifact")
    report = preflight(source)
    if not report["archive_preflight"] or report["sha256"] != expected_sha256:
        raise ValueError("Source preflight/hash does not match pinned input")
    if report.get("world_root") != "." or report["level"].get("data_version") != 3700:
        raise ValueError("Expected original Arena root and DataVersion 3700")
    converted, pack_reports = {}, []
    with zipfile.ZipFile(source) as original:
        for name in PACKS:
            result, entry_report = transform_pack(original.read(name))
            converted[name] = result
            pack_reports.append({"path": name, **entry_report})
        # Validate all transforms before creating any output. No world extraction.
        target.parent.mkdir(parents=True, exist_ok=True)
        retained = []
        with target.open("xb") as stream:
            with zipfile.ZipFile(stream, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=6) as candidate:
                for item in sorted(original.infolist(), key=lambda item: item.filename):
                    name = safe_member(item.filename)
                    if item.is_dir():
                        continue
                    raw = original.read(item)  # verifies every copied member's CRC
                    content = converted.get(name, raw)
                    info = zipfile.ZipInfo(name, date_time=(1980, 1, 1, 0, 0, 0))
                    info.create_system = 3
                    info.external_attr = 0o100644 << 16
                    info.compress_type = zipfile.ZIP_STORED if name.endswith(".zip") else zipfile.ZIP_DEFLATED
                    candidate.writestr(info, content, compresslevel=6)
                    if name not in converted:
                        retained.append({"path": name, "sha256": digest(raw), "bytes": len(raw)})
    with target.open("rb") as stream:
        candidate_sha = hashlib.file_digest(stream, "sha256").hexdigest()
    output_preflight = preflight(target)
    if not output_preflight["archive_preflight"] or output_preflight["sha256"] != candidate_sha:
        raise ValueError("Produced candidate failed actual ZIP/NBT preflight")
    return {"schema_version": 1, "kind": "partial_static_migration_candidate",
        "source_sha256": report["sha256"], "output_sha256": candidate_sha,
        "output_bytes": target.stat().st_size, "output": str(target),
        "source_version": "1.20.4", "target_version": "1.21.1",
        "compatibility": {"status": "blocked_static", "installable": False},
        "acceptance": {"archive_preflight": True, "world_load": False,
                       "boss_fight": False, "reset_replay": False},
        "installed": False, "game_input_sent": False,
        "output_preflight": output_preflight,
        "changes": pack_reports, "retained_payloads": retained,
        "sources": SOURCES,
        "unresolved": [
            "Command-block and structure command text still uses legacy item/NBT/particle/attribute syntax",
            "One advancement custom head icon retains legacy item/nbt fields; NBT was not discarded",
            "Resource pack format22 and its two custom shader files remain untouched; require interface review",
            "Disabled legacy datapacks and Bukkit metadata remain byte-identical",
            "level.dat DataVersion3700 and all MCA/entity/structure NBT remain byte-identical; engine DFU and isolated play still required",
            "No target command parser, actual world loading, Boss battle, failure/reset or fused damage has been verified"],
        "no_world_version_stamp_rewrite": True,
        "scope": "Only three active nested datapacks; never a complete compatibility claim"}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--manifest", type=Path, required=True)
    args = parser.parse_args()
    if args.manifest.exists():
        raise FileExistsError("Choose a new private/evidence manifest path")
    manifest = build_candidate(args.source, args.output)
    args.manifest.parent.mkdir(parents=True, exist_ok=True)
    with args.manifest.open("x", encoding="utf-8") as stream:
        json.dump(manifest, stream, ensure_ascii=False, indent=2)
        stream.write("\n")
    print(json.dumps({k: manifest[k] for k in ("output_sha256", "output_bytes", "compatibility", "installed")}, ensure_ascii=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
