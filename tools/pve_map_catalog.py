"""Read-only PVE metadata and ZIP preflight. Never extracts or installs a world."""
from __future__ import annotations

import argparse
import gzip
import hashlib
import io
import json
from pathlib import Path, PurePosixPath
import re
import stat
import struct
import zipfile

CATALOG = Path(__file__).resolve().parents[1] / "config" / "pve-maps.json"
ACCEPTANCE = ("archive_preflight", "world_load", "boss_fight", "reset_replay")
RESERVED = {"CON", "PRN", "AUX", "NUL", *(f"COM{i}" for i in range(1, 10)),
            *(f"LPT{i}" for i in range(1, 10))}
EXECUTABLE = {".exe", ".dll", ".com", ".bat", ".cmd", ".ps1", ".vbs", ".msi", ".scr", ".lnk", ".jar"}


def challenge_ready(row: dict) -> bool:
    return (row.get("compatibility", {}).get("status") == "accepted"
            and all(row.get("acceptance", {}).get(key) is True for key in ACCEPTANCE))


def load_catalog(path: Path = CATALOG) -> dict:
    data = json.loads(path.read_text(encoding="utf-8"))
    if data.get("schema_version") != 1 or not isinstance(data.get("maps"), list):
        raise ValueError("Unsupported PVE catalog schema")
    ids = set()
    for row in data["maps"]:
        ident = row.get("id", "")
        if not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", ident) or ident in ids:
            raise ValueError("Invalid or repeated map ID")
        ids.add(ident)
        if not row.get("source_url", "").startswith("https://"):
            raise ValueError("Map source must be an HTTPS author/upload page")
        if row.get("status") == "ready" and not challenge_ready(row):
            raise ValueError("Map marked ready without all actual acceptance gates")
    return data


def safe_member(name: str) -> str:
    """Reject Windows path ambiguities before any future extraction can use it."""
    if (any(ord(c) < 32 or c in '<>:"|?*' for c in name)
            or "\\" in name or name.startswith("/")):
        raise ValueError(f"Unsafe archive path: {name!r}")
    parts = name.rstrip("/").split("/")
    if not parts or any(not p or p in {".", ".."} or p[-1:] in {".", " "}
                        or p.split(".")[0].upper() in RESERVED for p in parts):
        raise ValueError(f"Unsafe archive path: {name!r}")
    return str(PurePosixPath(*parts))


class _NBT:
    """Bounded Java NBT reader for level.dat metadata, not a world upgrader."""
    def __init__(self, raw: bytes):
        self.data = memoryview(raw)
        self.pos = 0
        self.nodes = 0

    def take(self, count: int) -> bytes:
        if count < 0 or self.pos + count > len(self.data):
            raise ValueError("Truncated or invalid level.dat NBT")
        result = bytes(self.data[self.pos:self.pos + count])
        self.pos += count
        return result

    def number(self, fmt: str):
        return struct.unpack(">" + fmt, self.take(struct.calcsize(">" + fmt)))[0]

    def string(self) -> str:
        # Java NBT modified UTF-8 can differ for unusual names. Metadata is ASCII.
        return self.take(self.number("H")).decode("utf-8", errors="replace")

    def payload(self, tag: int, depth: int = 0):
        self.nodes += 1
        if depth > 64 or self.nodes > 200_000:
            raise ValueError("NBT nesting/node budget exceeded")
        if tag in {1, 2, 3, 4, 5, 6}:
            return self.number({1: "b", 2: "h", 3: "i", 4: "q", 5: "f", 6: "d"}[tag])
        if tag in {7, 11, 12}:
            count = self.number("i")
            self.take(count * {7: 1, 11: 4, 12: 8}[tag])
            return None
        if tag == 8:
            return self.string()
        if tag == 9:
            child, count = self.number("B"), self.number("i")
            if count < 0 or count > 100_000 or (child == 0 and count):
                raise ValueError("Invalid NBT list")
            return [self.payload(child, depth + 1) for _ in range(count)]
        if tag == 10:
            result = {}
            while True:
                child = self.number("B")
                if child == 0:
                    return result
                name = self.string()
                result[name] = self.payload(child, depth + 1)
        raise ValueError(f"Invalid NBT tag {tag}")


