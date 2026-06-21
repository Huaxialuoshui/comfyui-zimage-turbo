#!/usr/bin/env python3
"""
10-Stage Iterative Storyboard Generator
Uses ComfyUI API to generate a visual narrative:
Stage 1: txt2img from keywords
Stages 2-10: img2img, each using previous stage output as input
"""

import json
import time
import urllib.request
import urllib.parse
import uuid
import os
import sys
from pathlib import Path

# ========== CONFIG ==========
COMFYUI_URL = "http://127.0.0.1:8188"
OUTPUT_DIR = Path(r"D:\A_Study\Image\comfyui-zimage-package\outputs\storyboard")
STAGES = 10

# Story keywords for each stage (QwenVL will expand these)
STAGE_PROMPTS = [
    "chinese girl, traditional red dress, standing alone in ancient temple courtyard, morning mist, peaceful atmosphere",
    "girl notices a glowing golden light behind the temple, curious expression, turning around, dust particles in light",
    "girl walking toward the golden light, stone path, cherry blossom petals falling, awe and wonder",
    "girl discovers hidden garden, magical glowing flowers, butterflies, water reflection, enchanted expression",
    "a spirit fox appears from the light, nine tails shimmering, girl reaches out hand, connection moment",
    "fox transforms into a young woman, elegant white dress, fox ears, they stand face to face, emotional encounter",
    "they walk together through the garden, holding hands, talking, warm golden sunset light, serene mood",
    "they reach a stone altar, ancient carvings glowing, mystical energy rising, dramatic composition",
    "the girl receives a magical jade pendant, blue energy swirling, tears of joy, close-up emotional shot",
    "farewell as fox spirit fades into golden light, girl standing alone but transformed, confident smile, sunrise, new beginning"
]

# ========== HELPER FUNCTIONS ==========

def api_request(method, endpoint, data=None, files=None):
    """Make a request to ComfyUI API"""
    url = f"{COMFYUI_URL}{endpoint}"
    if data is not None:
        data = json.dumps(data).encode("utf-8")
    req = urllib.request.Request(url, data=data, method=method)
    req.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(req, timeout=300) as resp:
            return json.loads(resp.read())
    except Exception as e:
        print(f"  [!] API error: {e}")
        return None

def queue_prompt(workflow):
    """Submit a workflow to ComfyUI queue"""
    payload = {"prompt": workflow, "client_id": "storyboard_script"}
    result = api_request("POST", "/prompt", payload)
    return result.get("prompt_id") if result else None

def get_history(prompt_id):
    """Get execution history for a prompt"""
    return api_request("GET", f"/history/{prompt_id}")

def wait_for_prompt(prompt_id, timeout=600):
    """Wait for prompt to finish and return output images"""
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
    """Download generated image from ComfyUI"""
    params = urllib.parse.urlencode({
        "filename": img_info["filename"],
        "subfolder": img_info["subfolder"],
        "type": img_info["type"]
    })
    url = f"{COMFYUI_URL}/view?{params}"
    try:
        urllib.request.urlretrieve(url, save_path)
        return True
    except Exception as e:
        print(f"  [!] Download failed: {e}")
        return False

def upload_image(image_path):
    """Upload an image to ComfyUI for img2img"""
    import http.client
    import mimetypes
    
    boundary = str(uuid.uuid4())
    filename = os.path.basename(image_path)
    
    body = []
    body.append(f"--{boundary}".encode())
    body.append(f'Content-Disposition: form-data; name="image"; filename="{filename}"'.encode())
    body.append(f"Content-Type: {mimetypes.guess_type(filename)[0] or 'image/png'}".encode())
    body.append(b"")
    with open(image_path, "rb") as f:
        body.append(f.read())
    body.append(f"--{boundary}--".encode())
    body.append(b"")
    
    body_data = b"\r\n".join(body)
    
    conn = http.client.HTTPConnection("127.0.0.1", 8188, timeout=30)
    conn.request("POST", "/upload/image", body_data, {
        "Content-Type": f"multipart/form-data; boundary={boundary}"
    })
    resp = conn.getresponse()
    result = json.loads(resp.read())
    conn.close()
    return result.get("name", filename)

