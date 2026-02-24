# 🎨 CHARACTER CREATOR PRO

**v10.1 · ComfyUI Custom Node**

*The most advanced character generation system for Stable Diffusion*

---

| **45 Quadrillion+** | **12 Art Styles** | **3 LoRA Slots** | **8 Quick Presets** | **Triple Lockdown** |
|---|---|---|---|---|
| Unique Combinations | SD1.5 + SDXL | Stacked & Weighted | Ready to Generate | Gender · Age · Ethnicity |

---

## 1 · What is Character Creator Pro?

Character Creator Pro is a **professional-grade ComfyUI custom node** that replaces the entire text-prompt workflow with a **structured, visual interface**. Instead of writing complex weighted prompts manually, you configure your character through organized dropdowns and sliders — and the node builds a **precisely engineered, multi-layer prompt** behind the scenes.

The core innovation is the **Triple Lockdown System**: a three-layer enforcement mechanism for gender, age, and ethnicity that prevents Stable Diffusion's natural tendency to drift toward default demographics. Every parameter is weighted and positioned in the prompt according to attention priority — ensuring what you configure is what you get.

> **⚡ Why This Node Exists**
>
> Standard SD workflows require dozens of trial-and-error prompt iterations to get consistent characters.
>
> Character Creator Pro encodes years of prompt engineering best-practices into a reusable, reproducible system.
>
> One configuration → one consistent character → infinite generations with the same DNA.

---

## 2 · Installation

### Requirements

| **Component** | **Minimum** | **Recommended** |
|---|---|---|
| ComfyUI | Any recent build | Latest stable |
| Python | 3.9+ | 3.10 / 3.11 |
| GPU VRAM | 4 GB (SD 1.5) | 8 GB+ (SDXL) |
| PyTorch | 2.0+ | 2.1+ with CUDA 12 |

### Step-by-Step Installation

