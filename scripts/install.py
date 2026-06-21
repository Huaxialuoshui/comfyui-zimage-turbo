#!/usr/bin/env python3
"""
ComfyUI + Z-Image Turbo + QwenVL 整合包安装脚本 (国内镜像优化版)
基于知乎文档：ComfyUI部署指南 - 本地AI绘图工作流
"""

import os
import sys
import subprocess
import shutil
import json
from pathlib import Path

# ========== 配置区 ==========
BASE_DIR = Path(__file__).parent.parent.resolve()
COMFYUI_DIR = BASE_DIR / "ComfyUI"
MODELS_DIR = COMFYUI_DIR / "models"
CHECKPOINT_DIR = MODELS_DIR / "checkpoints"
CUSTOM_NODES_DIR = COMFYUI_DIR / "custom_nodes"
PYTHON_EXE = sys.executable

# ---- GitHub 镜像源 (国内加速) ----
GITHUB_MIRRORS = [""]  # VPN直连

# ComfyUI 官方仓库
COMFYUI_REPO_PATH = "comfyanonymous/ComfyUI.git"
COMFYUI_MANAGER_REPO_PATH = "ltdrdata/ComfyUI-Manager.git"

# QwenVL 节点仓库 (多个备选)
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


def run_cmd(cmd, cwd=None, desc="", timeout=300):
    """运行命令并实时输出"""
    print(f"\n{'='*60}")
    print(f">>> {desc}")
    print(f">>> {' '.join(cmd) if isinstance(cmd, list) else cmd}")
    print(f"{'='*60}")
    try:
        result = subprocess.run(cmd, cwd=cwd, shell=isinstance(cmd, str), timeout=timeout)
        if result.returncode != 0:
            print(f"  [!] 命令返回非零退出码 {result.returncode}")
        return result.returncode == 0
    except subprocess.TimeoutExpired:
        print(f"  [!] 命令超时 ({timeout}s)")
        return False
    except Exception as e:
        print(f"  [!] 命令执行异常: {e}")
        return False


def git_clone_with_mirrors(repo_path, target_dir):
    """通过多个镜像源尝试克隆 GitHub 仓库"""
    if target_dir.exists():
        shutil.rmtree(target_dir)
    
    target_dir.parent.mkdir(parents=True, exist_ok=True)
    
    for mirror in GITHUB_MIRRORS:
        if mirror:
            url = f"{mirror}https://github.com/{repo_path}"
        else:
            url = f"https://github.com/{repo_path}"
        
        print(f"    尝试: {url}")
        ok = run_cmd(["git", "clone", url, str(target_dir)], 
                     desc=f"克隆 {repo_path}", timeout=120)
        if ok:
            print(f"    [✓] 克隆成功!")
            return True
        else:
            if target_dir.exists():
                shutil.rmtree(target_dir)
            print(f"    [✗] 失败, 尝试下一个镜像...")
    
    return False


def install_comfyui():
    """安装 ComfyUI"""
    if COMFYUI_DIR.exists():
        print(f"[✓] ComfyUI 目录已存在: {COMFYUI_DIR}")
        choice = input("是否重新安装? (y/N): ").strip().lower()
        if choice == "y":
            print("  [*] Deleting old ComfyUI...")
            def on_rm_error(func, path, exc_info):
                import stat
                os.chmod(path, stat.S_IWRITE)
                func(path)
            shutil.rmtree(COMFYUI_DIR, onerror=on_rm_error)
        else:
            return True
    
    print("\n[1/5] 克隆 ComfyUI...")
    ok = git_clone_with_mirrors(COMFYUI_REPO_PATH, COMFYUI_DIR)
    if not ok:
        print("[✗] ComfyUI 克隆失败, 所有镜像源均不可用")
        return False
    
    # 安装ComfyUI依赖 (使用国内pip镜像)
    print("\n[2/5] 安装 ComfyUI 依赖 (使用清华镜像)...")
    req_file = COMFYUI_DIR / "requirements.txt"
    if req_file.exists():
        run_cmd([PYTHON_EXE, "-m", "pip", "install", "-r", str(req_file)] + PIP_INDEX_ARGS,
                desc="安装ComfyUI Python依赖 (清华镜像)", timeout=600)
    
    return True


