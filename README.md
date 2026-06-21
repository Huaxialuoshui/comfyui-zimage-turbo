# ComfyUI + Z-Image Turbo 本地文生图整合包

> 基于 ComfyUI + Z-Image Turbo 模型的一站式本地 AI 绘图工作流套件。
> 含 12+ 即用工作流、QwenVL 提示词扩写、参考图身份保持、图片对齐工具。
> 下载即用，无需联网，**中文友好**。

---

## ?? 快速预览

`
start.bat        → 一键启动 ComfyUI (8188) + Image Resizer (8199)
resizer.bat      → 仅启动 Image Resizer
setup.bat        → 一键安装 (首次运行)
`

---

## ?? 核心特性

| 特性 | 说明 |
|------|------|
| **Z-Image Turbo** | 高性能文生图模型，4~8 步秒级出图 |
| **QwenVL** | 阿里通义千问 VL 模型，短关键词自动扩写成高质量 Prompt |
| **ComfyUI** | 节点式工作流引擎，可视化搭建出图管线 |
| **12+ 即用工作流** | 覆盖文生图、图生图、身份保持、姿势变换、故事板等场景 |
| **Image Resizer** | Web UI 图片对齐工具，适配工作流分辨率要求 |
| **Appearance + Pose** | 双参考图——一张锁面部发型，一张锁姿态 |

---

## ?? 快速开始

### 环境要求

- **系统**: Windows 10/11
- **Python**: 3.10+
- **显卡**: NVIDIA, 建议 8GB+ 显存
  - 16G+ → BF16 模型（默认）
  - 8~12G → FP8 模型（显存更友好）
- **硬盘**: 建议 50GB+ 剩余空间（含模型）

### 一键安装

`atch
双击 setup.bat
`

自动完成：
1. 克隆 ComfyUI + 安装依赖
2. 安装 ComfyUI-Manager 节点管理器
3. 安装 QwenVL 节点
4. 下载 Z-Image Turbo 模型（安装时可选 bf16 / fp8）
5. 生成全部工作流

### 一键启动

`atch
双击 start.bat
`

启动后自动打开两个页面：

| 服务 | 地址 | 说明 |
|------|------|------|
| ComfyUI | http://127.0.0.1:8188 | 工作流出图 |
| Image Resizer | http://127.0.0.1:8199 | 图片对齐工具 |

---

## ?? 工作流总览

### ?? 文生图 (TXT2IMG)

| 工作流 | 文件 | 说明 | 默认分辨率 |
|--------|------|------|-----------|
| **Basic** | zimage_turbo_basic.json | 单段 Prompt，直接出图，最简单快速 | 1024×1024 |
| **Long Prompt** | zimage_turbo_long_prompt.json | 三段式 Prompt（主体/服饰/氛围），避免构图冲突 | 768×1360 |
| **QwenVL Expand** | zimage_turbo_qwenvl.json | 输入短关键词 → QwenVL 自动扩写 → 出图 | 1024×1024 |

### ?? 图生图 (IMG2IMG / 身份保持)

| 工作流 | 文件 | 说明 |
|--------|------|------|
| **Img2Img** | zimage_turbo_img2img.json | 加载参考图 + 修改 Prompt，低 denoise 锁脸换背景/服饰 |
| **Appearance + Pose** | zimage_turbo_appearance_pose.json | **双参考图**：Image A 锁面部+发型，Image B 锁姿态动作 |
| **Max Pose Change** | zimage_turbo_maxpose.json | 单张参考图 + Prompt 描述新动作，denoise 滑块控制变化幅度 |
| **Pose Transform** | zimage_turbo_pose_transform.json | QwenVL 先分析人物外观，再用 Prompt 指定新姿态 |
| **Multi-Image Fusion** | zimage_turbo_multifusion.json | 多张图片 latent 混合融合（3 输入） |

### ?? QwenVL 智能工作流

| 工作流 | 文件 | 说明 |
|--------|------|------|
| **QwenVL Analyze + Generate** | zimage_turbo_qwenvl_analyze_gen.json | 上传参考图，AI 分析后混合你给的 Hint 生成 |
| **QwenVL Img2Img** | zimage_turbo_qwenvl_img2img.json | QwenVL 扩写 + 参考图图生图 |
| **QwenVL Iterative Refine** | zimage_turbo_qwenvl_iterative_refine.json | 两阶段：生图 → AI 评价 → 图生图精修，质量最高 |

### ?? 其他

| 工作流 | 文件 | 说明 |
|--------|------|------|
| **Storyboard** | zimage_turbo_storyboard.json | 一次输入主题，自动生成 3 个连续场景的故事板 |

### ?? 通用设置

所有工作流默认已配置好分辨率控件：

| 参数 | 预设值 | 说明 |
|------|--------|------|
| Width / Height | 见各工作流 | 直接在 UI 中调整，步进 8px |
| Steps | 4~8 | Z-Image Turbo 低步数即可出图 |
| CFG | 1.0 | Turbo 模型推荐值 |
| Scheduler | simple / beta | beta 调度器更稳定 |

---

## ??? Image Resizer 图片对齐工具

用于将参考图片缩放到工作流所需的精确分辨率，避免 latent 尺寸不匹配导致的报错。

**启动方式：**
- start.bat 自动启动（端口 8199）
- 单独双击 
esizer.bat

