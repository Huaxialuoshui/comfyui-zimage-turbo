import os, sys, json, time, shutil, datetime, urllib.request

SRC = r"D:\A_Study\Image\comfyui-zimage-package\ComfyUI\output"
DST = r"D:\A_Study\Image\comfyui-zimage-package\outputs\saved_videos"
LOG = os.path.join(DST, "monitor_log.txt")
MAX_MINUTES = 75

os.makedirs(DST, exist_ok=True)

def log(msg):
    line = f"[{datetime.datetime.now():%H:%M:%S}] {msg}"
    with open(LOG, "a", encoding="utf-8") as f:
        f.write(line + "\n")
    print(line, flush=True)

def queue_state():
    try:
        q = json.load(urllib.request.urlopen("http://127.0.0.1:8188/queue", timeout=10))
        return len(q.get("queue_running", [])), len(q.get("queue_pending", []))
    except Exception:
        return None, None

def all_mp4():
    res = {}
    for dp, dn, fn in os.walk(SRC):
        for f in fn:
            if f.lower().endswith(".mp4"):
                p = os.path.join(dp, f)
                res[p] = os.path.getmtime(p)
    return res

def save_new(seen):
    saved = []
    current = all_mp4()
    for p, mt in current.items():
        if p not in seen:
            time.sleep(5)  # 等文件写完
            if not os.path.exists(p):
                continue
            rel = os.path.relpath(p, SRC).replace(os.sep, "_")
            ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            dst = os.path.join(DST, f"{ts}_{rel}")
            try:
                shutil.copy2(p, dst)
                saved.append((os.path.basename(dst), os.path.getsize(dst)/1e6))
                log(f"SAVED {os.path.basename(dst)} ({os.path.getsize(dst)/1e6:.2f} MB)")
            except Exception as e:
                log(f"COPY FAILED {p}: {e}")
    seen.update(current)
    return saved

log("=== monitor start ===")
r, p = queue_state()
log(f"initial queue: running={r} pending={p}")

seen = all_mp4()
start = time.time()
idle = 0

while time.time() - start < MAX_MINUTES * 60:
    save_new(seen)
    r, p = queue_state()
    if r == 0 and p == 0:
        idle += 1
        if idle >= 5:
            log("queue empty & idle for 5 min, stopping")
            break
    else:
        idle = 0
    time.sleep(60)

r, p = queue_state()
total = len([f for f in os.listdir(DST) if f.endswith(".mp4")])
log(f"=== monitor end: queue r={r} p={p}, total saved={total} ===")
