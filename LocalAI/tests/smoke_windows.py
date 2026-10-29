"""ทดสอบส่วนที่ใช้ Windows API (รันใน GitHub Actions บน windows-latest)

  python LocalAI/tests/smoke_windows.py

ตรวจ: วางรูปจากคลิปบอร์ด, วางไฟล์ที่คัดลอกจาก Explorer, ลากไฟล์มาวาง, ข้อความยังวางได้ตามปกติ
"""
import ctypes
import os
import struct
import sys
import tempfile
import time
from ctypes import wintypes as wt
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")  # คอนโซลของ runner เป็น cp1252 พิมพ์ภาษาไทยไม่ได้
HOME = tempfile.mkdtemp()
os.environ["USERPROFILE"] = HOME  # ไม่ให้ไปเขียนทับข้อมูลแชตจริง
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import tkinter as tk  # noqa: E402

import LocalAI as L  # noqa: E402

u, k = ctypes.windll.user32, ctypes.windll.kernel32
k.GlobalAlloc.argtypes = [wt.UINT, ctypes.c_size_t]
k.GlobalAlloc.restype = wt.HGLOBAL
k.GlobalLock.argtypes = [wt.HGLOBAL]
k.GlobalLock.restype = ctypes.c_void_p
k.GlobalUnlock.argtypes = [wt.HGLOBAL]
u.OpenClipboard.argtypes = [wt.HWND]
u.SetClipboardData.argtypes = [wt.UINT, wt.HANDLE]
u.SetClipboardData.restype = wt.HANDLE
u.PostMessageW.argtypes = [wt.HWND, wt.UINT, wt.WPARAM, wt.LPARAM]

failures = []


def check(name, ok, detail=""):
    print(("PASS " if ok else "FAIL ") + name + (f"  ({detail})" if detail else ""))
    if not ok:
        failures.append(name)


def hglobal(data):
    h = k.GlobalAlloc(0x0002, len(data))  # GMEM_MOVEABLE
    p = k.GlobalLock(h)
    ctypes.memmove(p, data, len(data))
    k.GlobalUnlock(h)
    return h


def set_clipboard(fmt, data):
    for _ in range(20):
        if u.OpenClipboard(None):
            break
        time.sleep(0.05)
    u.EmptyClipboard()
    u.SetClipboardData(fmt, hglobal(data))
    u.CloseClipboard()


def dropfiles(paths):
    names = ("\0".join(paths) + "\0\0").encode("utf-16-le")
    return struct.pack("<IiiII", 20, 0, 0, 0, 1) + names  # DROPFILES, fWide=1


def pump(sec=0.5):
    end = time.time() + sec
    while time.time() < end:
        root.update()
        time.sleep(0.01)


root = tk.Tk()
app = L.App(root)
pump()
check("WinShell loaded", app.shell is not None)

# 1) รูปในคลิปบอร์ด (CF_DIB 24 บิต 4x3)
w, h = 4, 3
stride = (w * 24 + 31) // 32 * 4
dib = struct.pack("<IiiHHIIiiII", 40, w, h, 1, 24, 0, 0, 0, 0, 0, 0)
dib += b"".join(bytes([0, 0, 255] * w) + b"\0" * (stride - w * 3) for _ in range(h))
set_clipboard(8, dib)
result = app.on_prompt_paste()
att = app.pending[-1] if app.pending else {}
check("paste image", result == "break" and att.get("kind") == "image", str(att.get("name")))
if att.get("kind") == "image":
    photo = tk.PhotoImage(data=att["data"])
    check("pasted PNG decodes", (photo.width(), photo.height()) == (w, h),
          f"{photo.width()}x{photo.height()}")

# 2) ข้อความ → ต้องวางเป็นข้อความตามปกติ
root.clipboard_clear()
root.clipboard_append("hello")
root.update()
check("text clipboard is not an attachment", app.clipboard_attachment() == (None, None))

# 3) ไฟล์ที่คัดลอกจาก Explorer (CF_HDROP)
f1 = Path(HOME) / "ข้อมูล.txt"
f1.write_text("สวัสดี", encoding="utf-8")
set_clipboard(15, dropfiles([str(f1)]))
app.pending = []
result = app.on_prompt_paste()
check("paste copied file", result == "break" and [a["name"] for a in app.pending] == [f1.name],
      str([a["name"] for a in app.pending]))

# 4) ลากไฟล์มาวาง (WM_DROPFILES)
f2 = Path(HOME) / "drop.csv"
f2.write_text("a,b\n1,2\n", encoding="utf-8")
app.pending = []
u.PostMessageW(root.winfo_id(), 0x0233, hglobal(dropfiles([str(f2)])), 0)
pump(1.0)
check("drag and drop", [a["name"] for a in app.pending] == [f2.name],
      str([a["name"] for a in app.pending]))

root.destroy()
print("\nall passed" if not failures else f"\n{len(failures)} failed: {failures}")
sys.exit(1 if failures else 0)
