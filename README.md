# Character Creator Pro v10.1 — ComfyUI Custom Node

## Installation
1. Copy the `CharacterCreatorPro/` folder to `ComfyUI/custom_nodes/`
2. Restart ComfyUI
3. Load `character_creator_v10_workflow.json` via **Load** in ComfyUI

## Fixes in v10.1
| # | Bug | Fix |
|---|-----|-----|
| 1 | `apply_lora` crashed if ComfyUI returned tuple instead of dict | Now handles both |
| 2 | `character_seed` used md5 (collision-prone) | Upgraded to sha256 |
| 3 | `_detect_sdxl` logic was duplicated in 3 places | Refactored to single function |
| 4 | `build_positive_prompt` raised KeyError on old presets | All `cfg[]` → `cfg.get()` with fallbacks |
| 5 | `QuickPreset` used `lora_1_model_str` for both model+clip | Separate `lora_1_clip_str` parameter added |
| 6 | `IS_CHANGED` used md5 | Upgraded to sha256 |
| 7 | Workflow: KSampler seed/cfg/steps hardcoded | Wired to CharacterCreatorPro outputs |
| 8 | Workflow: no upscale pipeline | `ImageUpscaleWithModel` node added and wired |

## New in v10.1
- **ControlNet** optional input (pose / depth / canny)  
- **Upscale model** pass-through (connect `4x-UltraSharp.pth` etc.)  
- **Workflow** fully wired: seed, cfg, steps auto-flow from node  
- **Workflow** 4x upscale pipeline included as separate save branch  

## Workflow nodes
| Node | Purpose |
|------|---------|
| CheckpointLoaderSimple | Load SD model |
| CharacterCreatorPro | All character settings → prompts + latent |
| KSampler | Sampling (seed/cfg/steps auto-wired) |
| VAEDecode | Decode latent → image |
| PreviewImage | Live preview |
| SaveImage | Save final image |
| ImageUpscaleWithModel | 4x upscale (if upscale_model set) |
| SaveImage (4x) | Save upscaled image |
| Note | Debug info display |

## Optional node packs (recommended)
- **ADetailer** — install from ComfyUI Manager for face sharpening
- **IP-Adapter** — for face consistency across generations
- **ControlNet** — for pose control
