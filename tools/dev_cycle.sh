#!/usr/bin/env bash
# 开发循环：正常关闭 -> 构建/安装 -> 启动 -> 一个实测；MC崩溃退出4，正常清理，不重试崩溃。
# 用法：bash tools/dev_cycle.sh <实测脚本.py> <输出目录>
set -uo pipefail
cd "$(dirname "$0")/.." || exit 1
[ "$#" = 2 ] || { echo '用法: bash tools/dev_cycle.sh <实测脚本.py> <输出目录>'; exit 2; }
PY=.venv/Scripts/python.exe; TEST=$1; OUT=$2; LOGS=research/dev-cycle
mkdir -p "$LOGS"
SUPPORT=("$PY" tools/dev_cycle_support.py)
cleanup(){ "${SUPPORT[@]}" cleanup --logs "$LOGS"; }
check_crash(){ "${SUPPORT[@]}" check; }
crash_exit(){ cleanup; echo "本轮因MC崩溃终止（退出码4）；详见 $LOGS/minecraft-crash.json 和 $LOGS/cleanup-result.json"; exit 4; }
COUNT=$("${SUPPORT[@]}" alive) || exit 1
if [ "$COUNT" != 0 ]; then cleanup || exit 1; fi
"${SUPPORT[@]}" backup --logs "$LOGS" || exit 1
# 忽略历史报告，只追踪本轮新建/改写的client crash、JVM fatal和新增日志标记。
"${SUPPORT[@]}" snapshot || exit 1
GRADLE_USER_HOME="$PWD/tools/gradle-cache" cmd //c "tools\gradle\gradle-8.10.2\bin\gradle.bat -p guest --console=plain --no-daemon build -x test" > "$LOGS/build.log" 2>&1
grep -q "BUILD SUCCESSFUL" "$LOGS/build.log" || { echo "构建失败:"; grep -E "error:|\.java:[0-9]+" "$LOGS/build.log" | head -5; exit 1; }
"$PY" - <<'PY'
import hashlib,re
from pathlib import Path
j=Path('guest/build/libs/owmc-guest-0.1.0.jar');d=j.read_bytes();sha=hashlib.sha256(d).hexdigest()
for p in ('guest-passthrough-client','aoa3-connector-client'):(Path(p)/'mods'/j.name).write_bytes(d)
f=Path('tools/aoa3_passthrough_lab.py');s,n=re.subn(r"SHA='[0-9a-f]{64}'","SHA='"+sha+"'",f.read_text(encoding='utf-8'));assert n==1;f.write_text(s,encoding='utf-8');print('已安装',sha[:16])
PY
[ "$?" = 0 ] || exit 1
# 当前桌面若已是受支持16:9就保留，否则临时切1920×1080。
"$PY" - <<'PY2'
import json,sys;sys.path.insert(0,'tools')
from native_display_mode import DisplayLease,CURRENT,signature
cur=signature(DisplayLease().display().read(CURRENT));p='passthrough-settings.json';s=json.load(open(p,encoding='utf-8'))
s['width'],s['height']=(cur[0],cur[1]) if tuple(cur[:2]) in ((2560,1440),(1920,1080)) else (1920,1080)
open(p,'w',encoding='utf-8').write(json.dumps(s,indent=2)+chr(10));print('游戏分辨率',s['width'],s['height'],'桌面',cur)
PY2
[ "$?" = 0 ] || exit 1
launch(){
  : > "$LOGS/launch.log"
  T0=$("$PY" -c 'import time;print(time.time())') || return 1
  "$PY" tools/project_launcher.py --action start --log "$LOGS/launch.log" >/dev/null 2>&1 || return 1
  for ((i=0;i<90;i++)); do
    check_crash; CHECK=$?
    [ "$CHECK" = 0 ] || return "$CHECK"
    PHASE=$("${SUPPORT[@]}" phase --since "$T0") || return 1
    case "$PHASE" in gameplay|hero-selection) return 0;; esac
    case "$(tail -1 "$LOGS/launch.log")" in *rror*|*refused*) return 1;; esac
    sleep 5
  done
  return 1
}
launch; CODE=$?
[ "$CODE" != 4 ] || crash_exit
if [ "$CODE" != 0 ]; then
  FIRST=$(tail -1 "$LOGS/launch.log")
  echo "第一次启动失败，正常关闭后重试: $FIRST"
  cleanup || exit 1
  launch; CODE=$?
  [ "$CODE" != 4 ] || crash_exit
  if [ "$CODE" != 0 ]; then
    LAST=$(tail -1 "$LOGS/launch.log"); echo "启动失败: $LAST"
    cleanup || exit 1
    case "$FIRST$LAST" in *"Prepared fullscreen mode changed"*|*"Expected one original render window"*) echo "原因：远程桌面改回了分辨率，稍后重试"; exit 3;; esac
    exit 1
  fi
fi
sleep 12
check_crash; CODE=$?
[ "$CODE" != 4 ] || crash_exit
if [ "$CODE" != 0 ]; then cleanup; exit 1; fi
# 用参数数组运行，不使用eval；保留实测真实退出码，期间检查MC崩溃并正常收尾。
"${SUPPORT[@]}" run --test "$TEST" --evidence "$OUT" --logs "$LOGS"; CODE=$?
if [ "$CODE" != 0 ] && [ "$CODE" != 4 ]; then cleanup; fi
exit "$CODE"
