# ComfyUI + Z-Image Turbo 本地文生图整合包

> 基于 ComfyUI + Z-Image Turbo 模型的一站式本地 AI 绘图工作流套件。
> 含 **15 个即用工作流**、QwenVL 提示词扩写、参考图身份保持、图片对齐工具。
> 下载即用，无需联网，**中文友好**。

---

## 快速开始

```batch
start.bat         → 一键启动 ComfyUI (8188) + Image Resizer (8199)
resizer.bat       → 仅启动 Image Resizer
setup.bat         → 一键安装（首次运行）
download_face_detector.bat  → 下载人脸检测模型（Face Detailer 需要）
```

启动后自动打开两个页面：

| 服务 | 地址 | 说明 |
|------|------|------|
| ComfyUI | http://127.0.0.1:8188 | 工作流出图 |
| Image Resizer | http://127.0.0.1:8199 | 图片对齐工具 |

---

## 环境要求

- **系统**: Windows 10/11
- **Python**: 3.10+
- **显卡**: NVIDIA, 建议 8GB+ 显存
  - 8GB → `--lowvram` + 页面文件 ≥32GB
  - 16GB+ → 正常模式
- **硬盘**: 建议 50GB+ 剩余空间（含模型）

---

## 工作流总览（15 个）

### 文生图（TXT2IMG）

| 工作流 | 文件 | 说明 | 默认分辨率 |
|--------|------|------|-----------|
| **Basic** | `zimage_turbo_basic.json` | 单段 Prompt 直接出图，最简单快速 | 1024×1024 |
| **Long Prompt** | `zimage_turbo_long_prompt.json` | 三段式 Prompt（主体/服饰/氛围），避免构图冲突 | 768×1360 |
| **QwenVL Expand** | `zimage_turbo_qwenvl.json` | 输入短关键词 → QwenVL 自动扩写 → 出图 | 1024×1024 |

### 图生图 / 身份保持（IMG2IMG）

| 工作流 | 文件 | 说明 |
|--------|------|------|
| **Img2Img** ⭐ | `zimage_turbo_img2img.json` | 加载参考图 + 修改 Prompt，denoise 控制保脸/换场景 |
| **Face Detailer** | `zimage_turbo_face_detailer.json` | 双通道增强：Img2Img → 细节精修，不依赖第三方检测模型 |
| **Max Pose Change** | `zimage_turbo_maxpose.json` | 单张参考图 + 文字描述新动作，denoise 滑块控制变化幅度 |
| **Appearance + Pose** | `zimage_turbo_appearance_pose.json` | 双参考图风格融合（不锁脸，换画风/色调用） |
| **Multi-Image Fusion** | `zimage_turbo_multifusion.json` | 3 张图 latent 混合融合 |

### 批量 / 探索

| 工作流 | 文件 | 说明 |
|--------|------|------|
| **Seed Explorer** | `zimage_turbo_seed_explorer.json` | 一次跑 4~8 张不同种子，网格视图挑选最佳 |

### QwenVL 智能工作流

| 工作流 | 文件 | 说明 |
|--------|------|------|
| **QwenVL Analyze + Generate** | `zimage_turbo_qwenvl_analyze_gen.json` | 上传参考图，AI 分析后混合你的 Hint 生成 |
| **QwenVL Img2Img** | `zimage_turbo_qwenvl_img2img.json` | QwenVL 扩写 + 参考图图生图 |
| **QwenVL Iterative Refine** | `zimage_turbo_qwenvl_iterative_refine.json` | 两阶段：生图 → AI 评价 → 图生图精修，质量最高 |
| **Pose Transform** | `zimage_turbo_pose_transform.json` | QwenVL 分析人物外观 → Prompt 指定新姿态 |

### 其他

| 工作流 | 文件 | 说明 |
|--------|------|------|
| **Storyboard** | `zimage_turbo_storyboard.json` | 一次输入主题，自动生成 3 个连续场景的故事板 |
| **Inpainting** ⚠️ | `zimage_turbo_inpaint.json` | 加载图片 + 遮罩 → 局部重绘（Z-Image 兼容性待验证） |

---

## 核心特性

| 特性 | 说明 |
|------|------|
| **Z-Image Turbo** | SD3 架构高性能文生图模型，bf16 11.5GB / nvfp4 ~3GB |
| **QwenVL** | 阿里通义千问 VL 模型，短关键词自动扩写成高质量 Prompt |
| **15 个即用工作流** | 每个节点自带中文使用提示，覆盖主流场景 |
| **Image Resizer** | Web UI 图片对齐工具，预设尺寸 + 居中裁剪/拉伸/留黑边 |
| **分辨率可配** | 所有工作流 Width/Height 输入可调，默认适配模型训练分布 |
| **OOM 保护** | 支持 `--lowvram` 模式，8GB 显存可用 |
| **工作流备份** | `backup/v2/` 保存所有版本，出问题可回滚 |