def install_comfyui_manager():
    """安装 ComfyUI-Manager 节点管理器"""
    manager_dir = CUSTOM_NODES_DIR / "ComfyUI-Manager"
    
    if manager_dir.exists() and (manager_dir / "__init__.py").exists():
        print(f"[✓] ComfyUI-Manager 已安装: {manager_dir}")
        return True
    
    print("\n[3/5] 安装 ComfyUI-Manager (节点管理器)...")
    CUSTOM_NODES_DIR.mkdir(parents=True, exist_ok=True)
    ok = git_clone_with_mirrors(COMFYUI_MANAGER_REPO_PATH, manager_dir)
    
    if ok:
        req_file = manager_dir / "requirements.txt"
        if req_file.exists():
            run_cmd([PYTHON_EXE, "-m", "pip", "install", "-r", str(req_file)] + PIP_INDEX_ARGS,
                    desc="安装ComfyUI-Manager依赖 (清华镜像)", timeout=300)
    
    return ok


def install_qwenvl_node():
    """安装 QwenVL 自定义节点"""
    qwenvl_dir = CUSTOM_NODES_DIR / "ComfyUI-QwenVL"
    
    # 检查是否有效安装 (目录存在且有Python文件)
    if qwenvl_dir.exists():
        py_files = list(qwenvl_dir.glob("*.py"))
        if py_files:
            print(f"[✓] ComfyUI-QwenVL 节点已安装 ({len(py_files)} 个Python文件)")
            return True
        else:
            print(f"[!] QwenVL 目录存在但为空, 重新安装...")
            shutil.rmtree(qwenvl_dir)
    
    print("\n[4/5] 安装 ComfyUI-QwenVL 节点...")
    CUSTOM_NODES_DIR.mkdir(parents=True, exist_ok=True)
    
    for repo_path in QWENVL_REPOS:
        ok = git_clone_with_mirrors(repo_path, qwenvl_dir)
        if ok:
            req_file = qwenvl_dir / "requirements.txt"
            if req_file.exists():
                run_cmd([PYTHON_EXE, "-m", "pip", "install", "-r", str(req_file)] + PIP_INDEX_ARGS,
                        desc="安装QwenVL节点依赖 (清华镜像)", timeout=300)
            return True
        else:
            if qwenvl_dir.exists():
                shutil.rmtree(qwenvl_dir)
    
    print("[!] QwenVL 节点安装失败")
    print("[!] 你可以稍后在 ComfyUI-Manager 中通过界面手动安装")
    return False