def level_metadata(compressed: bytes) -> dict:
    with gzip.GzipFile(fileobj=io.BytesIO(compressed)) as stream:
        raw = stream.read(16 * 1024 * 1024 + 1)
    if len(raw) > 16 * 1024 * 1024:
        raise ValueError("level.dat decompression budget exceeded")
    reader = _NBT(raw)
    if reader.number("B") != 10:
        raise ValueError("level.dat root must be a compound")
    reader.string()
    root = reader.payload(10)
    if reader.pos != len(raw) or not isinstance(root.get("Data"), dict):
        raise ValueError("Invalid level.dat Data compound/trailing bytes")
    data = root["Data"]
    version = data.get("Version", {})
    return {"data_version": data.get("DataVersion"),
            "version_name": version.get("Name") if isinstance(version, dict) else None,
            "level_name": data.get("LevelName"),
            "game_type": data.get("GameType"),
            "allow_commands": data.get("allowCommands"),
            "data_packs": data.get("DataPacks")}


def preflight(archive: Path, *, max_files: int = 100_000,
              max_total_bytes: int = 2 * 1024 ** 3,
              max_entry_bytes: int = 256 * 1024 ** 2) -> dict:
    """Only reads ZIP/metadata; successful preflight is NOT gameplay compatibility."""
    with archive.open("rb") as source:
        digest = hashlib.file_digest(source, "sha256").hexdigest()
    report = {"schema_version": 1, "archive": str(archive.resolve()), "sha256": digest,
              "archive_preflight": False, "installed": False, "world_load": False,
              "boss_fight": False, "reset_replay": False, "payload_crc_checked": False,
              "errors": [], "warnings": []}
    try:
        with zipfile.ZipFile(archive) as z:
            items = z.infolist()
            if len(items) > max_files:
                raise ValueError("Archive member budget exceeded")
            names, seen, total = {}, set(), 0
            for item in items:
                name = safe_member(item.filename)
                canonical = name.casefold()
                if canonical in seen:
                    raise ValueError(f"Duplicate/case-alias archive path: {name}")
                seen.add(canonical)
                if stat.S_ISLNK(item.external_attr >> 16):
                    raise ValueError(f"Symbolic link in map package: {name}")
                if item.flag_bits & 1:
                    raise ValueError("Encrypted member cannot be inspected")
                if item.file_size > max_entry_bytes or item.file_size < 0:
                    raise ValueError(f"Archive entry exceeds budget: {name}")
                total += item.file_size
                if total > max_total_bytes:
                    raise ValueError("Archive expanded-size budget exceeded")
                if PurePosixPath(name).suffix.casefold() in EXECUTABLE:
                    raise ValueError(f"Executable/mod installer is not a Java world: {name}")
                names[name] = item
            levels = [name for name in names if name == "level.dat" or name.endswith("/level.dat")]
            if len(levels) != 1:
                raise ValueError(f"Expected one world level.dat, found {len(levels)}")
            level = levels[0]
            if names[level].file_size > 8 * 1024 ** 2:
                raise ValueError("Compressed level.dat exceeds metadata budget")
            report["level"] = level_metadata(z.read(level))
            root = level[:-len("level.dat")]
            report["world_root"] = root.rstrip("/") or "."
            report["file_count"] = len(items)
            report["uncompressed_bytes"] = total
            report["resource_packs"] = [n for n in names if n == root + "resources.zip"]
            report["data_pack_entries"] = [n for n in names if n.startswith(root + "datapacks/") and not names[n].is_dir()]
            report["readme_entries"] = [n for n in names if PurePosixPath(n).name.casefold().startswith(("readme", "read me", "instructions", "license"))]
            report["region_files"] = sum(n.startswith(root + "region/") and n.endswith(".mca") for n in names)
            report["warnings"].append("ZIP/NBT metadata only; command blocks, nested packs and boss rules remain untested")
            if report["resource_packs"]:
                report["warnings"].append("Embedded resource ZIP requires a separate bounded inspection")
            report["archive_preflight"] = True
    except (ValueError, OSError, EOFError, zipfile.BadZipFile, RuntimeError) as exc:
        report["errors"].append(str(exc))
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--catalog", type=Path, default=CATALOG)
    parser.add_argument("--preflight", type=Path)
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()
    result = preflight(args.preflight) if args.preflight else load_catalog(args.catalog)
    encoded = json.dumps(result, ensure_ascii=False, indent=2)
    if args.out:
        if args.out.exists():
            raise FileExistsError("Choose a fresh report path; do not replace evidence")
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(encoded + "\n", encoding="utf-8")
    print(encoded)
    return 0 if not args.preflight or result["archive_preflight"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
