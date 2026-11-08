"""Read the SHA-guarded owned beta archive; no game, injection or installation."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import struct

from ow_asset_chain import Archive
from inspect_hanzo_dragon_assets import FlatGraph
from inspect_symmetra_graphs import schemas, names, summarize

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "research/roadhog/evidence"


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    archive = Archive("roadhog-audit")
    archive.load_package("02e0000000000040")
    schema, labels = schemas(), names()
    result = {"offlineOnly": True, "inGameVerified": False, "graphs": {}, "prefabs": {}}
    requested = [guid for guid in archive.records if guid.startswith("0580")
                 and any(owner.startswith("02e0000000000040") for owner in archive.owners[guid])]
    for guid in sorted(requested):
        row = archive.records[guid]
        raw = archive.fetch(row["ckey"], guid + ".raw")
        if len(raw) != row["bytes"] or hashlib.md5(raw).hexdigest() != row["ckey"]:
            raise ValueError("original content-key mismatch: " + guid)
        graph = FlatGraph(raw)
        nodes = []
        for i, at in enumerate(graph.nodes):
            node = summarize(graph, at, schema, labels)
            node["node"] = i
            nodes.append(node)
        result["graphs"][guid] = {"sha256": hashlib.sha256(raw).hexdigest(), "ckey": row["ckey"], "nodes": nodes}
    for suffix in ("028f", "0294", "0295", "029a", "0405", "03f7"):
        guid = "040000000000" + suffix
        try:
            row = archive.resolve(guid)
            if row is None:
                raise ValueError("prefab is not present in this original package")
            raw = archive.fetch(row["ckey"], guid + ".raw")
            if hashlib.md5(raw).hexdigest() != row["ckey"]:
                raise ValueError("prefab content-key mismatch")
            refs = sorted({f"{struct.unpack_from('<Q', raw, i)[0]:016x}" for i in range(0, len(raw)-7, 8)
                           if struct.unpack_from('<Q', raw, i)[0] >> 48 in (0x0580, 0x0300, 0x0400)})
            result["prefabs"][guid] = {"sha256": hashlib.sha256(raw).hexdigest(), "ckey": row["ckey"], "refs": refs}
        except (ValueError, KeyError) as error:
            result["prefabs"][guid] = {"error": str(error)}
    (OUT / "original-graphs.json").write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    def node(graph,index):return result["graphs"]["058000000000"+graph]["nodes"][index]["fields"]
    def number(obj,*path):
        for key in path:obj=obj[key]
        return obj["literal"]
    weapon=node("01c6",30);parent=node("01c6",34);q=node("01c6",37)
    nested=parent["3ac99059"]["fields"]["m_volley"]["fields"]
    body=(archive.out/"040000000000028f.raw").read_bytes()
    key=struct.pack("<Q",0x0d800000000000c7)
    if body.count(key)!=1:raise ValueError("original base HP variable not unique")
    at=body.index(key);value=struct.unpack_from("<Q",body,at+8)[0]
    if struct.unpack_from("<Q",body,at-8)[0]!=0xffffffffffffffff or struct.unpack_from("<I",body,value)[0]!=0x3ae7427e:
        raise ValueError("original HP config entry changed")
    facts={"build":"0.8.0.24919","nativeHealth":struct.unpack_from("<i",body,value+16)[0],
           "healthSource":{"prefab":"040000000000028f","variable":"0d800000000000c7","entryOffset":at,"literalOffset":value},
           "ammo":number(node("01c6",3),"m_value"),"reloadSeconds":number(node("01c6",15),"m_value"),
           "primary":{"count":number(weapon,"m_numProjectilesPerShot"),"speed":number(weapon,"m_projectileSpeed"),"lifetime":number(weapon,"m_projectileLifetime"),
                      "damage":number(weapon["3d131607"]["fields"]["m_modifyHealth"]["fields"],"m_amount"),"falloff":[10,20,.3]},
           "secondary":{"speed":number(parent,"m_projectileSpeed"),"lifetime":number(parent,"m_projectileLifetime"),"damage":number(parent["3d131607"]["fields"]["m_modifyHealth"]["fields"],"m_amount"),
                        "onExpiryChild":{"count":number(nested,"m_numProjectilesPerShot"),"speed":number(nested,"m_projectileSpeed"),"lifetime":number(nested,"m_projectileLifetime"),
                                         "damage":number(nested["3d131607"]["fields"]["m_modifyHealth"]["fields"],"m_amount"),"spread":number(parent["3ac99059"]["fields"],"m_spread")}},
           "hook":{"damage":number(node("01c8",21)["m_modifyHealth"]["fields"],"m_amount"),"cooldown":number(node("01c8",4),"m_value"),
                   "searchRadius":number(node("01c8",19),"m_radius"),"rangeVariable670":number(node("01c8",63),"m_value")},
           "breather":{"amount":number(node("0240",23)["m_modifyHealth"]["fields"],"m_amount"),"cooldown":number(node("0240",1),"m_value"),
                       "animationSeconds":number(node("0240",3),"m_value"),"warmupSeconds":number(node("0240",24),"m_timeout"),"damageReductionDeclarationAuthenticated":False},
           "wholeHog":{"pelletsPerShot":number(q,"m_numProjectilesPerShot"),"shotsPerSecond":number(q,"m_numShotsPerSecond"),
                       "damage":number(q["3d131607"]["fields"]["m_modifyHealth"]["fields"],"m_amount"),"ballisticSpeedLifetimeAuthenticated":False},
           "inGameVerified":False}
    if facts["nativeHealth"]!=600 or facts["ammo"]!=4:raise ValueError("original Roadhog HP/ammo declaration changed")
    (OUT / "original-numbers.json").write_text(json.dumps(facts,ensure_ascii=False,indent=2),encoding="utf-8")
    print("original Roadhog graphs=" + str(len(result["graphs"])) + "; offline only")


if __name__ == "__main__":
    main()