def download_zimage_model(variant="bf16"):
    """Download Z-Image Turbo from Comfy-Org (split format)"""
    model_files = ZIMAGE_FILES.get(variant, ZIMAGE_FILES["bf16"])
    
    print(f"\n[5/5] Download Z-Image Turbo ({variant.upper()})...")
    print(f"  [i] {model_files['desc']}")
    print(f"  [i] Repo: {ZIMAGE_REPO}")
    print(f"  [i] Format: ComfyUI split_files (diffusion_model + text_encoder + VAE)")
    print(f"  [!] Total ~10-15GB, please wait...")
    
    from huggingface_hub import hf_hub_download
    
    all_ok = True
    
    for local_name, remote_name in model_files["files"].items():
        local_path = MODELS_DIR / local_name
        if local_path.exists():
            sz = local_path.stat().st_size / (1024**3)
            print(f"  [OK] Exists: {local_name} ({sz:.1f}GB)")
            continue
        local_path.parent.mkdir(parents=True, exist_ok=True)
        print(f"  [>>] {remote_name}")
        try:
            hf_hub_download(repo_id=ZIMAGE_REPO, filename=remote_name, local_dir=str(MODELS_DIR), local_dir_use_symlinks=False)
            # Move from split_files/ to correct dir if needed
            import shutil as _shutil
            split_path = MODELS_DIR / remote_name
            target_path = MODELS_DIR / local_name
            if split_path.exists() and split_path != target_path:
                target_path.parent.mkdir(parents=True, exist_ok=True)
                _shutil.move(str(split_path), str(target_path))
                # Clean empty split_files dirs
                for _d in [MODELS_DIR / 'split_files' / 'diffusion_models', MODELS_DIR / 'split_files' / 'text_encoders', MODELS_DIR / 'split_files' / 'vae', MODELS_DIR / 'split_files']:
                    try: _d.rmdir()
                    except: pass
            print(f"  [OK] Done: {local_name}")
        except Exception as e:
            print(f"  [FAIL] {e}")
            all_ok = False
    
    for local_name, remote_name in ZIMAGE_COMMON_FILES.items():
        local_path = MODELS_DIR / local_name
        if local_path.exists():
            sz = local_path.stat().st_size / (1024**3)
            print(f"  [OK] Exists: {local_name} ({sz:.1f}GB)")
            continue
        local_path.parent.mkdir(parents=True, exist_ok=True)
        print(f"  [>>] {remote_name}")
        try:
            hf_hub_download(repo_id=ZIMAGE_REPO, filename=remote_name, local_dir=str(MODELS_DIR), local_dir_use_symlinks=False)
            # Move from split_files/ to correct dir if needed
            import shutil as _shutil
            split_path = MODELS_DIR / remote_name
            target_path = MODELS_DIR / local_name
            if split_path.exists() and split_path != target_path:
                target_path.parent.mkdir(parents=True, exist_ok=True)
                _shutil.move(str(split_path), str(target_path))
                # Clean empty split_files dirs
                for _d in [MODELS_DIR / 'split_files' / 'diffusion_models', MODELS_DIR / 'split_files' / 'text_encoders', MODELS_DIR / 'split_files' / 'vae', MODELS_DIR / 'split_files']:
                    try: _d.rmdir()
                    except: pass
            print(f"  [OK] Done: {local_name}")
        except Exception as e:
            print(f"  [FAIL] {e}")
            all_ok = False
    
    if not all_ok:
        print(f"\n[!] Manual download: https://huggingface.co/{ZIMAGE_REPO}")
    return all_ok

def setup_model_config():
    """创建 extra_model_paths.yaml 配置"""
    config_path = COMFYUI_DIR / "extra_model_paths.yaml"
    
    config_content = f"""# ComfyUI 模型路径配置
# 自动生成 by install.py

comfyui:
    base_path: {str(COMFYUI_DIR).replace(chr(92), '/')}
    checkpoints: models/checkpoints/
    clip: models/clip/
    clip_vision: models/clip_vision/
    configs: models/configs/
    controlnet: models/controlnet/
    embeddings: models/embeddings/
    loras: models/loras/
    upscale_models: models/upscale_models/
    vae: models/vae/
"""
    
    config_path.write_text(config_content, encoding="utf-8")
    print(f"[✓] 模型配置已创建: {config_path}")


