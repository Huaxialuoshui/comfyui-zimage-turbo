# ComfyUI + Z-Image Turbo / Anima / SeFi / MiniMax H3 本地 AI 创作整合包 (v4)

> **开箱即用的本地图像 + 视频生成工作站**：四套模型引擎、78 个中文工作流，装完即用，不需要命令行基础。
>
> 🖼️ 写实 **Z-Image Turbo** · 🎨 二次元 **Anima** · ⚡ 5B Turbo **SeFi** · 🎬 全模态视频 **MiniMax H3**（自带原生双声道音频）

**三步上手**

```
1. setup.bat     → 自动安装 ComfyUI + Z-Image Turbo 模型（首次必跑）
2. start.bat     → 启动 ComfyUI (8188) + 图片对齐工具 (8199)
3. 打开 http://127.0.0.1:8188 → 拖入 workflows/ 里的 JSON → Queue Prompt
```

---

## 快速开始

### 首次安装

| 脚本 | 内容 | 体积 | 是否必须 |
|------|------|:----:|:--------:|
| `setup.bat` | ComfyUI 引擎 + ComfyUI-Manager + QwenVL 节点 + Z-Image Turbo 模型 + Qwen 语言模型 | ~19 GB | ✅ 必须 |
| `anima_setup.bat` | Anima 二次元引擎（UNET + CLIP + VAE） | ~5.2 GB | 可选 |
| `sefi_setup.bat` | SeFi-5B-Turbo 引擎 + `ComfyUI_Rebels_SeFi` 节点 | ~17 GB | 可选 |
| `minimax_h3_setup.bat` | MiniMax H3 全模态视频模型（魔搭源，加 `--ref2va` 再下 20 GB） | ~42.5 GB | 可选 |
| `download_face_detector.bat` | MediaPipe 人脸关键点模型（Face Detailer 用） | 3.6 MB | 可选 |
| `download_qwen_models.bat` | 补齐 Qwen3-0.6B / Qwen2-VL-2B / Qwen3-VL-4B | ~13 GB | 可选 |
| `qwen3vl_download.bat` | Qwen3-VL-2B（替换旧的 Qwen2-VL-2B 提示词链路） | ~4 GB | 可选 |

> 所有下载脚本都支持 **断点续传 + 多次重试 + 文件大小校验**：切换 VPN 节点后重新双击即可续传，不会重复下载。

### 日常启动

| 命令 | 作用 |
|------|------|
| `start.bat` | 一键启动 ComfyUI + Image Resizer，并自动打开 DanbooruSearch 在线标签助手 |
| `resizer.bat` | 只启动 Image Resizer 图片对齐工具 |

### 服务端口

| 服务 | 地址 | 用途 |
|------|------|------|
| ComfyUI | http://127.0.0.1:8188 | 全部图像 / 视频工作流 |
| Image Resizer | http://127.0.0.1:8199 | 参考图裁剪对齐（消除崩脸、马赛克） |

### 环境要求

| 组件 | 要求 |
|------|------|
| 系统 | Windows 10 / 11 |
| Python | 3.10+（本包在 Python 3.13 实测） |
| 显卡 | NVIDIA，8 GB 显存起步；MiniMax H3 建议 24 GB 或开启 CPU offload |
| 内存 | 建议 32 GB+ |
| 硬盘 | 建议 80 GB+（四引擎全装约 85 GB） |
| 页面文件 | **必须 ≥ 32 GB**（系统属性 → 高级 → 性能 → 虚拟内存），否则易在换模型时崩 |
| 运行时 | ComfyUI 0.31.0 · PyTorch 2.11 + CUDA 13（`setup.bat` 会给出安装指引） |

---

## 四大引擎

| 引擎 | 风格 | 默认分辨率 | 采样 | 最适合 |
|------|------|-----------|------|--------|
| **Z-Image Turbo** | 写实 / 照片级 | 1024×1024 | 8 步 beta | 人像、光影、产品图、摄影氛围 |
| **Anima** | 二次元 / 动漫 | 1024×1024 | 35 步 er_sde | 动漫角色、Danbooru 标签、插画风 |
| **SeFi-5B-Turbo** | 通用 Turbo | 1024×1024 | Turbo 少步数 | 快速草稿与风格探索的备选链路 |
| **MiniMax H3** | 全模态视频 | 768P / 24 fps | Turbo LoRA 4~8 步 | 文生视频、首尾帧生视频，**原生双声道音频** |

