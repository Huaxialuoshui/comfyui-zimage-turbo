#!/usr/bin/env python3
"""
ComfyUI + Z-Image Turbo + QwenVL 鏁村悎鍖呭畨瑁呰剼鏈?(鍥藉唴闀滃儚浼樺寲鐗?
鍩轰簬鐭ヤ箮鏂囨。锛欳omfyUI閮ㄧ讲鎸囧崡 - 鏈湴AI缁樺浘宸ヤ綔娴?
"""

import os
import sys
import subprocess
import shutil
import json
from pathlib import Path

# ========== 閰嶇疆鍖?==========
BASE_DIR = Path(__file__).parent.parent.resolve()
COMFYUI_DIR = BASE_DIR / "ComfyUI"
MODELS_DIR = COMFYUI_DIR / "models"
CHECKPOINT_DIR = MODELS_DIR / "checkpoints"
CUSTOM_NODES_DIR = COMFYUI_DIR / "custom_nodes"
PYTHON_EXE = sys.executable

# ---- GitHub 闀滃儚婧?(鍥藉唴鍔犻€? ----
GITHUB_MIRRORS = [""]  # VPN鐩磋繛

# ComfyUI 瀹樻柟浠撳簱
COMFYUI_REPO_PATH = "comfyanonymous/ComfyUI.git"
COMFYUI_MANAGER_REPO_PATH = "ltdrdata/ComfyUI-Manager.git"

# QwenVL 鑺傜偣浠撳簱 (澶氫釜澶囬€?

# Qwen LLM / VL models for ComfyUI-QwenVL nodes
QWEN_MODELS = {
    "Qwen3-0.6B": {
        "repo_id": "Qwen/Qwen3-0.6B",
        "target_dir": "LLM/Qwen-VL",
        "desc": "Qwen3 0.6B 绾枃鏈?- 鐢ㄤ簬 PromptEnhancer 鎻愮ず璇嶆墿鍐?,
    },
    "Qwen2-VL-2B-Instruct": {
        "repo_id": "Qwen/Qwen2-VL-2B-Instruct",
        "target_dir": "LLM/Qwen-VL",
        "desc": "Qwen2-VL 2B - 鐢ㄤ簬 pose_transform 濮挎€佸垎鏋?,
    },
    "Qwen3-VL-4B-Instruct": {
        "repo_id": "Qwen/Qwen3-VL-4B-Instruct",
        "target_dir": "LLM/Qwen-VL",
        "desc": "Qwen3-VL 4B - 鐢ㄤ簬 analyze_gen 鍜?iterative_refine 鏅鸿兘鍒嗘瀽",
    },
}

QWENVL_REPOS = [
    "1038lab/ComfyUI-QwenVL.git",         # 785 stars, 鏈€娲昏穬
    "alexcong/ComfyUI_QwenVL.git",        # 144 stars (娉ㄦ剰涓嬪垝绾?
    "WingeD123/ComfyUI_QwenVL_PromptCaption.git",  # 鎻愮ず璇嶆墿鍐欎笓鐢?
    "aistudynow/ComfyUI-QwenVL.git",      # 14 stars, 澶囩敤
]

# ---- HuggingFace 闀滃儚 ----
HF_MIRROR = "https://huggingface.co"

# Z-Image Turbo 妯″瀷
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
    "1038lab/ComfyUI-QwenVL.git",         # 785 stars, 鏈€娲昏穬
    "alexcong/ComfyUI_QwenVL.git",        # 144 stars (娉ㄦ剰涓嬪垝绾?
    "WingeD123/ComfyUI_QwenVL_PromptCaption.git",  # 鎻愮ず璇嶆墿鍐欎笓鐢?
    "aistudynow/ComfyUI-QwenVL.git",      # 14 stars, 澶囩敤
]

# ---- HuggingFace 闀滃儚 ----
HF_MIRROR = "https://huggingface.co"

# Z-Image Turbo 妯″瀷
ZIMAGE_MODELS = {
    "bf16": {
        "name": "z-image-turbo-bf16-aio.safetensors",
        "repo": "LLMhacker/Z-Image-Turbo",
        "file": "z-image-turbo-bf16-aio.safetensors",
        "desc": "BF16绮惧害 - 鎺ㄨ崘16G+鏄惧瓨浣跨敤, AIO鍐呯疆CLIP+VAE"
    },
    "fp8": {
        "name": "z-image-turbo-fp8-aio.safetensors",
        "repo": "LLMhacker/Z-Image-Turbo",
        "file": "z-image-turbo-fp8-aio.safetensors",
        "desc": "FP8绮惧害 - 閫傚悎8-12G鏄惧瓨, AIO鍐呯疆CLIP+VAE"
    }
}

