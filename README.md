# ComfyUI + Z-Image Turbo 本地文生图整合包

> 基于 ComfyUI + Z-Image Turbo 模型的一站式本地 AI 绘图工作流套件。
> 含 **15 个即用工作流**、QwenVL 提示词扩写、图生图身份保持、图片对齐工具。
> 每个节点自带中文使用提示，下载即用，**中文友好**。

---

## 快速开始

```batch
start.bat         → 一键启动 ComfyUI (8188) + Image Resizer (8199)
resizer.bat       → 仅启动 Image Resizer
setup.bat         → 一键安装（仅首次运行）
```

启动后自动打开两个页面：

| 服务 | 地址 | 说明 |
|------|------|------|
| ComfyUI | http://127.0.0.1:8188 | 工作流出图 |
| Image Resizer | http://127.0.0.1:8199 | 图片对齐工具 |

---

## 环境要求

| 组件 | 要求 |
|------|------|
| 系统 | Windows 10/11 |
| Python | 3.10+ |
| 显卡 | NVIDIA，建议 8GB+ 显存 |
| 内存 | 建议 32GB+ |
| 硬盘 | 建议 50GB+ 剩余空间 |
| 页面文件 | **必须 ≥ 32GB**（系统属性 → 高级 → 性能 → 虚拟内存） |

---

## 工作流总览（15 个）

### 文生图

| 工作流 | 文件 | 说明 | 默认分辨率 |
|--------|------|------|-----------|
| **Basic** | `zimage_turbo_basic.json` | 单段 Prompt 直接出图 | 1024×1024 |
| **Long Prompt** | `zimage_turbo_long_prompt.json` | 三段式 Prompt，避免构图冲突 | 768×1360 |
| **QwenVL Expand** | `zimage_turbo_qwenvl.json` | 短关键词 → QwenVL 自动扩写 → 出图 | 1024×1024 |

### 图生图 / 身份保持

| 工作流 | 文件 | 说明 | 保脸 |
|--------|------|------|:--:|
| **Img2Img** ⭐ | `zimage_turbo_img2img.json` | 参考图 + 修改 Prompt，denoise 控制变化幅度 | ✅ |
| **Face Detailer** | `zimage_turbo_face_detailer.json` | 双通道增强：Img2Img → 细节精修，纯模型驱动 | ✅ |
| **Max Pose** | `zimage_turbo_maxpose.json` | 参考图 + 文字描述新动作，denoise 滑块 | ✅ |
| **Appearance + Pose** | `zimage_turbo_appearance_pose.json` | 双参考图风格/色调融合（不锁脸） | ❌ |
| **Multi-Fusion** | `zimage_turbo_multifusion.json` | 3 张图 latent 混合融合 | ❌ |

### 批量 / 探索

| 工作流 | 文件 | 说明 |
|--------|------|------|
| **Seed Explorer** | `zimage_turbo_seed_explorer.json` | 一次跑 N 张不同种子，预览滑块挑选最佳 |

### QwenVL 智能工作流

| 工作流 | 文件 | 说明 |
|--------|------|------|
| **Analyze + Generate** | `zimage_turbo_qwenvl_analyze_gen.json` | 上传图 → AI 分析 → 混合你的 Hint |
| **Img2Img** | `zimage_turbo_qwenvl_img2img.json` | QwenVL 扩写 + 参考图图生图 |
| **Iterative Refine** | `zimage_turbo_qwenvl_iterative_refine.json` | 两阶段：生图 → AI 评价 → 精修 |
| **Pose Transform** | `zimage_turbo_pose_transform.json` | AI 分析人物外观 + Prompt 指定新姿态 |

### 其他

| 工作流 | 文件 | 说明 |
|--------|------|------|
| **Storyboard** | `zimage_turbo_storyboard.json` | 一个主题 → 自动生成三幕故事板 |
| **Inpainting** ⚠️ | `zimage_turbo_inpaint.json` | 图片 + 遮罩 → 局部重绘 (实测中) |

---

## 身份保持指南

你需要"放自己的照片 + 换场景/光影/姿态"，按需求选：

| 需求 | 工作流 | denoise | 说明 |
|------|--------|---------|------|
| 保脸 + 换场景 | `img2img` | 0.35~0.45 | 只改光影氛围 |
| 保脸 + 微改姿态 | `img2img` | 0.50~0.60 | 姿势和场景一起变 |
| 保脸 + 自动增强 | `face_detailer` | S1:0.5 S2:0.25 | 双通道，细节更锐 |
| 大动作换姿态 | `maxpose` | 0.55~0.70 | 文字描述新动作 |
| 只换风格色调 | `appearance_pose` | — | 不锁脸，换画风 |