四套引擎共用同一个 ComfyUI，工作流按目录分开存放，随时切换互不影响。

---

## 我该选哪个工作流

| 你想做什么 | 推荐入口 |
|-----------|---------|
| 写实照片级 AI 图像 | Z-Image → `zimage_turbo_basic` / `zimage_turbo_long_prompt` |
| 短关键词自动扩写出图 | Z-Image → `zimage_turbo_qwenvl` |
| 二次元动漫风格 | Anima → `anima_basic` |
| 动漫角色换姿态 | Anima → `anima_maxpose` |
| 多人互动合成 | Anima → `anima_multifusion` |
| 用自己的照片换场景/光影 | Z-Image → `zimage_turbo_img2img` |
| 保脸 + 自动锐化面部 | Z-Image → `zimage_turbo_face_detailer` |
| 大动作换姿态 | Z-Image → `zimage_turbo_maxpose` |
| 换身体保留脸（最稳） | Z-Image → `zimage_turbo_face_body` |
| 先换脸位再重绘身体 | Z-Image → `zimage_turbo_maskplus`（配 MaskPlus 导出图） |
| 生成正/侧视三视图底图 | Z-Image → `zimage_turbo_threeview_hairless` |
| 让 AI 看图反推提示词 | Z-Image → `qwenvl_image_recognition` |
| 自动生成多幕故事 | Z-Image → `zimage_turbo_storyboard` |
| 批量探索不同种子 | Z-Image → `zimage_turbo_seed_explorer` |
| 快速草稿 / 另一条链路 | SeFi → `sefi_basic` |
| 文生视频（带声音） | MiniMax H3 → `01_文生视频_t2v` |
| 首帧/首尾帧生视频 | MiniMax H3 → `02_图生视频_i2v` |
| 4~8 步快速出片 | MiniMax H3 → `03_Turbo快速` |
| 参考图/视频/音频生成 | MiniMax H3 → `04_全能参考`（需另下 `--ref2va` 模型） |

---

## 工作流总览（共 78 个）

### Z-Image Turbo（19 个，`workflows/`）

#### 文生图

| 工作流 | 文件 | 说明 | 默认分辨率 |
|--------|------|------|-----------|
| **Basic** | `zimage_turbo_basic.json` | 单段 Prompt 直接出图，新手首选 | 1024×1024 |
| **Long Prompt** | `zimage_turbo_long_prompt.json` | 三段式 Prompt（构图/主体/细节），避免长句互相干扰 | 768×1360 |
| **QwenVL Expand** | `zimage_turbo_qwenvl.json` | 短关键词 → AI 自动扩写 → 出图 | 1024×1024 |

#### 图生图 / 身份保持

| 工作流 | 文件 | 说明 | 保脸 |
|--------|------|------|:----:|
| **Img2Img** | `zimage_turbo_img2img.json` | 参考图 + Prompt，denoise 控制变化幅度 | ✅ |
| **Face Detailer** | `zimage_turbo_face_detailer.json` | 双通道：Img2Img 出图 → MediaPipe 识别人脸后精修 | ✅ |
| **Max Pose** | `zimage_turbo_maxpose.json` | 参考图 + 文字描述新动作 | ✅ |
| **Face + Body** | `zimage_turbo_face_body.json` | Mask 锁脸 + 身体重绘（最稳保脸方案） | ✅ |
| **MaskPlus** | `zimage_turbo_maskplus.json` | 换脸位专用：读入 MaskPlus 导出的 `moved.png` + `face_body_mask.png`，两段式（重绘身体 → 羽化合成脸部） | ✅ |
| **Appearance + Pose** | `zimage_turbo_appearance_pose.json` | 双参考图，迁移风格 / 色调 | ➖ |
| **Multi-Fusion** | `zimage_turbo_multifusion.json` | 3 张参考图 latent 混合 | ➖ |
| **Threeview Hairless** | `zimage_turbo_threeview_hairless.json` | 从 `moved.png` 生成正/侧视无发型三视图底图（依赖 `zimage-threeview` 节点） | ✅ |

