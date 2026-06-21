#!/usr/bin/env python3
"""QwenVL Image Variation Generator."""

import json, time, urllib.request, urllib.parse, uuid, os, sys, argparse
import http.client, mimetypes
from pathlib import Path
from datetime import datetime

COMFYUI_URL = "http://127.0.0.1:8188"

def api_request(method, endpoint, data=None):
    url = COMFYUI_URL + endpoint
    if data is not None:
        data = json.dumps(data).encode("utf-8")
    req = urllib.request.Request(url, data=data, method=method)
    req.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(req, timeout=300) as resp:
            return json.loads(resp.read())
    except Exception as e:
        print(f"  API error: {e}")
        return None

def queue_prompt(workflow):
    payload = {"prompt": workflow, "client_id": "qwenvl_script"}
    result = api_request("POST", "/prompt", payload)
    return result.get("prompt_id") if result else None

def get_history(prompt_id):
    return api_request("GET", f"/history/{prompt_id}")

def wait_for_prompt(prompt_id, timeout=600):
    start = time.time()
    while time.time() - start < timeout:
        history = get_history(prompt_id)
        if history and prompt_id in history:
            outputs = history[prompt_id].get("outputs", {})
            images = []
            for node_id, node_output in outputs.items():
                for img in node_output.get("images", []):
                    images.append({
                        "filename": img["filename"],
                        "subfolder": img.get("subfolder", ""),
                        "type": img.get("type", "output")
                    })
            if images:
                return images
        time.sleep(3)
    return None

def download_image(img_info, save_path):
    params = urllib.parse.urlencode({
        "filename": img_info["filename"],
        "subfolder": img_info["subfolder"],
        "type": img_info["type"]
    })
    url = COMFYUI_URL + "/view?" + params
    try:
        urllib.request.urlretrieve(url, str(save_path))
        return True
    except Exception as e:
        print(f"  Download failed: {e}")
        return False

def upload_image(image_path):
    boundary = str(uuid.uuid4())
    filename = os.path.basename(image_path)
    parts = []
    parts.append(("--" + boundary).encode())
    parts.append(f'Content-Disposition: form-data; name="image"; filename="{filename}"'.encode())
    mime = mimetypes.guess_type(filename)[0] or "image/png"
    parts.append(("Content-Type: " + mime).encode())
    parts.append(b"")
    with open(image_path, "rb") as f:
        parts.append(f.read())
    parts.append(("--" + boundary + "--").encode())
    parts.append(b"")
    body_data = b"\r\n".join(parts)
    conn = http.client.HTTPConnection("127.0.0.1", 8188, timeout=30)
    conn.request("POST", "/upload/image", body_data,
                 {"Content-Type": f"multipart/form-data; boundary={boundary}"})
    resp = conn.getresponse()
    result = json.loads(resp.read())
    conn.close()
    img_name = result.get("name") or result.get("filename")
    print(f"  Uploaded: {img_name}")
    return img_name

def load_workflow_json(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def build_workflow(input_image_name, workflow_path):
    wf = load_workflow_json(workflow_path)
    for node in wf["nodes"]:
        if node["id"] == 10:
            node["widgets_values"][0] = input_image_name
    return wf

def mode_single(input_path, seed=None):
    print(f"Mode: Single-pass | Input: {input_path}")
    script_dir = Path(__file__).parent.parent
    output_dir = script_dir / "outputs" / "qwenvl_variations"
    output_dir.mkdir(parents=True, exist_ok=True)
    wf_dir = script_dir / "workflows"
    wf_path = wf_dir / "zimage_turbo_qwenvl_analyze_gen.json"

    print("[1/4] Uploading...")
    img_name = upload_image(input_path)
    if not img_name:
        return None

    print("[2/4] Submitting...")
    wf = build_workflow(img_name, wf_path)
    if seed:
        for node in wf["nodes"]:
            if node["id"] == 7:
                node["widgets_values"][0] = seed
    prompt_id = queue_prompt(wf)
    if not prompt_id:
        return None

    print("[3/4] Generating...")
    images = wait_for_prompt(prompt_id)
    if not images:
        return None

    print("[4/4] Saving...")
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    saved = []
    for i, img in enumerate(images):
        save_path = output_dir / f"variation_{stamp}_{i+1:02d}.png"
        if download_image(img, save_path):
            print(f"  Saved: {save_path}")
            saved.append(save_path)
    print(f"Done: {len(saved)} image(s)")
    return saved

def mode_refine(input_path, rounds=3, denoise=0.55):
    print(f"Mode: Refine ({rounds} rounds) | Input: {input_path}")
    script_dir = Path(__file__).parent.parent
    output_dir = script_dir / "outputs" / "qwenvl_variations"
    output_dir.mkdir(parents=True, exist_ok=True)
    wf_dir = script_dir / "workflows"
    wf_path = wf_dir / "zimage_turbo_qwenvl_analyze_gen.json"
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    current_image = Path(input_path)
    history = []

    for rnd in range(1, rounds + 1):
        print(f"Round {rnd}/{rounds}")
        img_name = upload_image(str(current_image))
        if not img_name:
            break
        wf = build_workflow(img_name, wf_path)
        for node in wf["nodes"]:
            if node["id"] == 7:
                node["widgets_values"][0] = rnd * 7777 + 12345
                if rnd > 1:
                    node["widgets_values"][6] = denoise
        prompt_id = queue_prompt(wf)
        if not prompt_id:
            break
        images = wait_for_prompt(prompt_id)
        if not images:
            break
        save_path = output_dir / f"refine_r{rnd:02d}_{stamp}.png"
        if download_image(images[0], save_path):
            print(f"  Saved: {save_path}")
            history.append({"round": rnd, "path": str(save_path)})
            current_image = save_path
        else:
            break
    print(f"Done: {len(history)} round(s)")
    return history

def mode_batch(input_dir, pattern="*.png"):
    input_path = Path(input_dir)
    images = sorted(input_path.glob(pattern))
    print(f"Mode: Batch | {len(images)} images")
    results = []
    for i, img_path in enumerate(images, 1):
        print(f"[{i}/{len(images)}] {img_path.name}")
        saved = mode_single(str(img_path))
        if saved:
            results.append({"input": str(img_path), "outputs": [str(p) for p in saved]})
    return results

def main():
    parser = argparse.ArgumentParser(description="QwenVL Image Variation Generator")
    parser.add_argument("--mode", "-m", choices=["single", "refine", "batch"], default="single")
    parser.add_argument("--input", "-i", required=True)
    parser.add_argument("--rounds", "-r", type=int, default=3)
    parser.add_argument("--denoise", "-d", type=float, default=0.55)
    parser.add_argument("--seed", "-s", type=int, default=None)
    parser.add_argument("--pattern", "-p", default="*.png")
    parser.add_argument("--url", default="http://127.0.0.1:8188")
    args = parser.parse_args()

    global COMFYUI_URL
    COMFYUI_URL = args.url
    if api_request("GET", "/system_stats") is None:
        print("Cannot reach ComfyUI. Start with start.bat first.")
        sys.exit(1)

    if args.mode == "single":
        mode_single(args.input, args.seed)
    elif args.mode == "refine":
        mode_refine(args.input, args.rounds, args.denoise)
    elif args.mode == "batch":
        mode_batch(args.input, args.pattern)

if __name__ == "__main__":
    main()