def load_workflow_template():
    """Load the base workflow with loaders, replace prompt per stage"""
    return {
        "1": {
            "inputs": {"unet_name": "z_image_turbo_bf16.safetensors", "weight_dtype": "default"},
            "class_type": "UNETLoader"
        },
        "2": {
            "inputs": {"clip_name": "qwen_3_4b.safetensors", "type": "qwen_image"},
            "class_type": "CLIPLoader"
        },
        "3": {
            "inputs": {"vae_name": "ae.safetensors"},
            "class_type": "VAELoader"
        },
        "4": {
            "inputs": {"clip": ["2", 0], "text": ""},
            "class_type": "CLIPTextEncode",
            "_meta": {"title": "Positive Prompt"}
        },
        "5": {
            "inputs": {"clip": ["2", 0], "text": "lowres, bad anatomy, bad hands, text, error, missing fingers"},
            "class_type": "CLIPTextEncode",
            "_meta": {"title": "Negative Prompt"}
        },
        "6": {
            "inputs": {"width": 1024, "height": 1024, "batch_size": 1},
            "class_type": "EmptySD3LatentImage"
        },
        "7": {
            "inputs": {
                "model": ["1", 0], "positive": ["4", 0], "negative": ["5", 0],
                "latent_image": ["6", 0], "seed": 0, "steps": 4, "cfg": 1.0,
                "sampler_name": "euler", "scheduler": "simple", "denoise": 1.0
            },
            "class_type": "KSampler"
        },
        "8": {
            "inputs": {"samples": ["7", 0], "vae": ["3", 0]},
            "class_type": "VAEDecode"
        },
        "9": {
            "inputs": {"images": ["8", 0]},
            "class_type": "PreviewImage"
        }
    }

def load_img2img_template(image_filename):
    """Load img2img workflow (uses uploaded image as latent)"""
    return {
        "1": {
            "inputs": {"unet_name": "z_image_turbo_bf16.safetensors", "weight_dtype": "default"},
            "class_type": "UNETLoader"
        },
        "2": {
            "inputs": {"clip_name": "qwen_3_4b.safetensors", "type": "qwen_image"},
            "class_type": "CLIPLoader"
        },
        "3": {
            "inputs": {"vae_name": "ae.safetensors"},
            "class_type": "VAELoader"
        },
        "4": {
            "inputs": {"clip": ["2", 0], "text": ""},
            "class_type": "CLIPTextEncode"
        },
        "5": {
            "inputs": {"clip": ["2", 0], "text": "lowres, bad anatomy, bad hands, text, error, missing fingers"},
            "class_type": "CLIPTextEncode"
        },
        "10": {
            "inputs": {"image": image_filename, "upload": "image"},
            "class_type": "LoadImage"
        },
        "11": {
            "inputs": {"pixels": ["10", 0], "vae": ["3", 0]},
            "class_type": "VAEEncode"
        },
        "7": {
            "inputs": {
                "model": ["1", 0], "positive": ["4", 0], "negative": ["5", 0],
                "latent_image": ["11", 0], "seed": 0, "steps": 4, "cfg": 1.0,
                "sampler_name": "euler", "scheduler": "simple", "denoise": 0.75
            },
            "class_type": "KSampler"
        },
        "8": {
            "inputs": {"samples": ["7", 0], "vae": ["3", 0]},
            "class_type": "VAEDecode"
        },
        "9": {
            "inputs": {"images": ["8", 0]},
            "class_type": "PreviewImage"
        }
    }

# ========== MAIN ==========

def main():
    print("=" * 60)
    print("  10-Stage Storyboard Generator")
    print(f"  Stages: {STAGES}")
    print(f"  Output: {OUTPUT_DIR}")
    print("=" * 60)
    
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    prev_image = None
    
    for stage in range(STAGES):
        stage_num = stage + 1
        prompt_text = STAGE_PROMPTS[stage]
        
        print(f"\n{'='*60}")
        print(f"  STAGE {stage_num}/{STAGES}")
        print(f"  {'txt2img' if stage == 0 else 'img2img'} | Prompt: {prompt_text[:80]}...")
        print(f"{'='*60}")
        
        # Build workflow
        if stage == 0:
            wf = load_workflow_template()
        else:
            # Upload previous image
            print(f"  [*] Uploading stage {stage} image for img2img...")
            img_name = upload_image(prev_image)
            print(f"  [OK] Uploaded as: {img_name}")
            wf = load_img2img_template(img_name)
        
        # Set prompt
        wf["4"]["inputs"]["text"] = prompt_text
        wf["7"]["inputs"]["seed"] = stage * 7777 + 12345
        
        # Submit
        print(f"  [*] Submitting to ComfyUI...")
        prompt_id = queue_prompt(wf)
        if not prompt_id:
            print(f"  [FAIL] Could not submit prompt")
            break
        
        print(f"  [*] Prompt ID: {prompt_id}, waiting...")
        images = wait_for_prompt(prompt_id)
        
        if not images:
            print(f"  [FAIL] No output images")
            break
        
        # Save
        save_path = OUTPUT_DIR / f"stage_{stage_num:02d}.png"
        if download_image(images[0], save_path):
            print(f"  [OK] Saved: {save_path}")
            prev_image = save_path
        else:
            print(f"  [FAIL] Could not download image")
            break
    
    print(f"\n{'='*60}")
    print(f"  DONE! {stage_num} stages generated")
    print(f"  Output: {OUTPUT_DIR}")
    print(f"{'='*60}")

if __name__ == "__main__":
    main()