#### 批量 / 探索

| 工作流 | 文件 | 说明 |
|--------|------|------|
| **Seed Explorer** | `zimage_turbo_seed_explorer.json` | 一次跑 N 张不同种子，滑块挑选最佳 |

#### QwenVL 智能链路

| 工作流 | 文件 | 说明 |
|--------|------|------|
| **Image Recognition** | `qwenvl_image_recognition.json` | 纯反推：上传图 → QwenVL 描述 → 复制提示词 |
| **Analyze + Generate** | `zimage_turbo_qwenvl_analyze_gen.json` | 上传图 → AI 分析 → 混合你写的 Hint |
| **QwenVL Img2Img** | `zimage_turbo_qwenvl_img2img.json` | QwenVL 扩写 + 参考图图生图 |
| **Iterative Refine** | `zimage_turbo_qwenvl_iterative_refine.json` | 两阶段：出图 → AI 评价 → 精修 |
| **Pose Transform** | `zimage_turbo_pose_transform.json` | AI 分析外观 + Prompt 指定新姿态 |

#### 其他

| 工作流 | 文件 | 说明 |
|--------|------|------|
| **Storyboard** | `zimage_turbo_storyboard.json` | 一个主题 → 三幕故事板（可配合 `scripts/storyboard.py` 跑 10 阶段长片） |
| **Inpainting** | `zimage_turbo_inpaint.json` | 图片 + 遮罩 → 局部重绘（兼容性实测中） |

> 历史版本保留在 `workflows/backup/v1`、`workflows/backup/v2`，需要回滚时复制回 `workflows/` 覆盖即可。

### Anima（7 个，`animaWorkFlows/`）

> 2B 参数动漫模型，基于 NVIDIA Cosmos-Predict2，`circlestone-labs/Anima`。
> 专注动画 / 插画 / 艺术风格，**不支持写实照片**。

| 工作流 | 文件 | 说明 |
|--------|------|------|
| **Anima Basic** | `anima_basic.json` | 文生图，Danbooru 标签格式，1024×1024 |
| **Anima Img2Img** | `anima_img2img.json` | 参考图 + 文本引导 |
| **Anima MaxPose** | `anima_maxpose.json` | 动漫角色换姿态（denoise 0.3 微调 ~ 0.7 大改） |
| **Anima Multi-Fusion** | `anima_multifusion.json` | 3 图合成（角色 A + 角色 B + 场景互动） |
| **Anima Face + Body** | `anima_face_body.json` | Mask 锁脸 + 身体重绘，羽化 40px 过渡 |
| **Anima MaskPlus** | `anima_maskplus.json` | 换脸位两段式流程（同 Z-Image MaskPlus 逻辑，35 步 er_sde） |
| **Anima 全家桶总控 V3** | `Anima-全家桶总控-V3-直连.json` | 7 条模型流同屏对比（miaomiao12 / miaomiaoBase / anima_baseV10 / oneObsessionAnima_v30 / anima-aesthetic-v1.1 / animayume_v05 / anima2.9）+ LORA 总控 + 对比图合并；**需额外安装 `ComfyUI-Lora-Manager` 节点** |

**试试 Anima Turbo LoRA**（更快更稳）：下载后放 `ComfyUI/models/loras/` 即可。

### SeFi（4 个，`sefiWorkFlows/`）

> SeFi-5B-Turbo 链路，依赖 `ComfyUI_Rebels_SeFi` 节点的 `RebelsSeFiLoader` / `RebelsSeFiSampler`。
> `sefi_setup.bat` 会一并安装节点与模型。

| 工作流 | 文件 | 说明 |
|--------|------|------|
| **SeFi Basic** | `sefi_basic.json` | 文生图基础链路 |
| **SeFi Long Prompt** | `sefi_long_prompt.json` | 长提示词版本 |
| **SeFi Face + Body** | `sefi_face_body.json` | 锁脸换身体 |
| **SeFi Seed Explorer** | `sefi_seed_explorer.json` | 批量种子探索 |