# ---- pip 鍥藉唴闀滃儚 ----
PIP_MIRROR = "https://pypi.org/simple"
PIP_INDEX_ARGS = []


def run_cmd(cmd, cwd=None, desc="", timeout=300):
    """杩愯鍛戒护骞跺疄鏃惰緭鍑?""
    print(f"\n{'='*60}")
    print(f">>> {desc}")
    print(f">>> {' '.join(cmd) if isinstance(cmd, list) else cmd}")
    print(f"{'='*60}")
    try:
        result = subprocess.run(cmd, cwd=cwd, shell=isinstance(cmd, str), timeout=timeout)
        if result.returncode != 0:
            print(f"  [!] 鍛戒护杩斿洖闈為浂閫€鍑虹爜 {result.returncode}")
        return result.returncode == 0
    except subprocess.TimeoutExpired:
        print(f"  [!] 鍛戒护瓒呮椂 ({timeout}s)")
        return False
    except Exception as e:
        print(f"  [!] 鍛戒护鎵ц寮傚父: {e}")
        return False


def git_clone_with_mirrors(repo_path, target_dir):
    """閫氳繃澶氫釜闀滃儚婧愬皾璇曞厠闅?GitHub 浠撳簱"""
    if target_dir.exists():
        shutil.rmtree(target_dir)
    
    target_dir.parent.mkdir(parents=True, exist_ok=True)
    
    for mirror in GITHUB_MIRRORS:
        if mirror:
            url = f"{mirror}https://github.com/{repo_path}"
        else:
            url = f"https://github.com/{repo_path}"
        
        print(f"    灏濊瘯: {url}")
        ok = run_cmd(["git", "clone", url, str(target_dir)], 
                     desc=f"鍏嬮殕 {repo_path}", timeout=120)
        if ok:
            print(f"    [鉁揮 鍏嬮殕鎴愬姛!")
            return True
        else:
            if target_dir.exists():
                shutil.rmtree(target_dir)
            print(f"    [鉁梋 澶辫触, 灏濊瘯涓嬩竴涓暅鍍?..")
    
    return False


def install_comfyui():
    """瀹夎 ComfyUI"""
    if COMFYUI_DIR.exists():
        print(f"[鉁揮 ComfyUI 鐩綍宸插瓨鍦? {COMFYUI_DIR}")
        choice = input("鏄惁閲嶆柊瀹夎? (y/N): ").strip().lower()
        if choice == "y":
            print("  [*] Deleting old ComfyUI...")
            def on_rm_error(func, path, exc_info):
                import stat
                os.chmod(path, stat.S_IWRITE)
                func(path)
            shutil.rmtree(COMFYUI_DIR, onerror=on_rm_error)
        else:
            return True
    
    print("\n[1/5] 鍏嬮殕 ComfyUI...")
    ok = git_clone_with_mirrors(COMFYUI_REPO_PATH, COMFYUI_DIR)
    if not ok:
        print("[鉁梋 ComfyUI 鍏嬮殕澶辫触, 鎵€鏈夐暅鍍忔簮鍧囦笉鍙敤")
        return False
    
    # 瀹夎ComfyUI渚濊禆 (浣跨敤鍥藉唴pip闀滃儚)
    print("\n[2/5] 瀹夎 ComfyUI 渚濊禆 (浣跨敤娓呭崕闀滃儚)...")
    req_file = COMFYUI_DIR / "requirements.txt"
    if req_file.exists():
        run_cmd([PYTHON_EXE, "-m", "pip", "install", "-r", str(req_file)] + PIP_INDEX_ARGS,
                desc="瀹夎ComfyUI Python渚濊禆 (娓呭崕闀滃儚)", timeout=600)
    
    return True


def install_comfyui_manager():
    """瀹夎 ComfyUI-Manager 鑺傜偣绠＄悊鍣?""
    manager_dir = CUSTOM_NODES_DIR / "ComfyUI-Manager"
    
    if manager_dir.exists() and (manager_dir / "__init__.py").exists():
        print(f"[鉁揮 ComfyUI-Manager 宸插畨瑁? {manager_dir}")
        return True
    
    print("\n[3/5] 瀹夎 ComfyUI-Manager (鑺傜偣绠＄悊鍣?...")
    CUSTOM_NODES_DIR.mkdir(parents=True, exist_ok=True)
    ok = git_clone_with_mirrors(COMFYUI_MANAGER_REPO_PATH, manager_dir)
    
    if ok:
        req_file = manager_dir / "requirements.txt"
        if req_file.exists():
            run_cmd([PYTHON_EXE, "-m", "pip", "install", "-r", str(req_file)] + PIP_INDEX_ARGS,
                    desc="瀹夎ComfyUI-Manager渚濊禆 (娓呭崕闀滃儚)", timeout=300)
    
    return ok


