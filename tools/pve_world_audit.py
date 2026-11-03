"""Bounded, read-only world command/NBT audit. Never installs or rewrites chunks.

Reports are private evidence: command text can contain an author's original map
logic. A clean scan is not a command parser, DFU upgrade, or a gameplay test.
"""
from __future__ import annotations

import argparse
from collections import Counter
import gzip
import hashlib
import io
import json
from pathlib import Path
import re
import stat
import struct
import zlib
import zipfile

from pve_map_catalog import _NBT, EXECUTABLE, preflight, safe_member

MIB = 1024 ** 2
ROOT_COMMANDS = {
    "advancement", "attribute", "bossbar", "clear", "clone", "damage", "data",
    "datapack", "difficulty", "effect", "enchant", "execute", "experience", "fill",
    "forceload", "function", "gamemode", "gamerule", "give", "item", "kill", "loot",
    "particle", "playsound", "recipe", "say", "schedule", "scoreboard", "setblock",
    "setworldspawn", "spawnpoint", "spreadplayers", "stopsound", "summon", "tag",
    "team", "teleport", "tellraw", "time", "title", "tp", "trigger", "weather", "xp",
}
# These are risk indicators, deliberately NOT a full Brigadier/SNBT parser.
RISKS = {
    "legacy_item_command": re.compile(r"\b(?:give|clear)\s+\S+\s+(?:minecraft:)?[a-z0-9_./]+\s*\{"),
    "legacy_item_fields": re.compile(r"\b(?:Count|CustomModelData|HideFlags|Unbreakable|Enchantments|StoredEnchantments|CanDestroy|CanPlaceOn|BlockEntityTag|SkullOwner)\s*:|\bSelectedItem\.tag\b|\bInventory[^\s]*\.tag\b"),
    "legacy_item_tag_path": re.compile(r"\b(?:SelectedItem|Inventory|HandItems|ArmorItems)[^\s]*\.tag(?:[.\s\[\{]|$)"),
    "legacy_attributes": re.compile(r"\b(?:Attributes|AttributeModifiers)\s*:|\b(?:Attributes|AttributeModifiers)(?:\[|\.)|\bmodifier\s+(?:add|remove|value)\s+[0-9a-fA-F-]{36}\b"),
    "legacy_particle_arguments": re.compile(r"\bparticle\s+(?:minecraft:)?(?:dust|dust_color_transition|block|block_marker|falling_dust|item|vibration|shriek|sculk_charge)\s"),
    "legacy_item_entity": re.compile(r"\bItem\s*:\s*\{[^\n]*?\b(?:Count|tag)\s*:"),
    "legacy_loot_schema": re.compile(r"\b(?:minecraft:)?(?:set_nbt|copy_nbt)\b"),
}