### MiniMax H3 全模态视频（48 个，`h3WorkFlows/`）

首个开源的全模态视频模型：文本 / 图像 / 视频 / 音频任意组合输入，一次生成带**原生双声道音频**的 768P 视频（24 fps，4~15 秒）。

| 目录 | 用途 | 文件数 |
|------|------|:------:|
| `01_文生视频_t2v` | 纯文字生成视频 + 音频（含 EasyCache 优化版） | 8 |
| `02_图生视频_i2v` | 首帧图 / 尾帧图生成视频 + 音频 | 8 |
| `03_Turbo快速` | turbo LoRA 少步数出片 | 8 |
| `04_全能参考` | T2VA + Ref2VA 多分支参考工作流 | 8 |
| `05_Work-Fisher整合` | 图生视频 + 参考生视频整合流程 | 8 |
| `06_破限增强` | 提示词增强专用（GenerationTail + PromptEnhancer） | 1 |
| `00_参考资料` | 官方提示词写作指南 + 中文反推指令包 | 3 |
| `_backup_fix` | 修复前的原始备份 | 7 |

**文件名后缀含义**

| 后缀 | 含义 |
|------|------|
| 无后缀 | int8 扩散模型版（`minimax_h3_fl2va_pruned_int8`，19.5 GB） |
| `_int4` | int4 低内存版（14.8 GB 扩散模型 + int8 VAE） |
| `_break` | 破限增强版：生成前先经 GenerationTail + PromptEnhancer 改写提示词 |
| `_break_int4` | 破限增强 + int4 低内存 |

**推荐用法**：先到 `06_破限增强` 跑一次增强器拿到改写后的长提示词，再把提示词粘到对应类别的**非 break 版**直接出片（速度最快）；需要每次现场增强就选 `_break` 版（每轮多 20~50 分钟）。

详细说明见 [`h3WorkFlows/README.md`](h3WorkFlows/README.md)，提示词写作规范见 `h3WorkFlows/00_参考资料/`。

> 也可以在启动 ComfyUI 后，直接从模板库 **Video** 分类加载官方 MiniMax H3 模板。

---

## 模型清单

全部模型放在 `ComfyUI/models/`（该目录不纳入 Git，由安装脚本下载）。

### 图像引擎

| 引擎 | 类型 | 文件 | 体积 |
|------|------|------|:----:|
| Z-Image Turbo | 扩散模型 | `diffusion_models/z_image_turbo_bf16.safetensors` | 11.5 GB |
| Z-Image Turbo | 文本编码器 | `text_encoders/qwen_3_4b.safetensors` | 7.5 GB |
| Z-Image Turbo | VAE | `vae/ae.safetensors` | 0.3 GB |
| Z-Image Turbo | 低显存替代 | `diffusion_models/split_files/diffusion_models/z_image_turbo_nvfp4.safetensors` | 4.2 GB |
| Anima | 扩散模型 | `diffusion_models/anima-base-v1.0.safetensors` | 3.9 GB |
| Anima | 文本编码器 | `text_encoders/qwen_3_06b_base.safetensors` | 1.1 GB |
| Anima | VAE | `vae/qwen_image_vae.safetensors` | 0.24 GB |
| SeFi-5B-Turbo | 扩散模型 | `diffusion_models/SeFi-5B-Turbo_transformer_bf16.safetensors` | 9.3 GB |
| SeFi-5B-Turbo | 文本编码器 | `text_encoders/SeFi_Qwen3-VL-4B_text_bf16.safetensors` | 7.5 GB |
| SeFi-5B-Turbo | VAE | `vae/SeFi_VAE.safetensors` | 0.16 GB |

### MiniMax H3 组件