1. **Copy the folder** — Place **CharacterCreatorPro/** into your **ComfyUI/custom_nodes/** directory

2. **Folder structure should be:**

```
ComfyUI/
└── custom_nodes/
    └── CharacterCreatorPro/
        ├── character_creator_pro_v10.py
        ├── __init__.py
        └── character_presets/   ← auto-created on first run
```

3. **Restart ComfyUI** — Full restart required (not just page refresh)

4. **Verify installation** — In the node search panel, search for **Character Creator**. Two nodes should appear:
   - **🎨 Character Creator Pro v10.1** — Full configuration node
   - **⚡ Character Quick Preset v10.1** — 8 ready-made presets

5. **Load the workflow** — Click **Load** in ComfyUI and select **character_creator_v10_workflow.json**

### Recommended Add-ons (Optional but Impactful)

| **Add-on** | **Install Method** | **Impact** | **Purpose** |
|---|---|---|---|
| ADetailer | ComfyUI Manager | 🔴 High | Sharp faces in full-body shots |
| ControlNet | ComfyUI Manager | 🟡 Medium | Precise pose control |
| IP-Adapter | ComfyUI Manager | 🔴 High | Face consistency across images |
| 4x-UltraSharp | Manual download | 🟡 Medium | 4K upscaling quality |
| Quality Embeddings | Manual download | 🟢 Moderate | EasyNegative, badhandv4 |

Download **4x-UltraSharp.pth** and place it in **ComfyUI/models/upscale_models/**. Place embedding files (**.pt** or **.safetensors**) in **ComfyUI/models/embeddings/**. The node detects and injects them automatically.

---

## 3 · Node Capabilities

### 3.1 Triple Lockdown System

The defining feature of Character Creator Pro. Standard SD models have strong biases that override prompt instructions — especially for gender, age, and ethnicity. The Triple Lockdown addresses this with a **three-layer weighted enforcement strategy** applied to each identity attribute:

| **Layer** | **Position in Prompt** | **Weight Range** | **Purpose** |
|---|---|---|---|
| L1 — Anchor Tokens | Blocks 2, 4, 7 | 1.20 – 1.65× | Primary identity lock at maximum attention |
| L2 — Physical Descriptors | Immediately after L1 | 0.85 – 1.40× | Body & face reinforcement |
| L3 — Tail Anchors | Final prompt blocks | 0.60 – 0.85× | Late diffusion step reinforcement |
| Negative Tokens | Negative prompt start | — | Block conflicting gender/age/ethnicity features |

**Adjustable Lock Strength:** The **gender_lock_strength** slider (1.0 – 2.0) lets you dial enforcement intensity. Higher values override stronger model biases. For minor age groups (Child/Teen), strength is automatically capped at 1.2× to prevent anatomy distortion.

---

### 3.2 Full Option Library

| **Category** | **Options** | **Examples** |
|---|---|---|
| Art Styles | 12 | Anime SD1.5, Photorealistic SD1.5, Dark Fantasy, 3D Render, Anime SDXL, Cyberpunk SDXL... |
| Quality Presets | 5 | Maximum, Balanced, Anime Max, Photo Max, SDXL Max |
| Gender | 4 | Female, Male, Non-Binary, Android / Robot |
| Age Groups | 7 | Child 8-12, Teen 14-17, Young Adult 18-24, Adult 25-35, Prime 36-45, Middle-Aged, Elder 60+ |
| Body Types | 7 | Athletic, Slim/Petite, Curvy, Muscular, Lean/Tall, Stocky, Ethereal |
| Ethnicities | 9 | No Preference, East Asian, South Asian, Southeast Asian, African/Black, Middle Eastern, European, Latino, Mixed |
| Hair Styles | 16 | Long & Flowing, Twin Tails, Afro, Braided, Undercut/Fade, Dreadlocks, Pixie Cut... |
| Hair Colors | 13 | Jet Black, Golden Blonde, Vivid Blue, Vivid Purple, Ombre/Rainbow, Ash Grey... |
| Eye Styles | 8 | Natural, Large Anime, Sharp Intense, Heterochromia, Glowing Magical, Cybernetic... |
| Eye Colors | 11 | Brown, Blue, Green, Amber, Red, Purple, Teal, Multi-gradient... |
| Archetypes | 18 | Hero/Warrior, Mage/Wizard, Rogue/Assassin, Vampire, Angel/Seraph, Dragon Slayer... |
| Outfits | 15 | Fantasy Armor, Mage Robes, School Uniform, Military Tactical, Steampunk, Gothic Dark... |
| Expressions | 10 | Neutral, Fierce, Warm Smile, Sinister, Melancholy, Battle Fury, Emotional... |
| Lighting | 10 | Cinematic Dramatic, Golden Hour, Moonlight, Neon/Cyberpunk, Divine/Holy, Fire/Torch... |
| Camera Angles | 9 | Portrait Close-Up, Full Body, Dynamic Action, Low Angle Epic, Bird's Eye, Back View... |
| Backgrounds | 12 | Epic Fantasy Land, Cyberpunk City, Space/Cosmos, Dark Dungeon, Japanese Garden... |

---

### 3.3 Smart Systems

#### Auto-Resolution by Camera Angle

The node automatically selects the optimal resolution for your chosen camera angle:

| **Camera Angle** | **SD 1.5 Resolution** | **SDXL Resolution** |
|---|---|---|
| Portrait / Head & Shoulders / Upper Body | 512 × 768 | 832 × 1216 |
| Full Body Standing / Low Angle Epic | 512 × 1024 | 768 × 1344 |
| Dynamic Action Pose | 768 × 960 | 896 × 1152 |
| Bird's Eye (Square) | 768 × 768 | 1024 × 1024 |

#### Auto-Sampler Recommendations

Based on your chosen art style, the node outputs the optimal sampler, scheduler, steps, and CFG scale through dedicated output slots:

| **Art Style** | **Sampler** | **Scheduler** | **Steps** | **CFG** |
|---|---|---|---|---|
| Anime SD1.5 | DPM++ 2M | Karras | 28 | 7.0 |
| Photorealistic SD1.5 | DPM++ 2M SDE | Karras | 30 | 6.5 |
| Fantasy Illustration SD1.5 | Euler A | Normal | 30 | 8.0 |
| Dark Fantasy SD1.5 | DPM++ 2M | Karras | 32 | 8.5 |
| 3D Render SD1.5 | DPM++ SDE | Karras | 35 | 7.0 |
| Anime SDXL | DPM++ 2M | Karras | 25 | 7.0 |
| Photorealistic SDXL | DPM++ 2M SDE | Karras | 30 | 6.0 |
| Dark Art SDXL | DPM++ 2M | Karras | 30 | 9.0 |

#### DNA Seed System

Enable **Character DNA Seed** to generate a **deterministic seed** from the character's name, gender, and ethnicity using SHA-256 hashing. The same character name always produces the same visual DNA — ensuring reproducible results across sessions, even if you change other settings.

#### Ethnicity Conflict Detection

When you select a hair or eye color that's unusual for the chosen ethnicity (e.g., blue eyes on an East Asian character), the node automatically appends **"fantasy character, unconventional appearance, stylized look"** to help the model accept the combination without fighting the ethnicity anchor.

#### Auto-Embedding Injection

The node scans **ComfyUI/models/embeddings/** on startup and automatically injects any found quality embeddings (**EasyNegative**, **badhandv4**, **negativeXL_D**, etc.) into the appropriate prompt positions — no manual setup required.

---

### 3.4 LoRA System (3 Slots)

Three independent LoRA slots with individual model and CLIP strength controls:

| **Slot** | **Default Model Str** | **Default CLIP Str** | **Typical Use** |
|---|---|---|---|
| LoRA 1 | 0.8 | 0.8 | Primary character style or face LoRA |
| LoRA 2 | 0.6 | 0.6 | Secondary style or clothing LoRA |
| LoRA 3 | 0.5 | 0.5 | Subtle detail enhancement LoRA |

All strength values accept **-2.0 to +2.0**. Negative values **subtract** the LoRA's influence, useful for reducing unwanted style bleed.

---

### 3.5 Character Preset System

Save any character configuration to a named JSON preset and reload it instantly in future sessions:

- **Save:** Enter a name in **save_as_name** → preset saved automatically to **character_presets/**
- **Load:** Select from **load_preset** dropdown → all settings are overridden from the saved file
- **Portable:** Preset files are plain JSON — shareable across machines or with other users

```json
// Example preset file: character_presets/Aria.json
{
  "gender": "👩 Female",
  "age_group": "🌟 Young Adult (18-24)",
  "ethnicity": "🏔️ European",
  "hair_color": "⬛ Jet Black",
  "archetype": "⚔️ Hero / Warrior",
  "custom_facial": "light scar on left cheek, silver earring"
}
```

---

### 3.6 ControlNet Support

The node accepts optional **CONTROL_NET** and **IMAGE** inputs, with a **controlnet_strength** slider (0.0 – 1.0). Connect any ControlNet preprocessor output (OpenPose, Depth, Canny, etc.) to the **controlnet_image** input for precise pose or composition control.

---

## 4 · Node Inputs & Outputs

### 4.1 Inputs Reference

#### Required Connections

| **Input** | **Type** | **Description** |
|---|---|---|
| model | MODEL | Checkpoint model from CheckpointLoaderSimple |
| clip | CLIP | CLIP encoder from CheckpointLoaderSimple |

#### Optional Connections

| **Input** | **Type** | **Description** |
|---|---|---|
| controlnet | CONTROL_NET | Connect a ControlNet model (OpenPose, Depth, Canny...) |
| controlnet_image | IMAGE | Preprocessed pose/depth/canny image for ControlNet |

#### Widget Parameters — Identity

| **Parameter** | **Type** | **Range / Options** | **Description** |
|---|---|---|---|
| gender | Dropdown | 4 options | Character gender with full lockdown enforcement |
| gender_lock_strength | Slider | 1.0 – 2.0 | How aggressively gender is enforced in prompt |
| age_group | Dropdown | 7 options | Age range with triple-layer enforcement |
| body_type | Dropdown | 7 options | Physical build descriptor |
| ethnicity | Dropdown | 9 options | Ethnic background with conflict detection |
| hair_style | Dropdown | 16 options | Hairstyle selection |
| hair_color | Dropdown | 13 options | Hair color (conflict auto-detected vs ethnicity) |
| eye_style | Dropdown | 8 options | Eye shape and rendering style |
| eye_color | Dropdown | 11 options | Eye color (conflict auto-detected vs ethnicity) |
| archetype | Dropdown | 18 options | Character role / class |
| expression | Dropdown | 10 options | Facial expression |
| outfit | Dropdown | 15 options | Clothing and armor style |

#### Widget Parameters — Scene & Quality

| **Parameter** | **Type** | **Range / Options** | **Description** |
|---|---|---|---|
| art_style | Dropdown | 12 options | Overall rendering style (SD1.5 or SDXL variants) |
| art_style_weight | Slider | 0.8 – 1.8 | Weight of art style tokens in prompt |
| quality_preset | Dropdown | 5 options | Quality tag package injected at prompt start |
| lighting | Dropdown | 10 options | Lighting setup and atmosphere |
| camera_angle | Dropdown | 9 options | Framing and shot type (also sets resolution) |
| background | Dropdown | 12 options | Scene environment |
| controlnet_strength | Slider | 0.0 – 1.0 | ControlNet conditioning strength (if connected) |

#### Widget Parameters — Seed & LoRA

| **Parameter** | **Type** | **Range** | **Description** |
|---|---|---|---|
| base_seed | Integer | 0 – 4,294,967,295 | Base generation seed |
| use_char_seed | Toggle | On / Off | Enable DNA seed mode (deterministic per character name) |
| lora_1/2/3 | Dropdown | Installed LoRAs | Select LoRA file for each slot |
| lora_N_model_str | Slider | -2.0 – +2.0 | Model influence weight for this LoRA slot |
| lora_N_clip_str | Slider | -2.0 – +2.0 | CLIP influence weight for this LoRA slot |

#### Widget Parameters — Custom Overrides

| **Parameter** | **Type** | **Description** |
|---|---|---|
| character_name | Text | Name used for DNA seed fingerprinting and debug display |
| custom_facial | Multiline | Extra facial details: scars, tattoos, jewelry, facial hair |
| custom_outfit_extra | Multiline | Additional outfit details appended to the selected outfit |
| custom_extra | Multiline | Any additional positive prompt tokens |
| extra_negative | Multiline | Additional negative prompt tokens |
| load_preset | Dropdown | Load a saved character preset (overrides all matching fields) |
| save_as_name | Text | Save current configuration as a named preset (leave blank to skip) |

---

### 4.2 Outputs Reference

| **Output** | **Type** | **Connect To** | **Description** |
|---|---|---|---|
| positive | CONDITIONING | KSampler positive | Fully built and encoded positive conditioning |
| negative | CONDITIONING | KSampler negative | Fully built and encoded negative conditioning |
| model | MODEL | KSampler model | LoRA-patched model (pass-through after LoRA injection) |
| clip | CLIP | — | LoRA-patched CLIP encoder |
| latent | LATENT | KSampler latent_image | Zero latent at correct resolution for chosen camera angle |
| width | INT | — | Recommended image width in pixels |
| height | INT | — | Recommended image height in pixels |
| seed | INT | KSampler seed | Final seed (DNA or base) — wire to KSampler |
| cfg | FLOAT | KSampler cfg | Recommended CFG for this art style — wire to KSampler |
| steps | INT | KSampler steps | Recommended step count for this art style — wire to KSampler |
| debug | STRING | Note node | Human-readable summary of all active settings |

---

## 5 · Workflow Guide

### 5.1 Workflow Architecture

The included workflow (`character_creator_v10_workflow.json`) contains 9 nodes organized into 4 groups:

| **Group** | **Nodes** | **Color** | **Purpose** |
|---|---|---|---|
| 🎨 Character Setup | CharacterCreatorPro | Blue | All character parameters and prompt generation |
| 🖼️ Sampling | KSampler | Green | Image generation with auto-wired settings |
| 🔍 Upscale (4x) | UpscaleModelLoader + ImageUpscaleWithModel | Red | Optional 4K upscaling pipeline |
| 💾 Output | VAEDecode + PreviewImage + 2× SaveImage + Note | Purple | Decode, preview, save standard + upscaled |

---

### 5.2 Data Flow Diagram

```
CheckpointLoaderSimple
├─ MODEL ──────────────────────────────────────────────────────────┐
├─ CLIP ──────────────────────────────────────────────────────┐    │
└─ VAE ──────────────────────────────────────────────────┐    │    │
                                                          │    │    │
CharacterCreatorPro  ◄── MODEL ◄──────────────────────────┘    │    │
  (all settings)    ◄── CLIP  ◄───────────────────────────────┘    │
                                                                    │
   ├─ positive (CONDITIONING) ──────────────────────────────► KSampler
   ├─ negative (CONDITIONING) ──────────────────────────────► KSampler
   ├─ model    (MODEL, LoRA-patched) ────────────────────────► KSampler
   ├─ latent   (LATENT, correct resolution) ─────────────────► KSampler
   ├─ seed     (INT) ────────────────────────────────────────► KSampler
   ├─ cfg      (FLOAT) ──────────────────────────────────────► KSampler
   ├─ steps    (INT) ────────────────────────────────────────► KSampler
   └─ debug    (STRING) ─────────────────────────────────────► Note
                         │
KSampler → LATENT ───────────────────────────────────────────────┐
                                                                  │
VAEDecode ◄── LATENT ◄────────────────────────────────────────────┘
          ◄── VAE    ◄──── CheckpointLoaderSimple
              │
   ├─ IMAGE ─────────────────────────────────────────────────► PreviewImage
   ├─ IMAGE ─────────────────────────────────────────────────► SaveImage
   └─ IMAGE ─────────────────────────────────────────────────────────────┐
                                                                         │
UpscaleModelLoader (4x-UltraSharp.pth)                                   │
└─ UPSCALE_MODEL ──────────────────────────────────────────────────────► │
                                                                         │
ImageUpscaleWithModel ◄──────────────────────────────────────────────────┘
└─ IMAGE ► SaveImage (4x)
```

---

### 5.3 Quick Start: First Generation in 5 Steps

1. **Load checkpoint** — In CheckpointLoaderSimple, select your model (e.g., **dreamshaper_8.safetensors**)
2. **Set art style** — Match the art style to your model: use **🎌 Anime SD1.5** for anime checkpoints, **📸 Photorealistic SD1.5** for realism models
3. **Configure identity** — Set gender, age, ethnicity, and any distinctive features. The node handles prompt engineering automatically
4. **Choose scene** — Pick lighting, camera angle, and background. The latent resolution auto-adjusts
5. **Generate** — Click Queue Prompt. CFG, steps, and seed are auto-wired from the node

---

### 5.4 Upscale Pipeline Setup

**Required:** Download **4x-UltraSharp.pth** from CivitAI and place in **ComfyUI/models/upscale_models/**

In the workflow:
- **UpscaleModelLoader** — Set the model to **4x-UltraSharp.pth** (or any other 4x upscale model)
- **ImageUpscaleWithModel** — Already connected to VAEDecode output and UpscaleModelLoader
- **SaveImage (4x)** — Saves upscaled result with suffix **_4x** automatically

> **💡 Tip: Disconnect Upscale to Save Generation Time**
>
> If you're iterating quickly, right-click ImageUpscaleWithModel → Bypass.
>
> Re-enable it only for your final confirmed character configuration.
>
> The standard SaveImage will continue saving non-upscaled results.

---

### 5.5 ControlNet Integration

To use ControlNet for pose control:

1. **Install ControlNet node pack** — Via ComfyUI Manager
2. **Add preprocessor** — DWPose, OpenposePreprocessor, etc. → connect its IMAGE output to **controlnet_image** on CharacterCreatorPro
3. **Add ControlNet model** — ControlNetLoader → connect **CONTROL_NET** output to **controlnet** input on CharacterCreatorPro
4. **Adjust strength** — Use **controlnet_strength** slider (0.6 – 0.9 recommended for pose)

---

## 6 · Quick Preset Node

The **Character Quick Preset v10.1** node provides 8 fully configured character templates. Drop it into any workflow for an instant production-ready character — no configuration required.

| **Preset** | **Style** | **Key Features** |
|---|---|---|
| ⚔️ Epic Female Warrior | Anime SD1.5 | Jet black hair, blue anime eyes, fantasy armor, scar detail, epic fantasy background |
| 🧙 Female Dark Mage | Fantasy Illustration SD1.5 | Purple hair, glowing red eyes, necromancer archetype, dark dungeon, moody lighting |
| 🚀 Male Space Commander | 3D Render SD1.5 | Military tactical, space cosmos background, cinematic dramatic lighting |
| 🌸 Cute Anime Girl | Anime SD1.5 | Pink twin tails, school uniform, East Asian ethnicity, Japanese garden background |
| ⚙️ Cyberpunk Assassin (F) | Cyberpunk SD1.5 | Platinum hair, cybernetic eyes, tactical vest, neon lighting, cyberpunk city |
| 🧛 Vampire Noble (M) | Dark Fantasy SD1.5 | Jet black long hair, red glowing eyes, royal attire, moonlight, European ethnicity |
| 😇 Divine Angel (F) | Fantasy Illustration SD1.5 | Golden hair, white glowing eyes, white wings, divine holy lighting, magical background |
| 🐉 Dragon Slayer (M) | Fantasy Illustration SD1.5 | Muscular build, amber eyes, battle scars, golden hour lighting, battlefield |

**Custom append:** Both **append_positive** and **append_negative** text fields let you add extra tokens to any preset without modifying the base configuration.

---

## 7 · Advanced Usage

### 7.1 Creating a Consistent Character Series

1. **Configure base character** — Set all identity parameters for your character
2. **Enter character name** — e.g., **Aria**, and enable **Character DNA Seed**
3. **Save as preset** — Enter **Aria** in save_as_name and generate once to save
4. **Vary only the scene** — Change camera, lighting, background, expression freely — identity remains locked
5. **Load preset next session** — Select **Aria** from load_preset — exact same character, any scene

---

### 7.2 Getting Consistent Results with a Face LoRA

- Train or download a face LoRA for your character
- Add it to **lora_1** with model_str **0.7** and clip_str **0.7**
- Use **custom_extra** to add the LoRA's trigger word if required
- Combine with **DNA Seed** for fully reproducible faces across all shots

---

### 7.3 Understanding the Prompt Builder

The node constructs prompts in 17 ordered blocks, each weighted for maximum effect:

| **Block** | **Content** | **Weight Strategy** |
|---|---|---|
| 1 | Quality preset tokens | No weight — maximum priority by position |
| 2 | Age anchor tokens (L1) | 1.50× — high priority, early position |
| 3 | Age physical descriptors (L2) | 1.27 – 1.35× |
| 4 | Art style tokens | User-defined (0.8 – 1.8×) |
| 5 | Camera / composition | 1.1× |
| 6 | Gender anchor tokens (L1) | User-defined lock strength |
| 7 | Gender body/face descriptors (L2) | 0.75 – 0.80× of lock strength |
| 8 | Body type | 1.0× — neutral weight |
| 9 | Ethnicity anchor tokens (L1) | 1.40× |
| 10 | Ethnicity skin/face descriptors (L2) | 1.15 – 1.23× |
| 11–14 | Archetype, Expression, Hair, Eyes | 1.05 – 1.15× |
| 15 | Outfit | 1.05× |
| 16 | Custom extras + Lighting + Background | 1.0× |
| 17 | Gender + Age tail anchors (L3) | 0.60 – 0.65× — late reinforcement |

---

### 7.4 Troubleshooting

| **Problem** | **Likely Cause** | **Solution** |
|---|---|---|
| Wrong gender generated | Low gender_lock_strength | Increase to 1.7 – 1.9. Check model's native gender bias |
| Age looks wrong | Archetype/outfit overriding age tokens | For child/teen, lock strength is auto-capped — this is correct behavior |
| Ethnicity not showing | Model lacks diversity training | Add ethnicity-specific LoRA in slot 1 |
| Full body missing feet | Camera negative tokens too strong | Switch to Full Body Standing angle — it removes bust/portrait negatives |
| LoRA not loading | File not in loras/ folder | Check ComfyUI/models/loras/ — restart after adding |
| Blurry face on full body | ADetailer not installed | Install ADetailer from ComfyUI Manager |
| Upscale node error | No upscale model in models/upscale_models/ | Download 4x-UltraSharp.pth or disconnect the upscale nodes |
| Wrong seed every time | use_char_seed off or no name entered | Enable toggle + enter character name in character_name field |

---

## 8 · Technical Reference

### 8.1 Architecture

| **Component** | **Implementation** | **Notes** |
|---|---|---|
| CLIP Encoding | Unified SD1.5 + SDXL | Auto-detects model type via tokenizer key count |
| Pooled Output | return_pooled=True with fallback | Compatible with all ComfyUI versions |
| SDXL Detection | _detect_sdxl() — checks dual tokenizer keys | Reliable across model variants |
| Seed Fingerprint | SHA-256 hash of name+gender+ethnicity | Collision-resistant, deterministic |
| LoRA Loading | comfy.sd.load_lora_for_models() | Handles both tuple and dict API returns |
| IS_CHANGED | SHA-256 hash of all widget values | Full cache invalidation on any change |
| Resolution | CAMERA_RESOLUTION table lookup | All values rounded to nearest 64px |

---

### 8.2 File Structure

```
CharacterCreatorPro/
├── __init__.py                              ← Node registration
├── character_creator_pro_v10.py             ← Main node code
├── character_creator_v10_workflow.json      ← Complete workflow
└── character_presets/                       ← JSON preset storage
    ├── Aria.json
    ├── MyWarrior.json
    └── ...                                  ← Your saved characters
```

---

### 8.3 Changelog

| **Version** | **Change** |
|---|---|
| v10.1 | ControlNet optional input (CONTROL_NET + IMAGE only — no widget leak) |
| v10.1 | Upscale pipeline moved to dedicated UpscaleModelLoader node (eliminates None crash) |
| v10.1 | SHA-256 replaces MD5 for seed fingerprinting and IS_CHANGED hashing |
| v10.1 | apply_lora() handles both tuple and dict API returns (version compatibility) |
| v10.1 | build_positive_prompt() uses cfg.get() with fallbacks (no KeyError on old presets) |
| v10.1 | QuickPreset lora_1_clip_str added as independent parameter (was duplicating model_str) |
| v10.1 | Workflow: KSampler seed/cfg/steps wired from node outputs (not hardcoded) |
| v10.1 | Workflow: debug link slot corrected after UPSCALE_MODEL removal (slot 11→10) |
| v10.0 | Triple lockdown for Gender, Age, Ethnicity. 3 LoRA slots. Preset system. DNA seed. |

---

**CHARACTER CREATOR PRO v10.1 · Professional ComfyUI Node · 45 Quadrillion+ Unique Combinations**
