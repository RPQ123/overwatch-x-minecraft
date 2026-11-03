"""Use the original offline Controls UI to unbind empty weapon selection slots.

The beta stores these bindings in its offline session. Apply at cold startup;
Minecraft's own inventory keys and other applications are untouched.
"""
import ctypes,subprocess
from ctypes import wintypes as W
from observe_overwatch import ResearchProcess,ROOT
from window_layout import windows_for_pid

def configure(pid):
    proof=ResearchProcess(pid);proof.close()
    windows=windows_for_pid(pid);window=max(windows,key=lambda w:w.width*w.height)
    u=ctypes.WinDLL('user32');u.GetClientRect.argtypes=[W.HWND,ctypes.POINTER(W.RECT)]
    rect=W.RECT()
    if not u.GetClientRect(window.handle,ctypes.byref(rect)):raise ctypes.WinError()
    width,height=rect.right,rect.bottom
    if width<1024 or height<576 or abs(width/height-16/9)>.025:raise ValueError('Native Controls automation needs the calibrated16:9 client')
    def xy(x,y):return f'{round(x*width/2560)} {round(y*height/1440)}'
    commands=['focus','mup','key 0x1B','sleep 350','click '+xy(240,626),'sleep 350',
        'click '+xy(1675,1135)+' right','click '+xy(1675,1195)+' right',
        'drag '+xy(2420,312)+' '+xy(2420,487),'sleep 300',
        'click '+xy(1675,388)+' right','click '+xy(1675,448)+' right',
        'key 0x0D','sleep 200','key 0x1B','key 0x1B','sleep 250']
    p=subprocess.run(['um','win','drive','--proc','GameClientApp.patched.exe',*commands],cwd=ROOT,capture_output=True,text=True,encoding='utf-8',errors='replace',timeout=25)
    if p.returncode or '-> fail' in p.stdout or 'no-window' in p.stdout:raise ValueError('Native Controls input interrupted: '+(p.stdout+p.stderr)[-800:])
    return dict(pid=pid,width=width,height=height,route='original-key-bindings-ui',actions=['equip-weapon-1','equip-weapon-2','next-weapon','previous-weapon'],input=p.stdout)
