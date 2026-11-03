"""对启动中途失败、正常关闭流程识别不了的原版进程：校验可执行文件路径后发送 WM_CLOSE（等同点窗口 ×），不强杀。"""
import ctypes,sys,time,psutil
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from window_layout import windows_for_pid
from launch_passthrough_session import native_pids
EXE=(Path(__file__).resolve().parents[1]/'overwatch-2015/Overwatch Beta 0.8.0.24919/GameClientApp.patched.exe').resolve()
for pid in native_pids():
    if Path(psutil.Process(pid).exe()).resolve()!=EXE:continue
    for w in windows_for_pid(pid):ctypes.windll.user32.PostMessageW(w.handle,0x0010,0,0)
    for _ in range(40):
        if not psutil.pid_exists(pid):break
        time.sleep(1)
    print(pid,'已退出' if not psutil.pid_exists(pid) else '仍在运行')
