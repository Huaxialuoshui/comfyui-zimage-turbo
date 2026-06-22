#!/usr/bin/env python3
"""Anima Model Setup - with mirror, fallback, retry, resume."""

import os, sys, time, shutil, urllib.request, ssl
from pathlib import Path

BASE_DIR = Path(__file__).parent.resolve()
MODELS_DIR = BASE_DIR / "ComfyUI" / "models"
MAX_RETRIES = 5
HF_REPO = "circlestone-labs/Anima"
def get_expected_sizes():
    """Fetch official file sizes from HuggingFace API."""
    import urllib.request, json
    try:
        url = f"https://huggingface.co/api/models/{HF_REPO}?expand[]=siblings"
        req = urllib.request.Request(url, headers={"User-Agent": "setup/1.0"})
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.load(resp)
        sizes = {}
        for s in data.get("siblings", []):
            sizes[s["rfilename"]] = s.get("size", 0)
        return sizes
    except Exception as e:
        print(f"  [!] Cannot fetch file sizes from API: {e}")
        return {}


# --- HF Mirror (China-friendly) ---
HF_MIRROR = "https://hf-mirror.com"
USE_MIRROR = False  # Set False if you have direct access

MODEL_FILES = {
    "UNET": {
        "filename": "split_files/diffusion_models/anima-base-v1.0.safetensors",
        "local_dir": MODELS_DIR / "diffusion_models",
        "desc": "anima-base-v1.0 (4.18 GB)",
        "min_mb": 4000,
    },
    "CLIP": {
        "filename": "split_files/text_encoders/qwen_3_06b_base.safetensors",
        "local_dir": MODELS_DIR / "text_encoders",
        "desc": "qwen_3_06b_base (1.19 GB)",
        "min_mb": 1100,
    },
    "VAE": {
        "filename": "split_files/vae/qwen_image_vae.safetensors",
        "local_dir": MODELS_DIR / "vae",
        "desc": "qwen_image_vae (254 MB)",
        "min_mb": 200,
    },
}


def download_direct(name, cfg, expected):
    """Download via direct URL (urllib) with resume support."""
    local_dir = Path(cfg["local_dir"])
    local_dir.mkdir(parents=True, exist_ok=True)
    local_name = Path(cfg["filename"]).name
    local_path = local_dir / local_name

    # Check if already fully downloaded (exact size match)
    expected_size = 0
    for k, v in expected.items():
        if cfg["filename"] in k or k.endswith(Path(cfg["filename"]).name):
            expected_size = v
            break
    if expected_size == 0:
        print(f"  [!!] API key not found for: {cfg['filename']}")
        print(f"       Available keys (partial): {list(expected.keys())[:5]}")
    if local_path.exists():
        local_size = local_path.stat().st_size
        if expected_size > 0 and local_size == expected_size:
            print(f"  [OK] {name} already complete ({local_size/(1024**3):.2f} GB)")
            return True
        elif expected_size > 0 and local_size > 1024:
            print(f"  [..] Partial: {local_size/(1024**3):.2f} / {expected_size/(1024**3):.2f} GB, resuming...")
        elif expected_size == 0 and local_size > 10 * 1024 * 1024:
            print(f"  [WARN] {name}: local={local_size/(1024**3):.2f} GB, expected size unknown from API")
            print(f"         Will re-download to be safe")

    # Build URL
    base = HF_MIRROR if USE_MIRROR else "https://huggingface.co"
    url = f"{base}/{HF_REPO}/resolve/main/{cfg['filename']}?download=true"

    for attempt in range(1, MAX_RETRIES + 1):
        if attempt > 1:
            wait = attempt * 10
            print(f"  [..] Retry {attempt}/{MAX_RETRIES} in {wait}s...")
            time.sleep(wait)

        print(f"  [>>] ({attempt}/{MAX_RETRIES}) {cfg['desc']}")
        print(f"       {url}")

        try:
            # Check existing partial download
            existing_size = local_path.stat().st_size if local_path.exists() else 0
            headers = {}
            if existing_size > 0:
                headers["Range"] = f"bytes={existing_size}-"
                print(f"       Resuming from {existing_size / (1024*1024):.0f} MB...")

            ctx = ssl.create_default_context()
            req = urllib.request.Request(url, headers=headers)
            req.add_header("User-Agent", "Anima-Setup/1.0")

            with urllib.request.urlopen(req, context=ctx, timeout=60) as resp:
                total = int(resp.headers.get("Content-Length", 0)) + existing_size
                mode = "ab" if existing_size > 0 else "wb"
                downloaded = existing_size

                with open(local_path, mode) as f:
                    chunk_size = 8 * 1024 * 1024  # 8 MB chunks
                    while True:
                        chunk = resp.read(chunk_size)
                        if not chunk:
                            break
                        f.write(chunk)
                        downloaded += len(chunk)
                        if total > 0:
                            pct = min(downloaded / total * 100, 100)
                            print(f"\r       {downloaded/(1024*1024):.0f} / {total/(1024*1024):.0f} MB ({pct:.0f}%)", end="")

            print()
            size_mb = local_path.stat().st_size / (1024 * 1024)
            print(f"  [OK] {name} done ({size_mb:.0f} MB)")
            return True

        except urllib.error.HTTPError as e:
            print(f"\n  [!] HTTP {e.code}: {e.reason}")
            if e.code == 416:  # Range Not Satisfiable = already complete
                size_mb = local_path.stat().st_size / (1024 * 1024)
                print(f"  [OK] {name} already complete ({size_mb:.0f} MB)")
                return True
        except urllib.error.URLError as e:
            print(f"\n  [!] Network: {e.reason}")
            print(f"       Try switching USE_MIRROR={'False' if USE_MIRROR else 'True'} in the script")
        except Exception as e:
            print(f"\n  [!] Error: {e}")

    return False


