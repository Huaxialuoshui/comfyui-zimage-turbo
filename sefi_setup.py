#!/usr/bin/env python3
"""SeFi-Image Model Setup - download models + install ComfyUI custom node."""

import os, sys, time, shutil, subprocess, json as jsonmod, ssl
from pathlib import Path

BASE_DIR = Path(__file__).parent.resolve()
COMFYUI_DIR = BASE_DIR / "ComfyUI"
MODELS_DIR = COMFYUI_DIR / "models"
CUSTOM_NODES_DIR = COMFYUI_DIR / "custom_nodes"
MAX_RETRIES = 5

USE_MIRROR = True
HF_MIRROR = "https://hf-mirror.com"

SEFI_NODE_REPO = "RealRebelAI/ComfyUI_Rebels_SeFi"
SEFI_NODE_DIR = CUSTOM_NODES_DIR / "ComfyUI_Rebels_SeFi"
HF_REPO = "realrebelai/SeFi-Image-5B-Turbo"

MODEL_FILES = {
    "TRANSFORMER": {
        "filename": "SeFi-5B-Turbo_transformer_bf16.safetensors",
        "local_dir": MODELS_DIR / "diffusion_models",
        "desc": "SeFi-5B-Turbo transformer bf16",
        "min_mb": 8000,
    },
    "TEXT_ENCODER": {
        "filename": "SeFi_Qwen3-VL-4B_text_bf16.safetensors",
        "local_dir": MODELS_DIR / "text_encoders",
        "desc": "SeFi Qwen3-VL-4B text encoder bf16",
        "min_mb": 2000,
    },
    "VAE": {
        "filename": "SeFi_VAE.safetensors",
        "local_dir": MODELS_DIR / "vae",
        "desc": "SeFi VAE",
        "min_mb": 200,
    },
}


def get_expected_sizes():
    import requests as req_lib
    try:
        url = "https://huggingface.co/api/models/" + HF_REPO + "?expand[]=siblings"
        resp = req_lib.get(url, headers={"User-Agent": "sefi-setup/1.0"}, timeout=15)
        resp.raise_for_status()
        data = resp.json()
        sizes = {}
        for s in data.get("siblings", []):
            sizes[s["rfilename"]] = s.get("size", 0)
        return sizes
    except Exception as e:
        print("  [!] Cannot fetch file sizes from API:", e)
        return {}


def download_file(name, cfg, expected):
    import requests as req_lib
    local_dir = Path(cfg["local_dir"])
    local_dir.mkdir(parents=True, exist_ok=True)
    local_name = Path(cfg["filename"]).name
    local_path = local_dir / local_name
    min_mb = cfg.get("min_mb", 100)

    if local_path.exists():
        local_size = local_path.stat().st_size
        if local_size > min_mb * 1024 * 1024 * 0.9:
            sz = local_size / (1024 * 1024)
            print("  [SKIP] " + name + " already exists (" + str(int(sz)) + " MB)")
            return True

    base = HF_MIRROR if USE_MIRROR else "https://huggingface.co"
    url = base + "/" + HF_REPO + "/resolve/main/" + cfg["filename"]

    for attempt in range(1, MAX_RETRIES + 1):
        if attempt > 1:
            wait = attempt * 10
            print("  [..] Retry " + str(attempt) + "/" + str(MAX_RETRIES) + " in " + str(wait) + "s...")
            time.sleep(wait)

        print("  [>>] (" + str(attempt) + "/" + str(MAX_RETRIES) + ") " + cfg["desc"])
        print("       " + url)

        try:
            existing_size = local_path.stat().st_size if local_path.exists() else 0
            headers = {"User-Agent": "SeFi-Setup/1.0"}
            if existing_size > 0:
                headers["Range"] = "bytes=" + str(existing_size) + "-"
                print("       Resuming from " + str(int(existing_size / (1024*1024))) + " MB...")

            resp = req_lib.get(url, headers=headers, stream=True, timeout=120)
            if resp.status_code == 416:
                size_mb = local_path.stat().st_size / (1024 * 1024)
                print("  [OK] " + name + " already complete (" + str(int(size_mb)) + " MB)")
                return True
            if resp.status_code in (401, 403):
                print("\n  [!!] Access denied - model may require login:")
                print("       https://huggingface.co/" + HF_REPO)
                print("       Run: huggingface-cli login")
                return False
            resp.raise_for_status()

            total = int(resp.headers.get("content-length", 0)) + existing_size
            mode = "ab" if existing_size > 0 else "wb"
            downloaded = existing_size

            with open(local_path, mode) as f:
                for chunk in resp.iter_content(chunk_size=8*1024*1024):
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)
                        if total > 0:
                            pct = min(downloaded / total * 100, 100)
                            bar = "#" * int(pct / 5) + "-" * (20 - int(pct / 5))
                            msg = "       [" + bar + "] " + str(int(downloaded/(1024*1024))) + " / " + str(int(total/(1024*1024))) + " MB (" + str(int(pct)) + "%)"
                            sys.stdout.write("\r" + msg)
                            sys.stdout.flush()
            print()

            size_mb = local_path.stat().st_size / (1024 * 1024)
            print("  [OK] " + name + " done (" + str(int(size_mb)) + " MB)")
            return True

        except req_lib.exceptions.HTTPError as e:
            print("\n  [!] HTTP Error:", e)
        except req_lib.exceptions.ConnectionError as e:
            print("\n  [!] Connection Error:", e)
            print("       Try: set USE_MIRROR=" + str(not USE_MIRROR) + " in sefi_setup.py")
        except Exception as e:
            print("\n  [!] Error:", e)

    return False


