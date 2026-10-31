# H3 可选工作流

## 全能参考（Ref2VA）

`04_全能参考_Ref2VA/` 需要额外的参考生成扩散模型：

`ComfyUI/models/diffusion_models/minimax_h3_ref2va_pruned_int8_convrot.safetensors`

文件大小约 19.5 GB，本机当前未完整安装。安装后这 8 个工作流即可正常加载；其它 H3 文生视频、图生视频和 Turbo 工作流不依赖它。

下载：

```powershell
python scripts/install_minimax_h3.py --ref2va
```

模型较大时也可以使用分段并发下载器：

```powershell
python scripts/download_model_segmented.py `
  "https://hf-mirror.com/Comfy-Org/MiniMax-H3/resolve/main/diffusion_models/minimax_h3_ref2va_pruned_int8_convrot.safetensors" `
  "ComfyUI/models/diffusion_models/minimax_h3_ref2va_pruned_int8_convrot.safetensors" `
  20970379616 --workers 8
```
