# H3 工作流分类说明

按用途分为 6 类，每个工作流有 1~4 个变体，通过文件后缀区分：

| 后缀 | 含义 |
|---|---|
| （无后缀） | int8 扩散模型版（minimax_h3_fl2va_pruned_int8，19.5GB） |
| `_int4` | int4 低内存版（MiniMax_H3_FL2VA_pruned_mixed_int4_int8，14.8GB + int8 VAE） |
| `_break` | 破限增强版：生成前先经 GenerationTail + PromptEnhancer 改写提示词 |
| `_break_int4` | 破限增强 + int4 低内存 |

所有版本共用 nvfp4 编码器（14.6GB）+ int8 生成 tail（7.1GB，仅 break 版需要）。

## 目录

| 文件夹 | 用途 | 文件 |
|---|---|---|
| `01_文生视频_t2v` | 纯文字生成视频+音频 | minimax_h3_t2v（含 EasyCache 优化版） |
| `02_图生视频_i2v` | 首帧图/尾帧图生成视频+音频 | minimax_h3_i2v（含 EasyCache 优化版） |
| `03_Turbo快速` | 4~8 步快速出片（Turbo LoRA） | MiniMax H3 turbo / MiniMax_H3_turbo_EasyCache_opt |
| `04_全能参考` | T2VA + Ref2VA 多分支参考工作流 | AllRef / MiniMax H3 全能参考工作流 |
| `05_Work-Fisher整合` | i2v + Reference-to-Video 整合流程 | Work-Fisher / 【Work-Fisher】整合流程 |
| `06_破限增强` | 提示词增强专用（GenerationTail + PromptEnhancer） | video_minimax_h3_i2v_uncensored_enhancer |

`_backup_fix` 目录为修复前的原始备份，`_break` 工作流的增强器参数（max_new_tokens 等）可在节点内调整。

## 推荐使用方式

1. **写提示词**：在 `06_破限增强` 里跑一次增强器，得到已破限改写的长提示词（PreviewAny 查看）。
2. **出片**：把增强后的提示词粘贴到对应类别里的**非 break 版**（如 `minimax_h3_t2v_int4.json`）直接跑，跳过增强阶段，速度最快。
3. 需要每次现场增强就选 `_break` 版（每轮多 20~50 分钟增强时间），内存紧张选 `_int4`。

## 模型文件对照

| 组件 | 文件 |
|---|---|
| 扩散 int8 | `diffusion_models/minimax_h3_fl2va_pruned_int8_convrot.safetensors`（19.5GB） |
| 扩散 int4 | `diffusion_models/MiniMax_H3_FL2VA_pruned_mixed_int4_int8_convrot.safetensors`（14.8GB） |
| 编码器 | `text_encoders/qwen3vl_32b_minimax_h3_nvfp4_awq.safetensors`（14.6GB） |
| 生成 tail（破限） | `text_encoders/qwen3vl_32b_h3_generation_tail_50_63_int8_convrot.safetensors`（7.1GB） |
| 视频 VAE int8 | `vae/minimax_h3_video_vae_int8_convrot.safetensors`（3.0GB） |
| 音频 VAE | `vae/minimax_h3_audio_vae_fp32.safetensors`（0.6GB） |