def save_workflows():
    """保存 ComfyUI 工作流 JSON 文件"""
    workflows_dir = BASE_DIR / "workflows"
    workflows_dir.mkdir(parents=True, exist_ok=True)
    
    # 基础工作流
    workflow_basic = {
        "last_node_id": 7,
        "last_link_id": 8,
        "nodes": [
            {
                "id": 1, "type": "CheckpointLoaderSimple", "pos": [50, 100],
                "size": [315, 98], "flags": {}, "order": 0, "mode": 0,
                "outputs": [
                    {"name": "MODEL", "type": "MODEL", "links": [1], "slot_index": 0},
                    {"name": "CLIP", "type": "CLIP", "links": [2], "slot_index": 1},
                    {"name": "VAE", "type": "VAE", "links": [3], "slot_index": 2}
                ],
                "properties": {"Node name for S&R": "CheckpointLoaderSimple"},
                "widgets_values": ["z-image-turbo-fp8-aio.safetensors"]
            },
            {
                "id": 2, "type": "CLIPTextEncode", "pos": [50, 300],
                "size": [400, 200], "flags": {}, "order": 1, "mode": 0,
                "inputs": [{"name": "clip", "type": "CLIP", "link": 2}],
                "outputs": [{"name": "CONDITIONING", "type": "CONDITIONING", "links": [4], "slot_index": 0}],
                "title": "正面提示词 (Positive Prompt)",
                "widgets_values": ["masterpiece, best quality, 1girl, beautiful detailed eyes"]
            },
            {
                "id": 3, "type": "CLIPTextEncode", "pos": [50, 550],
                "size": [400, 200], "flags": {}, "order": 2, "mode": 0,
                "inputs": [{"name": "clip", "type": "CLIP", "link": 2}],
                "outputs": [{"name": "CONDITIONING", "type": "CONDITIONING", "links": [5], "slot_index": 0}],
                "title": "负面提示词 (Negative Prompt)",
                "widgets_values": ["lowres, bad anatomy, bad hands, text, error, missing fingers, worst quality"]
            },
            {
                "id": 4, "type": "EmptyLatentImage", "pos": [500, 100],
                "size": [315, 106], "flags": {}, "order": 3, "mode": 0,
                "outputs": [{"name": "LATENT", "type": "LATENT", "links": [6], "slot_index": 0}],
                "widgets_values": [1024, 1024, 1]
            },
            {
                "id": 5, "type": "KSampler", "pos": [500, 300],
                "size": [315, 262], "flags": {}, "order": 4, "mode": 0,
                "inputs": [
                    {"name": "model", "type": "MODEL", "link": 1},
                    {"name": "positive", "type": "CONDITIONING", "link": 4},
                    {"name": "negative", "type": "CONDITIONING", "link": 5},
                    {"name": "latent_image", "type": "LATENT", "link": 6}
                ],
                "outputs": [{"name": "LATENT", "type": "LATENT", "links": [7], "slot_index": 0}],
                "widgets_values": [123456789, "fixed", 4, 1.0, "euler", "simple", 0.0]
            },
            {
                "id": 6, "type": "VAEDecode", "pos": [900, 300],
                "size": [210, 46], "flags": {}, "order": 5, "mode": 0,
                "inputs": [
                    {"name": "samples", "type": "LATENT", "link": 7},
                    {"name": "vae", "type": "VAE", "link": 3}
                ],
                "outputs": [{"name": "IMAGE", "type": "IMAGE", "links": [8], "slot_index": 0}]
            },
            {
                "id": 7, "type": "PreviewImage", "pos": [900, 400],
                "size": [210, 246], "flags": {}, "order": 6, "mode": 0,
                "inputs": [{"name": "images", "type": "IMAGE", "link": 8}]
            }
        ],
        "links": [
            [1, 1, 0, 5, 0, "MODEL"], [2, 1, 1, 2, 0, "CLIP"], [3, 1, 2, 6, 1, "VAE"],
            [4, 2, 0, 5, 1, "CONDITIONING"], [5, 3, 0, 5, 2, "CONDITIONING"],
            [6, 4, 0, 5, 3, "LATENT"], [7, 5, 0, 6, 0, "LATENT"], [8, 6, 0, 7, 0, "IMAGE"]
        ],
        "groups": [], "config": {}, "version": 0.4,
        "extra": {"workflow": {"name": "Z-Image Turbo 基础文生图"}}
    }
    
    # QwenVL高级工作流
    workflow_qwenvl = {
        "last_node_id": 9,
        "last_link_id": 10,
        "nodes": [
            {
                "id": 1, "type": "CheckpointLoaderSimple", "pos": [50, 100],
                "size": [315, 98], "flags": {}, "order": 0, "mode": 0,
                "outputs": [
                    {"name": "MODEL", "type": "MODEL", "links": [1]},
                    {"name": "CLIP", "type": "CLIP", "links": [2]},
                    {"name": "VAE", "type": "VAE", "links": [3]}
                ],
                "widgets_values": ["z-image-turbo-fp8-aio.safetensors"]
            },
            {
                "id": 8, "type": "QwenVLTextEncode", "pos": [50, 250],
                "size": [400, 180], "flags": {}, "order": 1, "mode": 0,
                "inputs": [{"name": "clip", "type": "CLIP", "link": 2}],
                "outputs": [{"name": "CONDITIONING", "type": "CONDITIONING", "links": [10]}],
                "title": "QwenVL 提示词扩写 (输入关键词即可)",
                "widgets_values": [
                    "1girl, anime style, beautiful",
                    "Qwen/Qwen2-VL-2B-Instruct",
                    "You are a prompt expert. Expand these keywords into a detailed image generation prompt.",
                    "masterpiece, best quality"
                ]
            },
            {
                "id": 3, "type": "CLIPTextEncode", "pos": [50, 480],
                "size": [400, 150], "flags": {}, "order": 2, "mode": 0,
                "inputs": [{"name": "clip", "type": "CLIP", "link": 2}],
                "outputs": [{"name": "CONDITIONING", "type": "CONDITIONING", "links": [5]}],
                "title": "负面提示词",
                "widgets_values": ["lowres, bad anatomy, bad hands, text, error, missing fingers, worst quality"]
            },
            {
                "id": 4, "type": "EmptyLatentImage", "pos": [500, 100],
                "size": [315, 106], "flags": {}, "order": 3, "mode": 0,
                "outputs": [{"name": "LATENT", "type": "LATENT", "links": [6]}],
                "widgets_values": [1024, 1024, 1]
            },
            {
                "id": 5, "type": "KSampler", "pos": [500, 300],
                "size": [315, 262], "flags": {}, "order": 4, "mode": 0,
                "inputs": [
                    {"name": "model", "type": "MODEL", "link": 1},
                    {"name": "positive", "type": "CONDITIONING", "link": 10},
                    {"name": "negative", "type": "CONDITIONING", "link": 5},
                    {"name": "latent_image", "type": "LATENT", "link": 6}
                ],
                "outputs": [{"name": "LATENT", "type": "LATENT", "links": [7]}],
                "widgets_values": [123456789, "fixed", 4, 1.0, "euler", "simple", 0.0]
            },
            {
                "id": 6, "type": "VAEDecode", "pos": [900, 300],
                "size": [210, 46], "flags": {}, "order": 5, "mode": 0,
                "inputs": [
                    {"name": "samples", "type": "LATENT", "link": 7},
                    {"name": "vae", "type": "VAE", "link": 3}
                ],
                "outputs": [{"name": "IMAGE", "type": "IMAGE", "links": [8]}]
            },
            {
                "id": 7, "type": "PreviewImage", "pos": [900, 400],
                "size": [300, 300], "flags": {}, "order": 6, "mode": 0,
                "inputs": [{"name": "images", "type": "IMAGE", "link": 8}]
            },
            {
                "id": 9, "type": "SaveImage", "pos": [900, 750],
                "size": [315, 270], "flags": {}, "order": 7, "mode": 0,
                "inputs": [{"name": "images", "type": "IMAGE", "link": 8}],
                "widgets_values": ["ComfyUI"]
            }
        ],
        "links": [
            [1, 1, 0, 5, 0, "MODEL"], [2, 1, 1, 8, 0, "CLIP"], [3, 1, 2, 6, 1, "VAE"],
            [5, 3, 0, 5, 2, "CONDITIONING"], [6, 4, 0, 5, 3, "LATENT"],
            [7, 5, 0, 6, 0, "LATENT"], [8, 6, 0, 7, 0, "IMAGE"],
            [10, 8, 0, 5, 1, "CONDITIONING"]
        ],
        "groups": [], "config": {}, "version": 0.4,
        "extra": {"workflow": {"name": "Z-Image Turbo + QwenVL 提示词扩写"}}
    }
    
    basic_path = workflows_dir / "zimage_turbo_basic.json"
    with open(basic_path, "w", encoding="utf-8") as f:
        json.dump(workflow_basic, f, indent=2, ensure_ascii=False)
    print(f"[✓] 基础工作流: {basic_path}")
    
    qwenvl_path = workflows_dir / "zimage_turbo_qwenvl.json"
    with open(qwenvl_path, "w", encoding="utf-8") as f:
        json.dump(workflow_qwenvl, f, indent=2, ensure_ascii=False)
    print(f"[✓] QwenVL工作流: {qwenvl_path}")


