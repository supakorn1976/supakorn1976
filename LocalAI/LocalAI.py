#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Local AI Chat • Ollama — tkinter edition
แปลงจาก local_ollama_chat.html เป็นโปรแกรม Desktop ด้วย tkinter

ความสามารถ:
  • แชตแบบ streaming กับ Ollama ในเครื่อง (/api/chat)
  • เลือก/โหลดรายชื่อโมเดล (/api/tags)
  • ประวัติแชต: ค้นหา เปลี่ยนชื่อ ลบ (บันทึกเป็นไฟล์ JSON ในโฟลเดอร์ home)
  • แสดงผล Markdown (หัวข้อ, ลิสต์, ตาราง, โค้ดบล็อก, ตัวหนา/เอียง, ลิงก์, quote)
  • แนบไฟล์ข้อความ/โค้ด, PDF, Word (.docx) และรูป (PNG/JPG/WEBP สำหรับโมเดลที่ดูรูปได้)
    — กดปุ่มแนบ, ลากไฟล์มาวาง (Windows) หรือ Ctrl+V รูป/ไฟล์ที่คัดลอกไว้
  • แก้ไขข้อความที่ส่งไปแล้ว แล้วให้ตอบใหม่ (✎ แก้ไข ใต้ข้อความ)
  • รูปที่แนบเก็บแยกในโฟลเดอร์ ~/.local_ai_ollama_images
  • คำตอบยาวไม่หน่วง: ระหว่าง stream วาดใหม่เฉพาะย่อหน้าท้าย
  • ไฮไลต์สีโค้ด (Python, JS/TS/Java/C/C#/Go/Rust/PHP, SQL, Shell, JSON)
  • จัดการโมเดล: ดาวน์โหลดพร้อมแถบความคืบหน้า, ดูข้อมูล, ลบ
  • บทบาท (System Prompt) หลายชุด เลือกแยกตามแชต
  • ขยาย/ย่อตัวอักษร Ctrl + / Ctrl − / Ctrl 0 หรือ Ctrl + ล้อเมาส์
  • โหมด Thinking (field "thinking" และแท็ก <think>…</think>) แบบพับ/ขยายได้
  • ตอบใหม่, ส่งออก .md, คัดลอกคำตอบ/โค้ด, แสดง tokens และ tok/s
  • คีย์ลัด: Enter ส่ง • Shift+Enter ขึ้นบรรทัด • Esc หยุด • Ctrl+N แชตใหม่
  • คัดลอก/วาง: คลิกขวาที่ช่องพิมพ์หรือข้อความแชต (ตัด/คัดลอก/วาง/เลือกทั้งหมด)
    และ Ctrl+C / Ctrl+V / Ctrl+X / Ctrl+A ใช้ได้แม้เปิดแป้นพิมพ์ภาษาไทยอยู่

ใช้เฉพาะ Python standard library (ไม่ต้อง pip install อะไรเพิ่ม)
"""

import base64
import datetime
import hashlib
import json
import os
import queue
import re
import shutil
import struct
import subprocess
import sys
import threading
import time
import urllib.error
import urllib.request
import uuid
import webbrowser
import xml.etree.ElementTree as ET
import zipfile
import zlib
from pathlib import Path

import tkinter as tk
import tkinter.font as tkfont
from tkinter import filedialog, messagebox, simpledialog, ttk

APP_TITLE = "Local AI Chat • Ollama"
DATA_FILE = Path.home() / ".local_ai_ollama_chat.json"

C = {
    "bg": "#202123", "side": "#151617", "panel": "#2c2d30", "panel_hover": "#3a3c3e",
    "line": "#414348", "border": "#4b4c50", "text": "#f0f0f0", "muted": "#a7a7aa",
    "accent": "#21c482", "accent_hover": "#35d793", "accent_text": "#092b1d",
    "red": "#eb747c", "stop_bg": "#4a2d31", "user_bubble": "#30353a",
    "code_bg": "#111315", "inline_code": "#38393c", "field": "#28292b",
    "link": "#8ad3ff", "user_name": "#a2dafa", "active_row": "#303134",
    "composer": "#2e3032", "thought_bg": "#26272a", "thought_fg": "#b2b5b7",
    "quote": "#c9c9ce", "select": "#2f5545",
    "table_head": "#36383c", "table_row": "#26282b", "table_alt": "#2c2e31",
}

DEFAULT_PRESETS = [
    {"name": "ผู้ช่วยเขียนโค้ด",
     "prompt": "คุณเป็นโปรแกรมเมอร์ผู้เชี่ยวชาญ ตอบเป็นภาษาไทย อธิบายสั้นกระชับ ให้โค้ดที่รันได้จริง"
               "ในโค้ดบล็อกพร้อมระบุภาษา และชี้จุดที่ควรระวัง"},
    {"name": "แปลไทย ↔ อังกฤษ",
     "prompt": "คุณเป็นนักแปลมืออาชีพ ถ้าข้อความเป็นภาษาไทยให้แปลเป็นภาษาอังกฤษ ถ้าเป็นภาษาอื่น"
               "ให้แปลเป็นภาษาไทย แปลให้เป็นธรรมชาติ รักษาความหมายและน้ำเสียงเดิม ตอบเฉพาะคำแปล"},
    {"name": "วิศวกรโยธา/ชลประทาน",
     "prompt": "คุณเป็นวิศวกรโยธาและวิศวกรชลประทานที่มีประสบการณ์ ตอบเป็นภาษาไทย อ้างอิงหลักการ"
               "และมาตรฐานที่เกี่ยวข้อง (เช่น วสท., ACI, กรมชลประทาน) แสดงสูตร หน่วย และขั้นตอน"
               "คำนวณให้ชัดเจน และระบุสมมติฐานที่ใช้"},
    {"name": "สรุปเอกสาร",
     "prompt": "สรุปเนื้อหาที่ได้รับเป็นภาษาไทย เริ่มด้วยใจความสำคัญ 1–2 ประโยค ตามด้วยประเด็นหลัก"
               "เป็นข้อ ๆ และตัวเลขสำคัญ ไม่เพิ่มข้อมูลที่ไม่มีในต้นฉบับ"},
]
PRESET_DEFAULT = "ค่าเริ่มต้น (จากตั้งค่า)"
PRESET_MANAGE = "✎ จัดการบทบาท..."

DEFAULTS = {
    "host": "http://localhost:11434", "model": "", "systemPrompt": "",
    "temperature": 0.7, "numCtx": 8192, "maxHistory": 20, "think": False,
    "presets": DEFAULT_PRESETS, "fontScale": 1.0,
}

SUGGESTED_MODELS = [
    "llama3.2:3b", "qwen3:8b", "qwen2.5:7b", "gemma3:4b", "gemma3:12b", "deepseek-r1:8b",
    "qwen2.5-coder:7b", "gpt-oss:20b", "llava:7b", "qwen2.5vl:7b", "mistral:7b", "phi4-mini",
]

INLINE_RE = re.compile(
    r"(`[^`\n]+`|\*\*[^*\n]+\*\*|~~[^~\n]+~~|\*[^*\n]+\*|\[[^\]]+\]\(https?://[^\s)]+\))"
)
FENCE_RE = re.compile(r"^\s*```\s*([\w.+-]*)")
LIST_RE = re.compile(r"^([-*]|\d+[.)])\s+(.+)")
HOST_RE = re.compile(r"^https?://(localhost|127\.0\.0\.1)(:\d+)?$", re.I)
TABLE_SEP_RE = re.compile(r"^\s*\|?\s*:?-{2,}:?\s*(\|\s*:?-{2,}:?\s*)*\|?\s*$")

IMAGE_EXT = {".png", ".jpg", ".jpeg", ".webp"}
MAX_IMAGE_BYTES = 15 * 1024 * 1024
MAX_FILE_CHARS = 200_000

# keycode ของปุ่มตัวอักษร ใช้จับ Ctrl+C/V/X/A/N ตอนเปิดแป้นภาษาไทย (keysym จะเป็นอักษรไทย)
# และ Ctrl + / Ctrl − / Ctrl 0 สำหรับขยายตัวอักษร
if sys.platform == "win32":
    CTRL_KEYCODES = {65: "a", 67: "c", 86: "v", 88: "x", 78: "n",
                     187: "+", 107: "+", 189: "-", 109: "-", 48: "0", 96: "0"}
elif sys.platform == "darwin":
    CTRL_KEYCODES = {}
else:
    CTRL_KEYCODES = {38: "a", 54: "c", 55: "v", 53: "x", 57: "n",
                     21: "+", 86: "+", 20: "-", 82: "-", 19: "0", 90: "0"}
ZOOM_STEPS = {"+": 0.1, "-": -0.1, "0": 0}
EDIT_EVENTS = {"c": "<<Copy>>", "v": "<<Paste>>", "x": "<<Cut>>"}


def now_ms():
    return int(time.time() * 1000)


def fmt_size(n):
    if not n:
        return "-"
    for unit in ("B", "KB", "MB", "GB"):
        if n < 1024 or unit == "GB":
            return f"{n:.0f} {unit}" if unit in ("B", "KB") else f"{n:.1f} {unit}"
        n /= 1024


def inline_parts(text):
    """แยก Markdown แบบ inline เป็น (ชนิด, ข้อความที่แสดง, url)"""
    for part in INLINE_RE.split(text):
        if not part:
            continue
        if part.startswith("`") and part.endswith("`") and len(part) > 2:
            yield "inline_code", part[1:-1], None
        elif part.startswith("**") and part.endswith("**") and len(part) > 4:
            yield "bold", part[2:-2], None
        elif part.startswith("~~") and part.endswith("~~") and len(part) > 4:
            yield "strike", part[2:-2], None
        elif part.startswith("*") and part.endswith("*") and len(part) > 2:
            yield "italic", part[1:-1], None
        elif part.startswith("[") and "](" in part and part.endswith(")"):
            label, url = part[1:-1].split("](", 1)
            yield "link", label, url
        else:
            yield None, part, None


def plain_inline(text):
    return "".join(shown for _, shown, _ in inline_parts(text))


def split_row(line):
    s = line.strip()
    if s.startswith("|"):
        s = s[1:]
    if s.endswith("|") and not s.endswith("\\|"):
        s = s[:-1]
    return [c.strip().replace("\\|", "|") for c in re.split(r"(?<!\\)\|", s)]


def table_aligns(sep):
    out = []
    for c in split_row(sep):
        if c.startswith(":") and c.endswith(":"):
            out.append("center")
        elif c.endswith(":"):
            out.append("right")
        else:
            out.append("left")
    return out


def stable_cut(text, start=0):
    """ตำแหน่งท้ายสุดที่ตัดข้อความ Markdown ได้โดยไม่กระทบการแสดงผล
    (หลังบรรทัดว่างนอกโค้ดบล็อก หรือหลังบรรทัดปิดโค้ดบล็อก) — start ต้องเป็นจุดตัดเดิม"""
    cut, pos, in_code = start, start, False
    while True:
        nl = text.find("\n", pos)
        if nl < 0:
            return cut
        line = text[pos:nl]
        if FENCE_RE.match(line):
            in_code = not in_code
            if not in_code:
                cut = nl + 1
        elif not in_code and not line.strip():
            cut = nl + 1
        pos = nl + 1


def read_text_file(path):
    raw = Path(path).read_bytes()
    if b"\x00" in raw[:4096]:
        raise ValueError("ไม่ใช่ไฟล์ข้อความ")
    for enc in ("utf-8-sig", "cp874"):
        try:
            return raw.decode(enc)
        except UnicodeDecodeError:
            pass
    return raw.decode("latin-1")


def api_message(m):
    """แปลงข้อความในประวัติเป็นรูปแบบที่ส่งให้ Ollama (รวมไฟล์แนบและรูป)"""
    content = m.get("content") or ""
    for f in m.get("files") or []:
        note = " (ตัดเหลือบางส่วน)" if f.get("truncated") else ""
        content += (f"\n\n--- ไฟล์แนบ: {f['name']}{note} ---\n{f['text']}\n"
                    f"--- จบไฟล์ {f['name']} ---")
    out = {"role": m["role"], "content": content.strip()}
    images = [b for b in (image_b64(img) for img in m.get("images") or []) if b]
    if images:
        out["images"] = images
    return out


# ---------------------------------------------------------------- documents
W_NS = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"


def read_docx(path):
    """ดึงข้อความจาก .docx (ย่อหน้า + ตารางแบบ Markdown) ด้วย zipfile/xml ล้วน"""
    with zipfile.ZipFile(path) as z:
        root = ET.fromstring(z.read("word/document.xml"))

    def para(p):
        parts = []
        for el in p.iter():
            if el.tag == W_NS + "t":
                parts.append(el.text or "")
            elif el.tag == W_NS + "tab":
                parts.append("\t")
            elif el.tag in (W_NS + "br", W_NS + "cr"):
                parts.append("\n")
        return "".join(parts)

    out = []

    def walk(container):
        for el in container:
            if el.tag == W_NS + "p":
                out.append(para(el))
            elif el.tag == W_NS + "tbl":
                rows = []
                for tr in el.iter(W_NS + "tr"):
                    cells = [" ".join(para(p) for p in tc.iter(W_NS + "p")).strip().replace("|", "\\|")
                             for tc in tr.findall(W_NS + "tc")]
                    rows.append("| " + " | ".join(cells) + " |")
                    if len(rows) == 1:
                        rows.append("|" + "---|" * len(cells))
                out.append("\n".join(rows))
            else:
                walk(el)  # เช่น content control (w:sdt)

    body = root.find(W_NS + "body")
    walk(body if body is not None else root)
    text = "\n".join(out).strip()
    if not text:
        raise ValueError("ไม่พบข้อความในไฟล์")
    return text


def read_pdf(path):
    try:
        from pypdf import PdfReader
    except ImportError:
        try:
            from PyPDF2 import PdfReader
        except ImportError:
            raise ValueError("อ่าน PDF ต้องติดตั้ง pypdf ก่อน: pip install pypdf") from None
    reader = PdfReader(str(path))
    if reader.is_encrypted:
        try:
            reader.decrypt("")
        except Exception:
            raise ValueError("PDF มีรหัสผ่าน") from None
    pages = []
    for i, page in enumerate(reader.pages, 1):
        text = (page.extract_text() or "").strip()
        if text:
            pages.append(f"[หน้า {i}]\n{text}")
    if not pages:
        raise ValueError("PDF นี้ไม่มีข้อความ (อาจเป็นภาพสแกน)")
    return "\n\n".join(pages)


def read_document(path):
    ext = Path(path).suffix.lower()
    if ext == ".docx":
        return read_docx(path)
    if ext == ".pdf":
        return read_pdf(path)
    if ext == ".doc":
        raise ValueError("ไฟล์ .doc แบบเก่ายังไม่รองรับ ให้บันทึกเป็น .docx ก่อน")
    return read_text_file(path)


# ---------------------------------------------------------------- image store
def image_dir():
    return DATA_FILE.with_name(".local_ai_ollama_images")


def image_ext(raw):
    if raw.startswith(b"\xff\xd8"):
        return ".jpg"
    if raw[:4] == b"RIFF" and raw[8:12] == b"WEBP":
        return ".webp"
    return ".png"


def store_image(raw):
    """เก็บรูปเป็นไฟล์ชื่อตาม hash (รูปเดียวกันเก็บครั้งเดียว) คืนชื่อไฟล์"""
    name = hashlib.sha1(raw).hexdigest()[:20] + image_ext(raw)
    folder = image_dir()
    folder.mkdir(parents=True, exist_ok=True)
    path = folder / name
    if not path.exists():
        path.write_bytes(raw)
    return name


def image_b64(img):
    if img.get("data"):  # ข้อมูลรุ่นเก่าที่ฝังรูปไว้ใน JSON
        return img["data"]
    try:
        return base64.b64encode((image_dir() / img["file"]).read_bytes()).decode("ascii")
    except (OSError, KeyError):
        return None


# ---------------------------------------------------------------- clipboard / drag-and-drop
def png_encode(width, height, rgb_rows):
    def chunk(tag, data):
        return (struct.pack(">I", len(data)) + tag + data
                + struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF))
    raw = b"".join(b"\x00" + row for row in rgb_rows)
    return (b"\x89PNG\r\n\x1a\n"
            + chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0))
            + chunk(b"IDAT", zlib.compress(raw, 6)) + chunk(b"IEND", b""))


def dib_to_png(dib):
    """แปลงรูปในคลิปบอร์ด Windows (CF_DIB: BITMAPINFO + พิกเซล 24/32 บิต) เป็น PNG"""
    if len(dib) < 40:
        return None
    size, width, height, _planes, bpp, comp = struct.unpack_from("<IiiHHI", dib, 0)
    colors = struct.unpack_from("<I", dib, 32)[0]
    if bpp not in (24, 32) or comp not in (0, 3) or width <= 0 or height == 0:
        return None
    offset = size + (12 if comp == 3 and size == 40 else 0) + colors * 4
    stride = (width * bpp + 31) // 32 * 4
    bottom_up, height = height > 0, abs(height)
    if len(dib) < offset + stride * height:
        return None
    step, rows = bpp // 8, []
    for y in range(height):
        start = offset + (height - 1 - y if bottom_up else y) * stride
        src = dib[start:start + width * step]
        row = bytearray(width * 3)
        row[0::3], row[1::3], row[2::3] = src[2::step], src[1::step], src[0::step]  # BGR(A) → RGB
        rows.append(bytes(row))
    return png_encode(width, height, rows)


def linux_clipboard_png():
    for cmd in (["wl-paste", "--no-newline", "--type", "image/png"],
                ["xclip", "-selection", "clipboard", "-t", "image/png", "-o"]):
        if shutil.which(cmd[0]):
            try:
                out = subprocess.run(cmd, capture_output=True, timeout=3).stdout
            except (OSError, subprocess.SubprocessError):
                continue
            if out.startswith(b"\x89PNG"):
                return out
    return None


class WinShell:
    """Windows API ผ่าน ctypes: อ่านรูป/ไฟล์จากคลิปบอร์ด และรับไฟล์ที่ลากมาวาง"""
    CF_UNICODETEXT, CF_DIB, CF_HDROP = 13, 8, 15
    WM_DROPFILES, GWLP_WNDPROC = 0x0233, -4

    def __init__(self):
        import ctypes
        from ctypes import wintypes as wt
        self.ct = ctypes
        u, k, s = ctypes.windll.user32, ctypes.windll.kernel32, ctypes.windll.shell32
        u.OpenClipboard.argtypes = [wt.HWND]
        u.OpenClipboard.restype = wt.BOOL
        u.CloseClipboard.argtypes = []
        u.IsClipboardFormatAvailable.argtypes = [wt.UINT]
        u.IsClipboardFormatAvailable.restype = wt.BOOL
        u.GetClipboardData.argtypes = [wt.UINT]
        u.GetClipboardData.restype = wt.HANDLE
        k.GlobalLock.argtypes = [wt.HGLOBAL]
        k.GlobalLock.restype = ctypes.c_void_p
        k.GlobalUnlock.argtypes = [wt.HGLOBAL]
        k.GlobalSize.argtypes = [wt.HGLOBAL]
        k.GlobalSize.restype = ctypes.c_size_t
        s.DragQueryFileW.argtypes = [wt.HANDLE, wt.UINT, wt.LPWSTR, wt.UINT]
        s.DragQueryFileW.restype = wt.UINT
        s.DragFinish.argtypes = [wt.HANDLE]
        s.DragAcceptFiles.argtypes = [wt.HWND, wt.BOOL]
        lresult = ctypes.c_ssize_t
        self.WNDPROC = ctypes.WINFUNCTYPE(lresult, wt.HWND, wt.UINT, wt.WPARAM, wt.LPARAM)
        setter = getattr(u, "SetWindowLongPtrW", None) or u.SetWindowLongW
        setter.argtypes = [wt.HWND, ctypes.c_int, ctypes.c_void_p]
        setter.restype = ctypes.c_void_p
        u.CallWindowProcW.argtypes = [ctypes.c_void_p, wt.HWND, wt.UINT, wt.WPARAM, wt.LPARAM]
        u.CallWindowProcW.restype = lresult
        self.u, self.k, self.s, self.set_wndproc = u, k, s, setter
        self._procs = []  # เก็บ callback ไว้ไม่ให้ถูก garbage collect

    def _drop_files(self, hdrop):
        names = []
        for i in range(self.s.DragQueryFileW(hdrop, 0xFFFFFFFF, None, 0)):
            length = self.s.DragQueryFileW(hdrop, i, None, 0)
            buf = self.ct.create_unicode_buffer(length + 1)
            self.s.DragQueryFileW(hdrop, i, buf, length + 1)
            names.append(buf.value)
        return names

    def clipboard(self):
        """("files", [path, ...]) / ("image", png) / (None, None) ถ้าเป็นข้อความหรือไม่มีอะไร"""
        has = self.u.IsClipboardFormatAvailable
        if not has(self.CF_HDROP) and (has(self.CF_UNICODETEXT) or not has(self.CF_DIB)):
            return None, None  # มีข้อความ (เช่นคัดลอกจาก Excel/Word) → วางเป็นข้อความตามปกติ
        for _ in range(10):
            if self.u.OpenClipboard(None):
                break
            time.sleep(0.02)
        else:
            return None, None
        try:
            if has(self.CF_HDROP):
                handle = self.u.GetClipboardData(self.CF_HDROP)
                return ("files", self._drop_files(handle)) if handle else (None, None)
            handle = self.u.GetClipboardData(self.CF_DIB)
            ptr = self.k.GlobalLock(handle) if handle else None
            if not ptr:
                return None, None
            try:
                dib = self.ct.string_at(ptr, self.k.GlobalSize(handle))
            finally:
                self.k.GlobalUnlock(handle)
            png = dib_to_png(dib)
            return ("image", png) if png else (None, None)
        finally:
            self.u.CloseClipboard()

    def accept_drops(self, hwnd, callback):
        """ให้หน้าต่าง hwnd รับไฟล์ที่ลากมาวาง แล้วเรียก callback(paths) (ห้ามเรียก Tk ใน callback)"""
        old = None

        def proc(h, msg, wparam, lparam):
            if msg == self.WM_DROPFILES:
                files = []
                try:
                    files = self._drop_files(wparam)
                    self.s.DragFinish(wparam)
                except Exception:
                    pass
                callback(files)
                return 0
            return self.u.CallWindowProcW(old, h, msg, wparam, lparam)

        wndproc = self.WNDPROC(proc)
        self._procs.append(wndproc)
        old = self.set_wndproc(hwnd, self.GWLP_WNDPROC, self.ct.cast(wndproc, self.ct.c_void_p))
        self.s.DragAcceptFiles(hwnd, True)


# ---------------------------------------------------------------- syntax highlight
HL_ALIASES = {
    "python": "python py python3 py3",
    "clike": ("js javascript jsx mjs ts typescript tsx java c h cpp c++ cc hpp cs csharp go golang "
              "rust rs php kotlin kt swift dart scala"),
    "sql": "sql mysql postgres postgresql psql sqlite plsql tsql",
    "shell": "sh bash shell zsh console powershell ps1 ps",
    "json": "json jsonc",
}
HL_LANG = {alias: lang for lang, names in HL_ALIASES.items() for alias in names.split()}
HL_KEYWORDS = {
    "python": ("False None True and as assert async await break class continue def del elif else "
               "except finally for from global if import in is lambda nonlocal not or pass raise "
               "return try while with yield match case"),
    "clike": ("abstract async await break case catch class const continue default delete do else "
              "enum export extends false final finally fn for func function go if impl implements "
              "import in instanceof interface let match mod mut new nil null package private "
              "protected pub public return static struct super switch this throw throws trait true "
              "try type typeof undefined use var void while yield"),
    "sql": ("select from where and or not insert into values update set delete create table drop "
            "alter add index view join left right inner outer full on as group by order having "
            "limit offset distinct union all null is in like between case when then else end "
            "primary key foreign references default exists asc desc with"),
    "shell": ("if then else elif fi for while do done case esac in function return local export "
              "echo exit set unset source cd"),
    "json": "true false null",
}
HL_BUILTINS = {
    "python": ("self cls print len range int str float bool list dict set tuple open isinstance "
               "super enumerate zip map filter sorted min max sum abs round"),
    "clike": ("int long short char float double bool boolean string String byte unsigned signed "
              "size_t usize i32 i64 u8 u32 u64 f32 f64 console Math Object Array Promise"),
    "sql": ("count sum avg min max coalesce int integer varchar text date timestamp boolean real "
            "numeric decimal"),
}
HL_COMMENTS = {
    "python": r"#[^\n]*",
    "shell": r"#[^\n]*",
    "clike": r"//[^\n]*|/\*[\s\S]*?(?:\*/|\Z)",
    "sql": r"--[^\n]*|/\*[\s\S]*?(?:\*/|\Z)",
}
HL_STRINGS = {
    "python": (r'(?<!\w)[rRbBuUfF]{0,2}(?:"""[\s\S]*?(?:"""|\Z)|' r"'''[\s\S]*?(?:'''|\Z)|"
               r'"(?:\\.|[^"\\\n])*"|' r"'(?:\\.|[^'\\\n])*')"),
    "clike": r'"(?:\\.|[^"\\\n])*"|' r"'(?:\\.|[^'\\\n])*'|`(?:\\.|[^`\\])*`",
    "sql": r"'(?:''|[^'])*'|" r'"[^"\n]*"',
    "shell": r'"(?:\\.|[^"\\])*"|' r"'[^']*'",
    "json": r'"(?:\\.|[^"\\\n])*"',
}


def _hl_regex(lang):
    words = lambda s: "|".join(map(re.escape, s.split()))
    parts = []
    if lang in HL_COMMENTS:
        parts.append(f"(?P<com>{HL_COMMENTS[lang]})")
    parts.append(f"(?P<str>{HL_STRINGS[lang]})")
    if lang == "python":
        parts.append(r"(?P<deco>^[ \t]*@[\w.]+)")
    parts.append(r"(?P<num>\b(?:0[xX][0-9a-fA-F]+|\d+(?:\.\d+)?(?:[eE][+-]?\d+)?)\b)")
    parts.append(rf"(?P<kw>\b(?:{words(HL_KEYWORDS[lang])})\b)")
    if lang in HL_BUILTINS:
        parts.append(rf"(?P<bi>\b(?:{words(HL_BUILTINS[lang])})\b)")
    if lang != "json":
        parts.append(r"(?P<fn>\b[A-Za-z_]\w*(?=\s*\())")
    return re.compile("|".join(parts), re.M | (re.I if lang == "sql" else 0))


HL_RULES = {lang: _hl_regex(lang) for lang in HL_KEYWORDS}


def highlight(code, lang):
    """แบ่งโค้ดเป็นชิ้น (ข้อความ, tag สี หรือ None) ตามภาษาในโค้ดบล็อก"""
    rx = HL_RULES.get(HL_LANG.get((lang or "").lower()))
    if rx is None:
        yield code, None
        return
    pos = 0
    for m in rx.finditer(code):
        if m.start() > pos:
            yield code[pos:m.start()], None
        yield m.group(), "hl_" + m.lastgroup
        pos = m.end()
    if pos < len(code):
        yield code[pos:], None


def pick_font(candidates, fallback):
    families = set(tkfont.families())
    for name in candidates:
        if name in families:
            return name
    return fallback


class App:
    # ------------------------------------------------------------ setup
    def __init__(self, root):
        self.root = root
        self.data = self.load_data()
        self.active = None          # สถานะการตอบที่กำลัง stream อยู่
        self.gen = 0                # เลขรุ่นของงาน ใช้ทิ้งข้อความค้างจากงานที่ถูกหยุด
        self.q = queue.Queue()
        self.ui_q = queue.Queue()   # งานจาก thread เบื้องหลังที่ต้องทำใน thread หลักของ Tk
        self.open_thoughts = set()
        self.hist_ids = []
        self._dyn_tags, self._stream_tags, self._tail_tags = [], [], []
        self._tag_target = self._dyn_tags
        self._tagn = 0
        self._pad = None
        self._tail = None           # ส่วนของคำตอบที่วาดแล้ว ระหว่าง stream
        self._dirty = False         # มีข้อความใหม่รอวาด
        self._next_render = 0.0
        self._thumbs = {}
        self._content_w = None
        self._resize_job = None
        self.pending = []           # ไฟล์/รูปที่แนบไว้ รอส่งพร้อมข้อความถัดไป
        self.model_sizes = {}
        self.editing = None         # {"chat", "index"} ตอนแก้ไขข้อความที่ส่งไปแล้ว
        self._draft = None
        self.shell = None
        if sys.platform == "win32":
            try:
                self.shell = WinShell()
            except Exception:
                self.shell = None

        root.title(APP_TITLE)
        root.geometry("1180x760")
        root.minsize(760, 480)
        root.configure(bg=C["bg"])

        self.setup_fonts()
        self.setup_style()
        self.build_ui()
        self.bind_keys()
        if self._migrated:
            self.save()
        if self.shell:
            try:  # ลากไฟล์จาก Explorer มาวางที่ไหนก็ได้ในหน้าต่าง
                self.shell.accept_drops(self.root.winfo_id(),
                                        lambda files: self.call_ui(self.add_files, files))
            except Exception:
                pass

        self.ensure_chat()
        self.render_all()
        self.resize_prompt()
        self.refresh_models()
        root.after(40, self.poll)
        root.protocol("WM_DELETE_WINDOW", self.on_close)

    def setup_fonts(self):
        ui = pick_font(["Leelawadee UI", "Noto Sans Thai UI", "Noto Sans Thai", "Sarabun",
                        "Thonburi", "Segoe UI", "Tahoma"], "TkDefaultFont")
        mono = pick_font(["Cascadia Mono", "Consolas", "Menlo", "JetBrains Mono",
                          "DejaVu Sans Mono", "Courier New"], "TkFixedFont")
        F = tkfont.Font
        self.f_base = F(family=ui, size=11)
        self.f_bold = F(family=ui, size=11, weight="bold")
        self.f_italic = F(family=ui, size=11, slant="italic")
        self.f_small = F(family=ui, size=9)
        self.f_label = F(family=ui, size=9)
        self.f_header = F(family=ui, size=10, weight="bold")
        self.f_title = F(family=ui, size=13, weight="bold")
        self.f_brand = F(family=ui, size=12, weight="bold")
        self.f_h2 = F(family=ui, size=16, weight="bold")
        self.f_h3 = F(family=ui, size=13, weight="bold")
        self.f_empty = F(family=ui, size=22, weight="bold")
        self.f_mono = F(family=mono, size=10)
        self.f_gap = F(family=ui, size=6)
        self._font_sizes = [(f, f.cget("size")) for f in (
            self.f_base, self.f_bold, self.f_italic, self.f_small, self.f_label, self.f_header,
            self.f_title, self.f_brand, self.f_h2, self.f_h3, self.f_empty, self.f_mono, self.f_gap)]
        self.apply_font_scale()

    def setup_style(self):
        s = ttk.Style(self.root)
        s.theme_use("clam")
        s.configure(".", background=C["bg"], foreground=C["text"], font=self.f_base,
                    bordercolor=C["line"], darkcolor=C["panel"], lightcolor=C["panel"],
                    troughcolor=C["field"], focuscolor=C["accent"])
        s.configure("TButton", background=C["panel"], foreground=C["text"], padding=(12, 8),
                    borderwidth=1, bordercolor="#424348", relief="flat")
        s.map("TButton", background=[("disabled", C["panel"]), ("active", C["panel_hover"])],
              foreground=[("disabled", C["muted"])])
        s.configure("Accent.TButton", background=C["accent"], foreground=C["accent_text"],
                    bordercolor=C["accent"], font=self.f_bold)
        s.map("Accent.TButton", background=[("disabled", "#1a7a54"), ("active", C["accent_hover"])])
        s.configure("Stop.TButton", background=C["stop_bg"], foreground=C["red"],
                    bordercolor=C["red"], font=self.f_bold)
        s.map("Stop.TButton", background=[("active", "#5c3439")])
        s.configure("Small.TButton", padding=(10, 5), font=self.f_small)
        s.configure("Ghost.TButton", background=C["side"], foreground=C["muted"],
                    bordercolor=C["side"], padding=(6, 4), font=self.f_small)
        s.map("Ghost.TButton", background=[("active", "#2a2b2e")], foreground=[("active", C["text"])])
        s.configure("Attach.TButton", background=C["composer"], foreground=C["muted"],
                    bordercolor=C["composer"], padding=(8, 6), font=self.f_small)
        s.map("Attach.TButton", background=[("active", C["panel_hover"])],
              foreground=[("active", C["text"])])
        s.configure("Top.TButton", background=C["bg"], foreground=C["text"],
                    bordercolor=C["bg"], padding=(8, 5))
        s.map("Top.TButton", background=[("active", C["panel"])])

        for w in ("TEntry", "TSpinbox", "TCombobox"):
            s.configure(w, fieldbackground=C["field"], foreground=C["text"], insertcolor=C["text"],
                        bordercolor=C["border"], lightcolor=C["field"], darkcolor=C["field"],
                        background=C["panel"], arrowcolor=C["text"], padding=6)
            s.map(w, bordercolor=[("focus", C["accent"])], lightcolor=[("focus", C["accent"])])
        s.map("TCombobox", fieldbackground=[("readonly", C["field"])],
              foreground=[("readonly", C["text"])], selectbackground=[("readonly", C["field"])],
              selectforeground=[("readonly", C["text"])], bordercolor=[("focus", C["accent"])])
        self.root.option_add("*TCombobox*Listbox.background", C["field"])
        self.root.option_add("*TCombobox*Listbox.foreground", C["text"])
        self.root.option_add("*TCombobox*Listbox.selectBackground", C["accent"])
        self.root.option_add("*TCombobox*Listbox.selectForeground", C["accent_text"])
        self.root.option_add("*TCombobox*Listbox.font", self.f_base)

        s.configure("Vertical.TScrollbar", background=C["panel"], troughcolor=C["bg"],
                    bordercolor=C["bg"], lightcolor=C["panel"], darkcolor=C["panel"],
                    arrowcolor=C["muted"], gripcount=0, arrowsize=12)
        s.map("Vertical.TScrollbar", background=[("active", C["line"])])
        s.configure("TCheckbutton", background=C["panel"], foreground=C["text"],
                    indicatorbackground=C["field"], indicatorforeground=C["accent_text"])
        s.map("TCheckbutton", indicatorbackground=[("selected", C["accent"])],
              background=[("active", C["panel"])])
        s.configure("Horizontal.TProgressbar", background=C["accent"], troughcolor=C["field"],
                    bordercolor=C["border"], lightcolor=C["accent"], darkcolor=C["accent"])
        s.configure("Horizontal.TScale", background=C["accent"], troughcolor=C["field"],
                    bordercolor=C["border"], lightcolor=C["accent"], darkcolor=C["accent"])

    # ------------------------------------------------------------ UI
    def build_ui(self):
        # ---------- sidebar
        self.sidebar = sb = tk.Frame(self.root, bg=C["side"], width=272)
        sb.pack(side="left", fill="y")
        sb.pack_propagate(False)
        tk.Frame(self.root, bg="#2d2d2d", width=1).pack(side="left", fill="y")
        self.sep = self.root.pack_slaves()[-1]

        inner = tk.Frame(sb, bg=C["side"])
        inner.pack(fill="both", expand=True, padx=12, pady=16)

        brand = tk.Frame(inner, bg=C["side"])
        brand.pack(fill="x", padx=6, pady=(0, 12))
        for txt, col in (("● LOCAL ", C["text"]), ("AI", C["accent"]), (" CHAT", C["text"])):
            tk.Label(brand, text=txt, fg=col, bg=C["side"], font=self.f_brand).pack(side="left")

        ttk.Button(inner, text="＋  แชตใหม่", command=self.new_chat).pack(fill="x")

        self._section(inner, "โมเดลใน Ollama")
        self.model_var = tk.StringVar(value=self.data["settings"].get("model") or "กำลังโหลด...")
        self.model_box = ttk.Combobox(inner, textvariable=self.model_var, state="readonly")
        self.model_box.pack(fill="x")
        self.model_box.bind("<<ComboboxSelected>>", self.on_model_change)
        self.refresh_btn = ttk.Button(inner, text="↻  โหลดรายชื่อโมเดลใหม่", command=self.refresh_models)
        self.refresh_btn.pack(fill="x", pady=(8, 0))
        mrow = tk.Frame(inner, bg=C["side"])
        mrow.pack(fill="x", pady=(4, 0))
        ttk.Button(mrow, text="⬇ ดาวน์โหลดโมเดล", style="Ghost.TButton",
                   command=self.open_pull).grid(row=0, column=0, columnspan=2, sticky="ew")
        for col, (text, cmd) in enumerate((("ℹ ข้อมูลโมเดล", self.show_model_info),
                                           ("× ลบโมเดล", self.delete_model))):
            mrow.columnconfigure(col, weight=1, uniform="model")
            ttk.Button(mrow, text=text, style="Ghost.TButton", command=cmd).grid(
                row=1, column=col, sticky="ew")

        self._section(inner, "ค้นหาประวัติ")
        self.search_var = tk.StringVar()
        self.search_var.trace_add("write", lambda *_: self.render_history())
        ttk.Entry(inner, textvariable=self.search_var).pack(fill="x")

        # footer (pack ก่อน list เพื่อให้อยู่ล่างสุดเสมอ)
        footer = tk.Frame(inner, bg=C["side"])
        footer.pack(side="bottom", fill="x", pady=(10, 0))
        tk.Frame(inner, bg="#303033", height=1).pack(side="bottom", fill="x", pady=(8, 0))
        self.dot = tk.Canvas(footer, width=10, height=10, bg=C["side"], highlightthickness=0)
        self.dot.pack(side="left", padx=(4, 6))
        self.dot_id = self.dot.create_oval(1, 1, 9, 9, fill="#777", outline="")
        self.conn_label = tk.Label(footer, text="กำลังตรวจสอบ...", fg=C["muted"], bg=C["side"],
                                   font=self.f_small, anchor="w")
        self.conn_label.pack(side="left", fill="x", expand=True)
        ttk.Button(footer, text="⚙ ตั้งค่า", style="Ghost.TButton",
                   command=self.open_settings).pack(side="right")

        actions = tk.Frame(inner, bg=C["side"])
        actions.pack(side="bottom", fill="x", pady=(6, 0))
        ttk.Button(actions, text="✎ เปลี่ยนชื่อ", style="Ghost.TButton",
                   command=self.rename_chat).pack(side="left")
        ttk.Button(actions, text="× ลบแชต", style="Ghost.TButton",
                   command=self.delete_chat).pack(side="left", padx=4)

        histf = tk.Frame(inner, bg=C["side"])
        histf.pack(fill="both", expand=True, pady=(12, 0))
        self.hist = tk.Listbox(histf, bg=C["side"], fg=C["text"], font=self.f_base, bd=0,
                               highlightthickness=0, activestyle="none", relief="flat",
                               selectbackground=C["active_row"], selectforeground=C["text"],
                               exportselection=False)
        hs = ttk.Scrollbar(histf, orient="vertical", command=self.hist.yview)
        self.hist.configure(yscrollcommand=hs.set)
        hs.pack(side="right", fill="y")
        self.hist.pack(side="left", fill="both", expand=True)
        self.hist.bind("<<ListboxSelect>>", self.on_hist_select)
        self.hist.bind("<Double-Button-1>", lambda e: self.rename_chat())
        self.hist.bind("<Delete>", lambda e: self.delete_chat())
        self.hist.bind("<Button-3>", self.on_hist_menu)
        self.hist.bind("<Button-2>", self.on_hist_menu)  # macOS
        self.hist_menu = tk.Menu(self.root, tearoff=0, bg=C["panel"], fg=C["text"],
                                 activebackground=C["accent"], activeforeground=C["accent_text"],
                                 bd=0, font=self.f_base)
        self.hist_menu.add_command(label="✎  เปลี่ยนชื่อ", command=self.rename_chat)
        self.hist_menu.add_command(label="↓  ส่งออก .md", command=self.export_md)
        self.hist_menu.add_separator()
        self.hist_menu.add_command(label="×  ลบแชต", command=self.delete_chat)

        # ---------- main
        self.main = main = tk.Frame(self.root, bg=C["bg"])
        main.pack(side="left", fill="both", expand=True)

        top = tk.Frame(main, bg=C["bg"], height=60)
        top.pack(fill="x")
        top.pack_propagate(False)
        ttk.Button(top, text="☰", style="Top.TButton", width=3,
                   command=self.toggle_sidebar).pack(side="left", padx=(12, 6))
        self.title_label = tk.Label(top, text="แชตใหม่", fg=C["text"], bg=C["bg"],
                                    font=self.f_title, anchor="w")
        self.title_label.pack(side="left", fill="x", expand=True)
        ttk.Button(top, text="↓ .md", style="Small.TButton",
                   command=self.export_md).pack(side="right", padx=(6, 20))
        ttk.Button(top, text="↻ ตอบใหม่", style="Small.TButton",
                   command=lambda: self.send_message(True)).pack(side="right")
        self.preset_var = tk.StringVar()
        self.preset_box = ttk.Combobox(top, textvariable=self.preset_var, state="readonly", width=24)
        self.preset_box.pack(side="right", padx=(0, 10))
        self.preset_box.bind("<<ComboboxSelected>>", self.on_preset_change)
        tk.Label(top, text="บทบาท", fg=C["muted"], bg=C["bg"], font=self.f_small).pack(
            side="right", padx=(0, 6))
        tk.Frame(main, bg="#36373b", height=1).pack(fill="x")

        # composer (pack ก่อน เพื่อให้ติดขอบล่าง)
        self.composer_wrap = cw = tk.Frame(main, bg=C["bg"])
        cw.pack(side="bottom", fill="x", padx=18, pady=(10, 12))
        tk.Frame(main, bg="#343538", height=1).pack(side="bottom", fill="x")

        self.edit_bar = tk.Frame(cw, bg=C["thought_bg"])
        tk.Label(self.edit_bar, text="✎ กำลังแก้ไขข้อความ — ส่งแล้วคำตอบเดิมและข้อความถัดจากนี้จะถูกแทนที่",
                 fg=C["accent"], bg=C["thought_bg"], font=self.f_small, anchor="w").pack(
            side="left", padx=(10, 4), pady=5)
        cancel = tk.Label(self.edit_bar, text="ยกเลิก (Esc) ✕", fg=C["muted"], bg=C["thought_bg"],
                          font=self.f_small, cursor="hand2")
        cancel.pack(side="right", padx=10)
        cancel.bind("<Button-1>", lambda e: self.cancel_edit())
        self.attach_bar = tk.Frame(cw, bg=C["bg"])
        comp = tk.Frame(cw, bg=C["composer"], highlightthickness=1,
                        highlightbackground="#505257", highlightcolor=C["accent"])
        comp.pack(fill="x")
        self.comp = comp
        self.prompt = tk.Text(comp, height=2, width=1, wrap="word", bg=C["composer"], fg=C["text"],
                              insertbackground=C["text"], bd=0, highlightthickness=0,
                              font=self.f_base, padx=10, pady=10, undo=True,
                              selectbackground=C["select"])
        self.prompt.pack(side="left", fill="both", expand=True, padx=(4, 0), pady=4)
        self.send_btn = ttk.Button(comp, text="ส่ง ↑", style="Accent.TButton", width=8,
                                   command=self.send_message)
        self.send_btn.pack(side="right", anchor="s", padx=9, pady=9)
        ttk.Button(comp, text="＋ แนบไฟล์", style="Attach.TButton",
                   command=self.attach_files).pack(side="right", anchor="s", pady=9)
        self.placeholder = tk.Label(comp, text="ถามอะไรก็ได้... (Enter เพื่อส่ง)",
                                    fg="#7d7f84", bg=C["composer"], font=self.f_base, cursor="xterm")
        self.placeholder.place(x=19, y=14)
        self.placeholder.bind("<Button-1>", lambda e: self.prompt.focus_set())
        self.prompt.bind("<FocusIn>", lambda e: comp.configure(highlightbackground=C["accent"]))
        self.prompt.bind("<FocusOut>", lambda e: comp.configure(highlightbackground="#505257"))

        self.status = tk.Label(cw, fg=C["muted"], bg=C["bg"], font=self.f_small,
                               text="Enter ส่ง • Shift+Enter ขึ้นบรรทัด • Esc หยุด • "
                                    "ทุกอย่างประมวลผลด้วย Ollama ในเครื่อง")
        self.status.pack(pady=(7, 0))

        # messages
        mf = tk.Frame(main, bg=C["bg"])
        mf.pack(fill="both", expand=True)
        self.msg = tk.Text(mf, bg=C["bg"], fg=C["text"], font=self.f_base, wrap="word", bd=0,
                           highlightthickness=0, padx=24, pady=20, cursor="arrow",
                           insertwidth=0, selectbackground=C["select"],
                           selectforeground=C["text"], spacing1=1, spacing3=1,
                           state="disabled", takefocus=0)
        ms = ttk.Scrollbar(mf, orient="vertical", command=self.msg.yview)
        self.msg.configure(yscrollcommand=ms.set)
        ms.pack(side="right", fill="y")
        self.msg.pack(side="left", fill="both", expand=True)
        self.msg.bind("<Configure>", self.on_msg_resize)
        # ให้คลิกแล้วรับโฟกัส เพื่อให้ Ctrl+C / Ctrl+A ใช้กับข้อความแชตได้
        self.msg.bind("<Button-1>", lambda e: self.msg.focus_set(), add="+")
        self.setup_tags()
        self.build_edit_menu()

    def _section(self, parent, text):
        tk.Label(parent, text=text, fg=C["muted"], bg=C["side"], font=self.f_label,
                 anchor="w").pack(fill="x", padx=4, pady=(14, 4))

    def setup_tags(self):
        t = self.msg
        t.tag_configure("ai_header", font=self.f_header, foreground=C["accent"], spacing1=4, spacing3=6)
        t.tag_configure("user_header", font=self.f_header, foreground=C["user_name"], spacing1=4, spacing3=6)
        t.tag_configure("user", background=C["user_bubble"], lmargin1=0, lmargin2=0,
                        spacing1=3, spacing3=3)
        t.tag_configure("p", spacing3=5)
        t.tag_configure("h2", font=self.f_h2, spacing1=10, spacing3=6)
        t.tag_configure("h3", font=self.f_h3, spacing1=8, spacing3=4)
        t.tag_configure("li", lmargin1=14, lmargin2=34, spacing3=3)
        t.tag_configure("quote", foreground=C["quote"], lmargin1=6, lmargin2=22, spacing3=4)
        t.tag_configure("quote_bar", foreground="#61646a")
        t.tag_configure("hr", foreground=C["line"], spacing1=6, spacing3=6)
        t.tag_configure("code_block", font=self.f_mono, background=C["code_bg"],
                        foreground="#e6e6e6", lmargin1=14, lmargin2=14, rmargin=14)
        t.tag_configure("code_lang", font=self.f_small, foreground=C["muted"], spacing1=6)
        t.tag_configure("code_end", spacing3=4)
        for name, color in (("hl_kw", "#c586c0"), ("hl_str", "#ce9178"), ("hl_com", "#6a9955"),
                            ("hl_num", "#b5cea8"), ("hl_bi", "#4ec9b0"), ("hl_fn", "#dcdcaa"),
                            ("hl_deco", "#dcdcaa")):
            t.tag_configure(name, foreground=color)
        t.tag_configure("inline_code", font=self.f_mono, background=C["inline_code"])
        t.tag_configure("bold", font=self.f_bold)
        t.tag_configure("italic", font=self.f_italic)
        t.tag_configure("strike", overstrike=1)
        t.tag_configure("link", foreground=C["link"], underline=1)
        t.tag_configure("thought_toggle", font=self.f_small, foreground=C["muted"], spacing3=4)
        t.tag_configure("thought", font=self.f_small, foreground=C["thought_fg"],
                        background=C["thought_bg"], lmargin1=12, lmargin2=12, rmargin=12)
        t.tag_configure("meta", font=self.f_small, foreground=C["muted"], spacing1=6)
        t.tag_configure("action", font=self.f_small, foreground=C["muted"], spacing1=4)
        t.tag_configure("gap", font=self.f_gap, spacing3=14)
        t.tag_configure("attach", font=self.f_small, foreground=C["link"], spacing1=2, spacing3=2)
        t.tag_configure("table_head", font=self.f_bold, background=C["table_head"],
                        spacing1=4, spacing3=4)
        t.tag_configure("table_row", background=C["table_row"], spacing1=3, spacing3=3)
        t.tag_configure("table_alt", background=C["table_alt"], spacing1=3, spacing3=3)
        t.tag_configure("table_end", font=self.f_gap, spacing3=4)
        t.tag_configure("center", justify="center")
        t.tag_configure("empty_title", font=self.f_empty, spacing3=6)
        t.tag_configure("empty_sub", foreground=C["muted"], spacing3=4)
        for tag in ("inline_code", "bold", "italic", "strike", "link"):
            t.tag_raise(tag)

    def bind_keys(self):
        self.prompt.bind("<Return>", self.on_enter)
        self.prompt.bind("<KP_Enter>", self.on_enter)
        self.prompt.bind("<KeyRelease>", lambda e: (self.resize_prompt(), self.update_placeholder()))
        self.prompt.bind("<<Paste>>", self.on_prompt_paste)
        self.prompt.bind("<<Cut>>", lambda e: self.root.after(1, self.after_prompt_edit))
        self.root.bind_all("<Control-KeyPress>", self.on_ctrl_key)
        self.root.bind_all("<Escape>", self.on_escape)
        self.root.bind_all("<Control-n>", lambda e: (self.new_chat(), "break")[1])
        self.root.bind_all("<Control-N>", lambda e: (self.new_chat(), "break")[1])
        for seq, step in (("<Control-plus>", 0.1), ("<Control-equal>", 0.1), ("<Control-KP_Add>", 0.1),
                          ("<Control-minus>", -0.1), ("<Control-KP_Subtract>", -0.1),
                          ("<Control-Key-0>", 0), ("<Control-KP_0>", 0)):
            self.root.bind_all(seq, lambda e, s=step: self.zoom(s))
        self.msg.bind("<Control-MouseWheel>", lambda e: self.zoom(0.1 if e.delta > 0 else -0.1))
        self.msg.bind("<Control-Button-4>", lambda e: self.zoom(0.1))
        self.msg.bind("<Control-Button-5>", lambda e: self.zoom(-0.1))

    # ------------------------------------------------------------ data
    def load_data(self):
        st = {"settings": json.loads(json.dumps(DEFAULTS)), "chats": [], "currentId": None}
        try:
            with open(DATA_FILE, encoding="utf-8") as f:
                saved = json.load(f)
            if isinstance(saved, dict):
                st["settings"].update(saved.get("settings") or {})
                if isinstance(saved.get("chats"), list):
                    st["chats"] = saved["chats"]
                st["currentId"] = saved.get("currentId")
        except FileNotFoundError:
            pass
        except Exception as e:
            print("โหลดข้อมูลแชตไม่ได้:", e, file=sys.stderr)
        self._migrated = False
        for c in st["chats"]:
            for m in c.get("messages", []):
                m.pop("streaming", None)
                for img in m.get("images") or []:
                    if img.get("data"):  # ย้ายรูปที่ฝังใน JSON (รุ่นก่อน) ไปเก็บเป็นไฟล์
                        try:
                            img["file"] = store_image(base64.b64decode(img["data"]))
                            del img["data"]
                            self._migrated = True
                        except Exception:
                            pass
        return st

    def gc_images(self):
        """ลบไฟล์รูปที่ไม่มีแชตไหนใช้แล้ว"""
        used = {img.get("file") for c in self.data["chats"] for m in c.get("messages", [])
                for img in m.get("images") or []}
        try:
            for path in image_dir().iterdir():
                if path.is_file() and path.name not in used:
                    path.unlink()
        except OSError:
            pass

    def save(self):
        try:
            tmp = DATA_FILE.with_name(DATA_FILE.name + ".tmp")
            with open(tmp, "w", encoding="utf-8") as f:
                json.dump(self.data, f, ensure_ascii=False, indent=1)
            os.replace(tmp, DATA_FILE)
        except Exception as e:
            self.set_status("บันทึกไม่ได้: " + str(e))

    def current(self):
        cid = self.data.get("currentId")
        return next((c for c in self.data["chats"] if c["id"] == cid), None)

    def ensure_chat(self):
        if not self.current():
            if self.data["chats"]:
                self.data["currentId"] = self.data["chats"][0]["id"]
            else:
                self.new_chat()

    def new_chat(self):
        if self.active:
            return
        self.cancel_edit()
        chat = {"id": str(uuid.uuid4()), "title": "แชตใหม่", "messages": [], "updated": now_ms()}
        preset = (self.current() or {}).get("preset")
        if preset:
            chat["preset"] = preset  # ใช้บทบาทเดียวกับแชตที่เปิดอยู่
        self.data["chats"].insert(0, chat)
        self.data["currentId"] = chat["id"]
        self.save()
        self.render_all()
        self.prompt.focus_set()

    def _target_chat(self):
        sel = self.hist.curselection()
        if sel and sel[0] < len(self.hist_ids):
            cid = self.hist_ids[sel[0]]
            return next((c for c in self.data["chats"] if c["id"] == cid), None)
        return self.current()

    def rename_chat(self):
        if self.active:
            return
        chat = self._target_chat()
        if not chat:
            return
        name = simpledialog.askstring("เปลี่ยนชื่อแชต", "ชื่อใหม่:", initialvalue=chat["title"],
                                      parent=self.root)
        if name and name.strip():
            chat["title"] = name.strip()[:80]
            chat["updated"] = now_ms()
            self.save()
            self.render_all()

    def delete_chat(self):
        if self.active:
            return
        chat = self._target_chat()
        if not chat or not messagebox.askyesno("ลบแชต", f"ลบการสนทนา “{chat['title']}” หรือไม่?",
                                               parent=self.root):
            return
        self.cancel_edit()
        self.data["chats"] = [c for c in self.data["chats"] if c["id"] != chat["id"]]
        if self.data["currentId"] == chat["id"]:
            self.data["currentId"] = self.data["chats"][0]["id"] if self.data["chats"] else None
        self.ensure_chat()
        self.save()
        self.gc_images()
        self.render_all()

    # ------------------------------------------------------------ history
    def render_history(self):
        q = self.search_var.get().strip().lower()
        lb = self.hist
        lb.delete(0, "end")
        self.hist_ids = []
        sel = None
        for chat in sorted(self.data["chats"], key=lambda c: c.get("updated", 0), reverse=True):
            if q:
                blob = " ".join([chat["title"]] + [m.get("content") or "" for m in chat["messages"]])
                if q not in blob.lower():
                    continue
            lb.insert("end", "  ▤  " + chat["title"])
            self.hist_ids.append(chat["id"])
            if chat["id"] == self.data.get("currentId"):
                sel = len(self.hist_ids) - 1
        if sel is not None:
            lb.selection_set(sel)
            lb.see(sel)

    def on_hist_select(self, _e=None):
        sel = self.hist.curselection()
        if not sel or sel[0] >= len(self.hist_ids):
            return
        if self.active:
            self.render_history()
            return
        cid = self.hist_ids[sel[0]]
        if cid != self.data.get("currentId"):
            self.cancel_edit()
            self.data["currentId"] = cid
            self.save()
            self.render_all()

    def on_hist_menu(self, e):
        idx = self.hist.nearest(e.y)
        if idx < 0 or idx >= len(self.hist_ids):
            return
        if not self.active:
            self.hist.selection_clear(0, "end")
            self.hist.selection_set(idx)
            self.on_hist_select()
        self.hist_menu.tk_popup(e.x_root, e.y_root)

    # ------------------------------------------------------------ rendering
    def render_all(self):
        self.update_preset_box()
        self.render_history()
        self.render_messages()

    def _near_bottom(self):
        return self.msg.yview()[1] > 0.985

    def ins(self, text, tags=()):
        self.msg.insert("end", text, tags)

    def new_tag(self, prefix):
        name = f"{prefix}{self._tagn}"
        self._tagn += 1
        self._tag_target.append(name)
        return name

    def dyn_tag(self, prefix, callback):
        name = self.new_tag(prefix)
        t = self.msg
        t.tag_bind(name, "<Button-1>", lambda e: callback())
        t.tag_bind(name, "<Enter>", lambda e: t.configure(cursor="hand2"))
        t.tag_bind(name, "<Leave>", lambda e: t.configure(cursor="arrow"))
        return name

    def _clear_tags(self, lst):
        for name in lst:
            try:
                self.msg.tag_delete(name)
            except tk.TclError:
                pass
        lst.clear()

    def render_messages(self):
        near = self._near_bottom()
        t = self.msg
        t.configure(state="normal", cursor="arrow")
        t.delete("1.0", "end")
        self._clear_tags(self._dyn_tags)
        self._clear_tags(self._stream_tags)
        self._clear_tags(self._tail_tags)
        for mark in ("stream", "tail"):
            if mark in t.mark_names():
                t.mark_unset(mark)
        self._tail = None
        if len(self._thumbs) > 64:
            self._thumbs.clear()
        chat = self.current()
        self.title_label.configure(text=(chat or {}).get("title", "แชตใหม่"))
        msgs = (chat or {}).get("messages", [])
        if not msgs:
            self.ins("\n\n\n\n")
            self.ins("สวัสดีครับ 👋\n", ("center", "empty_title"))
            self.ins("Local AI ของคุณ พร้อมตอบด้วย Ollama บนเครื่องนี้\n", ("center",))
            self.ins("\nเลือกโมเดลด้านซ้าย แล้วเริ่มพิมพ์ได้เลย\n", ("center", "empty_sub"))
        else:
            for i, m in enumerate(msgs):
                if i == len(msgs) - 1 and m.get("streaming"):
                    t.mark_set("stream", "end-1c")
                    t.mark_gravity("stream", "left")
                    self._tag_target = self._stream_tags
                self.render_message(chat, i, m)
            self._tag_target = self._dyn_tags
        t.configure(state="disabled")
        if near or (msgs and msgs[-1].get("streaming")):
            t.see("end")

    def render_stream(self):
        """วาดคำตอบที่กำลัง stream: ย่อหน้าที่จบแล้วไม่ต้องวาดซ้ำ วาดใหม่เฉพาะส่วนท้าย"""
        t = self.msg
        chat = self.current()
        if "stream" not in t.mark_names() or not chat or not chat["messages"]:
            self.render_messages()
            return
        m = chat["messages"][-1]
        content = m.get("content") or ""
        tail = self._tail
        near = self._near_bottom()
        t.configure(state="normal")
        if (tail and "tail" in t.mark_names() and len(content) >= tail["done"]
                and len(m.get("thinking") or "") == tail["think"]):
            t.delete("tail", "end-1c")
            self._clear_tags(self._tail_tags)
            cut = stable_cut(content, tail["done"])
            if cut > tail["done"]:
                self._tag_target = self._stream_tags
                self.render_markdown(content[tail["done"]:cut])
                t.mark_set("tail", "end-1c")
                tail["done"] = cut
            self._tag_target = self._tail_tags
            self.render_reply_rest(m, content[cut:])
            self.ins("\n", ("gap",))
        else:
            t.delete("stream", "end-1c")
            self._clear_tags(self._stream_tags)
            self._clear_tags(self._tail_tags)
            self._tail = None
            self._tag_target = self._stream_tags
            self.render_message(chat, len(chat["messages"]) - 1, m)
        self._tag_target = self._dyn_tags
        t.configure(state="disabled")
        if near:
            t.see("end")

    def render_message(self, chat, i, m):
        is_user = m.get("role") == "user"
        if is_user:
            self.ins("คุณ\n", ("user_header",))
            content = m.get("content") or ""
            if content:
                self.ins(" " + content.replace("\n", " \n ") + " \n", ("user",))
            for f in m.get("files") or []:
                note = "  (ตัดเหลือบางส่วน)" if f.get("truncated") else ""
                self.ins("▤ " + f["name"] + note + "\n", ("attach",))
            for img in m.get("images") or []:
                photo = self.thumbnail(img)
                if photo is not None:
                    self.msg.image_create("end", image=photo, padx=2, pady=4)
                    self.ins("\n")
                self.ins("▣ " + img["name"] + "\n", ("attach",))
            if content:
                tag = self.dyn_tag("ucopy", lambda c=content: self.copy_text(c, "คัดลอกข้อความแล้ว"))
                self.ins("⧉ คัดลอก", ("action", tag))
                self.ins("     ", ("action",))
            tag = self.dyn_tag("uedit", lambda k=i: self.start_edit(k))
            self.ins("✎ แก้ไข", ("action", tag))
            self.ins("\n", ("action",))
        else:
            name = m.get("model") or self.data["settings"].get("model") or "Local AI"
            self.ins("✦ " + name + "\n", ("ai_header",))
            streaming = m.get("streaming")
            if m.get("thinking"):
                key = (chat["id"], i)
                opened = key in self.open_thoughts
                if streaming and not m.get("content"):
                    label = ("▾ " if opened else "▸ ") + "กำลังคิด... (คลิกเพื่อดู)"
                else:
                    label = "▾ ซ่อน Thinking" if opened else "▸ แสดง Thinking"

                def toggle(k=key):
                    self.open_thoughts.symmetric_difference_update({k})
                    self.render_messages()
                self.ins(label + "\n", ("thought_toggle", self.dyn_tag("think", toggle)))
                if opened:
                    self.ins(m["thinking"].strip() + "\n", ("thought",))
                    self.ins("\n", ("gap",))
            content = m.get("content") or ""
            if streaming and content and self._tag_target is self._stream_tags:
                # ส่วนที่จบย่อหน้าแล้วอยู่หน้า mark "tail" — render_stream จะวาดใหม่แค่หลัง mark
                cut = stable_cut(content)
                self.render_markdown(content[:cut])
                self.msg.mark_set("tail", "end-1c")
                self.msg.mark_gravity("tail", "left")
                self._tail = {"done": cut, "think": len(m.get("thinking") or "")}
                self._tag_target = self._tail_tags
                content = content[cut:]
            self.render_reply_rest(m, content)
        self.ins("\n", ("gap",))

    def render_reply_rest(self, m, text):
        """ส่วนท้ายของคำตอบ AI: เนื้อหา text + สถิติ + ปุ่มคัดลอก"""
        streaming = m.get("streaming")
        if text:
            self.render_markdown(text)
        elif streaming and not m.get("content") and not m.get("thinking"):
            self.ins("▍ กำลังสร้างคำตอบ...\n", ("meta",))
        stats = m.get("stats")
        if stats or m.get("interrupted"):
            parts = []
            if stats:
                parts.append(f"{stats.get('tokens', 0)} tokens · {stats.get('tps', 0):.1f} tok/s")
            if m.get("interrupted"):
                parts.append("หยุดกลางคัน")
            self.ins(" · ".join(parts) + "\n", ("meta",))
        if not streaming:
            content = m.get("content") or ""
            tag = self.dyn_tag("copy", lambda c=content: self.copy_text(c, "คัดลอกคำตอบแล้ว"))
            self.ins("⧉ คัดลอก", ("action", tag))
            self.ins("\n", ("action",))

    def thumbnail(self, img):
        """รูปย่อสำหรับแสดงในแชต (Tk แสดงได้เฉพาะ PNG — ไฟล์อื่นคืน None)"""
        data = img.get("data") or ""
        key = img.get("file") or (img.get("name"), len(data), data[-48:])
        if key not in self._thumbs:
            photo = None
            try:
                if img.get("file"):
                    full = tk.PhotoImage(file=str(image_dir() / img["file"]))
                else:
                    full = tk.PhotoImage(data=data)
                factor = -(-max(full.width(), full.height()) // 240)
                photo = full.subsample(factor) if factor > 1 else full
            except tk.TclError:
                pass
            self._thumbs[key] = photo
        return self._thumbs[key]

    def render_inline(self, text, base=()):
        base = tuple(base)
        for kind, shown, url in inline_parts(text):
            tags = base + ((kind,) if kind else ())
            if url:
                tags += (self.dyn_tag("link", lambda u=url: webbrowser.open(u)),)
            self.ins(shown, tags)

    def measure_inline(self, text, bold=False):
        fonts = {"inline_code": self.f_mono, "bold": self.f_bold, "italic": self.f_italic}
        base = self.f_bold if bold else self.f_base
        return sum(fonts.get(kind, base).measure(shown) for kind, shown, _ in inline_parts(text))

    def render_table(self, rows, aligns):
        n = max(len(r) for r in rows)
        rows = [r + [""] * (n - len(r)) for r in rows]
        aligns = (aligns + ["left"] * n)[:n]
        widths = [max(self.measure_inline(r[c], bold=k == 0) for k, r in enumerate(rows))
                  for c in range(n)]
        gap = 24
        avail = self.msg.winfo_width() - 2 * (self._pad or 24) - 16
        tsv = "\n".join("\t".join(plain_inline(c) for c in r) for r in rows)
        if avail > 100 and sum(widths) + gap * n > avail:
            # จอแคบเกินไป: แสดงแต่ละแถวเป็นรายการ "หัวคอลัมน์: ค่า"
            for r in rows[1:]:
                for c in range(n):
                    if not r[c] and not rows[0][c]:
                        continue
                    self.ins("•  ", ("li",))
                    self.render_inline(rows[0][c], ("li", "bold"))
                    self.ins(": ", ("li",))
                    self.render_inline(r[c], ("li",))
                    self.ins("\n", ("li",))
                self.ins("\n", ("table_end",))
        else:
            stops, x = [], 10
            for c in range(n):
                pos = {"left": x, "center": x + widths[c] // 2, "right": x + widths[c]}[aligns[c]]
                stops += [str(pos), aligns[c]]
                x += widths[c] + gap
            stops += [str(x - gap // 2), "left"]
            tabs = self.new_tag("tbl")
            self.msg.tag_configure(tabs, tabs=stops, tabstyle="tabular")
            for k, r in enumerate(rows):
                style = "table_head" if k == 0 else ("table_alt" if k % 2 == 0 else "table_row")
                base = (style, tabs)
                for c in range(n):
                    self.ins("\t", base)
                    self.render_inline(r[c], base)
                self.ins("\t", base)
                self.ins("\n", (tabs,))
        tag = self.dyn_tag("tcopy", lambda s=tsv: self.copy_text(s, "คัดลอกตารางแล้ว (วางใน Excel ได้)"))
        self.ins("⧉ คัดลอกตาราง", ("action", tag))
        self.ins("\n", ("code_end",))

    def render_markdown(self, text):
        in_code, code, lang = False, [], ""

        def flush_code():
            if lang:
                self.ins(lang + "\n", ("code_block", "code_lang"))
            src = "\n".join(code)
            for chunk, kind in highlight(src, lang):
                self.ins(chunk, ("code_block", kind) if kind else ("code_block",))
            self.ins("\n", ("code_block",))
            tag = self.dyn_tag("ccopy", lambda s=src: self.copy_text(s, "คัดลอกโค้ดแล้ว"))
            self.ins("⧉ คัดลอกโค้ด", ("action", tag))
            self.ins("\n", ("code_end",))

        lines = text.split("\n")
        i = 0
        while i < len(lines):
            line = lines[i]
            i += 1
            fence = FENCE_RE.match(line)
            if fence:
                if in_code:
                    flush_code()
                    code, in_code = [], False
                else:
                    in_code, lang = True, fence.group(1)
                continue
            if in_code:
                code.append(line)
                continue
            trim = line.strip()
            if not trim:
                continue
            if "|" in trim and i < len(lines) and "|" in lines[i] and TABLE_SEP_RE.match(lines[i]):
                rows, aligns = [split_row(trim)], table_aligns(lines[i])
                i += 1
                while i < len(lines) and "|" in lines[i] and lines[i].strip():
                    rows.append(split_row(lines[i]))
                    i += 1
                self.render_table(rows, aligns)
                continue
            h = re.match(r"^(#{1,6})\s+(.*)", trim)
            if h:
                self.render_inline(h.group(2), ("h2" if len(h.group(1)) == 1 else "h3",))
                self.ins("\n", ("h2" if len(h.group(1)) == 1 else "h3",))
                continue
            if trim.startswith("> ") or trim == ">":
                self.ins("▎ ", ("quote", "quote_bar"))
                self.render_inline(trim[2:], ("quote",))
                self.ins("\n", ("quote",))
                continue
            item = LIST_RE.match(trim)
            if item:
                marker = "•  " if item.group(1) in "-*" else item.group(1).rstrip(")").rstrip(".") + ".  "
                indent = len(line) - len(line.lstrip())
                if indent >= 2:
                    marker = "    " + ("◦  " if marker == "•  " else marker)
                self.ins(marker, ("li",))
                self.render_inline(item.group(2), ("li",))
                self.ins("\n", ("li",))
                continue
            if re.fullmatch(r"[-*_]{3,}", trim):
                self.ins("─" * 48 + "\n", ("hr",))
                continue
            self.render_inline(line, ("p",))
            self.ins("\n", ("p",))
        if in_code:
            flush_code()

    def on_msg_resize(self, e):
        pad = max(20, (e.width - 880) // 2)
        if pad != self._pad:
            self._pad = pad
            self.msg.configure(padx=pad)
            self.composer_wrap.pack_configure(padx=max(18, pad - 4))
        # ความกว้างเนื้อหาเปลี่ยน → วาดตารางใหม่ให้พอดีจอ (หน่วงไว้ไม่ให้วาดถี่ตอนลากขยาย)
        width = e.width - 2 * pad
        if self._content_w is None or abs(width - self._content_w) > 30:
            self._content_w = width
            chat = self.current() or {}
            if any("|" in (m.get("content") or "") for m in chat.get("messages", [])):
                if self._resize_job:
                    self.root.after_cancel(self._resize_job)
                self._resize_job = self.root.after(200, self._rerender_after_resize)

    def _rerender_after_resize(self):
        self._resize_job = None
        if not self.active:
            self.render_messages()

    # ------------------------------------------------------------ misc UI
    def set_status(self, text):
        self.status.configure(text=text)

    def set_connection(self, ok, text):
        self.dot.itemconfigure(self.dot_id, fill=C["accent"] if ok else C["red"])
        self.conn_label.configure(text=text)

    def copy_text(self, text, msg):
        self.root.clipboard_clear()
        self.root.clipboard_append(text)
        self.set_status("✓ " + msg)

    # ------------------------------------------------------------ copy / paste
    def build_edit_menu(self):
        self.edit_menu = tk.Menu(self.root, tearoff=0, bg=C["panel"], fg=C["text"],
                                 activebackground=C["accent"], activeforeground=C["accent_text"],
                                 disabledforeground="#6c6e73", bd=0, font=self.f_base)
        self.edit_menu.add_command(label="✂  ตัด", accelerator="Ctrl+X",
                                   command=lambda: self.edit_action(self._menu_widget, "x"))
        self.edit_menu.add_command(label="⧉  คัดลอก", accelerator="Ctrl+C",
                                   command=lambda: self.edit_action(self._menu_widget, "c"))
        self.edit_menu.add_command(label="⎘  วาง", accelerator="Ctrl+V",
                                   command=lambda: self.edit_action(self._menu_widget, "v"))
        self.edit_menu.add_separator()
        self.edit_menu.add_command(label="▣  เลือกทั้งหมด", accelerator="Ctrl+A",
                                   command=lambda: self.edit_action(self._menu_widget, "a"))
        self._menu_widget = None
        # ผูกกับทุกช่องข้อความ (ช่องพิมพ์, ข้อความแชต, ช่องค้นหา, หน้าตั้งค่า)
        buttons = ("<Button-3>", "<Button-2>") if sys.platform == "darwin" else ("<Button-3>",)
        for cls in ("Text", "Entry", "TEntry", "TSpinbox"):
            for b in buttons:
                self.root.bind_class(cls, b, self.show_edit_menu, add="+")

    @staticmethod
    def _is_editable(w):
        return isinstance(w, (tk.Text, tk.Entry, ttk.Entry))

    @staticmethod
    def _readonly(w):
        if isinstance(w, ttk.Entry):
            return w.instate(["readonly"]) or w.instate(["disabled"])
        return str(w.cget("state")) == "disabled"

    @staticmethod
    def _has_selection(w):
        if isinstance(w, tk.Text):
            return bool(w.tag_ranges("sel"))
        return bool(w.selection_present())

    def _clipboard_text(self):
        try:
            return self.root.clipboard_get()
        except tk.TclError:
            return ""

    def show_edit_menu(self, e):
        w = e.widget
        if not self._is_editable(w):
            return
        w.focus_set()
        self._menu_widget = w
        ro, sel = self._readonly(w), self._has_selection(w)
        st = lambda ok: "normal" if ok else "disabled"
        self.edit_menu.entryconfigure(0, state=st(sel and not ro))
        self.edit_menu.entryconfigure(1, state=st(sel))
        self.edit_menu.entryconfigure(2, state=st(not ro and bool(self._clipboard_text())))
        self.edit_menu.tk_popup(e.x_root, e.y_root)
        return "break"

    def edit_action(self, w, key):
        """ตัด/คัดลอก/วาง/เลือกทั้งหมด ในช่องข้อความ w"""
        if w is None or not self._is_editable(w):
            return
        w.focus_set()
        if key == "a":
            if isinstance(w, tk.Text):
                w.tag_remove("sel", "1.0", "end")
                w.tag_add("sel", "1.0", "end-1c")
                w.mark_set("insert", "end-1c")
            else:
                w.selection_range(0, "end")
                w.icursor("end")
            return
        if key in ("x", "v") and self._readonly(w):
            return
        if key == "c" and not self._has_selection(w):
            return
        if key == "v" and isinstance(w, tk.Text) and self._has_selection(w):
            w.delete("sel.first", "sel.last")  # วางทับข้อความที่เลือกไว้ (Linux ไม่ทำให้เอง)
        w.event_generate(EDIT_EVENTS[key])
        if key == "c":
            self.set_status("✓ คัดลอกแล้ว")

    def on_ctrl_key(self, e):
        """รองรับ Ctrl+A ทุกช่อง และ Ctrl+C/V/X/N/+/−/0 เมื่อแป้นพิมพ์ไม่ใช่ภาษาอังกฤษ"""
        ks = (e.keysym or "").lower()
        if ks in EDIT_EVENTS or ks == "n":
            return None  # แป้นภาษาอังกฤษ: tkinter จัดการเองอยู่แล้ว
        key = "a" if ks == "a" else CTRL_KEYCODES.get(e.keycode)
        if not key:
            return None
        if key == "n":
            self.new_chat()
            return "break"
        if key in ZOOM_STEPS:
            return self.zoom(ZOOM_STEPS[key])
        if not self._is_editable(e.widget):
            return None
        self.edit_action(e.widget, key)
        return "break"

    def after_prompt_edit(self):
        self.resize_prompt()
        self.update_placeholder()

    def toggle_sidebar(self):
        if self.sidebar.winfo_ismapped():
            self.sidebar.pack_forget()
            self.sep.pack_forget()
        else:
            self.sidebar.pack(side="left", fill="y", before=self.main)
            self.sep.pack(side="left", fill="y", before=self.main)

    def resize_prompt(self):
        try:
            r = self.prompt.count("1.0", "end", "displaylines")
            n = r[0] if isinstance(r, tuple) else int(r or 1)
        except Exception:
            n = int(self.prompt.index("end-1c").split(".")[0])
        self.prompt.configure(height=min(max(n, 2), 8))

    def update_placeholder(self):
        if self.prompt.get("1.0", "end-1c"):
            self.placeholder.place_forget()
        else:
            self.placeholder.place(x=19, y=14)

    def on_enter(self, e):
        if e.state & 0x0001:  # Shift → ขึ้นบรรทัดใหม่ตามปกติ
            self.root.after(1, self.resize_prompt)
            return None
        self.send_message()
        return "break"

    def on_escape(self, _e=None):
        if self.active:
            self.stop()
        elif self.editing is not None:
            self.cancel_edit()

    def on_model_change(self, _e=None):
        self.data["settings"]["model"] = self.model_var.get()
        self.save()

    def on_close(self):
        if self.active:
            self.stop()
        self.save()
        self.root.destroy()

    def export_md(self):
        c = self._target_chat() if self.hist.focus_get() == self.hist else self.current()
        if not c or not c["messages"]:
            return
        path = filedialog.asksaveasfilename(
            parent=self.root, defaultextension=".md", filetypes=[("Markdown", "*.md")],
            initialfile="ollama-chat-" + datetime.date.today().isoformat() + ".md")
        if not path:
            return
        txt = "# " + c["title"] + "\n\n"
        for m in c["messages"]:
            who = "คุณ" if m["role"] == "user" else (m.get("model") or "AI")
            txt += "## " + who + "\n\n" + (m.get("content") or "") + "\n\n"
            names = [a["name"] for a in (m.get("files") or []) + (m.get("images") or [])]
            if names:
                txt += "> แนบ: " + ", ".join(names) + "\n\n"
        with open(path, "w", encoding="utf-8") as f:
            f.write(txt)
        self.set_status("ส่งออกแล้ว: " + path)

    # ------------------------------------------------------------ models
    def host(self):
        return self.data["settings"]["host"].rstrip("/")

    def refresh_models(self):
        self.refresh_btn.state(["disabled"])
        host = self.host()

        def work():
            try:
                with urllib.request.urlopen(host + "/api/tags", timeout=8) as r:
                    data = json.loads(r.read().decode("utf-8"))
                models = [x.get("name") for x in data.get("models", []) if x.get("name")]
                self.model_sizes = {x.get("name"): x.get("size") for x in data.get("models", [])}
                self.call_ui(self._apply_models, models, None)
            except Exception as e:
                self.call_ui(self._apply_models, None, e)
        threading.Thread(target=work, daemon=True).start()

    def _apply_models(self, models, err):
        self.refresh_btn.state(["!disabled"])
        s = self.data["settings"]
        if err is not None:
            self.set_connection(False, "เชื่อมต่อไม่ได้")
            self.model_box.configure(values=[s["model"]] if s.get("model") else [])
            self.model_var.set(s.get("model") or "ไม่พบ Ollama")
            self.set_status("เชื่อมต่อ Ollama ไม่ได้ ตรวจว่า Ollama เปิดอยู่: " + str(err))
            return
        if not models:
            self.model_box.configure(values=[])
            self.model_var.set("ยังไม่มีโมเดล")
            self.set_connection(False, "ยังไม่มีโมเดล")
            return
        self.model_box.configure(values=models)
        if s.get("model") not in models:
            s["model"] = models[0]
        self.model_var.set(s["model"])
        self.set_connection(True, f"เชื่อมต่อแล้ว · {len(models)} โมเดล")
        self.save()

    # ------------------------------------------------------------ model management
    def api(self, path, body=None, method=None, timeout=30):
        data = json.dumps(body).encode("utf-8") if body is not None else None
        req = urllib.request.Request(self.host() + path, data=data, method=method,
                                     headers={"Content-Type": "application/json"})
        return urllib.request.urlopen(req, timeout=timeout)

    @staticmethod
    def http_error_text(e):
        try:
            return json.loads(e.read().decode("utf-8")).get("error") or f"HTTP {e.code}"
        except Exception:
            return f"HTTP {e.code}"

    def _place_dialog(self, win):
        win.update_idletasks()
        x = self.root.winfo_rootx() + (self.root.winfo_width() - win.winfo_width()) // 2
        y = self.root.winfo_rooty() + (self.root.winfo_height() - win.winfo_height()) // 3
        win.geometry(f"+{max(x, 0)}+{max(y, 0)}")
        win.grab_set()
        win.focus_set()

    def _dialog(self, title, heading):
        win = tk.Toplevel(self.root, bg=C["panel"])
        win.title(title)
        win.transient(self.root)
        win.resizable(False, False)
        body = tk.Frame(win, bg=C["panel"])
        body.pack(fill="both", expand=True, padx=22, pady=18)
        tk.Label(body, text=heading, fg=C["text"], bg=C["panel"], font=self.f_title,
                 anchor="w").pack(fill="x")
        return win, body

    def _dlg_label(self, parent, text):
        tk.Label(parent, text=text, fg="#d0d0d2", bg=C["panel"], font=self.f_small,
                 anchor="w", justify="left").pack(fill="x", pady=(12, 4))

    def show_model_info(self):
        name = self.data["settings"].get("model")
        if not name:
            self.set_status("ยังไม่ได้เลือกโมเดล")
            return

        def work():
            try:
                with self.api("/api/show", {"model": name}) as r:
                    info = json.loads(r.read().decode("utf-8"))
                self.call_ui(self._model_info_window, name, info, None)
            except urllib.error.HTTPError as e:
                self.call_ui(self._model_info_window, name, None, self.http_error_text(e))
            except Exception as e:
                self.call_ui(self._model_info_window, name, None, str(e))
        threading.Thread(target=work, daemon=True).start()

    def _model_info_window(self, name, info, err):
        if err:
            messagebox.showerror("ข้อมูลโมเดล", f"ดูข้อมูล {name} ไม่ได้: {err}", parent=self.root)
            return
        d = info.get("details") or {}
        mi = info.get("model_info") or {}
        ctx = next((v for k, v in mi.items() if k.endswith(".context_length")), None)
        caps = {"completion": "แชต", "vision": "ดูรูปได้", "tools": "เรียกใช้เครื่องมือ",
                "thinking": "โหมด Thinking", "embedding": "Embedding", "insert": "เติมโค้ด"}
        rows = [
            ("ชื่อ", name),
            ("ขนาดไฟล์", fmt_size(self.model_sizes.get(name))),
            ("ตระกูล", d.get("family") or "-"),
            ("จำนวนพารามิเตอร์", d.get("parameter_size") or "-"),
            ("Quantization", d.get("quantization_level") or "-"),
            ("Context สูงสุด", f"{ctx:,} tokens" if isinstance(ctx, int) else "-"),
            ("num_ctx ที่ตั้งไว้", f"{int(self.data['settings']['numCtx']):,} tokens"),
            ("ความสามารถ", ", ".join(caps.get(c, c) for c in info.get("capabilities") or []) or "-"),
            ("แก้ไขล่าสุด", (info.get("modified_at") or "-")[:10]),
        ]
        win, body = self._dialog("ข้อมูลโมเดล", "ℹ  ข้อมูลโมเดล")
        grid = tk.Frame(body, bg=C["panel"])
        grid.pack(fill="x", pady=(12, 0))
        for r, (k, v) in enumerate(rows):
            tk.Label(grid, text=k, fg=C["muted"], bg=C["panel"], font=self.f_small,
                     anchor="w").grid(row=r, column=0, sticky="w", padx=(0, 18), pady=3)
            tk.Label(grid, text=v, fg=C["text"], bg=C["panel"], font=self.f_base, anchor="w",
                     wraplength=380, justify="left").grid(row=r, column=1, sticky="w", pady=3)
        ttk.Button(body, text="ปิด", command=win.destroy).pack(side="right", pady=(18, 0))
        win.bind("<Escape>", lambda e: (win.destroy(), "break")[1])
        self._place_dialog(win)

    def delete_model(self):
        name = self.data["settings"].get("model")
        if not name or self.active:
            return
        if not messagebox.askyesno("ลบโมเดล", f"ลบโมเดล “{name}” ออกจากเครื่องหรือไม่?\n"
                                   "ถ้าจะใช้อีกต้องดาวน์โหลดใหม่", parent=self.root):
            return

        def work():
            try:
                with self.api("/api/delete", {"model": name}, method="DELETE"):
                    pass
                self.call_ui(self._after_delete, name, None)
            except urllib.error.HTTPError as e:
                self.call_ui(self._after_delete, name, self.http_error_text(e))
            except Exception as e:
                self.call_ui(self._after_delete, name, str(e))
        threading.Thread(target=work, daemon=True).start()

    def _after_delete(self, name, err):
        if err:
            self.set_status(f"ลบ {name} ไม่ได้: {err}")
            return
        if self.data["settings"].get("model") == name:
            self.data["settings"]["model"] = ""
        self.set_status(f"ลบโมเดล {name} แล้ว")
        self.refresh_models()

    def open_pull(self):
        win, body = self._dialog("ดาวน์โหลดโมเดล", "⬇  ดาวน์โหลดโมเดล")
        self._dlg_label(body, "ชื่อโมเดล (เลือกหรือพิมพ์เอง • ดูทั้งหมดที่ ollama.com/library)")
        name_var = tk.StringVar()
        combo = ttk.Combobox(body, textvariable=name_var, values=SUGGESTED_MODELS, width=44)
        combo.pack(fill="x")
        bar = ttk.Progressbar(body, mode="determinate", maximum=100)
        bar.pack(fill="x", pady=(16, 4))
        status = tk.Label(body, text="ดาวน์โหลดค้างไว้แล้วกดใหม่ จะดาวน์โหลดต่อจากเดิม",
                          fg=C["muted"], bg=C["panel"], font=self.f_small, anchor="w")
        status.pack(fill="x")
        foot = tk.Frame(body, bg=C["panel"])
        foot.pack(fill="x", pady=(18, 0))
        st = {"stop": None, "resp": None, "q": queue.Queue(), "speed": None}

        def start(_e=None):
            name = name_var.get().strip()
            if not name or st["stop"] is not None:
                return
            st["stop"] = threading.Event()
            st["speed"] = None
            go.state(["disabled"])
            combo.state(["disabled"])
            bar.configure(value=0)
            status.configure(text="กำลังเริ่ม...")
            threading.Thread(target=self._pull_worker, args=(name, st), daemon=True).start()
            poll()

        def finish_run():
            st["stop"] = None
            go.state(["!disabled"])
            combo.state(["!disabled"])

        def poll():
            if not win.winfo_exists():
                return
            try:
                while True:
                    kind, data = st["q"].get_nowait()
                    if kind == "progress":
                        status.configure(text=self._pull_text(data, st))
                        if data.get("total"):
                            bar.configure(value=100 * (data.get("completed") or 0) / data["total"])
                    elif kind == "done":
                        finish_run()
                        bar.configure(value=100)
                        status.configure(text=f"✓ ดาวน์โหลด {data} เสร็จแล้ว และเลือกใช้โมเดลนี้")
                        self.data["settings"]["model"] = data if ":" in data else data + ":latest"
                        self.refresh_models()
                    elif kind == "error":
                        finish_run()
                        status.configure(text="⚠ " + data)
            except queue.Empty:
                pass
            if st["stop"] is not None:
                win.after(100, poll)

        def close(_e=None):
            if st["stop"] is not None:
                if not messagebox.askyesno("ยกเลิกการดาวน์โหลด",
                                           "หยุดดาวน์โหลดหรือไม่? (ครั้งหน้าจะดาวน์โหลดต่อจากเดิม)",
                                           parent=win):
                    return "break"
                st["stop"].set()
                try:
                    st["resp"] and st["resp"].close()
                except Exception:
                    pass
            win.destroy()
            return "break"

        go = ttk.Button(foot, text="ดาวน์โหลด", style="Accent.TButton", command=start)
        go.pack(side="right")
        ttk.Button(foot, text="ปิด", command=close).pack(side="right", padx=8)
        combo.bind("<Return>", start)
        win.bind("<Escape>", close)
        win.protocol("WM_DELETE_WINDOW", close)
        self._place_dialog(win)
        combo.focus_set()

    def _pull_worker(self, name, st):
        q, stop = st["q"], st["stop"]
        try:
            with self.api("/api/pull", {"model": name, "stream": True}, timeout=3600) as resp:
                st["resp"] = resp
                for raw in resp:
                    if stop.is_set():
                        return
                    line = raw.decode("utf-8", "replace").strip()
                    if not line:
                        continue
                    obj = json.loads(line)
                    if obj.get("error"):
                        raise RuntimeError(obj["error"])
                    if obj.get("status") == "success":
                        q.put(("done", name))
                        return
                    q.put(("progress", obj))
            q.put(("error", "การเชื่อมต่อสิ้นสุดก่อนดาวน์โหลดเสร็จ"))
        except urllib.error.HTTPError as e:
            q.put(("error", self.http_error_text(e)))
        except Exception as e:
            if not stop.is_set():
                q.put(("error", str(e)))

    @staticmethod
    def _pull_text(obj, st):
        s = obj.get("status") or ""
        names = {"pulling manifest": "กำลังดึงข้อมูลโมเดล", "verifying sha256 digest": "กำลังตรวจสอบไฟล์",
                 "writing manifest": "กำลังบันทึก", "removing any unused layers": "กำลังเก็บกวาด"}
        if s in names:
            return names[s] + "..."
        total, done = obj.get("total"), obj.get("completed") or 0
        if not total:
            return s
        now, speed = time.monotonic(), ""
        prev = st.get("speed")
        if prev and prev[2] == obj.get("digest") and now - prev[0] >= 0.5:
            rate = (done - prev[1]) / (now - prev[0])
            st["speed"] = (now, done, obj.get("digest"), rate)
        elif not prev or prev[2] != obj.get("digest"):
            st["speed"] = (now, done, obj.get("digest"), None)
        rate = st["speed"][3]
        if rate and rate > 0:
            speed = f" · {fmt_size(rate)}/s"
        return f"กำลังดาวน์โหลด {100 * done / total:.0f}%  ({fmt_size(done)} / {fmt_size(total)}){speed}"

    # ------------------------------------------------------------ presets
    def preset_names(self):
        return [p["name"] for p in self.data["settings"].get("presets") or []]

    def chat_system_prompt(self, chat):
        name = (chat or {}).get("preset")
        for p in self.data["settings"].get("presets") or []:
            if p["name"] == name:
                return p.get("prompt") or ""
        return self.data["settings"].get("systemPrompt") or ""

    def update_preset_box(self):
        names = self.preset_names()
        self.preset_box.configure(values=[PRESET_DEFAULT] + names + [PRESET_MANAGE])
        name = (self.current() or {}).get("preset")
        self.preset_var.set(name if name in names else PRESET_DEFAULT)

    def on_preset_change(self, _e=None):
        value, chat = self.preset_var.get(), self.current()
        if value == PRESET_MANAGE:
            self.update_preset_box()
            self.open_presets()
            return
        if chat:
            if value == PRESET_DEFAULT:
                chat.pop("preset", None)
            else:
                chat["preset"] = value
            self.save()
            self.set_status(f"แชตนี้ใช้บทบาท: {value}")
        self.prompt.focus_set()

    def open_presets(self):
        work = [dict(p, _orig=p["name"]) for p in self.data["settings"].get("presets") or []]
        win, body = self._dialog("จัดการบทบาท", "✎  จัดการบทบาท (System Prompt)")
        tk.Label(body, text="แต่ละแชตเลือกบทบาทได้จากช่อง “บทบาท” ด้านบน", fg=C["muted"],
                 bg=C["panel"], font=self.f_small, anchor="w").pack(fill="x", pady=(4, 0))
        main = tk.Frame(body, bg=C["panel"])
        main.pack(fill="both", expand=True, pady=(12, 0))
        left = tk.Frame(main, bg=C["panel"])
        left.pack(side="left", fill="y")
        lb = tk.Listbox(left, bg=C["field"], fg=C["text"], font=self.f_base, width=22, height=12,
                        bd=0, highlightthickness=1, highlightbackground=C["border"],
                        selectbackground=C["accent"], selectforeground=C["accent_text"],
                        activestyle="none", exportselection=False)
        lb.pack(fill="y", expand=True)
        btns = tk.Frame(left, bg=C["panel"])
        btns.pack(fill="x", pady=(8, 0))
        right = tk.Frame(main, bg=C["panel"])
        right.pack(side="left", fill="both", expand=True, padx=(16, 0))
        self._dlg_label(right, "ชื่อบทบาท")
        name_var = tk.StringVar()
        name_entry = ttk.Entry(right, textvariable=name_var, width=50)
        name_entry.pack(fill="x")
        self._dlg_label(right, "System Prompt")
        sp = tk.Text(right, height=10, width=56, wrap="word", bg=C["field"], fg=C["text"],
                     insertbackground=C["text"], bd=0, highlightthickness=1,
                     highlightbackground=C["border"], highlightcolor=C["accent"],
                     font=self.f_base, padx=8, pady=6, undo=True)
        sp.pack(fill="both", expand=True)
        cur = {"i": None}

        def store():
            i = cur["i"]
            if i is None or i >= len(work):
                return
            work[i]["name"] = name_var.get().strip()
            work[i]["prompt"] = sp.get("1.0", "end-1c").strip()
            lb.delete(i)
            lb.insert(i, work[i]["name"] or "(ไม่มีชื่อ)")

        def load(i):
            cur["i"] = i
            state = "normal" if i is not None else "disabled"
            name_var.set(work[i]["name"] if i is not None else "")
            sp.configure(state="normal")
            sp.delete("1.0", "end")
            if i is not None:
                sp.insert("1.0", work[i].get("prompt") or "")
                lb.selection_clear(0, "end")
                lb.selection_set(i)
                lb.see(i)
            sp.configure(state=state)
            name_entry.state(["!disabled"] if i is not None else ["disabled"])

        def on_select(_e=None):
            sel = lb.curselection()
            if sel and sel[0] != cur["i"]:
                store()
                load(sel[0])

        def add():
            store()
            n, base = 1, "บทบาทใหม่"
            names = {p["name"] for p in work}
            while f"{base} {n}" in names:
                n += 1
            work.append({"name": f"{base} {n}", "prompt": "", "_orig": None})
            lb.insert("end", work[-1]["name"])
            load(len(work) - 1)
            name_entry.focus_set()
            name_entry.select_range(0, "end")

        def remove():
            i = cur["i"]
            if i is None:
                return
            work.pop(i)
            lb.delete(i)
            cur["i"] = None
            load(min(i, len(work) - 1) if work else None)

        def do_save():
            store()
            names = [p["name"] for p in work]
            if any(not n for n in names) or len(set(names)) != len(names):
                messagebox.showwarning("ชื่อบทบาท", "ชื่อบทบาทต้องไม่ว่างและไม่ซ้ำกัน", parent=win)
                return
            if PRESET_DEFAULT in names or PRESET_MANAGE in names:
                messagebox.showwarning("ชื่อบทบาท", "ใช้ชื่อนี้ไม่ได้", parent=win)
                return
            renamed = {p["_orig"]: p["name"] for p in work if p["_orig"]}
            for chat in self.data["chats"]:
                old = chat.get("preset")
                if old is None:
                    continue
                if old in renamed:
                    chat["preset"] = renamed[old]
                else:
                    chat.pop("preset", None)
            self.data["settings"]["presets"] = [{"name": p["name"], "prompt": p["prompt"]}
                                                for p in work]
            self.save()
            self.update_preset_box()
            win.destroy()

        ttk.Button(btns, text="＋ เพิ่ม", style="Small.TButton", command=add).pack(side="left")
        ttk.Button(btns, text="× ลบ", style="Small.TButton", command=remove).pack(side="left", padx=6)
        for p in work:
            lb.insert("end", p["name"])
        lb.bind("<<ListboxSelect>>", on_select)
        foot = tk.Frame(body, bg=C["panel"])
        foot.pack(fill="x", pady=(18, 0))
        ttk.Button(foot, text="บันทึก", style="Accent.TButton", command=do_save).pack(side="right")
        ttk.Button(foot, text="ยกเลิก", command=win.destroy).pack(side="right", padx=8)
        win.bind("<Escape>", lambda e: (win.destroy(), "break")[1])
        load(0 if work else None)
        self._place_dialog(win)

    # ------------------------------------------------------------ font size
    def zoom(self, step):
        s = self.data["settings"]
        scale = 1.0 if step == 0 else min(2.0, max(0.7, (s.get("fontScale") or 1.0) + step))
        s["fontScale"] = round(scale, 1)
        self.apply_font_scale()
        self.save()
        self.set_status(f"ขนาดตัวอักษร {round(s['fontScale'] * 100)}%  (Ctrl + / Ctrl − / Ctrl 0)")
        self.resize_prompt()
        if not self.active:
            self.render_messages()  # ตารางต้องวัดความกว้างใหม่
        return "break"

    def apply_font_scale(self):
        scale = float(self.data["settings"].get("fontScale") or 1.0)
        for font, size in self._font_sizes:
            font.configure(size=max(5, round(size * scale)))

    # ------------------------------------------------------------ edit sent message
    def start_edit(self, index):
        if self.active:
            self.set_status("รอให้ตอบเสร็จ หรือกด Esc เพื่อหยุดก่อน")
            return
        chat = self.current()
        if not chat or index >= len(chat["messages"]):
            return
        m = chat["messages"][index]
        if self.editing is None:  # เก็บข้อความที่พิมพ์ค้างไว้ คืนให้ตอนยกเลิก
            self._draft = (self.prompt.get("1.0", "end-1c"), list(self.pending))
        self.editing = {"chat": chat["id"], "index": index}
        self.prompt.delete("1.0", "end")
        self.prompt.insert("1.0", m.get("content") or "")
        self.pending = [{"kind": "file", "name": f["name"], "text": f["text"],
                         "truncated": f.get("truncated", False)} for f in m.get("files") or []]
        for img in m.get("images") or []:
            data = image_b64(img)
            if data:
                self.pending.append({"kind": "image", "name": img["name"], "data": data})
        self.render_attachments()
        self.render_edit_bar()
        self.after_prompt_edit()
        self.prompt.focus_set()
        self.prompt.mark_set("insert", "end-1c")

    def cancel_edit(self):
        if self.editing is None:
            return
        self.editing = None
        text, pending = self._draft or ("", [])
        self._draft = None
        self.prompt.delete("1.0", "end")
        self.prompt.insert("1.0", text)
        self.pending = pending
        self.render_attachments()
        self.render_edit_bar()
        self.after_prompt_edit()

    def render_edit_bar(self):
        bar = self.edit_bar
        if self.editing is None:
            bar.pack_forget()
            return
        if not bar.winfo_manager():
            before = self.attach_bar if self.attach_bar.winfo_manager() else self.comp
            bar.pack(fill="x", pady=(0, 6), before=before)

    # ------------------------------------------------------------ attachments
    def attach_files(self):
        exts = " ".join("*" + e for e in sorted(IMAGE_EXT))
        paths = filedialog.askopenfilenames(
            parent=self.root, title="แนบไฟล์หรือรูป",
            filetypes=[("เอกสาร ข้อความ และรูป", "*.pdf *.docx *.txt *.md *.py *.js *.ts *.html *.css *.json "
                        "*.csv *.xml *.yaml *.yml *.sql *.log *.ini *.rb *.java *.c *.cpp *.h "
                        "*.cs *.go *.rs *.php *.sh *.bat " + exts),
                       ("PDF / Word", "*.pdf *.docx"), ("รูปภาพ", exts), ("ทุกไฟล์", "*.*")])
        for path in paths:
            self.add_attachment(path)
        self.prompt.focus_set()

    def add_attachment(self, path):
        p = Path(path)
        if p.is_dir():
            self.set_status(f"แนบโฟลเดอร์ไม่ได้: {p.name}")
            return
        try:
            if p.suffix.lower() in IMAGE_EXT:
                if p.stat().st_size > MAX_IMAGE_BYTES:
                    raise ValueError("รูปใหญ่เกิน 15 MB")
                self.add_image_bytes(p.read_bytes(), p.name)
                return
            if p.suffix.lower() in (".pdf", ".docx"):
                self.set_status(f"กำลังอ่าน {p.name} ...")
                self.root.update_idletasks()
            text = read_document(p)
        except Exception as e:
            self.set_status(f"แนบ {p.name} ไม่ได้: {e}")
            return
        att = {"kind": "file", "name": p.name, "text": text[:MAX_FILE_CHARS],
               "truncated": len(text) > MAX_FILE_CHARS}
        self.pending.append(att)
        self.render_attachments()
        if att["truncated"]:
            self.set_status(f"ไฟล์ {p.name} ยาวเกินไป ส่งเฉพาะ {MAX_FILE_CHARS:,} ตัวอักษรแรก")
        else:
            self.set_status(f"แนบ {p.name} แล้ว ({len(text):,} ตัวอักษร)")

    def add_image_bytes(self, raw, name):
        if len(raw) > MAX_IMAGE_BYTES:
            self.set_status(f"แนบ {name} ไม่ได้: รูปใหญ่เกิน 15 MB")
            return
        self.pending.append({"kind": "image", "name": name,
                             "data": base64.b64encode(raw).decode("ascii")})
        self.render_attachments()
        self.set_status("แนบรูปแล้ว • ต้องใช้โมเดลที่ดูรูปได้ เช่น llava, gemma3, qwen2.5vl")

    def add_files(self, paths):
        for path in paths:
            self.add_attachment(path)
        self.prompt.focus_set()

    def clipboard_attachment(self):
        """รูปหรือไฟล์ในคลิปบอร์ด → ("image", png) / ("files", [...]) / (None, None)"""
        if self.shell:
            try:
                return self.shell.clipboard()
            except Exception:
                return None, None
        if sys.platform.startswith("linux"):
            try:
                if self.root.clipboard_get():
                    return None, None  # มีข้อความ → วางตามปกติ
            except tk.TclError:
                pass
            png = linux_clipboard_png()
            if png:
                return "image", png
        return None, None

    def on_prompt_paste(self, _e=None):
        kind, data = self.clipboard_attachment()
        if kind == "files":
            self.add_files(data)
            return "break"
        if kind == "image":
            self.add_image_bytes(data, f"clipboard-{datetime.datetime.now():%Y%m%d-%H%M%S}.png")
            return "break"
        self.root.after(1, self.after_prompt_edit)
        return None

    def remove_attachment(self, att):
        self.pending = [a for a in self.pending if a is not att]
        self.render_attachments()

    def render_attachments(self):
        bar = self.attach_bar
        for w in bar.winfo_children():
            w.destroy()
        if not self.pending:
            bar.pack_forget()
            return
        for att in self.pending:
            chip = tk.Frame(bar, bg=C["panel"], highlightthickness=1, highlightbackground=C["line"])
            chip.pack(side="left", padx=(0, 6))
            icon = "▣ " if att["kind"] == "image" else "▤ "
            tk.Label(chip, text=icon + att["name"], fg=C["text"], bg=C["panel"],
                     font=self.f_small).pack(side="left", padx=(8, 2), pady=3)
            x = tk.Label(chip, text="✕", fg=C["muted"], bg=C["panel"], font=self.f_small,
                         cursor="hand2")
            x.pack(side="left", padx=(2, 6))
            x.bind("<Button-1>", lambda e, a=att: self.remove_attachment(a))
        bar.pack(fill="x", pady=(0, 6), before=self.comp)

    @staticmethod
    def pending_title(user):
        names = [a["name"] for a in (user.get("files") or []) + (user.get("images") or [])]
        return "ไฟล์: " + ", ".join(names) if names else "แชตใหม่"

    # ------------------------------------------------------------ chat
    def send_message(self, regenerate=False):
        if self.active:
            self.stop()
            return
        chat = self.current()
        if not chat:
            return
        msgs = chat["messages"]
        if regenerate:
            if msgs and msgs[-1]["role"] == "assistant":
                msgs.pop()
            if not msgs or msgs[-1]["role"] != "user":
                self.render_all()
                return
        else:
            text = self.prompt.get("1.0", "end-1c").strip()
            if not text and not self.pending:
                return
            user = {"role": "user", "content": text}
            files = [a for a in self.pending if a["kind"] == "file"]
            images = [a for a in self.pending if a["kind"] == "image"]
            if files:
                user["files"] = [{k: a[k] for k in ("name", "text", "truncated")} for a in files]
            if images:
                try:
                    user["images"] = [{"name": a["name"], "file": store_image(base64.b64decode(a["data"]))}
                                      for a in images]
                except OSError as e:
                    self.set_status("บันทึกรูปไม่ได้: " + str(e))
                    return
            edit = self.editing
            if edit and edit["chat"] == chat["id"] and edit["index"] < len(msgs):
                del msgs[edit["index"]:]  # แทนที่ข้อความที่แก้ และทุกอย่างหลังจากนั้น
            self.editing, self._draft = None, None
            self.render_edit_bar()
            msgs.append(user)
            self.pending = []
            self.render_attachments()
            self.prompt.delete("1.0", "end")
            self.resize_prompt()
            self.update_placeholder()
            if chat["title"] == "แชตใหม่":
                first = text or self.pending_title(user)
                chat["title"] = re.sub(r"\s+", " ", first)[:42]
        s = self.data["settings"]
        if not s.get("model"):
            self.set_status("ยังไม่มีโมเดล กรุณาติดตั้งโมเดลใน Ollama ก่อน")
            self.save()
            self.render_all()
            return
        chat["updated"] = now_ms()
        assistant = {"role": "assistant", "model": s["model"], "content": "",
                     "thinking": "", "streaming": True}
        previous = [api_message(m) for m in msgs if m.get("role") in ("user", "assistant")]
        msgs.append(assistant)
        mx = int(s.get("maxHistory") or 0)
        history = previous[-mx:] if mx > 0 else previous
        sp = self.chat_system_prompt(chat).strip()
        body = {"model": s["model"],
                "messages": ([{"role": "system", "content": sp}] if sp else []) + history,
                "stream": True,
                "options": {"temperature": float(s["temperature"]), "num_ctx": int(s["numCtx"])}}
        if s.get("think"):
            body["think"] = True

        self.gc_images()
        self.gen += 1
        self.active = {"gen": self.gen, "stop": threading.Event(), "resp": None,
                       "msg": assistant, "in_think": False, "tagbuf": "", "seen": False}
        self.send_btn.configure(text="หยุด ■", style="Stop.TButton")
        self.save()
        self.render_all()
        self.set_status("AI กำลังสร้างคำตอบ... กด Esc หรือปุ่มหยุดเพื่อยกเลิก")
        threading.Thread(target=self._worker, args=(self.active, self.host(), body),
                         daemon=True).start()

    def _worker(self, act, host, body):
        gen, stop, q = act["gen"], act["stop"], self.q

        def post(b):
            req = urllib.request.Request(host + "/api/chat", data=json.dumps(b).encode("utf-8"),
                                         headers={"Content-Type": "application/json"},
                                         method="POST")
            return urllib.request.urlopen(req, timeout=600)
        try:
            try:
                resp = post(body)
            except urllib.error.HTTPError as e:
                if body.get("think") and e.code in (400, 422):
                    body.pop("think", None)
                    resp = post(body)
                else:
                    raise
            act["resp"] = resp
            with resp:
                for raw in resp:
                    if stop.is_set():
                        break
                    line = raw.decode("utf-8", "replace").strip()
                    if not line:
                        continue
                    obj = json.loads(line)
                    if obj.get("error"):
                        raise RuntimeError(obj["error"])
                    msg = obj.get("message") or {}
                    q.put((gen, "delta", msg.get("thinking") or "", msg.get("content") or ""))
                    if obj.get("done"):
                        n, d = obj.get("eval_count") or 0, obj.get("eval_duration") or 0
                        q.put((gen, "stats", {"tokens": n, "tps": n / (d / 1e9) if d else 0}))
            q.put((gen, "end"))
        except urllib.error.HTTPError as e:
            reason = ""
            try:
                reason = json.loads(e.read().decode("utf-8")).get("error", "")
            except Exception:
                pass
            q.put((gen, "error", reason or f"HTTP {e.code}"))
        except Exception as e:
            if not stop.is_set():
                q.put((gen, "error", str(e)))

    def feed_content(self, chunk):
        """แยกข้อความในแท็ก <think>…</think> ออกจากคำตอบ แม้แท็กจะขาดกลาง chunk"""
        a, m = self.active, self.active["msg"]
        a["tagbuf"] += chunk
        while a["tagbuf"]:
            tag = "</think>" if a["in_think"] else "<think>"
            key = "thinking" if a["in_think"] else "content"
            buf = a["tagbuf"]
            at = buf.find(tag)
            if at >= 0:
                m[key] += buf[:at]
                a["tagbuf"] = buf[at + len(tag):]
                a["in_think"] = not a["in_think"]
                continue
            hold = 0
            for k in range(min(len(tag) - 1, len(buf)), 0, -1):
                if buf.endswith(tag[:k]):
                    hold = k
                    break
            m[key] += buf[:len(buf) - hold]
            a["tagbuf"] = buf[len(buf) - hold:]
            break

    def flush_tagbuf(self):
        a = self.active
        if a and a["tagbuf"]:
            a["msg"]["thinking" if a["in_think"] else "content"] += a["tagbuf"]
            a["tagbuf"] = ""

    def call_ui(self, fn, *args):
        """เรียก fn(*args) ใน thread หลัก (ใช้จาก thread เบื้องหลัง แทน root.after)"""
        self.ui_q.put((fn, args))

    def poll(self):
        while True:
            try:
                fn, args = self.ui_q.get_nowait()
            except queue.Empty:
                break
            fn(*args)
        changed = False
        try:
            while True:
                item = self.q.get_nowait()
                a = self.active
                if not a or a["gen"] != item[0]:
                    continue
                kind, m = item[1], a["msg"]
                if kind == "delta":
                    m["thinking"] = (m.get("thinking") or "") + item[2]
                    self.feed_content(item[3])
                    changed = True
                elif kind == "stats":
                    m["stats"] = item[2]
                    a["seen"] = True
                elif kind == "end":
                    self.flush_tagbuf()
                    if not a["seen"] and not (m["content"] or m["thinking"]):
                        m["content"] += "\n\n⚠ ข้อผิดพลาด: การเชื่อมต่อสิ้นสุดก่อนมีคำตอบ"
                        self.set_status("เกิดข้อผิดพลาด: การเชื่อมต่อสิ้นสุดก่อนมีคำตอบ")
                    else:
                        self.set_status("ตอบเสร็จแล้ว • Enter ส่ง • Shift+Enter ขึ้นบรรทัด • Esc หยุด")
                    self.finish()
                    changed = False
                elif kind == "error":
                    m["content"] += "\n\n⚠ ข้อผิดพลาด: " + item[2]
                    self.set_status("เกิดข้อผิดพลาด: " + item[2])
                    self.finish()
                    changed = False
        except queue.Empty:
            pass
        if changed:
            self._dirty = True
        if self._dirty and self.active and time.monotonic() >= self._next_render:
            # ถ้าวาดช้า (คำตอบยาว) ให้เว้นช่วงวาดนานขึ้น จะได้ไม่กินเวลาจนหน้าจอค้าง
            started = time.monotonic()
            self.render_stream()
            spent = time.monotonic() - started
            self._next_render = started + spent * 4
            self._dirty = False
        self.root.after(40, self.poll)

    def stop(self):
        a = self.active
        if not a:
            return
        a["stop"].set()
        a["msg"]["interrupted"] = True
        resp = a.get("resp")
        if resp is not None:
            try:
                resp.close()
            except Exception:
                pass
        self.set_status("หยุดการตอบแล้ว")
        self.finish()

    def finish(self):
        self._dirty = False
        if self.active:
            self.flush_tagbuf()
            self.active["msg"]["streaming"] = False
        self.active = None
        self.send_btn.configure(text="ส่ง ↑", style="Accent.TButton")
        self.save()
        self.render_all()
        self.prompt.focus_set()

    # ------------------------------------------------------------ settings
    def open_settings(self):
        s = self.data["settings"]
        win = tk.Toplevel(self.root, bg=C["panel"])
        win.title("ตั้งค่า Local AI")
        win.transient(self.root)
        win.resizable(False, False)
        body = tk.Frame(win, bg=C["panel"])
        body.pack(fill="both", expand=True, padx=22, pady=18)

        def label(text):
            tk.Label(body, text=text, fg="#d0d0d2", bg=C["panel"], font=self.f_small,
                     anchor="w").pack(fill="x", pady=(12, 4))

        tk.Label(body, text="⚙  ตั้งค่า Local AI", fg=C["text"], bg=C["panel"],
                 font=self.f_title, anchor="w").pack(fill="x")

        label("Ollama Host")
        host_var = tk.StringVar(value=s["host"])
        ttk.Entry(body, textvariable=host_var, width=52).pack(fill="x")

        label("System Prompt เริ่มต้น (ใช้เมื่อแชตไม่ได้เลือกบทบาท)")
        sp = tk.Text(body, height=5, wrap="word", bg=C["field"], fg=C["text"],
                     insertbackground=C["text"], bd=0, highlightthickness=1,
                     highlightbackground=C["border"], highlightcolor=C["accent"],
                     font=self.f_base, padx=8, pady=6)
        sp.insert("1.0", s.get("systemPrompt") or "")
        sp.pack(fill="x")

        temp_var = tk.DoubleVar(value=float(s["temperature"]))
        temp_lbl = tk.Label(body, fg="#d0d0d2", bg=C["panel"], font=self.f_small, anchor="w")
        temp_lbl.pack(fill="x", pady=(12, 4))

        def upd_temp(*_):
            v = round(temp_var.get() / 0.05) * 0.05
            temp_var.set(round(v, 2))
            temp_lbl.configure(text=f"Temperature: {temp_var.get():.2f}")
        ttk.Scale(body, from_=0, to=1.5, variable=temp_var, command=upd_temp).pack(fill="x")
        upd_temp()

        row = tk.Frame(body, bg=C["panel"])
        row.pack(fill="x")
        c1, c2 = tk.Frame(row, bg=C["panel"]), tk.Frame(row, bg=C["panel"])
        c1.pack(side="left", fill="x", expand=True, padx=(0, 6))
        c2.pack(side="left", fill="x", expand=True, padx=(6, 0))
        tk.Label(c1, text="Context Window (num_ctx)", fg="#d0d0d2", bg=C["panel"],
                 font=self.f_small, anchor="w").pack(fill="x", pady=(12, 4))
        ctx_var = tk.StringVar(value=str(s["numCtx"]))
        ttk.Spinbox(c1, from_=512, to=131072, increment=1024, textvariable=ctx_var).pack(fill="x")
        tk.Label(c2, text="ข้อความย้อนหลัง (0 = ทั้งหมด)", fg="#d0d0d2", bg=C["panel"],
                 font=self.f_small, anchor="w").pack(fill="x", pady=(12, 4))
        hist_var = tk.StringVar(value=str(s["maxHistory"]))
        ttk.Spinbox(c2, from_=0, to=1000, increment=2, textvariable=hist_var).pack(fill="x")

        think_var = tk.BooleanVar(value=bool(s.get("think")))
        ttk.Checkbutton(body, text=" เปิดโหมด Thinking (เฉพาะโมเดลที่รองรับ)",
                        variable=think_var).pack(fill="x", pady=(14, 0))

        tk.Label(body, text=f"ข้อมูลแชตบันทึกที่ {DATA_FILE}\nใช้กับ Ollama ที่คุณเปิดใช้งานเองในเครื่อง",
                 fg="#c6c9cb", bg=C["panel"], font=self.f_small, justify="left",
                 anchor="w").pack(fill="x", pady=(12, 0))

        def do_save():
            host = host_var.get().strip().rstrip("/")
            if not HOST_RE.match(host):
                messagebox.showwarning("Host ไม่ถูกต้อง", "เพื่อความปลอดภัย โปรดใช้ "
                                       "http://localhost:11434 หรือ http://127.0.0.1:11434",
                                       parent=win)
                return

            def to_int(v, default):
                try:
                    return int(float(v))
                except (TypeError, ValueError):
                    return default
            s.update(host=host, systemPrompt=sp.get("1.0", "end-1c"),
                     temperature=float(temp_var.get()),
                     numCtx=max(512, to_int(ctx_var.get(), 8192)),
                     maxHistory=max(0, to_int(hist_var.get(), 0)),
                     think=bool(think_var.get()))
            self.save()
            win.destroy()
            self.refresh_models()

        foot = tk.Frame(body, bg=C["panel"])
        foot.pack(fill="x", pady=(20, 0))
        ttk.Button(foot, text="บันทึก", style="Accent.TButton", command=do_save).pack(side="right")
        ttk.Button(foot, text="ยกเลิก", command=win.destroy).pack(side="right", padx=8)
        win.bind("<Escape>", lambda e: (win.destroy(), "break")[1])

        self._place_dialog(win)


def main():
    if sys.platform == "win32":
        try:  # ให้ตัวอักษรคมชัดบนจอ High-DPI
            import ctypes
            ctypes.windll.shcore.SetProcessDpiAwareness(1)
        except Exception:
            pass
    root = tk.Tk()
    App(root)
    root.mainloop()


if __name__ == "__main__":
    main()
