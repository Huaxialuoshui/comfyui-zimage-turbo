#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Image Resizer Tool - Web UI
多语言 / 多主题 / 单/批量图片对齐工具
"""

import os, io, zipfile, sys, webbrowser, uuid, threading
from pathlib import Path
from flask import Flask, render_template_string, request, send_file, jsonify

try:
    from PIL import Image
except ImportError:
    print("[!] Pillow not installed. Run: pip install Pillow")
    sys.exit(1)

PORT = 8199
UPLOAD_FOLDER = Path(__file__).parent / "tmp_resizer"
OUTPUT_FOLDER = Path(__file__).parent / "output_resized"
UPLOAD_FOLDER.mkdir(exist_ok=True)
OUTPUT_FOLDER.mkdir(exist_ok=True)

PRESETS_EN = {
    "1024x1024 (Square 1:1)": (1024, 1024),
    "768x1360 (Portrait 9:16)": (768, 1360),
    "576x1408 (Portrait 9:16 alt)": (576, 1408),
    "1360x768 (Landscape 16:9)": (1360, 768),
    "1408x576 (Landscape 16:9 alt)": (1408, 576),
    "1080x1920 (Full HD Portrait)": (1080, 1920),
    "1920x1080 (Full HD Landscape)": (1920, 1080),
}
PRESETS_CN = {
    "1024x1024 (正方形 1:1)": (1024, 1024),
    "768x1360 (竖屏 9:16)": (768, 1360),
    "576x1408 (竖屏 9:16 备选)": (576, 1408),
    "1360x768 (横屏 16:9)": (1360, 768),
    "1408x576 (横屏 16:9 备选)": (1408, 576),
    "1080x1920 (全高清竖屏)": (1080, 1920),
    "1920x1080 (全高清横屏)": (1920, 1080),
}

THEMES = {
    "miku": {
        "name": "Miku / 初音",
        "bg": "#13162b", "panel": "#1a1f3a", "header": "#0e1229",
        "accent": "#66ccff", "secondary": "#39C5BB", "border": "#2a3050",
        "text": "#e0e8f0", "text2": "#8899aa", "card": "#181d38"
    },
    "sakura": {
        "name": "Sakura / 樱花",
        "bg": "#2b1a22", "panel": "#3a1f2a", "header": "#22151c",
        "accent": "#ff6b9d", "secondary": "#ff9ec4", "border": "#553040",
        "text": "#f0e0e4", "text2": "#aa8892", "card": "#381d28"
    },
    "matrix": {
        "name": "Matrix / 矩阵",
        "bg": "#0a1a0a", "panel": "#0d240d", "header": "#081408",
        "accent": "#00ff41", "secondary": "#39ff77", "border": "#1a3a1a",
        "text": "#c0e0c0", "text2": "#558855", "card": "#0f2a0f"
    },
    "sunset": {
        "name": "Sunset / 日落",
        "bg": "#1a1218", "panel": "#2a1618", "header": "#1a0e12",
        "accent": "#ff8844", "secondary": "#ffcc44", "border": "#442828",
        "text": "#f0d8c8", "text2": "#aa8870", "card": "#281a1a"
    },
}

EXPORT_FORMATS = {
    "JPEG (高质量)": "jpeg_95",
    "JPEG (中等)": "jpeg_80",
    "JPEG (快速)": "jpeg_60",
    "PNG (无损)": "png",
    "WEBP (高质量)": "webp_90",
    "WEBP (快速)": "webp_70",
}

STR = {
    "zh": {
        "title": "图片对齐工具 - Z-Image Turbo",
        "subtitle": "用于 ComfyUI 工作流参考图对齐",
        "drop": "拖拽图片到此处或点击选择",
        "drop_hint": "支持 JPG, PNG, WEBP, BMP",
        "preset": "预设尺寸",
        "preset_custom": "-- 自定义 --",
        "custom_size": "自定义尺寸",
        "fit_mode": "裁剪模式",
        "center_crop": "居中\n裁剪",
        "stretch": "拉伸\n填充",
        "fit_pad": "等比\n留黑边",
        "process": "处理所有图片",
        "download": "下载全部 ZIP",
        "clear": "清空全部",
        "remove": "移除",
        "processed": "处理完成",
        "lang": "English",
        "theme": "主题配色",
        "width": "宽",
        "height": "高",
        "start_hint": "拖拽图片到此处开始",
    },
    "en": {
        "title": "Image Resizer - Z-Image Turbo",
        "subtitle": "For ComfyUI workflow reference images",
        "drop": "Drop images here or click to browse",
        "drop_hint": "Supports JPG, PNG, WEBP, BMP",
        "preset": "Preset Size",
        "preset_custom": "-- Custom --",
        "custom_size": "Custom Size",
        "fit_mode": "Fit Mode",
        "center_crop": "Center\nCrop",
        "stretch": "Stretch\nFill",
        "fit_pad": "Fit +\nPad",
        "process": "Process All Images",
        "download": "Download All as ZIP",
        "clear": "Clear All",
        "remove": "Remove",
        "processed": "Processed successfully",
        "lang": "中文",
        "theme": "Theme",
        "width": "Width",
        "height": "Height",
        "start_hint": "Drop images to get started",
    }
}

HTML = r"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title data-i18n="title">Image Resizer</title>
<style>
:root {
  --bg: #13162b;
  --panel: #1a1f3a;
  --header: #0e1229;
  --accent: #66ccff;
  --secondary: #39C5BB;
  --border: #2a3050;
  --text: #e0e8f0;
  --text2: #8899aa;
  --card: #181d38;
  --radius: 10px;
  --shadow: 0 2px 12px rgba(0,0,0,0.3);
}
*{margin:0;padding:0;box-sizing:border-box}
body{font-family:'Segoe UI','PingFang SC','Microsoft YaHei',system-ui,sans-serif;background:var(--bg);color:var(--text);min-height:100vh;transition:background .3s,color .3s}
.header{background:var(--header);padding:12px 20px;display:flex;align-items:center;gap:12px;border-bottom:2px solid var(--accent);flex-wrap:wrap}
.header h1{font-size:19px;font-weight:600;background:linear-gradient(135deg,var(--accent),var(--secondary));-webkit-background-clip:text;-webkit-text-fill-color:transparent;white-space:nowrap}
.header span{font-size:12px;color:var(--text2)}
.header-right{margin-left:auto;display:flex;gap:8px;align-items:center}
.header-btn{padding:5px 12px;border-radius:6px;border:1px solid var(--border);background:var(--panel);color:var(--text);cursor:pointer;font-size:12px;transition:.2s;white-space:nowrap}
.header-btn:hover{border-color:var(--accent);color:var(--accent)}
.main{display:flex;gap:0;height:calc(100vh - 56px)}
.panel{flex:0 0 380px;background:var(--panel);padding:16px;overflow-y:auto;border-right:1px solid var(--border);transition:background .3s}
.preview-area{flex:1;padding:16px;overflow-y:auto;display:flex;flex-wrap:wrap;gap:14px;align-content:flex-start}
.drop-zone{border:2px dashed var(--border);border-radius:var(--radius);padding:36px 16px;text-align:center;cursor:pointer;transition:.2s;margin-bottom:14px}
.drop-zone:hover,.drop-zone.drag{border-color:var(--accent);background:rgba(102,204,255,0.05)}
.drop-zone p{color:var(--text2);font-size:13px}
.drop-zone .icon{font-size:36px;margin-bottom:6px}
input[type=file]{display:none}
.section{margin-bottom:14px}
.section label{display:block;font-size:12px;color:var(--text2);margin-bottom:5px;font-weight:500}
select,input[type=number]{width:100%;padding:9px 10px;border-radius:6px;border:1px solid var(--border);background:var(--bg);color:var(--text);font-size:13px;transition:border .2s}
select:focus,input:focus{outline:none;border-color:var(--accent);box-shadow:0 0 0 2px rgba(102,204,255,0.15)}
.mode-row{display:flex;gap:6px}
.mode-btn{flex:1;padding:8px 6px;border-radius:6px;border:1px solid var(--border);background:var(--bg);color:var(--text2);cursor:pointer;font-size:11px;text-align:center;transition:.15s;line-height:1.3}
.mode-btn.active{border-color:var(--accent);color:var(--accent);background:rgba(102,204,255,0.08)}
.size-row{display:flex;gap:8px;align-items:center}
.size-row input{flex:1}
.size-row span{color:var(--text2);font-size:13px}
.btn{width:100%;padding:10px;border-radius:6px;border:none;font-size:14px;font-weight:600;cursor:pointer;transition:.15s;margin-bottom:6px}
.btn-primary{background:linear-gradient(135deg,var(--accent),var(--secondary));color:#fff}
.btn-primary:hover{opacity:.9}
.btn-secondary{background:var(--bg);color:var(--text);border:1px solid var(--border)}
.btn-secondary:hover{border-color:var(--accent);color:var(--accent)}
.btn-danger{background:transparent;color:#ff5555;border:1px solid transparent;font-size:12px;padding:6px}
.btn-danger:hover{border-color:#ff5555}
.card{background:var(--card);border-radius:var(--radius);overflow:hidden;width:200px;border:1px solid var(--border);box-shadow:var(--shadow);transition:transform .15s}
.card:hover{transform:translateY(-2px)}
.card img{width:100%;display:block;aspect-ratio:1;object-fit:cover}
.card .info{padding:8px 10px;font-size:11px;color:var(--text2)}
.card .info strong{color:var(--text);display:block;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.card .actions{display:flex;gap:4px;padding:0 10px 8px}
.theme-dot{width:28px;height:28px;border-radius:50%;border:2px solid transparent;cursor:pointer;transition:.15s;display:inline-block}
.theme-dot.active{border-color:var(--text);transform:scale(1.15)}
.theme-row{display:flex;gap:8px;flex-wrap:wrap;margin-top:4px}
.toast{position:fixed;bottom:20px;right:20px;background:linear-gradient(135deg,var(--accent),var(--secondary));color:#fff;padding:10px 20px;border-radius:8px;font-size:13px;z-index:999;display:none;box-shadow:0 4px 20px rgba(0,0,0,0.4)}
.spinner{width:18px;height:18px;border:2px solid rgba(255,255,255,0.2);border-top-color:#fff;border-radius:50%;animation:spin .6s linear infinite;display:inline-block;vertical-align:middle;margin-right:6px}
@keyframes spin{to{transform:rotate(360deg)}}
</style>
</head>
<body>
<div class="header">
  <h1 data-i18n="title">&#9881; Image Resizer</h1>
  <span data-i18n="subtitle">for Z-Image Turbo</span>
  <div class="header-right">
    <button class="header-btn" onclick="toggleLang()" id="langBtn" data-i18n="lang">中文</button>
    <button class="header-btn" onclick="toggleThemeMenu()">&#9881; <span data-i18n="theme">Theme</span></button>
  </div>
</div>
<div class="main">
  <div class="panel">
    <div class="drop-zone" id="dropZone" onclick="document.getElementById('fileInput').click()">
      <div class="icon">&#128247;</div>
      <p data-i18n="drop">Drop images here or click to browse</p>
      <p style="font-size:11px;margin-top:4px;color:var(--text2)" data-i18n="drop_hint">Supports JPG, PNG, WEBP, BMP</p>
    </div>
    <input type="file" id="fileInput" accept="image/*" multiple onchange="handleFiles(this.files)">

    <div class="status-bar">
      <span class="dot new"></span> <span id="newCount">0 </span>
      <span style="margin:0 6px">|</span>
      <span class="dot done"></span> <span id="doneCount">0 </span>
    </div>

    <div class="section">
      <label data-i18n="preset">Preset Size</label>
      <select id="presetSelect" onchange="onPresetChange()">
        <option value="" data-i18n-op="preset_custom">-- Custom --</option>
        {% for name, (w, h) in presets.items() %}
        <option value="{{w}}x{{h}}">{{name}}</option>
        {% endfor %}
      </select>
    </div>

    <div class="section">
      <label data-i18n="custom_size">Custom Size</label>
      <div class="size-row">
        <input type="number" id="width" value="768" min="64" max="8192" step="8" placeholder="W">
        <span>&times;</span>
        <input type="number" id="height" value="1360" min="64" max="8192" step="8" placeholder="H">
      </div>
    </div>

    <div class="section">
      <label data-i18n="fit_mode">Fit Mode</label>
      <div class="mode-row">
        <button class="mode-btn active" data-mode="center-crop" data-i18n-mode="center_crop" onclick="setMode(this)">Center<br>Crop</button>
        <button class="mode-btn" data-mode="stretch" data-i18n-mode="stretch" onclick="setMode(this)">Stretch<br>Fill</button>
        <button class="mode-btn" data-mode="fit-pad" data-i18n-mode="fit_pad" onclick="setMode(this)">Fit +<br>Pad</button>
        <button class="mode-btn" data-mode="smart-crop" onclick="setMode(this)">Smart<br>Crop</button>
      </div>
    </div>

    <div class="section">
      <label data-i18n="format">Export Format</label>
      <select id="formatSelect">
        {% for name, val in formats.items() %}
        <option value="{{val}}">{{name}}</option>
        {% endfor %}
      </select>
    </div>

    <div class="section">
      <label data-i18n="format">Export Format</label>
      <select id="formatSelect">
        {% for name, val in formats.items() %}
        <option value="{{val}}">{{name}}</option>
        {% endfor %}
      </select>
    </div>

    <div class="section" id="themeSection" style="display:none">
      <label data-i18n="theme">Theme</label>
      <div class="theme-row">
        {% for key, t in themes.items() %}
        <button class="theme-dot {% if key == 'miku' %}active{% endif %}"
                style="background:linear-gradient(135deg,{{t.accent}},{{t.secondary}})"
                onclick="setTheme('{{key}}')" title="{{t.name}}"></button>
        {% endfor %}
      </div>
    </div>

    <button class="btn btn-primary" id="processBtn" onclick="processAll()">
      &#128260; <span data-i18n="process">Process All Images</span> (<span id="imgCount">0</span>)
    </button>
    <button class="btn btn-secondary" onclick="downloadAll()">&#128229; <span data-i18n="download">Download All as ZIP</span></button>
    <button class="btn btn-secondary" onclick="clearAll()">&#128465; <span data-i18n="clear">Clear All</span></button>
  </div>

  <div class="preview-area" id="previewArea">
    <p style="color:var(--text2);margin:auto;font-size:13px" data-i18n="start_hint">Drop images to get started</p>
  </div>
</div>
<div class="toast" id="toast"></div>

<script>
const THEMES = {{themes_json|safe}};
let lang = 'cn';
let mode = 'center-crop';
let sessionId = null;
let currentTheme = 'miku';

async function init() {
  let r = await fetch('/api/session', {method:'POST'});
  let d = await r.json();
  sessionId = d.session_id;
}

async function handleFiles(fileList) {
  let fd = new FormData();
  for (let f of fileList) fd.append('files', f);
  await fetch('/api/upload/' + sessionId, {method:'POST', body:fd});
  await renderPreviews();
  updateCount();
}

function updateCount() {
  fetch('/api/count/' + sessionId).then(r=>r.json()).then(d=>{
    document.getElementById('imgCount').textContent = d.count;
  });
}

async function renderPreviews() {
  let r = await fetch('/api/list/' + sessionId);
  let images = await r.json();
  let area = document.getElementById('previewArea');
  area.innerHTML = images.length ? '' :
    '<p style="color:var(--text2);margin:auto;font-size:13px" data-i18n="start_hint">Drop images to get started</p>';
  for (let img of images) {
    let card = document.createElement('div');
    card.className = 'card';
    let badge = img.processed ? '<div class=\"badge done\">&#10003; ' + (lang=='cn'?'已处理':'Done') + '</div>' : '<div class=\"badge new\">&#9888; ' + (lang=='cn'?'未处理':'New') + '</div>';
    card.innerHTML = badge + '<img src="/api/preview/' + sessionId + '/' + img.index + '" alt="' + img.name + '">' +
      '<div class="info"><strong title="' + img.name + '">' + img.name + '</strong>' +
      img.width + ' &times; ' + img.height + '</div>' +
      '<div class="actions"><button class="btn-danger" onclick="removeImage(' + img.index + ')">' +
      (lang === 'cn' ? '&#10005; 移除' : '&#10005; Remove') + '</button></div>';
    area.appendChild(card);
  }
  applyLang();
}

function onPresetChange() {
  let v = document.getElementById('presetSelect').value;
  if (!v) return;
  let [w, h] = v.split('x');
  document.getElementById('width').value = w;
  document.getElementById('height').value = h;
}

function setMode(btn) {
  document.querySelectorAll('.mode-btn').forEach(b=>b.classList.remove('active'));
  btn.classList.add('active');
  mode = btn.dataset.mode;
}

async function processAll() {
  let w = parseInt(document.getElementById('width').value) || 768;
  let h = parseInt(document.getElementById('height').value) || 1360;
  let fmt = document.getElementById('formatSelect').value || 'jpeg_95';
  let btn = document.getElementById('processBtn');
  btn.disabled = true;
  btn.innerHTML = '<span class="spinner"></span>' + (lang === 'cn' ? '处理中...' : 'Processing...');
  try {
    let r = await fetch('/api/process/' + sessionId, {
      method:'POST', headers:{'Content-Type':'application/json'},
      body: JSON.stringify({width:w, height:h, mode:mode, format:fmt})
    });
    let d = await r.json();
    await renderPreviews();
    updateCount();
    toast((lang === 'cn' ? '&#10003; 处理完成 ' : '&#10003; Processed ') + d.count + (lang === 'cn' ? ' 张' : ' image(s)'));
  } catch(e) { toast('Error: ' + e.message); }
  var cnt = document.getElementById('imgCount');
  btn.innerHTML = '💪 ' + (lang === 'cn' ? '处理图片' : 'Process Images') + ' (' + (cnt ? cnt.textContent : '0') + ')';
  btn.disabled = false;
}

async function removeImage(idx) {
  await fetch('/api/remove/' + sessionId + '/' + idx, {method:'POST'});
  await renderPreviews();
  updateCount();
}

function downloadAll() { window.open('/api/download/' + sessionId, '_blank'); }

async function clearAll() {
  await fetch('/api/clear/' + sessionId, {method:'POST'});
  document.getElementById('previewArea').innerHTML =
    '<p style="color:var(--text2);margin:auto;font-size:13px" data-i18n="start_hint">Drop images to get started</p>';
  document.getElementById('imgCount').textContent = '0';
}

function toggleThemeMenu() {
  let s = document.getElementById('themeSection');
  s.style.display = s.style.display === 'none' ? 'block' : 'none';
}

function setTheme(key) {
  currentTheme = key;
  let t = THEMES[key];
  document.documentElement.style.setProperty('--bg', t.bg);
  document.documentElement.style.setProperty('--panel', t.panel);
  document.documentElement.style.setProperty('--header', t.header);
  document.documentElement.style.setProperty('--accent', t.accent);
  document.documentElement.style.setProperty('--secondary', t.secondary);
  document.documentElement.style.setProperty('--border', t.border);
  document.documentElement.style.setProperty('--text', t.text);
  document.documentElement.style.setProperty('--text2', t.text2);
  document.documentElement.style.setProperty('--card', t.card);
  document.querySelectorAll('.theme-dot').forEach(d=>d.classList.remove('active'));
  document.querySelector('.theme-dot[onclick*=\\"' + key + '\\"]').classList.add('active');
  document.getElementById('themeSection').style.display = 'none';
}

function toggleLang() {
  lang = lang === 'cn' ? 'en' : 'cn';
  localStorage.setItem('resizer_lang', lang);
  applyLang();
  renderPreviews();
}

function applyLang() {
  let s = lang === 'cn' ? {{str_cn|safe}} : {{str_en|safe}};
  document.querySelectorAll('[data-i18n]').forEach(el => {
    let key = el.dataset.i18n;
    if (s[key]) el.innerHTML = key === 'lang' ? s[key] : (s[key].replace(/\\n/g, '<br>'));
  });
  document.querySelectorAll('[data-i18n-op]').forEach(el => {
    let key = el.dataset.i18nOp;
    if (s[key]) el.textContent = s[key];
  });
  document.querySelectorAll('[data-i18n-mode]').forEach(el => {
    let key = el.dataset.i18nMode;
    if (s[key]) el.innerHTML = s[key].replace(/\\n/g, '<br>');
  });
  updateCount();
}

function toast(msg) {
  let t = document.getElementById('toast');
  t.innerHTML = msg;
  t.style.display = 'block';
  setTimeout(()=>t.style.display='none', 2500);
}

let dz = document.getElementById('dropZone');
dz.addEventListener('dragover', e=>{e.preventDefault();dz.classList.add('drag')});
dz.addEventListener('dragleave', ()=>dz.classList.remove('drag'));
dz.addEventListener('drop', e=>{
  e.preventDefault(); dz.classList.remove('drag');
  handleFiles(e.dataTransfer.files);
});

let saved = localStorage.getItem('resizer_lang');
if (saved) lang = saved;
init();
window.onload = function(){ applyLang(); };
</script>
</body>
</html>"""

