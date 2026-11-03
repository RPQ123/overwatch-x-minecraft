"""Release only a verified offline native picker's smaller stale cursor clip.

No hook or focus change. Never touches gameplay, Minecraft, another foreground
app, hidden cursor or a held mouse button. The existing supervisor owns polling.
"""
import ctypes,time
from ctypes import wintypes as w
from observe_overwatch import ROOT,ResearchProcess
from stop_passthrough import read_report
import psutil

def can_release(mode,foreground,cursor,drag,window,clip):
    if mode!=2 or not foreground or not cursor or drag:return False
    l,t,r,b=window;a,c,d,e=clip
    if not 0<r-l<=16384 or not 0<b-t<=16384:return False
    return (l<=a<d<=r and t<=c<e<=b and a<=(l+r)/2<d and c<=(t+b)/2<e
            and (d-a<r-l or e-c<b-t))

class CursorInfo(ctypes.Structure):
    _fields_=[('size',w.DWORD),('flags',w.DWORD),('cursor',w.HANDLE),('point',w.POINT)]

class PickerCursorRepair:
    def __init__(self,pid,version=40):
        process=ResearchProcess(pid);process.close()
        self.process=psutil.Process(pid);self.pid=pid;self.created=self.process.create_time();self.version=version;self.released=0
        self.user=ctypes.WinDLL('user32',use_last_error=True)
        self.user.GetForegroundWindow.restype=w.HWND
        self.user.GetWindowThreadProcessId.argtypes=[w.HWND,ctypes.POINTER(w.DWORD)]
        self.user.GetCursorInfo.argtypes=[ctypes.POINTER(CursorInfo)]
        self.user.GetClientRect.argtypes=[w.HWND,ctypes.POINTER(w.RECT)]
        self.user.ClientToScreen.argtypes=[w.HWND,ctypes.POINTER(w.POINT)]
        self.user.GetClipCursor.argtypes=[ctypes.POINTER(w.RECT)]
        self.user.ClipCursor.argtypes=[ctypes.POINTER(w.RECT)]
    def poll(self):
        if not self.process.is_running():return False
        path=ROOT/f'native-host/build/world-live-{self.pid}.json';stamp=path.stat().st_mtime
        if stamp<self.created or not 0<=time.time()-stamp<1:return False
        proof=read_report(path)
        if proof.get('pid')!=self.pid or proof.get('probeVersion')!=self.version or proof.get('enabled') is not True or proof.get('failures') or proof.get('viewMode')!=2:return False
        hwnd=self.user.GetForegroundWindow();owner=w.DWORD();self.user.GetWindowThreadProcessId(hwnd,ctypes.byref(owner))
        if owner.value!=self.pid:return False
        cursor=CursorInfo();cursor.size=ctypes.sizeof(cursor);client=w.RECT();origin=w.POINT();clip=w.RECT()
        if not self.user.GetCursorInfo(ctypes.byref(cursor)) or not self.user.GetClientRect(hwnd,ctypes.byref(client)) or not self.user.ClientToScreen(hwnd,ctypes.byref(origin)) or not self.user.GetClipCursor(ctypes.byref(clip)):return False
        win=(origin.x,origin.y,origin.x+client.right,origin.y+client.bottom);rect=(clip.left,clip.top,clip.right,clip.bottom)
        drag=any(self.user.GetAsyncKeyState(key)&0x8000 for key in (1,2,4))
        if not can_release(2,True,bool(cursor.flags&1),drag,win,rect) or hwnd!=self.user.GetForegroundWindow():return False
        again=w.RECT()
        if not self.user.GetClipCursor(ctypes.byref(again)) or (again.left,again.top,again.right,again.bottom)!=rect:return False
        if not self.user.ClipCursor(None):raise ctypes.WinError(ctypes.get_last_error())
        self.released+=1;return True