def download_file(name, cfg, expected):
    """Download via direct URL with Range resume, fallback to huggingface_hub."""
    # Try direct download first (works across VPN node changes)
    ok = download_direct(name, cfg, expected)
    if ok:
        return True
    
    print("  [..] Direct download failed, trying huggingface_hub...")
    try:
        from huggingface_hub import hf_hub_download
        from huggingface_hub.errors import HfHubHTTPError

        local_dir = str(cfg["local_dir"])
        local_name = Path(cfg["filename"]).name
        local_path = Path(local_dir) / local_name

        expected_size = 0
        for k, v in expected.items():
            if cfg["filename"] in k or k.endswith(Path(cfg["filename"]).name):
                expected_size = v
                break
        if expected_size == 0:
            print(f"  [!!] API key not found for: {cfg['filename']}")
            print(f"       Available keys (partial): {list(expected.keys())[:5]}")
        if local_path.exists() and expected_size > 0 and local_path.stat().st_size == expected_size:
            print(f"  [OK] {name} already exists ({local_path.stat().st_size/(1024*1024):.0f} MB)")
            return True

        endpoint = HF_MIRROR if USE_MIRROR else None
        for attempt in range(1, MAX_RETRIES + 1):
            if attempt > 1:
                time.sleep(attempt * 10)
            print(f"  [>>] ({attempt}/{MAX_RETRIES}) {cfg['desc']} [via huggingface_hub]")
            try:
                path = hf_hub_download(
                    HF_REPO, cfg["filename"],
                    local_dir=local_dir,
                                        endpoint=endpoint,
                    etag_timeout=30,
                )
                size_mb = os.path.getsize(path) / (1024 * 1024)
                if size_mb < min_mb * 0.9:
                    os.remove(path)
                    raise ValueError(f"File too small: {size_mb:.1f} MB, expected >{min_mb*0.9:.0f}")
                print(f"  [OK] {name} ({size_mb:.0f} MB)")
                return True
            except (HfHubHTTPError, OSError, ConnectionError, TimeoutError) as e:
                print(f"  [!] {e}")
            except Exception as e:
                print(f"  [!] {e}")
    except ImportError:
        print("  [..] huggingface_hub not available, using direct download")

    return False


def main():
    print("=" * 60)
    print("  Anima Model Setup")
    print(f"  {HF_REPO}")
    print(f"  Mirror: {'ON (' + HF_MIRROR + ')' if USE_MIRROR else 'OFF (direct)'}")
    print("=" * 60)
    print()

    # Fetch expected sizes from HF API
    print("[*] Checking file sizes from HuggingFace...")
    expected = get_expected_sizes()
    if expected:
        print(f"     Got {len(expected)} file sizes from API")
    else:
        print("     Using local thresholds as fallback")
    print()

    # Create all target dirs
    for cfg in MODEL_FILES.values():
        cfg["local_dir"].mkdir(parents=True, exist_ok=True)

    total = len(MODEL_FILES)
    success = 0

    for i, (name, cfg) in enumerate(MODEL_FILES.items(), 1):
        print(f"[{i}/{total}] {name}")
        print(f"       File:  {cfg['filename']}")
        print(f"       Dest:  {cfg['local_dir']}")

        ok = download_file(name, cfg, expected)
        if ok:
            success += 1
        else:
            print(f"  [FAIL] {name} after {MAX_RETRIES} attempts")
        print()

    print("=" * 60)
    if success == total:
        print(f"  [DONE] All {total} files installed!")
        print()
        print("  Next:")
        print("    1. Restart ComfyUI")
        print("    2. Load animaWorkFlows/anima_basic.json")
    else:
        print(f"  [PARTIAL] {success}/{total} downloaded.")
        print(f"  Re-run this script to resume.")
        print()
        print(f"  If downloads keep failing:")
        print(f"    - Edit anima_setup.py: set USE_MIRROR={'False' if USE_MIRROR else 'True'}")
        print(f"    - Or set proxy: set HTTP_PROXY=http://127.0.0.1:7890")
    print("=" * 60)

    input("\nPress Enter to exit...")


if __name__ == "__main__":
    main()
