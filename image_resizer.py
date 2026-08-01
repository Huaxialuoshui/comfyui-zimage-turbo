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
        "title": "图片对齐工具 - Z-Image/anima Turbo",
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
        "mask": "Mask",
        "mask_new": "Create Mask",
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
        "mask": "Mask",
        "mask_new": "Create Mask",
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
.btn-save{background:var(--bg2);color:var(--text);border:1px solid var(--border);border-radius:6px;padding:4px 8px;cursor:pointer;font-size:12px;margin-right:4px}.btn-save:hover{background:var(--primary);color:white}
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

.mask-overlay{position:fixed;inset:0;background:rgba(0,0,0,0.85);z-index:9999;display:flex;align-items:center;justify-content:center}
.mask-panel{background:var(--bg);border-radius:12px;padding:16px;max-width:95vw;max-height:95vh;overflow:hidden;box-shadow:0 8px 32px rgba(0,0,0,0.5)}
.mask-toolbar{display:flex;align-items:center;gap:10px;margin-bottom:10px;flex-wrap:wrap}
.mask-canvas-wrap{position:relative;display:inline-block;cursor:crosshair}
#maskCanvas{max-width:90vw;max-height:70vh;border:2px solid var(--border);border-radius:4px}
</style>
</head>
<body>
<div class="header">
  <h1 data-i18n="title">&#9881; Image Resizer</h1>
  <span data-i18n="subtitle">for Z-Image Turbo</span>
  <div class="header-right">
    <button class="header-btn" onclick="toggleLang()" id="langBtn" data-i18n="lang">中文</button>
    <button class="header-btn" onclick="toggleThemeMenu()">&#9881; <span data-i18n="theme">Theme</span></button>
    <button class="header-btn" onclick="openMaskEditor()" style="background:#9b59b6;margin-left:4px">&#128396; Mask</button>
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

  <div class="mask-overlay" id="maskplusOverlay" style="display:none">
    <div class="mask-panel" style="max-width:1100px">
      <div class="mask-toolbar">
        <span style="font-weight:600;font-size:15px">&#127912; MaskPlus: Face Position Editor</span>
        <div style="margin-left:auto;display:flex;gap:6px;align-items:center">
          <span id="mpStatus" style="font-size:11px;font-weight:600;color:#e74c3c;margin-right:6px">No face selected</span>
          <label style="font-size:10px;color:var(--text2);margin-right:2px"><input type="checkbox" id="mpModeToggle" onchange="setMaskPlusMode()"> Auto</label>
          <select id="mpShapeSelect" onchange="setMaskPlusShape()" style="padding:4px 8px;border-radius:4px;border:1px solid var(--border);background:var(--bg);color:var(--text);font-size:12px"><option value="rect">Rectangle</option><option value="ellipse">Ellipse</option></select>
          <button class="header-btn" id="mpDrawBtn" onclick="startFaceDraw()" style="background:#3498db">&#9998; Draw Face</button>
          <button class="header-btn" id="mpAutoBtn" onclick="autoDetectFace()" style="background:#3498db;display:none">&#9889; Auto Detect</button>
          <button class="header-btn" id="mpConfirmBtn" onclick="confirmFaceSelection()" style="background:#27ae60;display:none">&#10003; Confirm</button>
          <button class="header-btn" id="mpResetSelBtn" onclick="resetFaceSelection()" style="display:none">&#8634; Re-select</button>
          <button class="header-btn" id="mpRandomBtn" onclick="randomFacePosition()" style="background:#e67e22;display:none">&#127922; Random</button>
          <button class="header-btn" id="mpExportBtn" onclick="exportMaskPlus()" style="background:#27ae60;display:none">&#128229; Export All</button>
          <button class="header-btn" onclick="closeMaskPlus()">&#10005; Close</button>
        </div>
      </div>
      <div style="display:flex;gap:12px;flex-wrap:wrap">
        <div style="flex:1;min-width:300px">
          <p style="font-size:11px;color:var(--text2);margin:0 0 4px 0" id="mpHint">1. Click <b>Draw Face</b> to manually select face area, or check <b>Auto</b> for center detection. 2. <b>Confirm</b> to lock selection. 3. Drag green box to reposition, then <b>Export All</b>.</p>
          <div class="mask-canvas-wrap" style="max-height:60vh">
            <canvas id="maskplusCanvas"></canvas>
          </div>
        </div>
        <div style="width:180px;padding:8px;background:var(--bg);border-radius:6px;font-size:12px">
          <label>X: <input type="range" id="mpX" min="-200" max="200" value="0" oninput="updateMaskPlusFromSliders()"></label>
          <label>Y: <input type="range" id="mpY" min="-200" max="200" value="0" oninput="updateMaskPlusFromSliders()"></label>
          <label>Scale: <input type="range" id="mpScale" min="50" max="200" value="100" oninput="updateMaskPlusFromSliders()"> <span id="mpScaleVal">100%</span></label>
          <label>Rotate: <input type="range" id="mpRotate" min="-45" max="45" value="0" oninput="updateMaskPlusFromSliders()"> <span id="mpRotateVal">0</span></label>
          <hr style="border-color:var(--border);margin:8px 0">
          <div style="font-size:10px;color:var(--text2)">
            <b>Export files:</b><br>
            1. moved.png (img2img)<br>
            2. face_mask.png (IPAdapter)<br>
            3. face_body_mask.png (face_body)<br>
            4. metadata.json
          </div>
        </div>
      </div>
    </div>
  </div>

  <div class="mask-overlay" id="maskOverlay" style="display:none">
    <div class="mask-panel">
      <div class="mask-toolbar">
        <span style="font-weight:600;font-size:15px">&#128396; Mask Editor: Draw face area (BLACK=locked, WHITE=repaint)</span>
        <div style="margin-left:auto;display:flex;gap:6px">
          <select id="maskShape" onchange="setMaskShape()" style="padding:4px 8px;border-radius:4px;border:1px solid var(--border)">
            <option value="rect">Rectangle</option>
            <option value="ellipse">Ellipse</option>
          </select>
          <label style="font-size:12px;margin-left:8px"><input type="checkbox" id="repositionMode" onchange="toggleReposition()"> Reposition Face</label>
          <button class="header-btn" id="btnMoved" onclick="downloadRepositioned()" style="background:#8e44ad;display:none">&#128229; Export Moved</button>
          <button class="header-btn" onclick="downloadMask()" style="background:#27ae60">&#128229; Download Mask</button>
          <button class="header-btn" onclick="closeMaskEditor()">&#10005; Close</button>
        </div>
      </div>
      <div class="mask-canvas-wrap" id="maskCanvasWrap">
        <canvas id="maskCanvas"></canvas>
      </div>
      <p style="text-align:center;font-size:11px;color:var(--text2);margin-top:6px">Drag to draw face region (black). Rest auto-fills white. Resize handles on corners.</p>
    </div>
  </div>