**功能：**
- 拖拽上传，单张/批量处理
- **预设尺寸**：10242、768×1360、576×1408、1080×1920 等
- **自定义尺寸**：宽高独立输入，步进 8px
- **三种裁剪模式**：Center Crop / Stretch Fill / Fit + Pad（黑边）
- **实时预览** + ZIP 打包下载
- **中英文切换** + **四套主题色**

---

## ?? 目录结构

`
comfyui-zimage-package/
├── ComfyUI/                        # ComfyUI 主程序
│   ├── main.py                     # 启动入口
│   ├── models/
│   │   ├── checkpoints/            # 模型 (z_image_turbo*.safetensors)
│   │   ├── vae/                    # VAE 模型 (ae.safetensors)
│   │   ├── clip/                   # CLIP 模型 (qwen_3_4b*.safetensors)
│   │   └── LLM/                    # QwenVL 模型
│   ├── custom_nodes/               # 扩展节点
│   │   ├── ComfyUI-Manager/
│   │   └── ComfyUI-QwenVL/
│   └── comfy_extras/
│       └── nodes_zimage.py         # Z-Image 自定义节点 (TextEncodeZImageOmni)
├── workflows/                      # ? 12+ 即用工作流
│   ├── zimage_turbo_basic.json
│   ├── zimage_turbo_long_prompt.json
│   ├── zimage_turbo_img2img.json
│   ├── zimage_turbo_appearance_pose.json
│   ├── zimage_turbo_maxpose.json
│   ├── zimage_turbo_pose_transform.json
│   ├── zimage_turbo_multifusion.json
│   ├── zimage_turbo_qwenvl.json
│   ├── zimage_turbo_qwenvl_analyze_gen.json
│   ├── zimage_turbo_qwenvl_img2img.json
│   ├── zimage_turbo_qwenvl_iterative_refine.json
│   ├── zimage_turbo_storyboard.json
│   └── backup/                     # 工作流备份
├── scripts/
│   ├── install.py                  # 一键安装脚本
│   ├── qwenvl_image_variation.py
│   └── storyboard.py
├── image_resizer.py                # Web UI 图片对齐工具
├── prompt_template.txt             # 提示词编写模板
├── resizer.bat                     # Image Resizer 独立启动
├── setup.bat                       # 一键安装
├── start.bat                       # 一键启动 (ComfyUI + Resizer)
└── README.md                       # 本文件
`

---

## ?? 使用技巧

### 提示词编写原则

参考 prompt_template.txt：
- 简短精炼，5~10 个英文关键词/短语
- 全小写，逗号分隔
- 结构：[主体] [动作/姿态] [服饰] [场景] [光影]
- 无需加 quality 标签（已内置）

### 身份保持 (人脸锁定)

| 方法 | 工作流 | 效果 |
|------|--------|------|
| **最佳** | ppearance_pose | 参考图 → TextEncodeZImageOmni 注入，保脸保发型保服装 |
| **次选** | img2img | denoise 0.35~0.45，修改背景/服饰/风格 |
| **灵活** | maxpose | 1 张参考图 + 文字描述新动作，denoise 控制变化幅度 |

### 参考图正确使用流程

1. 打开 **Image Resizer** → 选择目标分辨率（如 768×1360）
2. 上传参考图 → 选 Center Crop → 处理并下载
3. 在 ppearance_pose 工作流中加载处理后的图片
4. **关掉** TextEncodeZImageOmni 的 uto_resize_images
5. 出图

### 性能优化

| 场景 | 操作 |
|------|------|
| **显存不足** | 模型换 FP8 版 + 分辨率降至 768×768 |
| **速度优先** | Steps=4, Scheduler=simple |
| **质量优先** | 用 qwenvl_iterative_refine 两阶段精修 |
| **9:16 竖屏** | Width=768, Height=1360 |

---

## ?? GPU 相关问题

### CUDA out of memory

`atch
1. 换用 FP8 模型 (z_image_turbo_fp8.safetensors)
2. 降低分辨率: 1024×1024 → 768×768
3. 关闭浏览器/其他占用显存的程序
4. 减小 batch_size (部分工作流支持)
`

### 页面文件太小

`
系统属性 → 高级 → 性能设置 → 高级 → 虚拟内存更改
→ 自定义: 初始 32768 MB, 最大 65536 MB
→ 设置 → 确定 → 重启
`

### 找不到模型 / 节点

见 setup.bat，或通过 ComfyUI-Manager 手动安装缺失节点。

---

## ?? 参考来源

| 项目 | 链接 |
|------|------|
| ComfyUI | https://github.com/comfyanonymous/ComfyUI |
| Z-Image Turbo | https://huggingface.co/Comfy-Org/z_image_turbo |
| QwenVL (Qwen2-VL) | https://github.com/QwenLM/Qwen2-VL |
| ComfyUI-Manager | https://github.com/ltdrdata/ComfyUI-Manager |
| Pixaroma 工作流 | https://www.youtube.com/@pixaroma |

---

## ?? 许可

本项目整合的各组件遵循各自许可证：

| 组件 | 许可 |
|------|------|
| ComfyUI | GPL-3.0 |
| Z-Image Turbo | Apache 2.0 |
| QwenVL | Apache 2.0 |
| 本整合脚本 | MIT |

仅供学习和研究使用。