def install_qwenvl_node():
    """瀹夎 QwenVL 鑷畾涔夎妭鐐?""
    qwenvl_dir = CUSTOM_NODES_DIR / "ComfyUI-QwenVL"
    
    # 妫€鏌ユ槸鍚︽湁鏁堝畨瑁?(鐩綍瀛樺湪涓旀湁Python鏂囦欢)
    if qwenvl_dir.exists():
        py_files = list(qwenvl_dir.glob("*.py"))
        if py_files:
            print(f"[鉁揮 ComfyUI-QwenVL 鑺傜偣宸插畨瑁?({len(py_files)} 涓狿ython鏂囦欢)")
            return True
        else:
            print(f"[!] QwenVL 鐩綍瀛樺湪浣嗕负绌? 閲嶆柊瀹夎...")
            shutil.rmtree(qwenvl_dir)
    
    print("\n[4/5] 瀹夎 ComfyUI-QwenVL 鑺傜偣...")
    CUSTOM_NODES_DIR.mkdir(parents=True, exist_ok=True)
    
    for repo_path in QWENVL_REPOS:
        ok = git_clone_with_mirrors(repo_path, qwenvl_dir)
        if ok:
            req_file = qwenvl_dir / "requirements.txt"
            if req_file.exists():
                run_cmd([PYTHON_EXE, "-m", "pip", "install", "-r", str(req_file)] + PIP_INDEX_ARGS,
                        desc="瀹夎QwenVL鑺傜偣渚濊禆 (娓呭崕闀滃儚)", timeout=300)
            return True
        else:
            if qwenvl_dir.exists():
                shutil.rmtree(qwenvl_dir)
    
    print("[!] QwenVL 鑺傜偣瀹夎澶辫触")
    print("[!] 浣犲彲浠ョ◢鍚庡湪 ComfyUI-Manager 涓€氳繃鐣岄潰鎵嬪姩瀹夎")
    return False


def download_file_direct(local_path, url, desc, min_bytes=1024, max_retries=5, exp_size=0):
    """Download with Range header resume, VPN-node-safe."""
    import urllib.request, ssl, time
    
    local_path = Path(local_path)
    local_path.parent.mkdir(parents=True, exist_ok=True)
    
    for attempt in range(1, max_retries + 1):
        if attempt > 1:
            time.sleep(attempt * 10)
        
        existing = local_path.stat().st_size if local_path.exists() else 0
        if existing > min_bytes * 0.95:
            print(f"  [OK] Already complete: {local_path.name} ({existing/(1024**3):.1f}GB)")
            return True
        
        headers = {"User-Agent": "ComfyUI-Setup/1.0"}
        if existing > 1024:
            headers["Range"] = f"bytes={existing}-"
            print(f"  [..] Resuming from {existing/(1024**3):.1f}GB...")
        
        print(f"  [>>] ({attempt}/{max_retries}) {desc}")
        try:
            ctx = ssl.create_default_context()
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, context=ctx, timeout=120) as resp:
                mode = "ab" if existing > 1024 else "wb"
                total = int(resp.headers.get("Content-Length", 0)) + existing
                downloaded = existing
                with open(local_path, mode) as f:
                    while True:
                        chunk = resp.read(8*1024*1024)
                        if not chunk: break
                        f.write(chunk)
                        downloaded += len(chunk)
                        if total > 0:
                            pct = min(downloaded/total*100, 100)
                            print(f"\r       {downloaded/(1024**3):.1f}/{total/(1024**3):.1f}GB ({pct:.0f}%)", end="")
                print()
            # exp_size passed from caller
            if exp_size > 0 and local_path.stat().st_size == exp_size:
                return True
        except urllib.error.HTTPError as e:
            if e.code == 416:
                return True
            print(f"\n  [!] HTTP {e.code}")
            break
        except Exception as e:
            print(f"\n  [!] {e}")
    return False


def get_zimage_sizes(repo_id):
    """Fetch official file sizes from HuggingFace API."""
    import urllib.request, json
    try:
        url = f"https://huggingface.co/api/models/{repo_id}?expand[]=siblings"
        req = urllib.request.Request(url, headers={"User-Agent": "setup/1.0"})
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.load(resp)
        return {s["rfilename"]: s.get("size", 0) for s in data.get("siblings", [])}
    except Exception as e:
        print(f"  [!] Cannot fetch sizes: {e}")
        return {}

def download_zimage_model(variant="bf16"):
    from pathlib import Path
    """Download Z-Image Turbo - direct URL with Range resume, VPN-node-safe."""
    import time
    from urllib import request, error
    import ssl
    
    # Try huggingface_hub first for faster downloads, fall back to direct
    try:
        from huggingface_hub import hf_hub_download
        HAS_HF = True
    except ImportError:
        HAS_HF = False
    
    model_files = ZIMAGE_FILES.get(variant, ZIMAGE_FILES["bf16"])
    all_files = dict(**model_files["files"], **ZIMAGE_COMMON_FILES)
    
    expected = get_zimage_sizes(ZIMAGE_REPO)
    print(f"\n[5/5] Download Z-Image Turbo ({variant.upper()})...")
    if expected:
        print(f"  [i] Got {len(expected)} file sizes from API")
    print(f"  [i] {model_files['desc']}")
    total_gb = sum(26 if "diffusion" in k else 4 if "text_encoder" in k else 0.3 for k in all_files)
    print(f"  [i] Total ~{total_gb:.0f}GB (resume-safe across VPN changes)")
    print()
    
    done_marker = MODELS_DIR / ".zimage_download_done.txt"
    completed = set(done_marker.read_text("utf-8").strip().split("\n")) if done_marker.exists() else set()
    
    all_ok = True
    
    for local_name, remote_name in all_files.items():
        marker_key = local_name
        local_path = MODELS_DIR / local_name
        local_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Expected sizes per file type
        if "diffusion" in local_name or "bf16" in local_name or "fp8" in local_name:
            min_bytes = 10 * 1024**3  # ~10GB for UNET
        elif "text_encoder" in local_name or "qwen" in local_name.lower() or "clip" in local_name.lower():
            min_bytes = 3 * 1024**3   # ~3GB for CLIP
        else:
            min_bytes = 200 * 1024**2  # ~200MB for VAE
        
        exp_size = expected.get(remote_name, 0)
        if marker_key in completed and local_path.exists() and exp_size > 0 and local_path.stat().st_size == exp_size:
            print(f"  [OK] Already downloaded: {local_name}")
            continue
        
        # Direct URL
        url = f"https://huggingface.co/{ZIMAGE_REPO}/resolve/main/{remote_name}?download=true"
        
        success = download_file_direct(local_path, url, remote_name, min_bytes, exp_size=exp_size)
        
        if not success and HAS_HF:
            print("  [..] Direct failed, trying huggingface_hub...")
            for attempt in range(1, 4):
                if attempt > 1: time.sleep(attempt * 10)
                try:
                    hf_hub_download(ZIMAGE_REPO, remote_name, local_dir=str(MODELS_DIR))
                    if local_path.exists() and exp_size > 0 and local_path.stat().st_size == exp_size:
                        success = True
                        break
                except Exception as e:
                    print(f"  [!] HF: {e}")
        
        if success:
            sz = local_path.stat().st_size / (1024**3)
            print(f"  [OK] Done: {local_name} ({sz:.1f}GB)")
            completed.add(marker_key)
            done_marker.write_text("\n".join(sorted(completed)), "utf-8")
        else:
            all_ok = False
            print(f"  [FAIL] {local_name} after all attempts")
            print(f"         Manual: https://huggingface.co/{ZIMAGE_REPO}/blob/main/{remote_name}")
    
    if all_ok:
        print(f"\n  [OK] All {len(all_files)} files downloaded!")
        Path(done_marker).unlink(missing_ok=True)
    else:
        print(f"\n  [WARN] Some files failed. Re-run setup to resume.")
def download_qwen_models():
    """Download Qwen LLM/VL models with resume support."""
    from huggingface_hub import snapshot_download
    import time

    print(f"\n--- Download Qwen LLM/VL Models ---")
    all_ok = True

    for name, cfg in QWEN_MODELS.items():
        target = MODELS_DIR / cfg["target_dir"] / name
        if target.exists() and any(target.iterdir()):
            total = sum(f.stat().st_size for f in target.rglob("*") if f.is_file()) / 1e9
            print(f"  [OK] {name}: already exists ({total:.1f}GB)")
            continue

        print(f"  [>>] {name} - {cfg['desc']}")
        print(f"       Repo: {cfg['repo_id']}")
        target.mkdir(parents=True, exist_ok=True)

        max_retries = 3
        success = False
        for attempt in range(1, max_retries + 1):
            if attempt > 1:
                wait = attempt * 10
                print(f"  [..] Retry {attempt}/{max_retries} in {wait}s...")
                time.sleep(wait)
            try:
                snapshot_download(
                    repo_id=cfg["repo_id"],
                    local_dir=str(target),
                    etag_timeout=30,
                )
                total = sum(f.stat().st_size for f in target.rglob("*") if f.is_file()) / 1e9
                print(f"  [OK] {name} ({total:.1f}GB)")
                success = True
                break
            except Exception as e:
                print(f"  [!] {type(e).__name__}: {e}")

        if not success:
            all_ok = False
            print(f"  [FAIL] {name}")
            print(f"         Run setup again to resume or download manually from: https://huggingface.co/{cfg['repo_id']}")

    if all_ok:
        print(f"  [OK] All Qwen models ready")
    return all_ok

def main():
    print_banner("ComfyUI + Z-Image Turbo + QwenVL 鏁村悎鍖匼n鍥藉唴闀滃儚浼樺寲鐗?)
    
    print(f"Python: {PYTHON_EXE}")
    print(f"瀹夎鐩綍: {BASE_DIR}")
    print(f"HF闀滃儚: {HF_MIRROR}")
    print(f"pip闀滃儚: {PIP_MIRROR}")
    print()
    
    # 閫夋嫨妯″瀷鐗堟湰
    print("璇烽€夋嫨 Z-Image Turbo 妯″瀷鐗堟湰:")
    print("  [1] BF16 鐗堟湰 - 绮惧害鏇撮珮, 鎺ㄨ崘16G+鏄惧瓨 (~12GB)")
    print("  [2] FP8 鐗堟湰 - 鏄惧瓨鍗犵敤灏? 閫傚悎8-12G鏄惧瓨 (~6GB)")
    print("  [3] 璺宠繃妯″瀷涓嬭浇 (鎵嬪姩涓嬭浇)")
    
    choice = input("\n璇疯緭鍏ラ€夐」 (1/2/3): ").strip()
    variant_map = {"1": "bf16", "2": "fp8", "3": None}
    variant = variant_map.get(choice, "fp8")
    
    # 鎵ц瀹夎姝ラ
    steps = [
        ("瀹夎 ComfyUI", install_comfyui),
        ("瀹夎 ComfyUI-Manager", install_comfyui_manager),
        ("瀹夎 QwenVL 鑺傜偣", install_qwenvl_node),
        (f"涓嬭浇 Qwen LLM/VL 妯″瀷 (~13GB)" if variant else "璺宠繃 Qwen 妯″瀷涓嬭浇",
         lambda: download_qwen_models() if variant else True),
        (f"涓嬭浇 Z-Image Turbo 妯″瀷 ({variant.upper()})" if variant else "璺宠繃妯″瀷涓嬭浇",
         lambda: download_zimage_model(variant) if variant else True),
        ("閰嶇疆妯″瀷璺緞", setup_model_config),
        ("淇濆瓨宸ヤ綔娴佹枃浠?, lambda: save_workflows() or True),
    ]
    
    results = {}
    for step_name, step_fn in steps:
        print(f"\n{'鈹€'*50}")
        print(f">> {step_name}")
        print(f"{'鈹€'*50}")
        try:
            results[step_name] = step_fn()
        except Exception as e:
            print(f"[鉁梋 寮傚父: {e}")
            results[step_name] = False
    
    # 杈撳嚭缁撴灉
    print_banner("瀹夎缁撴灉姹囨€?, style="single")
    for name, ok in results.items():
        status = "[OK]" if ok else "[!!]"
        print(f"  {status} {name}")
    
    # 鎵嬪姩涓嬭浇鎻愮ず
    if variant and not results.get(f"涓嬭浇 Z-Image Turbo 妯″瀷 ({variant.upper()})", False):
        model_info = ZIMAGE_MODELS[variant]
        print(f"""
{'='*60}
[!] 妯″瀷涓嬭浇澶辫触锛岃鎵嬪姩涓嬭浇:
    HF闀滃儚: {HF_MIRROR}/{model_info['repo']}/resolve/main/{model_info['file']}
    HF鍘熺珯: https://huggingface.co/{model_info['repo']}/resolve/main/{model_info['file']}
    
    鏀剧疆鍒? {CHECKPOINT_DIR / model_info['name']}
{'='*60}""")
    
    # 瀹屾垚
    print_banner(f"""瀹夎瀹屾垚!
鍚姩: 鍙屽嚮 start.bat 鎴栧湪缁堢杩愯:
  cd {COMFYUI_DIR}
  python main.py
鐒跺悗鎵撳紑 http://127.0.0.1:8188""")


if __name__ == "__main__":
    main()

