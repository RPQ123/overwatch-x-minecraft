"""Private Arena v2: convert only proven dust commands in native Command NBT.

Preserves all non-Command NBT bytes, all unrelated commands and chunk timestamps.
It does not upgrade items, attributes, boss rules, shaders or world DataVersion.
"""
from __future__ import annotations

import argparse
from collections import Counter
from decimal import Decimal
import gzip
import hashlib
import json
import os
from pathlib import Path
import re
import struct
import zipfile
import zlib

from pve_arena_port import PRIVATE_ROOT, SOURCE_SHA256
from pve_map_catalog import preflight, safe_member
from pve_world_audit import StreamingNBT, bounded_inflate, region_chunks

V1_SHA256 = "0429bc43a220713412402c1fa344c10ad3d9035faa37672ef5cbe2e48e50ecdb"
NUM = re.compile(r"-?(?:\d+(?:\.\d*)?|\.\d+)\Z")
OWNER_IDS = {"minecraft:command_block", "minecraft:command_block_minecart",
             "command_block", "command_block_minecart"}


def digest(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def tokens(command: str) -> list[tuple[str, int, int]]:
    """Top-level tokens only: JSON, selectors, quoted SNBT remain opaque."""
    result, start, quote, escape, stack = [], None, None, False, []
    for index, char in enumerate(command):
        if start is None:
            if char.isspace():
                continue
            start = index
        if quote:
            if escape:
                escape = False
            elif char == "\\":
                escape = True
            elif char == quote:
                quote = None
        elif char in "\"'":
            quote = char
        elif char in "[{":
            stack.append(char)
        elif char in "]}":
            if not stack or stack.pop() != {"]": "[", "}": "{"}[char]:
                raise ValueError("Unbalanced command data")
        elif char.isspace() and not stack:
            result.append((command[start:index], start, index))
            start = None
    if quote or stack:
        raise ValueError("Unterminated command data")
    if start is not None:
        result.append((command[start:], start, len(command)))
    return result


def particle_index(parts: list[str]) -> int | None:
    """Parse a deliberately limited execute grammar; never search blindly for run."""
    pos = 0
    while pos < len(parts):
        root = parts[pos].lstrip("/")
        if root == "particle":
            return pos
        if root != "execute":
            return None
        pos += 1
        while pos < len(parts):
            name = parts[pos]
            if name == "run":
                pos += 1
                break
            if name in {"as", "at", "align", "anchored", "in", "on", "summon"}:
                pos += 2
            elif name == "positioned":
                pos += 3 if parts[pos + 1:pos + 2] in (["as"], ["over"]) else 4
            elif name == "rotated":
                pos += 3
            elif name == "facing":
                pos += 4  # facing x y z OR facing entity <selector> <anchor>
            elif name in {"if", "unless"}:
                if pos + 1 >= len(parts):
                    return None
                condition = parts[pos + 1]
                if condition == "score":
                    if pos + 4 >= len(parts):
                        return None
                    if parts[pos + 4] == "matches":
                        pos += 6
                    elif parts[pos + 4] in {"<", "<=", "=", ">=", ">"}:
                        pos += 7
                    else:
                        return None
                elif condition == "block":
                    pos += 6
                elif condition == "blocks":
                    pos += 12
                elif condition in {"entity", "predicate", "dimension"}:
                    pos += 3
                elif condition == "loaded":
                    pos += 5
                elif condition == "biome":
                    pos += 6
                else:
                    return None
            else:
                return None
        else:
            return None
    return None


def convert_dust(command: str) -> tuple[str, dict | None]:
    if "dust" not in command or "particle" not in command:
        return command, None
    try:
        words = tokens(command)
    except ValueError:
        return command, {"blocked": "unbalanced_command_data"}
    index = particle_index([word[0] for word in words])
    if index is None or index + 1 >= len(words):
        return command, {"blocked": "not_a_supported_particle_execution_context"}
    kind = words[index + 1][0]
    simple = kind.removeprefix("minecraft:")
    if simple not in {"dust", "dust_color_transition"}:
        return command, None  # Already converted options, or another particle type.
    count = 4 if simple == "dust" else 7
    selected = words[index + 2:index + 2 + count]
    if len(selected) != count or not all(NUM.fullmatch(word[0]) for word in selected):
        return command, {"blocked": "unsupported_old_dust_numeric_syntax"}
    values = [Decimal(word[0]) for word in selected]
    colors = values[:3] + (values[4:] if simple == "dust_color_transition" else [])
    if any(value < 0 or value > 1 for value in colors) or not Decimal("0.01") <= values[3] <= 4:
        return command, {"blocked": "dust_values_outside_target_codec_range"}
    numbers = [word[0] + "f" for word in selected]
    if simple == "dust":
        options = "{color:[" + ",".join(numbers[:3]) + "],scale:" + numbers[3] + "}"
    else:
        options = ("{from_color:[" + ",".join(numbers[:3]) + "],scale:" + numbers[3]
                   + ",to_color:[" + ",".join(numbers[4:]) + "]}")
    start, end = words[index + 1][1], selected[-1][2]
    prefix, suffix = command[:start], command[end:]
    output = prefix + kind + options + suffix
    return output, {"rule": "mojang_1_20_5_" + simple + "_options",
        "original_numeric_tokens": [word[0] for word in selected],
        "unchanged_prefix_sha256": digest(prefix.encode("utf-8")),
        "unchanged_suffix_sha256": digest(suffix.encode("utf-8"))}


class _Sink:
    def __init__(self):
        self.versions, self.legacy = Counter(), Counter()
        self.legacy_examples = {}
    def walk(self, *_args):
        pass


class CommandSpans(StreamingNBT):
    """Retain offsets, owner IDs and original strings; never reconstruct NBT types."""
    def __init__(self, raw):
        super().__init__(raw)
        self.frames, self.spans = [], []

    def scan(self, tag, findings, location, key="", depth=0):
        if tag == 10:
            frame = {"owner_id": None, "spans": []}
            self.frames.append(frame)
            super().scan(tag, findings, location, key, depth)
            self.frames.pop()
            for span in frame["spans"]:
                span["owner_id"] = frame["owner_id"]
        elif tag == 8 and key in {"Command", "id"}:
            self.nodes += 1
            if depth > 64 or self.nodes > 8_000_000:
                raise ValueError("Command span NBT budget exceeded")
            start = self.pos
            text = self.string()
            if key == "id" and self.frames:
                self.frames[-1]["owner_id"] = text
            elif key == "Command":
                span = {"start": start, "end": self.pos, "path": location, "text": text,
                        "owner_id": None}
                self.spans.append(span)
                if self.frames:
                    self.frames[-1]["spans"].append(span)
        else:
            super().scan(tag, findings, location, key, depth)


def command_spans(raw: bytes, location: str) -> list[dict]:
    scanner = CommandSpans(raw)
    if scanner.number("B") != 10:
        raise ValueError("Expected compound NBT root")
    scanner.string()
    scanner.scan(10, _Sink(), location)
    if scanner.pos != len(raw):
        raise ValueError("NBT has trailing bytes")
    return sorted(scanner.spans, key=lambda row: row["start"])


def encode_modified_utf8(text: str) -> bytes:
    # NBT uses DataOutput.writeUTF: NUL is two bytes and astral chars are CESU-8.
    raw16 = text.encode("utf-16-be")
    raw = b"".join(chr(int.from_bytes(raw16[i:i + 2], "big")).encode("utf-8", "surrogatepass")
                   for i in range(0, len(raw16), 2)).replace(b"\0", b"\xc0\x80")
    if len(raw) > 65535:
        raise ValueError("Patched command exceeds NBT string byte limit")
    return struct.pack(">H", len(raw)) + raw


def masked_nbt(raw: bytes, spans: list[dict]) -> bytes:
    result, end = [], 0
    for span in spans:
        if span["start"] < end:
            raise ValueError("Overlapping command spans")
        result.extend((raw[end:span["start"]], b"\0\0"))
        end = span["end"]
    result.append(raw[end:])
    return b"".join(result)


def patch_nbt(raw: bytes, location: str) -> tuple[bytes, list[dict], list[dict]]:
    if b"dust" not in raw:
        return raw, [], []
    spans = command_spans(raw, location)
    changes, blocked, edits = [], [], []
    for span in spans:
        old = span["text"]
        new, detail = convert_dust(old)
        if detail is None:
            continue
        if span["owner_id"] not in OWNER_IDS:
            blocked.append({"path": span["path"], "reason": "owner_is_not_native_command_block_or_minecart"})
        elif "blocked" in detail:
            blocked.append({"path": span["path"], "reason": detail["blocked"]})
        else:
            replacement = encode_modified_utf8(new)
            edits.append((span["start"], span["end"], replacement))
            changes.append({"path": span["path"], "owner_id": span["owner_id"],
                "before": old, "after": new, "before_sha256": digest(old.encode("utf-8")),
                "after_sha256": digest(new.encode("utf-8")), **detail})
    output = raw
    for start, end, replacement in reversed(edits):
        output = output[:start] + replacement + output[end:]
    if changes:
        after_spans = command_spans(output, location)
        if masked_nbt(raw, spans) != masked_nbt(output, after_spans):
            raise ValueError("Non-Command NBT bytes changed")
        expected = {row["path"]: row["after"] for row in changes}
        if len(spans) != len(after_spans):
            raise ValueError("Command field count changed")
        for old, new in zip(spans, after_spans):
            if old["path"] != new["path"] or new["text"] != expected.get(old["path"], old["text"]):
                raise ValueError("Unexpected command mutation")
    return output, changes, blocked


def patch_region(raw: bytes, location: str) -> tuple[bytes, list[dict], list[dict], int]:
    changed_chunks, changes, blocked = {}, [], []
    count = 0
    for slot, payload in region_chunks(raw):
        count += 1
        patched, rows, failures = patch_nbt(payload, f"{location}#slot{slot}")
        blocked.extend(failures)
        if rows:
            changed_chunks[slot] = patched
            changes.extend(rows)
    if not changed_chunks:
        return raw, changes, blocked, count
    # Preserve timestamp header. Only allocation bookkeeping/compression may differ.
    output = bytearray(8192)
    output[4096:8192] = raw[4096:8192]
    for slot in range(1024):
        entry = int.from_bytes(raw[slot * 4:slot * 4 + 4], "big")
        if not entry:
            continue
        start, old_count = (entry >> 8) * 4096, entry & 255
        if slot in changed_chunks:
            compressed = zlib.compress(changed_chunks[slot], level=6)
            chunk = struct.pack(">I", len(compressed) + 1) + b"\x02" + compressed
            sectors = (len(chunk) + 4095) // 4096
            chunk += bytes(sectors * 4096 - len(chunk))
        else:
            sectors = old_count
            chunk = raw[start:start + sectors * 4096].ljust(sectors * 4096, b"\0")
        if sectors > 255:
            raise ValueError("Patched chunk would require an external MCA file")
        offset = len(output) // 4096
        output[slot * 4:slot * 4 + 4] = struct.pack(">I", (offset << 8) | sectors)
        output.extend(chunk)
    before_chunks, after_chunks = dict(region_chunks(raw)), dict(region_chunks(bytes(output)))
    if before_chunks.keys() != after_chunks.keys() or output[4096:8192] != raw[4096:8192]:
        raise ValueError("MCA allocation identity/timestamps changed unexpectedly")
    for slot, old in before_chunks.items():
        if after_chunks[slot] != changed_chunks.get(slot, old):
            raise ValueError("Unexpected MCA chunk payload mutation")
    return bytes(output), changes, blocked, count


def build_particle_candidate(source: Path, output: Path, *, expected_sha256=V1_SHA256,
                             private_root=PRIVATE_ROOT) -> dict:
    target, root = output.resolve(), private_root.resolve()
    if not target.is_relative_to(root) or target.suffix.lower() != ".zip":
        raise ValueError("Output must be a private map-cache ZIP")
    if target.exists():
        raise FileExistsError("Never replace a map artifact")
    source_report = preflight(source)
    if not source_report["archive_preflight"] or source_report["sha256"] != expected_sha256:
        raise ValueError("Pinned parent package identity mismatch")
    if source_report["level"]["data_version"] != 3700 or source_report["world_root"] != ".":
        raise ValueError("Expected unchanged Arena DataVersion3700")
    target.parent.mkdir(parents=True, exist_ok=True)
    temporary = target.with_suffix(".building")
    report = {"schema_version": 1, "kind": "partial_dust_command_migration",
        "author_original_sha256": SOURCE_SHA256, "parent_sha256": expected_sha256,
        "compatibility": {"status": "blocked_static", "installable": False},
        "installed": False, "game_input_sent": False, "world_load": False,
        "boss_fight": False, "reset_replay": False, "regions": 0, "chunks": 0,
        "changes": [], "blocked": [], "retained": [],
        "source": "https://www.minecraft.net/en-us/article/minecraft-java-edition-1-20-5",
        "scope": "Only dust/dust_color_transition in native Command-owner NBT; all other command/NBT bytes preserved"}
    with temporary.open("xb") as stream, zipfile.ZipFile(source) as before:
        with zipfile.ZipFile(stream, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=6) as after:
            for item in sorted(before.infolist(), key=lambda item: item.filename):
                name = safe_member(item.filename)
                if item.is_dir():
                    continue
                raw, rows, blocked = before.read(item), [], []
                content = raw
                if name.endswith(".mca"):
                    content, rows, blocked, count = patch_region(raw, name)
                    report["regions"] += 1
                    report["chunks"] += count
                elif name.endswith((".nbt", ".dat", ".dat_old")) and not (name == "uid.dat" and len(raw) == 16):
                    compressed = raw.startswith(b"\x1f\x8b")
                    payload = bounded_inflate(raw, 1) if compressed else raw
                    patched, rows, blocked = patch_nbt(payload, name)
                    if rows:
                        content = gzip.compress(patched, compresslevel=6, mtime=0) if compressed else patched
                if rows:
                    report["changes"].append({"path": name, "source_sha256": digest(raw),
                        "output_sha256": digest(content), "commands": rows,
                        "non_command_nbt_bytes_preserved": True})
                else:
                    report["retained"].append({"path": name, "sha256": digest(raw)})
                report["blocked"].extend(blocked)
                info = zipfile.ZipInfo(name, date_time=(1980, 1, 1, 0, 0, 0))
                info.create_system = 3
                info.external_attr = 0o100644 << 16
                info.compress_type = zipfile.ZIP_STORED if name.endswith(".zip") else zipfile.ZIP_DEFLATED
                after.writestr(info, content, compresslevel=6)
    check = preflight(temporary)
    if not check["archive_preflight"]:
        raise ValueError("Produced candidate failed structural preflight")
    # Atomic no-replace publication on the same filesystem, never os.replace().
    os.link(temporary, target)
    temporary.unlink()
    report["output"] = str(target)
    report["output_sha256"] = check["sha256"]
    report["output_bytes"] = target.stat().st_size
    report["converted_commands"] = sum(len(row["commands"]) for row in report["changes"])
    report["output_preflight"] = {**check, "archive": str(target)}
    report["unresolved"] = ["Old item/tag/attribute and other particle syntax remain",
        "Resource shaders and custom-head advancement icon remain blocked",
        "No target parser, world load or Boss battle/reset validation performed"]
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--manifest", type=Path, required=True)
    args = parser.parse_args()
    if args.manifest.exists():
        raise FileExistsError("Choose a new evidence manifest")
    report = build_particle_candidate(args.source, args.output)
    args.manifest.parent.mkdir(parents=True, exist_ok=True)
    with args.manifest.open("x", encoding="utf-8") as stream:
        json.dump(report, stream, ensure_ascii=False, indent=2)
        stream.write("\n")
    print(json.dumps({key: report[key] for key in ("output_sha256", "output_bytes", "converted_commands", "regions", "chunks", "compatibility")}, ensure_ascii=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