| 组件 | 文件 | 体积 |
|------|------|:----:|
| 扩散 int8 | `diffusion_models/minimax_h3_fl2va_pruned_int8_convrot.safetensors` | 19.5 GB |
| 扩散 int4（省显存） | `diffusion_models/MiniMax_H3_FL2VA_pruned_mixed_int4_int8_convrot.safetensors` | 14.8 GB |
| 文本编码器 | `text_encoders/qwen3vl_32b_minimax_h3_nvfp4_awq.safetensors` | 14.6 GB |
| 生成 tail（破限用） | `text_encoders/qwen3vl_32b_h3_generation_tail_50_63_int8_convrot.safetensors` | 7.1 GB |
| 视频 VAE（int8） | `vae/minimax_h3_video_vae_int8_convrot.safetensors` | 3.0 GB |
| 视频 VAE（fp16） | `vae/minimax_h3_video_vae_fp16.safetensors` | 4.9 GB |
| 音频 VAE | `vae/minimax_h3_audio_vae_fp32.safetensors` | 0.6 GB |
| Turbo LoRA（4 步） | `loras/minimax_h3_turbo_4STEPS_comfyui.safetensors` | 0.7 GB |
| Ref2VA 扩散模型（可选） | `diffusion_models/minimax_h3_ref2va_pruned_int8_convrot.safetensors` | 19.5 GB |

### Qwen 语言 / 视觉模型

放在 `ComfyUI/models/LLM/Qwen-VL/`，供工作流里的智能扩写、图像分析、姿态迁移使用。

| 模型 | 用途 | 体积 |
|------|------|:----:|
| Qwen3-0.6B | PromptEnhancer 提示词扩写（Anima 用） | 1.4 GB |
| Qwen2-VL-2B-Instruct | 旧版姿态分析链路 | 4.1 GB |
| Qwen3-VL-2B-Instruct | 姿态分析 / 图像理解 | 4.0 GB |
| Qwen3-VL-4B-Instruct | analyze_gen、iterative_refine 智能分析 | 8.3 GB |
| Huihui-Qwen3-VL-4B/2B-Instruct-abliterated | 无限制版视觉理解（本地实验） | 8.3 / 4.0 GB |
| Felldude-Qwen3-VL-4B-Uncensored-FP8 | FP8 无限制视觉理解 | 5.3 GB |

### 自定义节点

`setup.bat` 会装好基础节点，其余按需通过 ComfyUI-Manager 安装：

| 节点 | 用途 |
|------|------|
| ComfyUI-Manager | 节点管理器（缺节点时点 Install Missing Nodes） |
| ComfyUI-QwenVL | 提示词扩写 / 图像理解 |
| ComfyUI_Rebels_SeFi | SeFi-5B-Turbo 加载与采样 |
| zimage-threeview | 三视图合成与保存 |
| ComfyUI-Impact-Pack | Face Detailer 面部检测精修 |
| ComfyUI-KJNodes / rgthree-comfy / ComfyUI-VideoHelperSuite | 通用工具、视频合成与预览 |
| ComfyUI-GGUF / ComfyUI_UniBlockSwap / ComfyUI-ReservedVRAM | 量化加载、显存调度 |
| ComfyUI-MiniMax-H3-Guide / -Turbo-2 / minimax-h3-audio-T8 | MiniMax H3 视频与音频链路 |

---

## 提示词指南

### Z-Image Turbo（写实）

```
medium full shot, young woman side lying on white bed, sheer white stockings,
warm golden backlight, photorealistic skin texture, soft bedroom lighting
```

- 结构：`[构图] [主体] [动作] [服饰] [光影] [质感]`，5~10 个短语，逗号分隔，全小写
- **不要**再写 `masterpiece, best quality` 之类的质量词（已内置）
- img2img 模式下**不要描述参考图已有的身体姿态**，只写想改变的部分
- 常见参数：8 步 / beta scheduler / CFG 1.0，denoise 0.35~0.45 保脸改光影

### Anima（二次元）

```
masterpiece, best quality, score_7, safe, 1girl, white sailor uniform,
running through rain, wet hair, puddle splashes, overcast sky
```

