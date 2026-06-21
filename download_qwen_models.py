#!/usr/bin/env python3
"""
Qwen LLM/VL 模型下载脚本（含进度条）
"""

import os, sys, time
from pathlib import Path
from tqdm import tqdm

BASE_DIR = Path(__file__).resolve().parent
MODELS_DIR = BASE_DIR / "ComfyUI" / "models"

QWEN_MODELS = {
    "Qwen3-0.6B": {
        "repo_id": "Qwen/Qwen3-0.6B",
        "target_dir": "LLM/Qwen-VL",
        "desc": "Qwen3 0.6B 纯文本 - 用于 PromptEnhancer 提示词扩写",
    },
    "Qwen2-VL-2B-Instruct": {
        "repo_id": "Qwen/Qwen2-VL-2B-Instruct",
        "target_dir": "LLM/Qwen-VL",
        "desc": "Qwen2-VL 2B - 用于 pose_transform 姿态分析",
    },
    "Qwen3-VL-4B-Instruct": {
        "repo_id": "Qwen/Qwen3-VL-4B-Instruct",
        "target_dir": "LLM/Qwen-VL",
        "desc": "Qwen3-VL 4B - 用于 analyze_gen 和 iterative_refine 智能分析",
    },
}

QWENVL_REPOS = [
    "1038lab/ComfyUI-QwenVL.git",         # 785 stars, 最活跃
    "alexcong/ComfyUI_QwenVL.git",        # 144 stars (注意下划线)
    "WingeD123/ComfyUI_QwenVL_PromptCaption.git",  # 提示词扩写专用
    "aistudynow/ComfyUI-QwenVL.git",      # 14 stars, 备用
]

# ---- HuggingFace 镜像 ----
HF_MIRROR = "https://huggingface.co"

# Z-Image Turbo 模型
ZIMAGE_REPO = "Comfy-Org/z_image_turbo"

ZIMAGE_FILES = {
    "bf16": {
        "files": {
            "diffusion_models/z_image_turbo_bf16.safetensors": "split_files/diffusion_models/z_image_turbo_bf16.safetensors",
        },
        "desc": "BF16 Diffusion Model - 16G+ VRAM recommended"
    },
    "fp8": {
        "files": {
            "diffusion_models/z_image_turbo_bf16.safetensors": "split_files/diffusion_models/z_image_turbo_bf16.safetensors",
        },
        "desc": "BF16 model + FP8 text encoder - 8-12G VRAM"
    }
}

ZIMAGE_COMMON_FILES = {
    "text_encoders/qwen_3_4b.safetensors": "split_files/text_encoders/qwen_3_4b.safetensors",
    "vae/ae.safetensors": "split_files/vae/ae.safetensors",
}

QWENVL_REPOS = [
    "1038lab/ComfyUI-QwenVL.git",         # 785 stars, 最活跃
    "alexcong/ComfyUI_QwenVL.git",        # 144 stars (注意下划线)
    "WingeD123/ComfyUI_QwenVL_PromptCaption.git",  # 提示词扩写专用
    "aistudynow/ComfyUI-QwenVL.git",      # 14 stars, 备用
]

# ---- HuggingFace 镜像 ----
HF_MIRROR = "https://huggingface.co"

# Z-Image Turbo 模型
ZIMAGE_MODELS = {
    "bf16": {
        "name": "z-image-turbo-bf16-aio.safetensors",
        "repo": "LLMhacker/Z-Image-Turbo",
        "file": "z-image-turbo-bf16-aio.safetensors",
        "desc": "BF16精度 - 推荐16G+显存使用, AIO内置CLIP+VAE"
    },
    "fp8": {
        "name": "z-image-turbo-fp8-aio.safetensors",
        "repo": "LLMhacker/Z-Image-Turbo",
        "file": "z-image-turbo-fp8-aio.safetensors",
        "desc": "FP8精度 - 适合8-12G显存, AIO内置CLIP+VAE"
    }
}