def print_banner(text, style="double"):
    """打印装饰横幅"""
    lines = text.split("\n")
    width = max(len(l) for l in lines) + 4
    if style == "double":
        top = chr(0x2554) + chr(0x2550)*(width-2) + chr(0x2557)
        bot = chr(0x255A) + chr(0x2550)*(width-2) + chr(0x255D)
        mid = chr(0x2551)
    else:
        top = bot = "="*width
        mid = "|"
    print(top)
    for l in lines:
        print(f"{mid} {l.center(width-4)} {mid}")
    print(bot)


def main():
    print_banner("ComfyUI + Z-Image Turbo + QwenVL 整合包\n国内镜像优化版")
    
    print(f"Python: {PYTHON_EXE}")
    print(f"安装目录: {BASE_DIR}")
    print(f"HF镜像: {HF_MIRROR}")
    print(f"pip镜像: {PIP_MIRROR}")
    print()
    
    # 选择模型版本
    print("请选择 Z-Image Turbo 模型版本:")
    print("  [1] BF16 版本 - 精度更高, 推荐16G+显存 (~12GB)")
    print("  [2] FP8 版本 - 显存占用小, 适合8-12G显存 (~6GB)")
    print("  [3] 跳过模型下载 (手动下载)")
    
    choice = input("\n请输入选项 (1/2/3): ").strip()
    variant_map = {"1": "bf16", "2": "fp8", "3": None}
    variant = variant_map.get(choice, "fp8")
    
    # 执行安装步骤
    steps = [
        ("安装 ComfyUI", install_comfyui),
        ("安装 ComfyUI-Manager", install_comfyui_manager),
        ("安装 QwenVL 节点", install_qwenvl_node),
        (f"下载 Z-Image Turbo 模型 ({variant.upper()})" if variant else "跳过模型下载",
         lambda: download_zimage_model(variant) if variant else True),
        ("配置模型路径", setup_model_config),
        ("保存工作流文件", lambda: save_workflows() or True),
    ]
    
    results = {}
    for step_name, step_fn in steps:
        print(f"\n{'─'*50}")
        print(f">> {step_name}")
        print(f"{'─'*50}")
        try:
            results[step_name] = step_fn()
        except Exception as e:
            print(f"[✗] 异常: {e}")
            results[step_name] = False
    
    # 输出结果
    print_banner("安装结果汇总", style="single")
    for name, ok in results.items():
        status = "[OK]" if ok else "[!!]"
        print(f"  {status} {name}")
    
    # 手动下载提示
    if variant and not results.get(f"下载 Z-Image Turbo 模型 ({variant.upper()})", False):
        model_info = ZIMAGE_MODELS[variant]
        print(f"""
{'='*60}
[!] 模型下载失败，请手动下载:
    HF镜像: {HF_MIRROR}/{model_info['repo']}/resolve/main/{model_info['file']}
    HF原站: https://huggingface.co/{model_info['repo']}/resolve/main/{model_info['file']}
    
    放置到: {CHECKPOINT_DIR / model_info['name']}
{'='*60}""")
    
    # 完成
    print_banner(f"""安装完成!
启动: 双击 start.bat 或在终端运行:
  cd {COMFYUI_DIR}
  python main.py
然后打开 http://127.0.0.1:8188""")


if __name__ == "__main__":
    main()
