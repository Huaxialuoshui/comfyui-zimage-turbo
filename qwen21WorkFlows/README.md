# Qwen-Image 2.1 工作流

Qwen-Image 2.1 与 Z-Image、Anima、SeFi、MiniMax H3 共用项目根目录下的 `ComfyUI`、模型目录和 `http://127.0.0.1:8188` 入口。

## 模型

运行 `scripts/qwen21/download_models.ps1`，三个文件会直接下载到主模型目录：

| 组件 | 路径 | 大小 |
|---|---|---:|
| Turbo INT8 扩散模型 | `ComfyUI/models/diffusion_models/qwen_image_2.1_turbo_int8_convrot.safetensors` | 6.76 GiB |
| Qwen3-VL 8B W4A8 文本编码器 | `ComfyUI/models/text_encoders/qwen3vl_8b_w4a8.safetensors` | 5.88 GiB |
| Qwen-Image 2.1 VAE | `ComfyUI/models/vae/qwen_image_2.1_vae_bf16.safetensors` | 0.63 GiB |

## 工作流

| 文件 | 用途 |
|---|---|
| `qwen_image_2_1_turbo_lowvram.json` | 8 GB 显存优先入口，默认 512×512、8 步 |
| `qwen_image_2_1_turbo_t2i.json` | 新版文生图模板，带分辨率选择 |
| `qwen_image_2_1_turbo_image_edit.json` | 参考图编辑与风格变换 |
| `qwen_image_2_1_turbo_img2img.json` | 潜空间图生图，保留原图构图并控制变化幅度 |

官方 T2I / Image Edit 模板中的文本编码器已经映射到本机现有的 `qwen3vl_8b_w4a8.safetensors`，避免打开工作流时出现找不到 `qwen3vl_8b_int8_convrot.safetensors`。模板内的高级提示增强分支保持关闭，因为对应的两个 9B PE 模型未下载。

## 启动与出图

双击项目根目录的 `start.bat`，打开 `http://127.0.0.1:8188`，再把工作流 JSON 拖入页面。

命令行冒烟测试：

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\qwen21\generate.ps1 `
  -Prompt "A blue ceramic cup on a wooden table, soft daylight" `
  -Width 512 -Height 512
```

脚本会自动使用统一引擎；如果 8188 尚未启动，它会先在后台启动 ComfyUI。生成图统一保存在 `ComfyUI/output/`。

## 图生图

`qwen_image_2_1_turbo_img2img.json` 使用标准的潜空间图生图链路：

```text
LoadImage -> ImageScaleToTotalPixels -> VAEEncode -> KSampler -> VAEDecode
```

它不会把原图交给视觉编码器，而是先把原图编码成 latent，再用 denoise 控制重绘比例。适合保留构图、人物位置和整体画面，只改变光影、质感、色调或部分细节。

| denoise | 效果 | 建议用途 |
|---:|---|---|
| 0.25~0.35 | 变化很小，保留原图最明显 | 调色、锐化、细微质感 |
| 0.40~0.55 | 保留构图，有明显风格变化 | 换光影、换质感、轻度改造 |
| 0.60~0.75 | 只保留大致构图 | 较大风格变化或动作变化 |

工作流默认 `0.25 MP / 8 步 / CFG 1 / euler + simple / denoise 0.55`，适合 8 GB 显存。需要更高画质时，将 `megapixels` 提升到 `0.5` 或 `1.0`。

命令行示例：

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\qwen21\generate_img2img.ps1 `
  -InputImage "D:\path\to\photo.jpg" `
  -Prompt "cinematic portrait, soft window light, clean background, photorealistic" `
  -NegativePrompt "lowres, bad anatomy, distorted face, blurry, watermark" `
  -Denoise 0.45 -Megapixels 0.5 -Steps 8 -Cfg 1.0 -Seed 20261031
```

脚本会自动启动 ComfyUI、上传输入图，并把结果保存到 `ComfyUI/output/`。

如果目标是“按文字精确修改画面内容”或需要多参考图，优先使用 `qwen_image_2_1_turbo_image_edit.json`；如果目标是“以现有图片为底图调整风格和细节”，使用本图生图工作流更直接。

## 显存建议

- 512×512：RTX 4070 Laptop 8 GB 实测可用，加载后单张约 17 秒。
- 1024×1024：显存压力更高，先关闭其它 GPU 程序再尝试。
- 首次运行需要加载扩散模型和文本编码器，耗时会明显长于后续生成。