def sha256(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def bounded_inflate(raw: bytes, method: int, limit: int = 32 * MIB) -> bytes:
    if method == 3:
        if len(raw) > limit:
            raise ValueError("Uncompressed NBT exceeds budget")
        return raw
    if method not in (1, 2):
        raise ValueError(f"Unsupported region compression {method}")
    decoder = zlib.decompressobj(31 if method == 1 else 15)
    result = decoder.decompress(raw, limit + 1)
    if len(result) > limit or decoder.unconsumed_tail:
        raise ValueError("NBT expansion budget exceeded")
    result += decoder.flush()
    if len(result) > limit or not decoder.eof or decoder.unused_data:
        raise ValueError("Invalid, concatenated, or over-budget compressed NBT")
    return result


class AuditNBT(_NBT):
    """Read-only compound view; arrays are skipped, so never serialize this view."""
    def string(self) -> str:
        raw = self.take(self.number("H"))
        value = raw.replace(b"\xc0\x80", b"\0").decode("utf-8", errors="surrogatepass")
        # Java's modified UTF-8 encodes supplementary characters as surrogate pairs.
        return value.encode("utf-16-le", errors="surrogatepass").decode("utf-16-le", errors="strict")

    def payload(self, tag: int, depth: int = 0):
        if tag != 10:
            return super().payload(tag, depth)
        self.nodes += 1
        if depth > 64 or self.nodes > 200_000:
            raise ValueError("NBT nesting/node budget exceeded")
        result = {}
        while True:
            child = self.number("B")
            if not child:
                return result
            name = self.string()
            if name in result:
                raise ValueError("Duplicate NBT compound name")
            result[name] = self.payload(child, depth + 1)


def parse_nbt(raw: bytes) -> dict:
    reader = AuditNBT(raw)
    if reader.number("B") != 10:
        raise ValueError("NBT root is not compound")
    reader.string()
    result = reader.payload(10)
    if reader.pos != len(raw):
        raise ValueError("Trailing NBT bytes")
    return result


class StreamingNBT(AuditNBT):
    """Scan large structure block lists without retaining a reconstructed world."""
    def scan(self, tag: int, findings, location: str, key: str = "", depth: int = 0):
        self.nodes += 1
        if depth > 64 or self.nodes > 8_000_000:
            raise ValueError("Streaming NBT nesting/node budget exceeded")
        if key in {"Attributes", "AttributeModifiers", "Count", "tag", "CustomModelData", "ActiveEffects"}:
            findings.legacy[key] += 1
            examples = findings.legacy_examples.setdefault(key, [])
            if len(examples) < 5:
                examples.append(location)
        if tag in {1, 2, 3, 4, 5, 6}:
            value = self.number({1: "b", 2: "h", 3: "i", 4: "q", 5: "f", 6: "d"}[tag])
            if key == "DataVersion":
                findings.versions[str(value)] += 1
        elif tag in {7, 11, 12}:
            count = self.number("i")
            size = count * {7: 1, 11: 4, 12: 8}[tag]
            if count < 0 or self.pos + size > len(self.data):
                raise ValueError("Invalid streaming NBT array size")
            self.pos += size
        elif tag == 8:
            value = self.string()
            if key == "Command":
                findings.command(value, location, "nbt_Command")
            else:
                findings.walk(value, location)
        elif tag == 9:
            child, count = self.number("B"), self.number("i")
            if count < 0 or count > 2_000_000 or (child == 0 and count):
                raise ValueError("Invalid streaming NBT list")
            for index in range(count):
                self.scan(child, findings, f"{location}[{index}]", "", depth + 1)
        elif tag == 10:
            seen = set()
            while True:
                child = self.number("B")
                if not child:
                    break
                name = self.string()
                if name in seen:
                    raise ValueError("Duplicate NBT compound name")
                seen.add(name)
                self.scan(child, findings, location + "." + name, name, depth + 1)
        else:
            raise ValueError(f"Invalid streaming NBT tag {tag}")


def scan_nbt(raw: bytes, findings, location: str):
    reader = StreamingNBT(raw)
    if reader.number("B") != 10:
        raise ValueError("NBT root is not compound")
    reader.string()
    reader.scan(10, findings, location)
    if reader.pos != len(raw):
        raise ValueError("Trailing NBT bytes")


def region_chunks(raw: bytes):
    """Yield allocated MCA slots; unsupported/external chunks fail closed."""
    if len(raw) == 0:
        return
    if len(raw) < 8192:
        raise ValueError("Invalid region file size")
    occupied = {0, 1}
    for slot in range(1024):
        entry = int.from_bytes(raw[slot * 4:slot * 4 + 4], "big")
        offset, sectors = entry >> 8, entry & 255
        if not entry:
            continue
        if offset < 2 or not sectors or offset + sectors > (len(raw) + 4095) // 4096:
            raise ValueError("Invalid region sector range")
        allocation = set(range(offset, offset + sectors))
        if occupied & allocation:
            raise ValueError("Overlapping region sectors")
        occupied.update(allocation)
        start = offset * 4096
        length = int.from_bytes(raw[start:start + 4], "big")
        if length <= 1 or length + 4 > sectors * 4096 or start + 4 + length > len(raw):
            raise ValueError("Invalid region payload length")
        method = raw[start + 4]
        if method & 128:
            raise ValueError("External region chunk requires separate .mcc support")
        yield slot, bounded_inflate(raw[start + 5:start + 4 + length], method)


class Findings:
    def __init__(self):
        self.commands = {}
        self.counts = Counter()
        self.versions = Counter()
        self.legacy = Counter()
        self.legacy_examples = {}
        self.walk_nodes = 0

    def command(self, text: str, location: str, kind: str) -> None:
        text = text.strip().lstrip("/")
        if not text or text.startswith("#"):
            return
        if len(self.commands) >= 100_000 and sha256(text.encode("utf-8")) not in self.commands:
            raise ValueError("Unique command budget exceeded")
        ident = sha256(text.encode("utf-8"))
        risks = [name for name, pattern in RISKS.items() if pattern.search(text)]
        row = self.commands.setdefault(ident, {"sha256": ident, "text": text,
            "occurrences": 0, "locations": [], "risk_indicators": risks})
        row["occurrences"] += 1
        if len(row["locations"]) < 5:
            row["locations"].append(location)
        self.counts[kind] += 1
        self.counts["root:" + text.split(None, 1)[0]] += 1

    def walk(self, value, location: str, depth: int = 0) -> None:
        self.walk_nodes += 1
        if depth > 96 or self.walk_nodes > 100_000_000:
            raise ValueError("Finding traversal budget exceeded")
        if isinstance(value, dict):
            if isinstance(value.get("DataVersion"), int):
                self.versions[str(value["DataVersion"])] += 1
            for name in ("Attributes", "AttributeModifiers", "Count", "tag", "CustomModelData"):
                if name in value:
                    self.legacy[name] += 1
                    examples = self.legacy_examples.setdefault(name, [])
                    if len(examples) < 5:
                        examples.append(location + "." + name)
            if value.get("action") == "run_command" and isinstance(value.get("value"), str):
                self.command(value["value"], location + ".value", "json_click_command")
            for key, child in value.items():
                path = location + "." + key
                if key == "Command" and isinstance(child, str):
                    self.command(child, path, "nbt_Command")
                else:
                    self.walk(child, path, depth + 1)
        elif isinstance(value, list):
            for index, child in enumerate(value):
                self.walk(child, f"{location}[{index}]", depth + 1)
        elif isinstance(value, str):
            first = value.lstrip().lstrip("/").split(None, 1)[0:1]
            if first and first[0] in ROOT_COMMANDS:
                self.command(value, location, "stored_command_string")
            if value.lstrip().startswith(("{", "[")):
                try:
                    parsed = json.loads(value)
                except (ValueError, RecursionError):
                    return
                if isinstance(parsed, (dict, list)):
                    self.walk(parsed, location + "<json>", depth + 1)

    def report(self) -> dict:
        rows = sorted(self.commands.values(), key=lambda row: row["sha256"])
        risks = Counter()
        for row in rows:
            for name in row["risk_indicators"]:
                risks[name] += row["occurrences"]
        return {"command_occurrences": sum(row["occurrences"] for row in rows),
                "unique_commands": len(rows), "counts": dict(sorted(self.counts.items())),
                "risk_occurrences": dict(sorted(risks.items())),
                "legacy_nbt_fields": dict(sorted(self.legacy.items())),
                "legacy_nbt_examples": self.legacy_examples,
                "data_versions": dict(sorted(self.versions.items())), "commands": rows}


def inspect_pack(raw: bytes, location: str, findings: Findings) -> dict:
    with zipfile.ZipFile(io.BytesIO(raw)) as pack:
        items = pack.infolist()
        if len(items) > 20_000 or sum(i.file_size for i in items) > 256 * MIB:
            raise ValueError("Nested pack expansion budget exceeded")
        seen = set()
        paths = []
        meta = None
        shader_files = []
        json_risks = []
        for item in items:
            name = safe_member(item.filename)
            if (name.casefold() in seen or item.file_size > 64 * MIB
                    or stat.S_ISLNK(item.external_attr >> 16) or item.flag_bits & 1
                    or Path(name).suffix.casefold() in EXECUTABLE):
                raise ValueError("Nested pack alias or size exceeds budget")
            seen.add(name.casefold())
            if item.is_dir():
                continue
            content = pack.read(item)
            paths.append(name)
            if name == "pack.mcmeta":
                meta = json.loads(content)
            if name.endswith(".mcfunction"):
                for line, text in enumerate(content.decode("utf-8-sig").splitlines(), 1):
                    findings.command(text, f"{location}!{name}:{line}", "mcfunction")
            elif name.endswith(".json"):
                try:
                    value = json.loads(content)
                except (ValueError, UnicodeError):
                    json_risks.append({"path": name, "risk": "invalid_json"})
                    continue
                findings.walk(value, f"{location}!{name}")
                for risk in ("set_nbt", "copy_nbt", "killer_player", "direct_killer", "killer"):
                    # Audit only; do not globally replace keys or text components.
                    if re.search(r'"(?:minecraft:)?' + risk + r'"', content.decode("utf-8")):
                        json_risks.append({"path": name, "risk": risk})
            if "/shaders/" in name:
                shader_files.append(name)
        return {"path": location, "sha256": sha256(raw), "pack_meta": meta,
                "files": len(paths), "shader_files": shader_files, "json_risks": json_risks,
                "legacy_paths": [n for n in paths if re.search(r"^data/[^/]+/(?:functions|recipes|advancements|loot_tables|predicates|item_modifiers|structures)/|^data/[^/]+/tags/(?:functions|items|blocks|entity_types|fluids|game_events)/", n)]}


def audit_world(archive: Path, expected_sha256: str) -> dict:
    base = preflight(archive)
    if not base["archive_preflight"]:
        raise ValueError("World failed structural preflight: " + repr(base["errors"]))
    if base["sha256"] != expected_sha256:
        raise ValueError("Source SHA256 does not match pinned author package")
    findings = Findings()
    report = {"schema_version": 1, "source": base, "static_complete": False,
              "installed": False, "game_input_sent": False, "world_load": False,
              "boss_fight": False, "reset_replay": False, "errors": [],
              "region_files": 0, "empty_region_files": [], "unpadded_region_files": [],
              "chunks": 0, "nbt_files": 0, "opaque_non_nbt": [], "packs": []}
    with zipfile.ZipFile(archive) as world:
        for item in world.infolist():
            name = safe_member(item.filename)
            if item.is_dir():
                continue
            try:
                if name.endswith(".mca"):
                    report["region_files"] += 1
                    raw_region = world.read(item)
                    if not raw_region:
                        report["empty_region_files"].append(name)
                    elif len(raw_region) % 4096:
                        report["unpadded_region_files"].append(name)
                    for slot, raw_chunk in region_chunks(raw_region):
                        report["chunks"] += 1
                        scan_nbt(raw_chunk, findings, f"{name}#slot{slot}")
                elif name.endswith((".nbt", ".dat", ".dat_old")):
                    content = world.read(item)
                    if name == "uid.dat" and len(content) == 16:
                        report["opaque_non_nbt"].append({"path": name, "bytes": 16,
                            "sha256": sha256(content), "reason": "Bukkit UUID identity, not an NBT compound"})
                        continue
                    raw = bounded_inflate(content, 1) if content.startswith(b"\x1f\x8b") else content
                    scan_nbt(raw, findings, name)
                    report["nbt_files"] += 1
                elif name.endswith(".zip"):
                    report["packs"].append(inspect_pack(world.read(item), name, findings))
            except (ValueError, OSError, EOFError, UnicodeError, zipfile.BadZipFile, RuntimeError) as exc:
                report["errors"].append({"path": name, "error": str(exc)})
    report.update(findings.report())
    report["static_complete"] = not report["errors"]
    report["limitations"] = ["Risk indicators are not a command grammar or proof of runtime validity",
        "Streaming NBT skips array values; no NBT is serialized or upgraded",
        "Zero-byte and last-sector-unpadded region files are listed separately, not rewritten",
        "Source commands and all world binaries remain unchanged",
        "Resource shader/model/font semantics and actual Boss lifecycle require separate validation"]
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("archive", type=Path)
    parser.add_argument("--expected-sha256", required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    if args.out.exists():
        raise FileExistsError("Do not replace evidence; choose a new output")
    report = audit_world(args.archive, args.expected_sha256)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    with args.out.open("x", encoding="utf-8") as stream:
        json.dump(report, stream, indent=2, ensure_ascii=False)
        stream.write("\n")
    print(json.dumps({key: report[key] for key in ("static_complete", "region_files", "chunks", "nbt_files", "command_occurrences", "unique_commands", "risk_occurrences", "errors")}, ensure_ascii=True))
    return 0 if report["static_complete"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
