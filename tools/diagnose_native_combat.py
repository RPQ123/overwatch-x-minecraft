"""Read current per-layer attack counters; never fire, load hooks or change heroes."""
import json
from pathlib import Path
import urllib.request
import psutil
from observe_overwatch import ROOT, ResearchProcess


def classify(native, guest):
    gate = native.get("weapon-gate", {})
    events = native.get("native-emissions", {})
    notes = []
    if not events.get("combatReady"):
        notes.append("native-weapon-not-calibrated-or-binding-not-ready")
    if gate.get("shotCalls", 0) == 0 and events.get("accepted", 0) == 0:
        notes.append("no-confirmed-native-shot-in-this-session")
    if events.get("accepted", 0) > 0 and guest.get("admitted", 0) == 0:
        notes.append("native-events-exist-but-minecraft-has-not-admitted-them")
    if guest.get("rejected", 0):
        notes.append("minecraft-rejected-events-check-world-session-and-freshness")
    if guest.get("admitted", 0) > 0 and "projectileEntitiesSpawned" not in guest:
        notes.append("old-minecraft-build-has-no-projectile-entity-presentation")
    if guest.get("presentationMode") == "original-assets-pending":
        notes.append("custom-effects-removed-original-asset-presentation-pending")
    if guest.get("presentationMode") == "original-genji-model" and not guest.get("originalEffectGraph"):
        notes.append("original-genji-model-loaded-full-effect-graph-pending")
    if guest.get("entityHits", 0) > 0 and guest.get("damageApplied", 0) == 0:
        notes.append("collision-found-check-target-invulnerability-or-damage-acceptance")
    return notes


def diagnose():
    executable=(ROOT/"overwatch-2015/Overwatch Beta 0.8.0.24919/GameClientApp.patched.exe").resolve()
    live=[]
    for process in psutil.process_iter(["pid", "exe"]):
        try:
            info=dict(process.info or {});image=info.get("exe")
            if image and Path(image).resolve()==executable:
                live.append(info.get("pid") or process.pid)
        except (OSError, psutil.Error):
            pass
    if len(live)!=1:
        return {"readOnly":True,"error":"expected-one-verified-offline-client","pids":live}
    pid=live[0];process=ResearchProcess(pid);process.close()
    creation=psutil.Process(pid).create_time()
    native={};errors=[]
    import time
    phase=None
    try:
        status=json.loads((ROOT/"research/session-status.json").read_text())
        if status.get("nativePid")==pid and abs(time.time()*1000-status.get("heartbeatMs",0))<4000:
            phase=status.get("phase")
    except (OSError,ValueError):
        pass
    stages=("world-live",) if phase=="hero-selection" else ("world-live", "body-sync", "weapon-gate", "native-emissions")
    for prefix in stages:
        path=ROOT/f"native-host/build/{prefix}-{pid}.json"
        try:
            if path.stat().st_mtime<creation or time.time()-path.stat().st_mtime>4:
                raise ValueError("report-is-stale")
            report=json.loads(path.read_text())
            if report.get("pid")!=pid:
                raise ValueError("report-pid-mismatch")
            native[prefix]=report
        except (OSError,ValueError) as error:
            errors.append(prefix+": "+str(error))
    guest={};health={}
    try:
        with urllib.request.urlopen("http://127.0.0.1:32133/health",timeout=2) as response:
            health=json.load(response)
        guest_process=psutil.Process(health["sourcePid"])
        if str(ROOT/"guest-passthrough-client") not in guest_process.cmdline():
            raise ValueError("guest-process-identity-mismatch")
        with urllib.request.urlopen("http://127.0.0.1:32133/combat",timeout=2) as response:
            guest=json.load(response)
    except (OSError,ValueError,KeyError,psutil.Error) as error:
        errors.append("guest: "+str(error))
    result={"readOnly":True,"pid":pid,"phase":phase,"native":native,"guest":guest,
            "health":health,"errors":errors,"findings":["hero-selection-awaiting-confirmation"] if phase=="hero-selection" else classify(native,guest),
            "visualAcceptance":"requires-inspected-composed-frames"}
    path=ROOT/f"research/combat-diagnosis-{pid}.json"
    path.write_text(json.dumps(result,indent=2)+"\n",encoding="utf-8")
    return {"path":str(path),"pid":pid,"errors":errors,"findings":result["findings"]}


if __name__=="__main__":
    print(json.dumps(diagnose(),indent=2))