- 格式：**Danbooru 标签**，全小写，空格分隔（不是逗号），下划线仅用于 score 标签
- 标签顺序：`[质量/年份/安全] [人数] [角色] [系列] [艺术家] [通用标签]`
- 正面前缀固定：`masterpiece, best quality, score_7, safe,`
- 负面提示词：`worst quality, low quality, score_1, score_2, score_3, artist name`
- 艺术家必须加 `@` 前缀，如 `@hiroyuki okiura`，否则几乎不起作用
- 加权语法可用但要比 SDXL 给得更高，例如 `(chibi:2)`
- 时间标签：`year 2025` 或 `newest` / `recent` / `mid` / `early` / `old`
- 首行写 `ye-pop` 或 `deviantart` 可切换到非动漫艺术数据集风格
- 采样器：`er_sde`（默认，中性平涂）／`euler_a`（柔和）／`dpmpp_2m_sde_gpu`（更有创意）

### MiniMax H3（视频）

- 官方写作规范：`h3WorkFlows/00_参考资料/VIDEO_PROMPT_WRITING_GUIDE_base_en.md`（基础）与 `..._ref_en.md`（参考模式）
- 中文反向改写模板：`h3WorkFlows/00_参考资料/MiniMax+H3反推指令包.txt`，可直接喂给任意大模型帮你写 H3 提示词
- 镜头、光线、音效都要写进提示词，音频与画面是一次生成的

### 内置提示词模板（喂给 LLM 用）

| 文件 | 用途 |
|------|------|
| `prompt_template.txt` | Z-Image 写实短提示词生成 |
| `prompt_template_zimage.txt` | Z-Image 提示词助手（含规则与示例） |
| `prompt_template_anima.txt` | Anima Danbooru 标签提示词生成 |
| `prompt_template_normal.txt` | 双模型通用：自动判断该用 Z-Image 还是 Anima |

用法：把模板内容整段粘贴给 ChatGPT / Claude 等大模型，再描述你的需求，它会按对应格式输出提示词。

---

## 身份保持指南

用自己的照片换场景 / 光影 / 姿态，按需求选：

| 需求 | 工作流 | denoise | 说明 |
|------|--------|---------|------|
| 保脸 + 换场景 | `zimage_turbo_img2img` | 0.35~0.45 | 只改光影氛围 |
| 保脸 + 微改姿态 | `zimage_turbo_img2img` | 0.50~0.60 | 姿势和场景一起变 |
| 保脸 + 自动增强 | `zimage_turbo_face_detailer` | 第一段 0.5 / 第二段 0.25 | 双通道，面部更锐 |
| 大动作换姿态 | `zimage_turbo_maxpose` | 0.55~0.70 | 用文字描述新动作 |
| 只换风格色调 | `zimage_turbo_appearance_pose` | — | 不锁脸，换画风 |
| 脸位也要挪 | `zimage_turbo_maskplus` | 0.80 + 0.45 | 先用 MaskPlus 导出 `moved.png` 与 `face_body_mask.png` |

**参考图预处理流程**

```
上传图片 → 选目标尺寸 → Center Crop → Download → 拖进 ComfyUI
```

1. 打开 Image Resizer（http://127.0.0.1:8199）
2. 上传参考图 → 选目标分辨率（如 768×1360）
3. Center Crop / Fit + Pad → Process → Download
4. 在工作流里加载处理后的图片
5. 用 `appearance_pose` 时记得关掉 `auto_resize_images`

---

## Image Resizer 图片对齐工具

> 解决参考图比例不对导致的崩图、人脸变形、马赛克。

| 功能 | 说明 |
|------|------|
| 拖拽 / 批量上传 | JPG / PNG / WEBP，多图一次处理 |
| 预设尺寸 | 1024²、768×1360、576×1408、1360×768、1408×576、1080×1920、1920×1080 |
| 自定义尺寸 | 步进 8 px，符合 latent 对齐要求 |
| 裁剪模式 | Center Crop（推荐）/ Smart Crop / Fit + Pad / Stretch |
| 预览对比 | 原图与处理结果切换查看 |
| 导出 | 单张下载或 ZIP 批量打包，也可直接保存到本地输出目录 |
| 界面 | 中英双语、多主题 |

---

## 性能参考