### 参考图预处理

1. 打开 **Image Resizer** (8199)
2. 上传参考图 → 选目标分辨率（如 768×1360）
3. Center Crop / Smart Crop / Fit+Pad → Process → Download
4. 工作流中加载处理后的图片
5. 如果用 `appearance_pose`：关掉 `auto_resize_images`

---

## Image Resizer 图片对齐工具

| 功能 | 说明 |
|------|------|
| 拖拽上传 | 支持单张/批量 JPG/PNG/WEBP |
| 预设尺寸 | 1024²、768×1360、576×1408、1080×1920 等 8 种 |
| 自定义 | 步进 8px，对齐 latent 要求 |
| Center Crop | 居中裁剪，推荐 |
| Smart Crop | 等同居中裁剪 |
| Stretch Fill | 拉伸填满 |
| Fit + Pad | 等比缩放 + 黑边填充 |
| 批量下载 | ZIP 打包 |

---

## 常见问题

### 显存不足 / access violation
```
1. 页面文件设为 32GB-64GB（系统属性 → 高级 → 性能 → 虚拟内存）
2. 重启电脑
3. 如果仍崩：start.bat 加 --lowvram，或换用 nvfp4 模型
```

### 工作流节点报错
```
ComfyUI-Manager 会自动提示缺失节点，点击 Install Missing Nodes。
Seed Explorer 已移除 ImageGridComposite 依赖，无需额外安装。
```

### 出图人脸崩/三手/马赛克
```
人脸崩 → 降 denoise (0.35~0.45) + 负面词加 different face
三手   → 去掉提示词中的手势描述（one hand lifting...）
马赛克 → 参考图与生成分辨率不一致，用 Image Resizer 对齐 + 关 auto_resize
```

### 回滚工作流
```
workflows/backup/v2/ 保存了全部历史版本，复制回 workflows/ 覆盖即可。
```

---

## 提示词模板

```
medium full shot, young woman side lying on white bed, sheer white stockings,
warm golden backlight, photorealistic skin texture, soft bedroom lighting
```

结构：`[构图] [主体] [动作] [服饰] [光影] [质感]`

- 简洁 5~10 个短语，逗号分隔
- 全小写英文
- img2img 模式下**不描述参考图已有的身体姿态**（避免冲突）

---

## 性能参考

| 场景 | Steps | Scheduler | 分辨率 | 说明 |
|------|-------|-----------|--------|------|
| 快速预览 | 4 | simple | 1024² | ~5 秒 |
| 日常出图 | 8 | beta | 768×1360 | ~10 秒 |
| 高质量 | 20 | beta | 1024² | ~25 秒 |
| 批量探索 | 8 | beta | 768×1360 | Seed Explorer |

---

## 已知限制

| 限制 | 说明 |
|------|------|
| IP-Adapter/InstantID | Z-Image 非 SDXL/Flux 架构，不兼容 |
| ControlNet/OpenPose | 无对应 ControlNet 模型 |
| Inpainting (VAEEncodeForInpaint) | SD3 架构兼容性待验证 |
| 极限长宽比 | 建议 3:2 ~ 2:3，极端比例可能出现 artifacts |

---

## 项目结构

```
comfyui-zimage-package/
├── ComfyUI/                    # ComfyUI 引擎 (setup.bat 安装)
├── workflows/                  # 15 个即用工作流
│   └── backup/v2/              # 工作流备份
├── image_resizer.py            # Web UI 图片对齐工具 (8199)
├── resizer.bat                 # Image Resizer 独立启动
├── setup.bat                   # 一键安装
├── start.bat                   # 一键启动
├── download_face_detector.bat  # 人脸检测模型下载 (暂不必须)
└── README.md
```

---

## 参考来源

| 项目 | 链接 |
|------|------|
| ComfyUI | https://github.com/comfyanonymous/ComfyUI |
| Z-Image Turbo | https://huggingface.co/Comfy-Org/z_image_turbo |
| QwenVL | https://github.com/QwenLM/Qwen2-VL |
| ComfyUI-Manager | https://github.com/ltdrdata/ComfyUI-Manager |

---

## 许可

本整合脚本 MIT 许可。ComfyUI (GPL-3.0)、Z-Image Turbo (Apache 2.0)、QwenVL (Apache 2.0) 遵循各自许可。仅供学习研究使用。
