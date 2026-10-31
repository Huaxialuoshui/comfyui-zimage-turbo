# Anima 高级可选工作流

这个目录不参与默认工作流清单。这里的工作流可以使用现有 Anima 基础链路，但还需要额外的第三方模型或 LoRA。

## Anima 全家桶总控 V3

`Anima-全家桶总控-V3-直连.json` 是一个 7 路底模对比工作流，默认引用了以下本机未安装的文件：

- `miaomiaoHarem_anima12.safetensors`
- `miaomiaoHarem_animaBase.safetensors`
- `anima_baseV10.safetensors`
- `oneObsessionAnima_v30.safetensors`
- `anima-aesthetic-v1.1.safetensors`
- `animayume_v05.safetensors`
- `Anima-2.9B-preview-v1.safetensors`

工作流还配置了多个第三方 LoRA。加载后请在各个 `UNETLoader` 和 LoRA 管理节点里改成自己的文件；如果只使用开箱即用模型，请打开上级目录的 `anima_basic.json` 或 `anima_img2img.json`。

必需的节点依赖已经统一安装：

- ComfyUI-Lora-Manager
- ComfyUI_Comfyroll_CustomNodes
- Comfyui-Memory_Cleanup