MODE_EXT = {'jpeg_95':('JPEG','jpg',95),'jpeg_80':('JPEG','jpg',80),'jpeg_60':('JPEG','jpg',60),'png':('PNG','png',None),'webp_90':('WEBP','webp',90),'webp_70':('WEBP','webp',70)}

app = Flask(__name__)
sessions = {}

def process_image(pil_img, width, height, mode):
    w, h = pil_img.size
    if w == width and h == height:
        return pil_img.copy()
    if mode == "stretch":
        return pil_img.resize((width, height), Image.LANCZOS)
    elif mode == "center-crop":
        scale = max(width / w, height / h)
        nw, nh = round(w * scale), round(h * scale)
        scaled = pil_img.resize((nw, nh), Image.LANCZOS)
        return scaled.crop(((nw - width)//2, (nh - height)//2, (nw + width)//2, (nh + height)//2))
    elif mode == "smart-crop":
        # Smart crop: scales to cover, then crops from center
        scale = max(width / w, height / h)
        new_w = round(w * scale)
        new_h = round(h * scale)
        scaled = pil_img.resize((new_w, new_h), Image.LANCZOS)
        left = (new_w - width) // 2
        top = (new_h - height) // 2
        return scaled.crop((left, top, left + width, top + height))

    elif mode == "fit-pad":
        scale = min(width / w, height / h)
        nw, nh = round(w * scale), round(h * scale)
        scaled = pil_img.resize((nw, nh), Image.LANCZOS)
        result = Image.new("RGB", (width, height), (0, 0, 0))
        result.paste(scaled, ((width - nw)//2, (height - nh)//2))
        return result
    return pil_img.copy()

@app.route("/")
def index():
    import json as jmod
    themes_json = jmod.dumps(THEMES)
    # Pass both lang strings as JSON for JS
    str_cn = jmod.dumps(STR["zh"])
    str_en = jmod.dumps(STR["en"])
    return render_template_string(HTML, presets=PRESETS_CN, themes=THEMES,
        themes_json=themes_json, str_cn=str_cn, str_en=str_en,
        formats=EXPORT_FORMATS)

@app.route("/api/session", methods=["POST"])
def api_session():
    sid = uuid.uuid4().hex[:12]
    sessions[sid] = {"images": [], "processed": {}}
    return jsonify({"session_id": sid})

@app.route("/api/upload/<session_id>", methods=["POST"])
def api_upload(session_id):
    if session_id not in sessions:
        return jsonify({"error": "no session"}), 400
    for f in request.files.getlist("files"):
        if not f.filename:
            continue
        img = Image.open(f.stream).convert("RGB")
        sessions[session_id]["images"].append({"name": f.filename, "image": img})
    return jsonify({"count": len(sessions[session_id]["images"])})

@app.route("/api/count/<session_id>")
def api_count(session_id):
    return jsonify({"count": len(sessions.get(session_id, {}).get("images", []))})

@app.route("/api/list/<session_id>")
def api_list(session_id):
    items = []
    for i, img_data in enumerate(sessions.get(session_id, {}).get("images", [])):
        thumb = img_data["image"].copy()
        thumb.thumbnail((440, 440), Image.LANCZOS)
        path = UPLOAD_FOLDER / f"{session_id}_{i}.jpg"
        thumb.save(path, "JPEG", quality=80)
        items.append({"index": i, "name": img_data["name"],
            "width": img_data["image"].width, "height": img_data["image"].height,
            "size_kb": round(os.path.getsize(path) / 1024, 1)})
    return jsonify(items)

@app.route("/api/preview/<session_id>/<int:index>")
def api_preview(session_id, index):
    path = UPLOAD_FOLDER / f"{session_id}_{index}.jpg"
    return send_file(path, mimetype="image/jpeg") if path.exists() else ("", 404)

@app.route("/api/process/<session_id>", methods=["POST"])
def api_process(session_id):
    if session_id not in sessions:
        return jsonify({"error": "no session"}), 400
    data = request.get_json()
    w, h, mode = int(data.get("width", 768)), int(data.get("height", 1360)), data.get("mode", "center-crop")
    for i, img_data in enumerate(sessions[session_id]["images"]):
        result = process_image(img_data["image"], w, h, mode)
        sessions[session_id]["images"][i]["image"] = result
        out = OUTPUT_FOLDER / f"{session_id}_{i}.jpg"
        result.save(out, "JPEG", quality=95)
    return jsonify({"count": len(sessions[session_id]["images"])})

@app.route("/api/remove/<session_id>/<int:index>", methods=["POST"])
def api_remove(session_id, index):
    if session_id in sessions and 0 <= index < len(sessions[session_id]["images"]):
        sessions[session_id]["images"].pop(index)
        (UPLOAD_FOLDER / f"{session_id}_{index}.jpg").unlink(missing_ok=True)
    return jsonify({"ok": True})

@app.route("/api/download/<session_id>")
def api_download(session_id):
    if session_id not in sessions or not sessions[session_id]["images"]:
        return "No images", 400
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        for i, img_data in enumerate(sessions[session_id]["images"]):
            b = io.BytesIO()
            img_data["image"].save(b, "JPEG", quality=95); b.seek(0)
            zf.writestr(Path(img_data["name"]).stem + "_resized.jpg", b.read())
    buf.seek(0)
    return send_file(buf, mimetype="application/zip", as_attachment=True,
        download_name="resized_images.zip")

@app.route("/api/clear/<session_id>", methods=["POST"])
def api_clear(session_id):
    if session_id in sessions:
        for f in UPLOAD_FOLDER.glob(f"{session_id}_*"): f.unlink(missing_ok=True)
        for f in OUTPUT_FOLDER.glob(f"{session_id}_*"): f.unlink(missing_ok=True)
        del sessions[session_id]
    return jsonify({"ok": True})

if __name__ == "__main__":
    print("=" * 50)
    print(f"  Image Resizer Tool")
    print(f"  http://127.0.0.1:{PORT}")
    print("=" * 50)
    threading.Timer(1.0, lambda: webbrowser.open(f"http://127.0.0.1:{PORT}")).start()
    app.run(host="127.0.0.1", port=PORT, debug=False)