def install_custom_node():
    print("[*] Installing ComfyUI custom node:", SEFI_NODE_REPO)
    target = SEFI_NODE_DIR

    if target.exists():
        print("  [SKIP] Node already exists at", target)
        return True

    node_url = "https://github.com/" + SEFI_NODE_REPO + ".git"
    print("       Cloning:", node_url)
    try:
        result = subprocess.run(
            ["git", "clone", "--depth", "1", node_url, str(target)],
            capture_output=True, text=True, timeout=120
        )
        if result.returncode == 0:
            print("  [OK] Node installed at", target)
            return True
        else:
            print("  [FAIL] git clone failed:", result.stderr[:300])
            return False
    except Exception as e:
        print("  [FAIL] git clone error:", e)
        return False


def upgrade_deps():
    print("[*] Upgrading Python dependencies...")
    deps = ["diffusers", "transformers", "omegaconf", "accelerate"]
    for dep in deps:
        try:
            result = subprocess.run(
                [sys.executable, "-m", "pip", "install", "-U", dep],
                capture_output=True, text=True, timeout=120
            )
            if result.returncode == 0:
                print("  [OK]", dep, "updated")
            else:
                print("  [!]", dep, "update failed (non-fatal)")
        except Exception as e:
            print("  [!] pip error for", dep, ":", e)


def print_banner(text):
    lines = text.split("\n")
    width = max(len(l) for l in lines) + 4
    top = chr(0x2554) + chr(0x2550) * (width - 2) + chr(0x2557)
    bot = chr(0x255A) + chr(0x2550) * (width - 2) + chr(0x255D)
    mid = chr(0x2551)
    print(top)
    for l in lines:
        print(mid, l.center(width - 4), mid)
    print(bot)


def main():
    print_banner("SeFi-Image Model Setup\nBased on FLUX.2-Klein")
    print("  HF Repo:", HF_REPO)
    print("  Custom Node:", SEFI_NODE_REPO)
    if USE_MIRROR:
        print("  Mirror: ON (" + HF_MIRROR + ")")
    else:
        print("  Mirror: OFF (direct)")
    print()

    print("-" * 50)
    print(">> Step 1/4: Install ComfyUI custom node")
    print("-" * 50)
    node_ok = install_custom_node()
    print()

    print("-" * 50)
    print(">> Step 2/4: Upgrade Python dependencies")
    print("-" * 50)
    upgrade_deps()
    print()

    print("-" * 50)
    print(">> Step 3/4: Check file sizes from HuggingFace API")
    print("-" * 50)
    expected = get_expected_sizes()
    if expected:
        print("     Got", len(expected), "file sizes from API")
    else:
        print("     Using local thresholds as fallback")
    print()

    print("-" * 50)
    print(">> Step 4/4: Download SeFi-Image model files")
    print("     (Transformer ~10GB, Text Encoder ~2.3GB, VAE ~250MB)")
    print("-" * 50)
    for cfg in MODEL_FILES.values():
        cfg["local_dir"].mkdir(parents=True, exist_ok=True)

    total = len(MODEL_FILES)
    success = 0
    for i, (name, cfg) in enumerate(MODEL_FILES.items(), 1):
        print()
        print("[" + str(i) + "/" + str(total) + "]", name)
        print("       File: ", cfg["filename"])
        print("       Dest: ", cfg["local_dir"])
        ok = download_file(name, cfg, expected)
        if ok:
            success += 1
        else:
            print("  [FAIL]", name, "after", MAX_RETRIES, "attempts")

    print()
    print("=" * 60)
    if success == total and node_ok:
        print_banner("Setup Complete!")
        print()
        print("  Next steps:")
        print("    1. Restart ComfyUI (or start with start.bat)")
        print("    2. Use Rebels -> SeFi nodes in ComfyUI")
        print("    3. If model loading fails, run: huggingface-cli login")
    else:
        print("  [PARTIAL] " + str(success) + "/" + str(total) + " files, node=" + ("OK" if node_ok else "FAIL"))
        print("  Re-run this script to resume.")
        if USE_MIRROR:
            print("  If downloads keep failing, check your network or proxy.")
        else:
            print("  Edit sefi_setup.py: set USE_MIRROR=True")
    print("=" * 60)

    input("\nPress Enter to exit...")

if __name__ == "__main__":
    main()