| 模型 | 场景 | 步数 | 分辨率 | 采样器 | 参考耗时 |
|------|------|:----:|--------|--------|---------|
| Z-Image | 快速预览 | 4 | 1024² | simple | ~5 s |
| Z-Image | 日常出图 | 8 | 768×1360 | beta | ~10 s |
| Z-Image | 高质量 | 20 | 1024² | beta | ~25 s |
| Z-Image | 批量探索 | 8 | 768×1360 | beta | Seed Explorer 批量 |
| Anima | 日常 | 35 | 1024² | er_sde | normal scheduler |
| Anima | 高质量 | 50 | 1536² | er_sde | 可搭配 euler_a / dpmpp_2m |
| MiniMax H3 | 8 步短片 | 8 | 512² | euler + Turbo LoRA | ~2 min（含模型加载） |
| MiniMax H3 | 4 步短片 | 4 | 512² | euler + Turbo LoRA | ~70 s（含模型加载） |

> 耗时为 RTX 4070 Laptop（8 GB）+ CPU offload 实测参考，显卡越强越快。

---

## 常见问题

**显存不足 / 崩溃**

```
1. 页面文件设为 32GB-64GB（虚拟内存），然后重启
2. 仍崩：start.bat 里给 ComfyUI 加 --lowvram
3. 图像换 z_image_turbo_nvfp4 量化模型；视频改用 _int4 工作流
4. 视频工作流在节点里开启 CPU offload
```

**节点报错 / 红框**

```
ComfyUI 菜单 → Manager → Install Missing Nodes → 重启
Anima 全家桶总控 V3 需要额外的 ComfyUI-Lora-Manager 节点
```

**人脸崩 / 三只手 / 马赛克**

```
人脸崩 → 降 denoise 到 0.35~0.45，负面词加 different face
三只手 → 去掉手势描述（one hand lifting... 之类）
马赛克 → 参考图与生成分辨率不一致，先用 Image Resizer 对齐
```

**Anima 出图发灰 / 马赛克 / 多图拼接**

```
步数太低 → 提到 30-50 步
CFG 太低 → 4-5
提示词格式不对 → 必须用 Danbooru 标签格式（见提示词指南）
写实词太多 → Anima 不支持写实，去掉 realistic / photorealistic
```

**下载失败 / 切换 VPN 后重下**

```
所有安装脚本都支持断点续传（Range + 大小校验 + 最多 5 次重试），
换节点后重新双击脚本即可续传，已下载的文件不会重复下载。
```

**工作流跑出来结果不对**

```
先确认模型文件齐全（对照上面的模型清单）
再确认加载节点的路径与文件名一致
需要回滚旧版工作流：workflows/backup/v2/ 复制回 workflows/ 覆盖
```

---

## 已知限制

| 限制 | 说明 |
|------|------|
| IP-Adapter / InstantID | Z-Image、Anima 均非 SDXL/Flux 架构，不兼容 |
| ControlNet / OpenPose | 无对应 ControlNet 模型，姿态控制靠 img2img + MaxPose |
| Anima 不支持写实 | 专注动漫 / 插画，写实会崩 |
| Anima 文本渲染 | 只能做单个单词或极短短语 |
| Inpainting | 兼容性仍在验证 |
| 极限长宽比 | 建议控制在 3:2 ~ 2:3 |
| MiniMax H3 时长 | 单次生成 4~15 秒，长片需要多段拼接 |

---

## 项目结构