# ---- pip 国内镜像 ----
PIP_MIRROR = "https://pypi.org/simple"
PIP_INDEX_ARGS = []

def _download_with_progress(repo_id, local_dir, desc):
    """Download a HuggingFace repo with tqdm progress bars."""
    from huggingface_hub import hf_hub_download, HfApi
    from huggingface_hub.utils import build_hf_headers, get_session

    api = HfApi()
    try:
        repo_info = api.repo_info(repo_id, repo_type="model")
        files = [f.rfilename for f in repo_info.siblings if not f.rfilename.endswith("/")]
    except Exception:
        # Fallback: use snapshot_download (less detailed progress)
        from huggingface_hub import snapshot_download
        print("  Using snapshot download (file list unavailable)...")
        snapshot_download(repo_id=repo_id, local_dir=str(local_dir), etag_timeout=30)
        return True

    local_dir.mkdir(parents=True, exist_ok=True)

    # Calculate total size
    total_bytes = 0
    file_sizes = {}
    for f in repo_info.siblings:
        if f.rfilename.endswith("/"):
            continue
        sz = f.size or 0
        file_sizes[f.rfilename] = sz
        total_bytes += sz

    downloaded = 0
    all_ok = True

    with tqdm(total=total_bytes, unit="B", unit_scale=True, desc=desc, position=0) as pbar:
        for remote_name in files:
            local_path = local_dir / remote_name
            if local_path.exists() and local_path.stat().st_size == file_sizes.get(remote_name, 0):
                pbar.update(file_sizes.get(remote_name, 0))
                continue

            local_path.parent.mkdir(parents=True, exist_ok=True)
            max_retries = 3
            ok = False
            for attempt in range(1, max_retries + 1):
                try:
                    hf_hub_download(
                        repo_id=repo_id,
                        filename=remote_name,
                        local_dir=str(local_dir),
                        local_dir_use_symlinks=False,
                        resume_download=True,
                        etag_timeout=30,
                    )
                    ok = True
                    break
                except Exception as e:
                    if attempt < max_retries:
                        tqdm.write(f"  [!] Retry {attempt}/{max_retries}: {type(e).__name__}")
                        time.sleep(attempt * 10)
                    else:
                        tqdm.write(f"  [!] FAILED: {remote_name} - {e}")
                        all_ok = False

            if ok and file_sizes.get(remote_name, 0) > 0:
                pbar.update(file_sizes[remote_name])

    return all_ok


def download_qwen_models():
    print("=" * 50)
    print("  Qwen LLM / VL Models Downloader")
    print("=" * 50)

    all_ok = True
    for name, cfg in QWEN_MODELS.items():
        target = MODELS_DIR / cfg["target_dir"] / name
        if target.exists() and any(target.iterdir()):
            total = sum(f.stat().st_size for f in target.rglob("*") if f.is_file()) / 1e9
            print(f"\n  [OK] {name}: already exists ({total:.1f}GB)\n")
            continue

        print(f"\n  >>> {name} ({cfg['desc']})")
        print(f"      Repo: {cfg['repo_id']}\n")

        try:
            ok = _download_with_progress(cfg["repo_id"], target, name)
            if not ok:
                all_ok = False
                print(f"  [FAIL] {name} - some files failed")
            else:
                total = sum(f.stat().st_size for f in target.rglob("*") if f.is_file()) / 1e9
                print(f"\n  [OK] {name} ({total:.1f}GB)\n")
        except Exception as e:
            all_ok = False
            print(f"  [FAIL] {name}: {e}")

    print("=" * 50)
    if all_ok:
        print("  All Qwen models ready! You can close this window.")
    else:
        print("  Some models failed. Re-run to resume.")
    print("=" * 50)
    return all_ok


if __name__ == "__main__":
    download_qwen_models()
    input("\nPress Enter to exit...")