---

## 提示词编写原则

- 简洁精炼，5~10 个英文关键词/短语
- 全小写，逗号分隔
- 结构：`[主体] [动作/姿态] [服饰] [场景] [光影]`
- 无需加 `quality` 标签（已内置）

**示例：**
```
medium full shot, young woman side lying on white bed, sheer white stockings, warm golden backlight, photorealistic
```

---

## 身份保持（人脸锁定）指南

| 方法 | 工作流 | 效果 | denoise |
|------|--------|------|---------|
| **最佳** | `img2img` | 保脸 + 换场景/光影 | 0.35~0.45 |
| **增强** | `face_detailer` | 保脸 + 自动细节增强 | Stage1:0.5, Stage2:0.25 |
| **灵活** | `maxpose` | 保脸 + 文字改姿态 | 0.3~0.6 |
| **不保脸** | `appearance_pose` | 只换画风/色调/构图 | — |

### 参考图正确使用流程

1. 打开 **Image Resizer** → 选择目标分辨率（如 768×1360）
2. 上传参考图 → 选 Center Crop → 处理并下载
3. 在工作流中加载处理后的图片
4. 如果用 `appearance_pose`：关掉 TextEncodeZImageOmni 的 `auto_resize_images`
5. 出图

---

## 性能优化

| 场景 | 操作 |
|------|------|
| **显存不足** | nvfp4 模型 + `--lowvram` + 页面文件 ≥32GB |
| **速度优先** | Steps=4, Scheduler=simple, 1024×1024 |
| **质量优先** | `qwenvl_iterative_refine` 两阶段精修 |
| **9:16 竖屏** | Width=768, Height=1360 (1.04M 像素, 模型分布内) |
| **批量挑选** | `seed_explorer`, Batch Size=4~8, randomize 种子 |

---

## 常见问题

### CUDA out of memory / access violation

```
1. 换用 nvfp4 模型（已在 models/diffusion_models/）
2. 设页面文件 ≥32GB: 系统属性 → 高级 → 性能 → 虚拟内存 → 自定义 32768-65536
3. 关闭浏览器等占用显存的程序
4. 重启电脑
```

### Face Detailer 报错

```
Face Detailer 使用纯双通道增强，不依赖 MediaPipe。
如果之前的 version 报 "face_landmarker" 错误，重新加载工作流即可。
```

### 工作流出问题想回滚

```
workflows/backup/v2/ 保存了所有历史版本，直接复制回 workflows/ 覆盖即可。
```

---

## 项目结构

```
comfyui-zimage-package/
├── ComfyUI/                    # ComfyUI 引擎
│   ├── models/
│   │   ├── diffusion_models/   # UNET 模型
│   │   ├── vae/                # VAE 模型
│   │   ├── clip/               # CLIP 模型
│   │   ├── detection/          # 人脸检测模型
│   │   └── LLM/                # QwenVL 模型
│   ├── custom_nodes/
│   │   ├── ComfyUI-Manager/
│   │   └── ComfyUI-QwenVL/
│   └── comfy_extras/
│       └── nodes_zimage.py     # Z-Image 自定义节点
├── workflows/                  # 15 个即用工作流
│   └── backup/v2/              # 工作流备份
├── image_resizer.py            # Web UI 图片对齐工具
├── download_face_detector.bat  # 人脸检测模型下载
├── resizer.bat                 # Image Resizer 独立启动
├── setup.bat                   # 一键安装
├── start.bat                   # 一键启动
└── README.md
```

---

## 参考来源

| 项目 | 链接 |
|------|------|
| ComfyUI | https://github.com/comfyanonymous/ComfyUI |
| Z-Image Turbo | https://huggingface.co/Comfy-Org/z_image_turbo |
| QwenVL (Qwen2-VL) | https://github.com/QwenLM/Qwen2-VL |
| ComfyUI-Manager | https://github.com/ltdrdata/ComfyUI-Manager |

---

## 许可

| 组件 | 许可 |
|------|------|
| ComfyUI | GPL-3.0 |
| Z-Image Turbo | Apache 2.0 |
| QwenVL | Apache 2.0 |
| 本整合脚本 | MIT |

仅供学习和研究使用。
