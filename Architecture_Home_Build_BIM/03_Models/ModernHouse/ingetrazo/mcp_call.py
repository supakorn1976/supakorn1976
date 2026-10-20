"""IngeTrazo AI Bridge client.  Usage: python mcp_call.py calls.json   (no argument -> list tools)
calls.json = [{"tool": "run_python", "args": {"code": "..."}},
              {"tool": "screenshot", "args": {"width": 1200, "height": 800}, "save": "shot.png"}]
Stops at the first call that reports an error or a Python traceback (exit code 1).
"""
import base64, json, os, subprocess, sys, threading

EXE = r"C:\Program Files\IngeTrazo\ingetrazo-mcp.exe"
HERE = os.path.dirname(os.path.abspath(__file__))
sys.stdout.reconfigure(encoding="utf-8")

p = subprocess.Popen([EXE], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
threading.Thread(target=lambda: [sys.stderr.write("[srv] " + l.decode("utf-8", "replace"))
                                 for l in p.stderr], daemon=True).start()
_id = 0


def send(method, params=None, notify=False):
    global _id
    msg = {"jsonrpc": "2.0", "method": method}
    if params is not None:
        msg["params"] = params
    if not notify:
        _id += 1
        msg["id"] = _id
    p.stdin.write((json.dumps(msg) + "\n").encode("utf-8"))
    p.stdin.flush()
    if notify:
        return None
    while True:
        line = p.stdout.readline()
        if not line:
            raise SystemExit("server closed stdout")
        try:
            r = json.loads(line.decode("utf-8"))
        except ValueError:
            continue
        if r.get("id") == _id:
            return r


send("initialize", {"protocolVersion": "2024-11-05", "capabilities": {},
                    "clientInfo": {"name": "claude", "version": "0.1"}})
send("notifications/initialized", notify=True)

calls = json.load(open(sys.argv[1], encoding="utf-8")) if len(sys.argv) > 1 else []
if not calls:
    print(json.dumps(send("tools/list").get("result"), ensure_ascii=False, indent=1))

failed = False
for i, c in enumerate(calls):
    res = send("tools/call", {"name": c["tool"], "arguments": c.get("args", {})}).get("result", {})
    print(f"--- call {i}: {c['tool']} isError={res.get('isError')}")
    text = ""
    for item in res.get("content", []):
        if item.get("type") == "image":
            fn = os.path.join(HERE, c.get("save", f"shot_{i}.png"))
            open(fn, "wb").write(base64.b64decode(item["data"]))
            print("IMAGE saved:", fn)
        elif item.get("type") == "text":
            text += item["text"]
            print(item["text"][:6000])
    if res.get("isError") or "Traceback" in text:
        print(f"STOPPED at call {i}: fix the error above (Ctrl+Z in IngeTrazo undoes finished stages)")
        failed = True
        break

p.stdin.close()
try:
    p.wait(timeout=5)
except Exception:
    p.kill()
sys.exit(1 if failed else 0)