<div class="toast" id="toast"></div>

<script>
console.log('=== image_resizer script loaded ===');
const THEMES = {{themes_json|safe}};
let lang = 'cn';
let mode = 'center-crop';
let sessionId = null;
let currentTheme = 'miku';

async function init() {
  let r = await fetch('/api/session', {method:'POST'});
  let d = await r.json();
  sessionId = d.session_id;

  // MaskPlus buttons use DOM onclick, no delegation needed
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
      '<div class="actions"><button class="btn-maskplus" onclick="openMaskPlus(' + img.index + ')" title="MaskPlus" style="background:#8e44ad;color:#fff;border:none;border-radius:4px;padding:3px 7px;cursor:pointer;margin-right:4px;font-size:12px">MaskPlus</button><button class="btn-save" onclick="saveImage(' + img.index + ')" title="Save">&#128190;</button><button class="btn-danger" onclick="removeImage(' + img.index + ')">' +
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

async function saveImage(idx) {
  let r = await fetch('/api/list/' + sessionId);
  let images = await r.json();
  let img = images.find(function(x) { return x.index == idx; });
  let name = img ? img.name : 'image_' + idx + '.png';
  window.open('/api/save/' + sessionId + '/' + idx + '?name=' + encodeURIComponent(name), '_blank');
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
console.log('calling init()...');
init();
window.onload = function(){ applyLang(); };


// ===== MaskPlus Editor =====
let mpImg = null, mpCanvas = null, mpCtx = null;
let mpFaceRect = { x: 0, y: 0, w: 0, h: 0 };
let mpOffsetX = 0, mpOffsetY = 0;
let mpScale = 1.0;
let mpRotation = 0;
let mpShape = 'rect';
let mpImageIndex = -1;
let mpPhase = 'idle';   // 'idle' = no face selected, 'drawing' = actively drawing, 'reposition' = moving face
let mpMode = 'manual';  // 'manual' or 'auto'
let mpDrawing = false, mpDrawStart = { x: 0, y: 0 };
let mpDragging = false, mpDragStart = { x: 0, y: 0 };
let mpFaceSnapshot = null;
let mpResizeHandle = null;

function openMaskPlus(imgIndex) {
  mpImageIndex = parseInt(imgIndex) || 0;
  mpOffsetX = 0; mpOffsetY = 0; mpScale = 1.0; mpRotation = 0;
  mpPhase = 'idle';
  mpMode = 'manual';
  mpFaceRect = { x: 0, y: 0, w: 0, h: 0 };
  mpFaceSnapshot = null;

  var overlay = document.getElementById("maskplusOverlay");
  if (!overlay) return;
  overlay.style.display = "flex";
  mpCanvas = document.getElementById("maskplusCanvas");
  if (!mpCanvas) return;
  mpCtx = mpCanvas.getContext("2d");

  var items = document.querySelectorAll(".card img");
  if (!items || items.length === 0) return;
  if (mpImageIndex >= items.length) mpImageIndex = 0;

  var imgEl = items[mpImageIndex];
  mpImg = new Image();
  mpImg.onload = function() {
    updatePhaseUI();
    drawMaskPlus();
  };
  mpImg.src = imgEl.src;
}

function setMaskPlusShape() {
  var sel = document.getElementById("mpShapeSelect");
  if (sel) mpShape = sel.value;
  drawMaskPlus();
}

function setMaskPlusMode() {
  var toggle = document.getElementById("mpModeToggle");
  if (toggle) mpMode = toggle.checked ? 'auto' : 'manual';
  updatePhaseUI();
}

function startFaceDraw() {
  mpPhase = 'drawing';
  mpFaceRect = { x: 0, y: 0, w: 0, h: 0 };
  updatePhaseUI();
  drawMaskPlus();
}

function autoDetectFace() {
  if (!mpImg) return;
  // Center 30% region
  mpFaceRect.x = Math.round(mpImg.width * 0.35);
  mpFaceRect.y = Math.round(mpImg.height * 0.2);
  mpFaceRect.w = Math.round(mpImg.width * 0.3);
  mpFaceRect.h = Math.round(mpImg.height * 0.35);
  mpPhase = 'drawing';
  updatePhaseUI();
  drawMaskPlus();
}

function confirmFaceSelection() {
  if (!mpFaceRect || mpFaceRect.w < 15 || mpFaceRect.h < 15) {
    toast("Face area too small. Draw a larger rectangle.");
    return;
  }
  var off = document.createElement("canvas");
  off.width = mpFaceRect.w; off.height = mpFaceRect.h;
  var octx = off.getContext("2d");
  octx.drawImage(mpImg, mpFaceRect.x, mpFaceRect.y, mpFaceRect.w, mpFaceRect.h, 0, 0, mpFaceRect.w, mpFaceRect.h);
  mpFaceSnapshot = off;
  mpPhase = 'reposition';
  mpOffsetX = 0; mpOffsetY = 0;
  mpScale = 1.0; mpRotation = 0;
  updatePhaseUI();
  drawMaskPlus();
}

function resetFaceSelection() {
  mpPhase = 'idle';
  mpFaceRect = { x: 0, y: 0, w: 0, h: 0 };
  mpOffsetX = 0; mpOffsetY = 0;
  mpScale = 1.0; mpRotation = 0;
  mpFaceSnapshot = null;
  updatePhaseUI();
  drawMaskPlus();
}

function updatePhaseUI() {
  var drawBtn = document.getElementById("mpDrawBtn");
  var autoBtn = document.getElementById("mpAutoBtn");
  var confirmBtn = document.getElementById("mpConfirmBtn");
  var resetBtn = document.getElementById("mpResetSelBtn");
  var exportBtn = document.getElementById("mpExportBtn");
  var randomBtn = document.getElementById("mpRandomBtn");
  var modeToggle = document.getElementById("mpModeToggle");
  var statusEl = document.getElementById("mpStatus");
  var sliders = document.querySelectorAll("#mpX, #mpY, #mpScale, #mpRotate");
  var shapeSel = document.getElementById("mpShapeSelect");

  if (mpPhase === 'idle') {
    if (drawBtn) drawBtn.style.display = "inline-block";
    if (autoBtn) autoBtn.style.display = "inline-block";
    if (confirmBtn) confirmBtn.style.display = "none";
    if (resetBtn) resetBtn.style.display = "none";
    if (exportBtn) exportBtn.style.display = "none";
    if (randomBtn) randomBtn.style.display = "none";
    if (modeToggle) modeToggle.disabled = false;
    if (statusEl) { statusEl.textContent = "No face selected"; statusEl.style.color = "#e74c3c"; }
    sliders.forEach(function(s) { s.disabled = true; });
    if (shapeSel) shapeSel.disabled = false;
  } else if (mpPhase === 'drawing') {
    if (drawBtn) drawBtn.style.display = "none";
    if (autoBtn) autoBtn.style.display = "none";
    if (confirmBtn) confirmBtn.style.display = "inline-block";
    if (resetBtn) resetBtn.style.display = "inline-block";
    if (exportBtn) exportBtn.style.display = "none";
    if (randomBtn) randomBtn.style.display = "none";
    if (modeToggle) modeToggle.disabled = true;
    if (statusEl) { statusEl.textContent = "Adjust face area then Confirm"; statusEl.style.color = "#f39c12"; }
    sliders.forEach(function(s) { s.disabled = true; });
    if (shapeSel) shapeSel.disabled = false;
  } else { // reposition
    if (drawBtn) drawBtn.style.display = "none";
    if (autoBtn) autoBtn.style.display = "none";
    if (confirmBtn) confirmBtn.style.display = "none";
    if (resetBtn) resetBtn.style.display = "inline-block";
    if (exportBtn) exportBtn.style.display = "inline-block";
    if (randomBtn) randomBtn.style.display = "inline-block";
    if (modeToggle) modeToggle.disabled = true;
    if (statusEl) { statusEl.textContent = "Face selected - drag to reposition"; statusEl.style.color = "#27ae60"; }
    sliders.forEach(function(s) { s.disabled = false; });
    if (shapeSel) shapeSel.disabled = true;
    updateSliders();
  }
}

function updateSliders() {
  var xEl = document.getElementById("mpX"); if (xEl) xEl.value = mpOffsetX;
  var yEl = document.getElementById("mpY"); if (yEl) yEl.value = mpOffsetY;
  var sEl = document.getElementById("mpScale"); if (sEl) sEl.value = Math.round(mpScale * 100);
  var rEl = document.getElementById("mpRotate"); if (rEl) rEl.value = mpRotation;
  var sv = document.getElementById("mpScaleVal"); if (sv) sv.textContent = Math.round(mpScale * 100) + "%";
  var rv = document.getElementById("mpRotateVal"); if (rv) rv.textContent = mpRotation + "°";
}

function updateMaskPlusFromSliders() {
  mpOffsetX = parseInt(document.getElementById("mpX").value) || 0;
  mpOffsetY = parseInt(document.getElementById("mpY").value) || 0;
  mpScale = (parseInt(document.getElementById("mpScale").value) || 100) / 100;
  mpRotation = parseInt(document.getElementById("mpRotate").value) || 0;
  var sv = document.getElementById("mpScaleVal"); if (sv) sv.textContent = Math.round(mpScale * 100) + "%";
  var rv = document.getElementById("mpRotateVal"); if (rv) rv.textContent = mpRotation + "°";
  drawMaskPlus();
}

function randomFacePosition() {
  if (!mpImg) return;
  mpOffsetX = Math.floor(Math.random() * mpImg.width * 0.8 - mpImg.width * 0.4);
  mpOffsetY = Math.floor(Math.random() * mpImg.height * 0.5 - mpImg.height * 0.25);
  mpScale = 0.8 + Math.random() * 0.8;
  mpRotation = Math.floor(Math.random() * 30 - 15);
  updateSliders();
  drawMaskPlus();
  toast("Random: (" + mpOffsetX + "," + mpOffsetY + ")");
}

function drawMaskPlus() {
  if (!mpImg || !mpCtx) return;
  var w = mpImg.width, h = mpImg.height;
  var maxW = Math.min(900, window.innerWidth - 300);
  var scale = Math.min(maxW / w, 0.8);
  mpCanvas.width = w * scale;
  mpCanvas.height = h * scale;
  mpCtx.setTransform(scale, 0, 0, scale, 0, 0);

  if (mpPhase === 'idle') {
    // Show image only, no face rect
    mpCtx.globalAlpha = 1.0;
    mpCtx.drawImage(mpImg, 0, 0, w, h);
    mpCtx.fillStyle = "rgba(0,0,0,0.15)";
    mpCtx.fillRect(0, 0, w, h);
    mpCtx.fillStyle = "#fff";
    mpCtx.font = "bold 18px sans-serif";
    mpCtx.textAlign = "center";
    mpCtx.fillText("Click 'Draw Face' or 'Auto Detect' to start", w/2, h/2);
    mpCtx.textAlign = "start";
  } else if (mpPhase === 'drawing') {
    if (mpFaceRect.w === 0 && mpFaceRect.h === 0) {
      // No rect drawn yet
      mpCtx.globalAlpha = 1.0;
      mpCtx.drawImage(mpImg, 0, 0, w, h);
      mpCtx.fillStyle = "rgba(0,0,0,0.2)";
      mpCtx.fillRect(0, 0, w, h);
      mpCtx.fillStyle = "#fff";
      mpCtx.font = "bold 16px sans-serif";
      mpCtx.textAlign = "center";
      mpCtx.fillText("Click and drag to draw face area", w/2, h/2);
      mpCtx.textAlign = "start";
    } else {
      // Dim outside, highlight selection
      mpCtx.globalAlpha = 1.0;
      mpCtx.drawImage(mpImg, 0, 0, w, h);
      mpCtx.fillStyle = "rgba(0,0,0,0.4)";
      mpCtx.fillRect(0, 0, w, h);
      mpCtx.clearRect(mpFaceRect.x, mpFaceRect.y, mpFaceRect.w, mpFaceRect.h);
      mpCtx.drawImage(mpImg, mpFaceRect.x, mpFaceRect.y, mpFaceRect.w, mpFaceRect.h, mpFaceRect.x, mpFaceRect.y, mpFaceRect.w, mpFaceRect.h);
      // Outline
      mpCtx.strokeStyle = "#f39c12";
      mpCtx.lineWidth = 2.5;
      mpCtx.setLineDash([6, 3]);
      if (mpShape === 'ellipse') {
        mpCtx.beginPath();
        mpCtx.ellipse(mpFaceRect.x + mpFaceRect.w/2, mpFaceRect.y + mpFaceRect.h/2, mpFaceRect.w/2, mpFaceRect.h/2, 0, 0, Math.PI*2);
        mpCtx.stroke();
      } else {
        mpCtx.strokeRect(mpFaceRect.x, mpFaceRect.y, mpFaceRect.w, mpFaceRect.h);
      }
      mpCtx.setLineDash([]);
      // Handles
      mpCtx.fillStyle = "#f39c12";
      [[mpFaceRect.x,mpFaceRect.y],[mpFaceRect.x+mpFaceRect.w,mpFaceRect.y],[mpFaceRect.x,mpFaceRect.y+mpFaceRect.h],[mpFaceRect.x+mpFaceRect.w,mpFaceRect.y+mpFaceRect.h]].forEach(function(p) {
        mpCtx.fillRect(p[0]-5, p[1]-5, 10, 10);
      });
    }
  } else {
    // Reposition
    mpCtx.globalAlpha = 0.35;
    mpCtx.drawImage(mpImg, 0, 0, w, h);
    mpCtx.globalAlpha = 1.0;
    var cx = mpFaceRect.x + mpFaceRect.w/2 + mpOffsetX;
    var cy = mpFaceRect.y + mpFaceRect.h/2 + mpOffsetY;
    mpCtx.save();
    mpCtx.translate(cx, cy);
    mpCtx.rotate(mpRotation * Math.PI / 180);
    mpCtx.scale(mpScale, mpScale);
    mpCtx.drawImage(mpFaceSnapshot, -mpFaceRect.w/2, -mpFaceRect.h/2);
    mpCtx.restore();
    // Original outline red
    mpCtx.strokeStyle = "#e74c3c";
    mpCtx.lineWidth = 2;
    mpCtx.setLineDash([4, 4]);
    if (mpShape === 'ellipse') {
      mpCtx.beginPath();
      mpCtx.ellipse(mpFaceRect.x + mpFaceRect.w/2, mpFaceRect.y + mpFaceRect.h/2, mpFaceRect.w/2, mpFaceRect.h/2, 0, 0, Math.PI*2);
      mpCtx.stroke();
    } else { mpCtx.strokeRect(mpFaceRect.x, mpFaceRect.y, mpFaceRect.w, mpFaceRect.h); }
    mpCtx.setLineDash([]);
    // New outline green
    var nw = mpFaceRect.w * mpScale, nh = mpFaceRect.h * mpScale;
    var nx = cx - nw/2, ny = cy - nh/2;
    mpCtx.strokeStyle = "#27ae60";
    mpCtx.lineWidth = 2;
    mpCtx.setLineDash([6, 3]);
    if (mpShape === 'ellipse') {
      mpCtx.beginPath(); mpCtx.ellipse(cx, cy, nw/2, nh/2, 0, 0, Math.PI*2); mpCtx.stroke();
    } else { mpCtx.strokeRect(nx, ny, nw, nh); }
    mpCtx.setLineDash([]);
    mpCtx.fillStyle = "#27ae60"; mpCtx.font = "14px sans-serif"; mpCtx.fillText("New Position", nx, ny - 6);
    mpCtx.fillStyle = "#e74c3c"; mpCtx.fillText("Original", mpFaceRect.x, mpFaceRect.y - 6);
  }
}

// Canvas events
(function initMaskPlusListeners() {
  var mc = document.getElementById("maskplusCanvas");
  if (!mc) return;
  mc.addEventListener("mousedown", function(e) {
    if (!mpImg || mpPhase === 'idle' || mpPhase === 'reposition') {
      if (mpPhase === 'reposition') {
        var rect2 = mc.getBoundingClientRect();
        var sx2 = (e.clientX - rect2.left) * (mpImg.width / mc.width);
        var sy2 = (e.clientY - rect2.top) * (mpImg.height / mc.height);
        var cx2 = mpFaceRect.x + mpFaceRect.w/2 + mpOffsetX;
        var cy2 = mpFaceRect.y + mpFaceRect.h/2 + mpOffsetY;
        var nw2 = mpFaceRect.w * mpScale, nh2 = mpFaceRect.h * mpScale;
        if (sx2 >= cx2 - nw2/2 && sx2 <= cx2 + nw2/2 && sy2 >= cy2 - nh2/2 && sy2 <= cy2 + nh2/2) {
          mpDragging = true;
          mpDragStart = { x: sx2 - mpOffsetX, y: sy2 - mpOffsetY };
        }
      }
      e.preventDefault();
      return;
    }
    // Drawing phase
    var rect = mc.getBoundingClientRect();
    var sx = (e.clientX - rect.left) * (mpImg.width / mc.width);
    var sy = (e.clientY - rect.top) * (mpImg.height / mc.height);
    if (mpFaceRect.w > 0) {
      var h = 12 * (mpImg.width / mc.width);
      var handles = [{id:'tl',x:mpFaceRect.x,y:mpFaceRect.y},{id:'tr',x:mpFaceRect.x+mpFaceRect.w,y:mpFaceRect.y},{id:'bl',x:mpFaceRect.x,y:mpFaceRect.y+mpFaceRect.h},{id:'br',x:mpFaceRect.x+mpFaceRect.w,y:mpFaceRect.y+mpFaceRect.h}];
      mpResizeHandle = null;
      for (var i=0;i<handles.length;i++) { if (Math.abs(sx-handles[i].x)<h && Math.abs(sy-handles[i].y)<h) { mpResizeHandle=handles[i].id; break; } }
      if (!mpResizeHandle && sx>=mpFaceRect.x && sx<=mpFaceRect.x+mpFaceRect.w && sy>=mpFaceRect.y && sy<=mpFaceRect.y+mpFaceRect.h) {
        mpDragging = true; mpDragStart = { x: sx-mpFaceRect.x, y: sy-mpFaceRect.y };
      } else if (!mpResizeHandle) {
        mpDrawing = true; mpDrawStart = { x: sx, y: sy }; mpFaceRect = { x: sx, y: sy, w: 0, h: 0 };
      }
    } else {
      mpDrawing = true; mpDrawStart = { x: sx, y: sy }; mpFaceRect = { x: sx, y: sy, w: 0, h: 0 };
    }
    e.preventDefault();
  });
  mc.addEventListener("mousemove", function(e) {
    if (!mpImg) return;
    if (mpPhase === 'reposition' && mpDragging) {
      var r3 = mc.getBoundingClientRect();
      var sx3 = (e.clientX - r3.left) * (mpImg.width / mc.width);
      var sy3 = (e.clientY - r3.top) * (mpImg.height / mc.height);
      mpOffsetX = Math.round(sx3 - mpDragStart.x);
      mpOffsetY = Math.round(sy3 - mpDragStart.y);
      updateSliders(); drawMaskPlus(); return;
    }
    if (mpPhase !== 'drawing') return;
    var rect = mc.getBoundingClientRect();
    var sx = (e.clientX - rect.left) * (mpImg.width / mc.width);
    var sy = (e.clientY - rect.top) * (mpImg.height / mc.height);
    if (mpResizeHandle) {
      if (mpResizeHandle.indexOf('l')>=0) { mpFaceRect.w += mpFaceRect.x-sx; mpFaceRect.x=sx; }
      if (mpResizeHandle.indexOf('r')>=0) { mpFaceRect.w = sx-mpFaceRect.x; }
      if (mpResizeHandle.indexOf('t')>=0) { mpFaceRect.h += mpFaceRect.y-sy; mpFaceRect.y=sy; }
      if (mpResizeHandle.indexOf('b')>=0) { mpFaceRect.h = sy-mpFaceRect.y; }
      if (mpFaceRect.w<10) mpFaceRect.w=10; if (mpFaceRect.h<10) mpFaceRect.h=10;
      drawMaskPlus();
    } else if (mpDrawing) {
      mpFaceRect.w = sx-mpDrawStart.x; mpFaceRect.h = sy-mpDrawStart.y;
      if (mpFaceRect.w<0) { mpFaceRect.x=sx; mpFaceRect.w=-mpFaceRect.w; }
      if (mpFaceRect.h<0) { mpFaceRect.y=sy; mpFaceRect.h=-mpFaceRect.h; }
      drawMaskPlus();
    } else if (mpDragging) {
      mpFaceRect.x = sx-mpDragStart.x; mpFaceRect.y = sy-mpDragStart.y;
      drawMaskPlus();
    }
  });
  mc.addEventListener("mouseup", function() { mpDragging=false; mpDrawing=false; mpResizeHandle=null; });
  mc.addEventListener("mouseleave", function() { mpDragging=false; mpDrawing=false; mpResizeHandle=null; });
})();

function exportMaskPlus() {
  if (!mpImg || !mpFaceSnapshot) { toast("Select and confirm face first!"); return; }
  var w=mpImg.width, h=mpImg.height;
  var cx=mpFaceRect.x+mpFaceRect.w/2+mpOffsetX, cy=mpFaceRect.y+mpFaceRect.h/2+mpOffsetY;
  var nw=mpFaceRect.w*mpScale, nh=mpFaceRect.h*mpScale, nx=cx-nw/2, ny=cy-nh/2;
  var c1=document.createElement("canvas"); c1.width=w; c1.height=h;
  var ctx1=c1.getContext("2d");
  ctx1.fillStyle="black"; ctx1.fillRect(0,0,w,h);
  ctx1.globalAlpha=0.3; ctx1.drawImage(mpImg,0,0,w,h); ctx1.globalAlpha=1.0;
  ctx1.save(); ctx1.translate(cx,cy); ctx1.rotate(mpRotation*Math.PI/180); ctx1.scale(mpScale,mpScale);
  ctx1.drawImage(mpFaceSnapshot,-mpFaceRect.w/2,-mpFaceRect.h/2); ctx1.restore();
  downloadCanvas(c1,"moved.png");
  setTimeout(function(){var c2=document.createElement("canvas");c2.width=w;c2.height=h;var ctx2=c2.getContext("2d");ctx2.fillStyle="black";ctx2.fillRect(0,0,w,h);ctx2.fillStyle="white";if(mpShape==='ellipse'){ctx2.beginPath();ctx2.ellipse(cx,cy,nw/2,nh/2,0,0,Math.PI*2);ctx2.fill();}else{ctx2.fillRect(nx,ny,nw,nh);}downloadCanvas(c2,"face_mask.png");},100);
  setTimeout(function(){var c3=document.createElement("canvas");c3.width=w;c3.height=h;var ctx3=c3.getContext("2d");ctx3.fillStyle="white";ctx3.fillRect(0,0,w,h);ctx3.fillStyle="black";if(mpShape==='ellipse'){ctx3.beginPath();ctx3.ellipse(cx,cy,nw/2,nh/2,0,0,Math.PI*2);ctx3.fill();}else{ctx3.fillRect(nx,ny,nw,nh);}downloadCanvas(c3,"face_body_mask.png");},200);
  setTimeout(function(){var meta={face_x:Math.round(nx),face_y:Math.round(ny),face_w:Math.round(nw),face_h:Math.round(nh),offset_x:mpOffsetX,offset_y:mpOffsetY,scale:Math.round(mpScale*100)/100,rotation:mpRotation,original_face:{x:Math.round(mpFaceRect.x),y:Math.round(mpFaceRect.y),w:Math.round(mpFaceRect.w),h:Math.round(mpFaceRect.h)},image_size:{width:w,height:h} };var blob=new Blob([JSON.stringify(meta,null,2)],{type:"application/json"});var a=document.createElement("a");a.download="metadata.json";a.href=URL.createObjectURL(blob);a.click();URL.revokeObjectURL(a.href);},300);
  // Export face_reference.png (face crop from original)
  setTimeout(function(){
    var fc=document.createElement("canvas");
    fc.width=mpFaceRect.w; fc.height=mpFaceRect.h;
    fc.getContext("2d").drawImage(mpFaceSnapshot,0,0);
    downloadCanvas(fc,"face_reference.png");
  },50);
  // Export identity_reference.png (face + upper body)
  setTimeout(function(){
    var idCanvas=document.createElement("canvas");
    var iw=Math.round(mpFaceRect.w*1.8);
    var ih=Math.round(mpFaceRect.h*3.0);
    var ix=Math.max(0,Math.round(mpFaceRect.x+mpFaceRect.w/2-iw/2));
    var iy=Math.max(0,Math.round(mpFaceRect.y+mpFaceRect.h/2-ih*0.25));
    ix=Math.min(ix,mpImg.width-iw); iy=Math.min(iy,mpImg.height-ih);
    if(ix<0){ix=0;iw=mpImg.width;}
    if(iy<0){iy=0;ih=mpImg.height;}
    iw=Math.min(iw,mpImg.width-ix); ih=Math.min(ih,mpImg.height-iy);
    idCanvas.width=iw; idCanvas.height=ih;
    idCanvas.getContext("2d").drawImage(mpImg,ix,iy,iw,ih,0,0,iw,ih);
    downloadCanvas(idCanvas,"identity_reference.png");
  },150);
  toast("Exported 6 files");
}

function downloadCanvas(canvas,filename) { var a=document.createElement("a"); a.download=filename; a.href=canvas.toDataURL("image/png"); a.click(); }

function closeMaskPlus() { document.getElementById("maskplusOverlay").style.display="none"; mpImg=null; mpFaceSnapshot=null; }

// ===== Mask Editor =====
let maskImg = null, maskCtx = null, maskCanvas = null;
let maskRect = { x: 0, y: 0, w: 200, h: 200 };
let maskDragging = false, maskDragStart = { x: 0, y: 0 };
let maskResizeHandle = null; // 'tl','tr','bl','br', null=none
let maskShape = 'rect';

function openMaskEditor() {
  let items = document.querySelectorAll('.card img');
  if (items.length === 0) { toast('Upload an image first'); return; }
  let overlay = document.getElementById('maskOverlay');
  let canvas = document.getElementById('maskCanvas');
  maskCanvas = canvas;
  maskCtx = canvas.getContext('2d');
  maskImg = new Image();
  maskImg.onload = function() {
    let maxW = window.innerWidth * 0.85, maxH = window.innerHeight * 0.65;
    let scale = Math.min(maxW / maskImg.width, maxH / maskImg.height, 1);
    canvas.width = maskImg.width * scale;
    canvas.height = maskImg.height * scale;
    maskRect = {
      x: maskImg.width * 0.3, y: maskImg.height * 0.2,
      w: maskImg.width * 0.4, h: maskImg.height * 0.4
    };
    maskCtx.setTransform(scale, 0, 0, scale, 0, 0);
    drawMask();
    overlay.style.display = 'flex';
  };
  let origSrc = items[0].src.replace('/api/preview/', '/api/original/'); maskImg.src = origSrc;
}

function closeMaskEditor() {
  document.getElementById('maskOverlay').style.display = 'none';
}

function setMaskShape() {
  maskShape = document.getElementById('maskShape').value;
  drawMask();
}

function drawMask() {
  if (!maskImg || !maskCtx) return;
  let w = maskImg.width, h = maskImg.height;
  maskCtx.clearRect(0, 0, w, h);
  maskCtx.fillStyle = 'white';
  maskCtx.fillRect(0, 0, w, h);
  maskCtx.drawImage(maskImg, 0, 0, w, h);
  maskCtx.fillStyle = 'rgba(0,0,0,0.55)';
  maskCtx.fillRect(0, 0, w, h);
  // Draw the face region (clear = black in final mask)
  maskCtx.save();
  let rx = maskRect.x, ry = maskRect.y, rw = maskRect.w, rh = maskRect.h;
  maskCtx.globalCompositeOperation = 'destination-out';
  if (maskShape === 'ellipse') {
    maskCtx.beginPath();
    maskCtx.ellipse(rx + rw/2, ry + rh/2, rw/2, rh/2, 0, 0, Math.PI*2);
    maskCtx.fill();
  } else {
    maskCtx.fillRect(rx, ry, rw, rh);
  }
  maskCtx.restore();
  // Draw outline
  maskCtx.strokeStyle = '#e74c3c';
  maskCtx.lineWidth = 2;
  if (maskShape === 'ellipse') {
    maskCtx.beginPath();
    maskCtx.ellipse(rx + rw/2, ry + rh/2, rw/2, rh/2, 0, 0, Math.PI*2);
    maskCtx.stroke();
  } else {
    maskCtx.strokeRect(rx, ry, rw, rh);
  }

  // Reposition mode: show face preview at MOVED position
  if (repositionActive && faceSnapshot) {
    let nx = rx + repositionOffsetX, ny = ry + repositionOffsetY;
    maskCtx.strokeStyle = "#27ae60";
    maskCtx.lineWidth = 2;
    maskCtx.setLineDash([6, 3]);
    if (maskShape === "ellipse") {
      maskCtx.beginPath();
      maskCtx.ellipse(nx + rw/2, ny + rh/2, rw/2, rh/2, 0, 0, Math.PI*2);
      maskCtx.stroke();
    } else {
      maskCtx.strokeRect(nx, ny, rw, rh);
    }
    maskCtx.setLineDash([]);
    maskCtx.globalAlpha = 0.7;
    maskCtx.drawImage(faceSnapshot, nx, ny, rw, rh);
    maskCtx.globalAlpha = 1.0;
  }
  // Draw resize handles
  let handles = [[rx,ry],[rx+rw,ry],[rx,ry+rh],[rx+rw,ry+rh]];
  maskCtx.fillStyle = '#e74c3c';
  handles.forEach(([x,y]) => { maskCtx.fillRect(x-4, y-4, 8, 8); });
}

maskCanvas = document.getElementById('maskCanvas');
maskCanvas.addEventListener('mousedown', function(e) {
  if (!maskImg) return;
  let rect = maskCanvas.getBoundingClientRect();
  let sx = (e.clientX - rect.left) * (maskImg.width / maskCanvas.width);
  let sy = (e.clientY - rect.top) * (maskImg.height / maskCanvas.height);
  // Check resize handles
  let h = 10 * (maskImg.width / maskCanvas.width);
  let handles = [
    {id:'tl', x:maskRect.x, y:maskRect.y},
    {id:'tr', x:maskRect.x+maskRect.w, y:maskRect.y},
    {id:'bl', x:maskRect.x, y:maskRect.y+maskRect.h},
    {id:'br', x:maskRect.x+maskRect.w, y:maskRect.y+maskRect.h}
  ];
  maskResizeHandle = null;
  for (let hh of handles) {
    if (Math.abs(sx - hh.x) < h && Math.abs(sy - hh.y) < h) {
      maskResizeHandle = hh.id; break;
    }
  }
  if (!maskResizeHandle) {
    if (repositionActive) {
      let rx = maskRect.x, ry = maskRect.y;
      if (sx >= rx && sx <= rx + maskRect.w && sy >= ry && sy <= ry + maskRect.h) {
        repositionDragging = true;
        repositionDragStart = { x: sx - repositionOffsetX, y: sy - repositionOffsetY };
      }
    } else {
      maskDragging = true;
      maskDragStart = { x: sx - maskRect.x, y: sy - maskRect.y };
    }
  }
  e.preventDefault();
});

maskCanvas.addEventListener('mousemove', function(e) {
  if (!maskImg) return;
  let rect = maskCanvas.getBoundingClientRect();
  let sx = (e.clientX - rect.left) * (maskImg.width / maskCanvas.width);
  let sy = (e.clientY - rect.top) * (maskImg.height / maskCanvas.height);
  if (maskResizeHandle) {
    if (maskResizeHandle.includes('l')) { maskRect.w += maskRect.x - sx; maskRect.x = sx; }
    if (maskResizeHandle.includes('r')) { maskRect.w = sx - maskRect.x; }
    if (maskResizeHandle.includes('t')) { maskRect.h += maskRect.y - sy; maskRect.y = sy; }
    if (maskResizeHandle.includes('b')) { maskRect.h = sy - maskRect.y; }
    if (maskRect.w < 20) maskRect.w = 20;
    if (maskRect.h < 20) maskRect.h = 20;
    drawMask();
  } else if (repositionDragging) {
    repositionOffsetX = sx - repositionDragStart.x;
    repositionOffsetY = sy - repositionDragStart.y;
    drawMask();
  } else if (maskDragging) {
    maskRect.x = sx - maskDragStart.x;
    maskRect.y = sy - maskDragStart.y;
    drawMask();
  }
});

maskCanvas.addEventListener('mouseup', function() {
  maskDragging = false;
  maskResizeHandle = null;
  repositionDragging = false;
});

function downloadMask() {
  if (!maskImg) return;
  let w = maskImg.width, h = maskImg.height;
  let offCanvas = document.createElement('canvas');
  offCanvas.width = w; offCanvas.height = h;
  let ctx = offCanvas.getContext('2d');
  // White background
  ctx.fillStyle = 'white';
  ctx.fillRect(0, 0, w, h);
  // Black face region
  ctx.fillStyle = 'black';
  if (maskShape === 'ellipse') {
    ctx.beginPath();
    ctx.ellipse(maskRect.x + maskRect.w/2, maskRect.y + maskRect.h/2, maskRect.w/2, maskRect.h/2, 0, 0, Math.PI*2);
    ctx.fill();
  } else {
    ctx.fillRect(maskRect.x, maskRect.y, maskRect.w, maskRect.h);
  }
  // Also feather 5px edges
  let link = document.createElement('a');
  link.download = 'face_mask.png';
  link.href = offCanvas.toDataURL('image/png');
  link.click();
  toast('Mask downloaded! Use in Load Mask node of face_body workflow');
}

let repositionActive = false;
let faceSnapshot = null;
let repositionOffsetX = 0;
let repositionOffsetY = 0;
let repositionDragging = false;
let repositionDragStart = { x: 0, y: 0 };

function toggleReposition() {
  repositionActive = document.getElementById("repositionMode").checked;
  document.getElementById("btnMoved").style.display = repositionActive ? "inline-block" : "none";
  if (repositionActive) {
    repositionOffsetX = 0;
    repositionOffsetY = 0;
    // Capture the face area from the original image
    if (maskImg) {
      let off = document.createElement("canvas");
      off.width = maskRect.w; off.height = maskRect.h;
      let ctx = off.getContext("2d");
      ctx.drawImage(maskImg, maskRect.x, maskRect.y, maskRect.w, maskRect.h, 0, 0, maskRect.w, maskRect.h);
      faceSnapshot = off;
    }
  }
  drawMask();
}

function downloadRepositioned() {
  if (!maskImg) return;
  let w = maskImg.width, h = maskImg.height;
  let offCanvas = document.createElement("canvas");
  offCanvas.width = w; offCanvas.height = h;
  let ctx = offCanvas.getContext("2d");
  // Black background
  ctx.fillStyle = "black";
  ctx.fillRect(0, 0, w, h);
  // Draw face at NEW position
  if (faceSnapshot) {
    let nx = maskRect.x + repositionOffsetX;
    let ny = maskRect.y + repositionOffsetY;
    ctx.drawImage(faceSnapshot, nx, ny, maskRect.w, maskRect.h);
  } else {
    // Fallback: draw from original
    ctx.drawImage(maskImg, maskRect.x, maskRect.y, maskRect.w, maskRect.h, maskRect.x, maskRect.y, maskRect.w, maskRect.h);
  }
  let link = document.createElement("a");
  link.download = "face_repositioned.png";
  link.href = offCanvas.toDataURL("image/png");
  link.click();
  setTimeout(function() {
    let maskCanvas = document.createElement("canvas");
    maskCanvas.width = w; maskCanvas.height = h;
    let mctx = maskCanvas.getContext("2d");
    mctx.fillStyle = "white";
    mctx.fillRect(0, 0, w, h);
    mctx.fillStyle = "black";
    let nx = maskRect.x + repositionOffsetX;
    let ny = maskRect.y + repositionOffsetY;
    if (maskShape === "ellipse") {
      mctx.beginPath();
      mctx.ellipse(nx + maskRect.w/2, ny + maskRect.h/2, maskRect.w/2, maskRect.h/2, 0, 0, Math.PI*2);
      mctx.fill();
    } else {
      mctx.fillRect(nx, ny, maskRect.w, maskRect.h);
    }
    let mlink = document.createElement("a");
    mlink.download = "face_mask_repositioned.png";
    mlink.href = maskCanvas.toDataURL("image/png");
    mlink.click();
  }, 250);

  toast("Exported: repositioned face + mask (new position)");
}


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
        idx = len(sessions[session_id]["images"])
        sessions[session_id]["images"].append({"name": f.filename, "image": img, "orig_w": img.width, "orig_h": img.height})
        # Save original to disk for mask editor
        orig_path = UPLOAD_FOLDER / f"orig_{session_id}_{idx}.png"
        img.save(orig_path, "PNG")
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
    # For preview, try original first, fall back to processed
    orig_path = UPLOAD_FOLDER / f"orig_{session_id}_{index}.png"
    if orig_path.exists():
        return send_file(orig_path, mimetype="image/png")
    path = UPLOAD_FOLDER / f"{session_id}_{index}.jpg"
    return send_file(path, mimetype="image/jpeg") if path.exists() else ("", 404)

@app.route("/api/original/<session_id>/<int:index>")
def api_original(session_id, index):
    path = UPLOAD_FOLDER / f"orig_{session_id}_{index}.png"
    return send_file(path, mimetype="image/png") if path.exists() else ("", 404)

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

@app.route("/api/save/<session_id>/<int:index>")
def api_save(session_id, index):
    import io as _io
    if session_id not in sessions:
        return jsonify({"error": "session not found"}), 404
    images = sessions[session_id].get("images", [])
    if index >= len(images):
        return jsonify({"error": "index out of range"}), 404
    img_data = images[index]
    name = request.args.get("name", img_data["name"])
    buf = _io.BytesIO()
    img_data["image"].save(buf, "PNG")
    buf.seek(0)
    return send_file(buf, mimetype="image/png", as_attachment=True, download_name=name)

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