```
comfyui-zimage-package/
├── README.md / AGENTS.md / .gitignore
│
├── setup.bat                   # 一键安装 ComfyUI + Z-Image Turbo
├── start.bat                   # 一键启动 ComfyUI + Image Resizer
├── resizer.bat                 # 只启动 Image Resizer
├── anima_setup.bat / .py       # Anima 引擎安装
├── sefi_setup.bat / .py        # SeFi 引擎安装 + 节点
├── minimax_h3_setup.bat        # MiniMax H3 视频模型下载（魔搭源）
├── download_face_detector.bat  # Face Detailer 人脸模型
├── download_qwen_models.bat/.py # Qwen 语言模型补齐
├── qwen3vl_download.bat / .py  # Qwen3-VL-2B 下载
├── image_resizer.py            # 图片对齐 Web 工具 (8199)
├── prompt_template*.txt        # 4 套提示词模板
│
├── scripts/
│   ├── install.py              # Z-Image 环境安装主脚本
│   ├── install_minimax_h3.py   # H3 模型下载（魔搭 / 断点续传）
│   ├── monitor_h3_videos.py    # H3 出片自动保存助手
│   ├── storyboard.py           # 10 阶段故事板批量生成
│   └── qwenvl_image_variation.py # QwenVL 图像变体生成
│
├── workflows/                  # Z-Image Turbo 19 个工作流
│   └── backup/v1/ v2/          # 历史版本
├── animaWorkFlows/             # Anima 7 个工作流
├── sefiWorkFlows/              # SeFi 4 个工作流
├── h3WorkFlows/                # MiniMax H3 48 个工作流 + 参考资料
│
├── ComfyUI/                    # 引擎本体（setup.bat 安装，不进 Git）
│   ├── models/{diffusion_models,text_encoders,vae,loras,LLM/Qwen-VL,detection}
│   └── custom_nodes/           # Manager / QwenVL / SeFi / threeview / H3 等
│
├── outputs/                    # 生成结果（不进 Git）
└── output_resized/ tmp_resizer/ # 对齐工具输出与缓存（不进 Git）
```

---

## 更新日志

**v4**（当前）

- 新增 MiniMax H3 全模态视频引擎：文生视频 / 首尾帧 / 参考生成，自带双声道音频，48 个工作流分 6 类
- 新增 SeFi-5B-Turbo 引擎与安装脚本（含 `ComfyUI_Rebels_SeFi` 节点）
- 新增 Z-Image `maskplus`（换脸位两段式）与 `threeview_hairless`（三视图底图）
- 新增 Anima `face_body`、`maskplus` 与全家桶总控 V3（7 流对比）
- 新增 QwenVL 图像反推助手 `qwenvl_image_recognition`
- README 全面重写：四大引擎、78 工作流清单、模型清单、提示词与排错手册

**v3**

- Anima 二次元引擎支持 + 独立安装脚本
- Face Detailer 面部精修就绪（MediaPipe 人脸检测）
- QwenVL 智能链路完成（扩写 / 分析 / 精修 / 姿态迁移）
- Image Resizer 图片对齐工具、Seed Explorer 批量探索
- 一键入口 `start.bat`，全工作流节点自带中文提示

**v2**

- 15 个工作流、Face Detailer、Seed Explorer、Image Resizer 与完整文档

**v1**

- 初始版本：ComfyUI + Z-Image Turbo 本地文生图整合包

---

## 许可

| 组件 | 许可 |
|------|------|
| 本整合脚本 | MIT |
| ComfyUI | GPL-3.0 |
| Z-Image Turbo | Apache 2.0 |
| Anima 模型权重 | CircleStone Labs Non-Commercial（**模型不可商用，生成的图片可商用**） |
| SeFi-5B-Turbo / QwenVL | 遵循各自仓库许可 |
| MiniMax H3 | 遵循官方模型许可 |

仅供学习研究使用。

---

## 参考来源

| 项目 | 链接 |
|------|------|
| ComfyUI | https://github.com/comfyanonymous/ComfyUI |
| Z-Image Turbo | https://huggingface.co/Comfy-Org/z_image_turbo |
| Anima | https://huggingface.co/circlestone-labs/Anima |
| Anima Turbo LoRA | https://civitai.com/models/2560840/anima-turbo-lora |
| SeFi-Image-5B-Turbo | https://huggingface.co/realrebelai/SeFi-Image-5B-Turbo |
| MiniMax H3（魔搭） | https://modelscope.cn/models/Comfy-Org/MiniMax-H3 |
| QwenVL | https://github.com/QwenLM/Qwen3-VL |
| ComfyUI-Manager | https://github.com/ltdrdata/ComfyUI-Manager |
| DanbooruSearch 标签助手 | https://huggingface.co/spaces/SAkizuki/DanbooruSearch |
