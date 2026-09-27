# -*- coding: utf-8 -*-
"""
MiniMax H3 (ComfyUI 量化版) 一键下载脚本

数据源：魔搭 ModelScope（Comfy-Org/MiniMax-H3），国内直连速度快，支持断点续传。
模型目录：ComfyUI/models/{diffusion_models,text_encoders,vae}

用法：
    python install_minimax_h3.py            # 下载 FL2VA 全家桶（文生视频/首尾帧，约 42.5 GB）
    python install_minimax_h3.py --ref2va   # 额外下载 Ref2VA 扩散模型（参考生成，+20 GB）
"""

import argparse
import os
import sys
import time
import urllib.request
import urllib.error

REPO = "Comfy-Org/MiniMax-H3"
REVISION = "master"
BASE_URL = f"https://modelscope.cn/models/{REPO}/resolve/{REVISION}/"

# (模型相对路径, 期望字节大小)
FILES_FL2VA = [
    ("diffusion_models/minimax_h3_fl2va_pruned_int8_convrot.safetensors", 20_970_379_616),
    ("text_encoders/qwen3vl_32b_minimax_h3_nvfp4_awq.safetensors", 15_687_142_551),
    ("vae/minimax_h3_video_vae_fp16.safetensors", 5_207_808_496),
    ("vae/minimax_h3_audio_vae_fp32.safetensors", 605_254_808),
]
FILES_REF2VA = [
    ("diffusion_models/minimax_h3_ref2va_pruned_int8_convrot.safetensors", 20_970_379_616),
]

CHUNK = 1024 * 1024  # 1 MiB


def models_dir():
    here = os.path.dirname(os.path.abspath(__file__))
    return os.path.normpath(os.path.join(here, "..", "ComfyUI", "models"))


def free_space_gb(path):
    try:
        import shutil
        return shutil.disk_usage(path).free / (1024 ** 3)
    except Exception:
        return None


def human(n):
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if n < 1024 or unit == "TB":
            return f"{n:.2f} {unit}"
        n /= 1024


def download_file(url, dest, expected_size):
    os.makedirs(os.path.dirname(dest), exist_ok=True)
    part = dest + ".part"
    resume = os.path.getsize(part) if os.path.exists(part) else 0

    if os.path.exists(dest) and os.path.getsize(dest) == expected_size:
        print(f"[跳过] 已存在且完整: {os.path.basename(dest)}")
        return True

    headers = {"User-Agent": "Mozilla/5.0 (compatible; MiniMax-H3-Setup)"}
    if resume:
        headers["Range"] = f"bytes={resume}-"

    req = urllib.request.Request(url, headers=headers)
    try:
        resp = urllib.request.urlopen(req, timeout=60)
    except urllib.error.HTTPError as e:
        if e.code in (416,):  # 已下载完成但目标文件缺失，重来
            resume = 0
            req = urllib.request.Request(url, headers={"User-Agent": headers["User-Agent"]})
            resp = urllib.request.urlopen(req, timeout=60)
        else:
            print(f"[失败] HTTP {e.code}: {url}")
            return False

    total = int(resp.headers.get("Content-Length") or 0) + resume
    if resp.status == 200:
        resume = 0  # 服务器不支持断点，从头下
        total = int(resp.headers.get("Content-Length") or expected_size)

    mode = "ab" if resume else "wb"
    start = time.time()
    last_print = time.time()
    with open(part, mode) as f:
        while True:
            chunk = resp.read(CHUNK)
            if not chunk:
                break
            f.write(chunk)
            now = time.time()
            if now - last_print > 2:
                done = os.path.getsize(part)
                speed = done / max(now - start, 0.001)
                pct = done * 100 / max(expected_size, 1)
                print(f"\r  {os.path.basename(dest)}: {human(done)} / {human(expected_size)} ({pct:.1f}%)  {human(speed)}/s", end="", flush=True)
                last_print = now
    resp.close()

    done = os.path.getsize(part)
    print()
    if done == expected_size:
        os.replace(part, dest)
        print(f"[完成] {os.path.basename(dest)} ({human(expected_size)})")
        return True
    print(f"[中断] 已下载 {human(done)}/{human(expected_size)}，可重新运行本脚本续传")
    return False


def main():
    parser = argparse.ArgumentParser(description="MiniMax H3 模型下载（魔搭源，断点续传）")
    parser.add_argument("--ref2va", action="store_true", help="额外下载 Ref2VA 扩散模型")
    args = parser.parse_args()

    mdl = models_dir()
    print(f"模型目录: {mdl}")
    free = free_space_gb(mdl)
    if free is not None:
        need = (sum(s for _, s in FILES_FL2VA) + sum(s for _, s in FILES_REF2VA)) / (1024 ** 3)
        need_show = need if args.ref2va else sum(s for _, s in FILES_FL2VA) / (1024 ** 3)
        print(f"剩余空间: {free:.1f} GB，需要约 {need_show:.1f} GB" + ("（含 Ref2VA）" if args.ref2va else ""))
        if free < need_show + 10:
            print("[警告] 剩余空间不足，可能下载失败！")

    ok = True
    for rel, size in FILES_FL2VA:
        ok &= download_file(BASE_URL + rel, os.path.join(mdl, rel), size)
    if args.ref2va:
        for rel, size in FILES_REF2VA:
            ok &= download_file(BASE_URL + rel, os.path.join(mdl, rel), size)

    print()
    print("全部完成！" if ok else "有文件未完成，请重新运行脚本续传。")
    print("启动 ComfyUI 后，在模板库 Video 分类可直接加载 MiniMax H3 工作流；")
    print("或使用 h3WorkFlows/ 目录下的适配工作流。")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
