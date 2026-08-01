#!/usr/bin/env python3
"""Download Qwen3-VL-2B-Instruct to replace Qwen2-VL-2B-Instruct."""

import os, sys, time, json as jsonmod
from pathlib import Path

BASE_DIR = Path(__file__).parent.resolve()
TARGET_DIR = BASE_DIR / "ComfyUI" / "models" / "LLM" / "Qwen-VL" / "Qwen3-VL-2B-Instruct"
HF_REPO = "Qwen/Qwen3-VL-2B-Instruct"
MAX_RETRIES = 5
USE_MIRROR = True
HF_MIRROR = "https://hf-mirror.com"

REQUIRED_FILES = [
    "model.safetensors",
    "config.json",
    "tokenizer.json",
    "tokenizer_config.json",
    "chat_template.json",
    "generation_config.json",
    "preprocessor_config.json",
    "vocab.json",
    "merges.txt",
    "video_preprocessor_config.json",
]


def download_with_resume(url, local_path, desc):
    import requests as req_lib
    for attempt in range(1, MAX_RETRIES + 1):
        if attempt > 1:
            wait = attempt * 10
            print("  [..] Retry " + str(attempt) + "/" + str(MAX_RETRIES) + " in " + str(wait) + "s...")
            time.sleep(wait)

        print("  [>>] (" + str(attempt) + "/" + str(MAX_RETRIES) + ") " + desc)

        try:
            existing_size = local_path.stat().st_size if local_path.exists() else 0
            headers = {"User-Agent": "Qwen3VL-Setup/1.0"}
            if existing_size > 0:
                headers["Range"] = "bytes=" + str(existing_size) + "-"
                print("       Resuming from " + str(int(existing_size / (1024*1024))) + " MB...")

            resp = req_lib.get(url, headers=headers, stream=True, timeout=120)
            if resp.status_code == 416:
                sz = local_path.stat().st_size / (1024 * 1024)
                print("  [OK] already complete (" + str(int(sz)) + " MB)")
                return True
            resp.raise_for_status()

            total = int(resp.headers.get("content-length", 0)) + existing_size
            mode = "ab" if existing_size > 0 else "wb"
            downloaded = existing_size

            with open(str(local_path), mode) as f:
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
            sz = local_path.stat().st_size / (1024 * 1024)
            print("  [OK] done (" + str(int(sz)) + " MB)")
            return True

        except req_lib.exceptions.HTTPError as e:
            print("\n  [!] HTTP Error:", e)
        except req_lib.exceptions.ConnectionError as e:
            print("\n  [!] Connection Error:", e)
        except Exception as e:
            print("\n  [!] Error:", e)

    return False


def main():
    print("=" * 60)
    print("  Qwen3-VL-2B-Instruct Downloader")
    print("  Repo: " + HF_REPO)
    if USE_MIRROR:
        print("  Mirror: ON (" + HF_MIRROR + ")")
    else:
        print("  Mirror: OFF (direct)")
    print("  Target: " + str(TARGET_DIR))
    print("=" * 60)
    print()

    TARGET_DIR.mkdir(parents=True, exist_ok=True)

    base = HF_MIRROR if USE_MIRROR else "https://huggingface.co"

    total = len(REQUIRED_FILES)
    success = 0

    for i, fname in enumerate(REQUIRED_FILES, 1):
        local_path = TARGET_DIR / fname
        url = base + "/" + HF_REPO + "/resolve/main/" + fname

        expected = 4255140312 if fname == "model.safetensors" else 100
        min_size = expected
        if local_path.exists() and local_path.stat().st_size > min_size:
            sz = local_path.stat().st_size / (1024*1024)
            print("[" + str(i) + "/" + str(total) + "] " + fname + " [SKIP] (" + str(int(sz)) + " MB)")
            success += 1
            continue

        print("[" + str(i) + "/" + str(total) + "] " + fname)
        ok = download_with_resume(url, local_path, fname)
        if ok:
            success += 1
        else:
            print("  [FAIL] " + fname)
        print()

    print("=" * 60)
    if success == total:
        print("  [DONE] All files downloaded to:")
        print("    " + str(TARGET_DIR))
        print()
        print("  Next steps:")
        print("    1. ComfyUI nodes using Qwen2-VL-2B should update their path")
        print("    2. If using QwenVL nodes, change model to Qwen3-VL-2B-Instruct")
    else:
        print("  [PARTIAL] " + str(success) + "/" + str(total) + " files")
        print("  Re-run to resume.")
    print("=" * 60)

    input("\nPress Enter to exit...")

if __name__ == "__main__":
    main()