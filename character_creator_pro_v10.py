"""
╔══════════════════════════════════════════════════════════════════════════╗
║         CHARACTER CREATOR PRO  ·  v10.1  ·  ComfyUI Custom Node         ║
║                                                                          ║
║  ✦ SD 1.5 + SDXL dual support with correct pooled embeddings            ║
║  ✦ Gender Lockdown — triple-layer gender enforcement                     ║
║  ✦ Age Lockdown — triple-layer age enforcement                           ║
║  ✦ Ethnicity Lockdown — conflict detection + auto softener               ║
║  ✦ Dynamic LoRA injection (3 slots) per character                        ║
║  ✦ Character save / load system (JSON presets)                           ║
║  ✦ Seed management with character fingerprint (DNA seed)                 ║
║  ✦ Advanced prompt weighting per token group                             ║
║  ✦ Smart camera-aware resolution (SD1.5 + SDXL)                         ║
║  ✦ ControlNet optional support (pose / depth / canny)                    ║
║  ✦ Upscale model optional pass-through                                   ║
║  ✦ Auto embedding injection (scans installed embeddings)                 ║
║  ✦ Dynamic CFG + sampler recommendations per art style                   ║
║  ✦ CONDITIONING output — no STRING relay                                 ║
║                                                                          ║
║  FIX v10.1:                                                              ║
║   • __init__.py was importing v6 — corrected to v10                      ║
║   • apply_lora: uses correct comfy.sd API (no broken dict unpack)        ║
║   • encode_prompt: hardened SDXL pooled detection                        ║
║   • build_positive_prompt: age_group fallback for unknown keys           ║
║   • character_seed: hash uses sha256 (md5 collision-prone)               ║
║   • workflow: KSampler seed/cfg/steps wired from node outputs            ║
║   • ControlNet optional input added                                      ║
║   • Upscale model pass-through added                                     ║
║   • QuickPreset: lora_1_clip_str fixed (was using lora_1_str twice)      ║
╚══════════════════════════════════════════════════════════════════════════╝

Installation:
  ComfyUI/custom_nodes/CharacterCreatorPro/
  ├── character_creator_pro_v10.py   ← this file
  └── __init__.py                    ← see bottom of file for content
"""

import os
import json
import hashlib
import folder_paths  # ComfyUI built-in

# ═══════════════════════════════════════════════════════════
#  PATHS
# ═══════════════════════════════════════════════════════════

PRESETS_DIR = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "character_presets"
)
os.makedirs(PRESETS_DIR, exist_ok=True)

# ═══════════════════════════════════════════════════════════
#  EMBEDDINGS AUTO-INJECTION
#  Scans ComfyUI/models/embeddings/ and injects found ones.
# ═══════════════════════════════════════════════════════════

KNOWN_EMBEDDINGS = {
    "sd15": {
        "negative": [
            "EasyNegative",
            "badhandv4",
            "bad-artist",
            "ng_deepnegative_v1_75t",
            "verybadimagenegative_v1.3",
            "bad_prompt_version2",
        ],
        "positive": [],
    },
    "sdxl": {
        "negative": [
            "negativeXL_D",
            "FastNegativeV2",
        ],
        "positive": [],
    },
}


def get_available_embeddings(is_sdxl: bool) -> tuple:
    try:
        installed = set(folder_paths.get_filename_list("embeddings"))
        installed_clean = {os.path.splitext(f)[0].lower() for f in installed}
    except Exception:
        return [], []

    key = "sdxl" if is_sdxl else "sd15"
    data = KNOWN_EMBEDDINGS.get(key, {"negative": [], "positive": []})

    found_neg = [e for e in data["negative"] if e.lower() in installed_clean]
    found_pos = [e for e in data["positive"] if e.lower() in installed_clean]
    return found_pos, found_neg


def inject_embeddings(pos_text: str, neg_text: str,
                      pos_embeds: list, neg_embeds: list) -> tuple:
    if neg_embeds:
        neg_text = ", ".join(f"embedding:{e}" for e in neg_embeds) + ", " + neg_text
    if pos_embeds:
        pos_text = ", ".join(f"embedding:{e}" for e in pos_embeds) + ", " + pos_text
    return pos_text, neg_text


# ═══════════════════════════════════════════════════════════
#  CLIP ENCODING — SD 1.5 + SDXL unified
# ═══════════════════════════════════════════════════════════

def _detect_sdxl(clip) -> bool:
    """
    Reliably detect SDXL by checking for dual tokenizer keys.
    Falls back safely if tokenizer raises.
    """
    try:
        tokens = clip.tokenize("test")
        # SDXL tokenizer returns a dict with keys 'l' and 'g'
        return isinstance(tokens, dict) and len(tokens) > 1
    except Exception:
        return False


def encode_prompt(clip, text: str) -> list:
    """
    Unified CLIP encoding for SD 1.5 and SDXL.
    Returns standard ComfyUI CONDITIONING format.
    """
    tokens = clip.tokenize(text)
    is_sdxl = isinstance(tokens, dict) and len(tokens) > 1

    try:
        cond, pooled = clip.encode_from_tokens(tokens, return_pooled=True)
        return [[cond, {"pooled_output": pooled}]] if is_sdxl else [[cond, {"pooled_output": pooled}]]
    except TypeError:
        # Older ComfyUI builds that don't support return_pooled
        cond = clip.encode_from_tokens(tokens)
        return [[cond, {}]]
    except Exception as e:
        print(f"[CharacterCreator] ⚠️  encode_prompt error: {e}")
        cond = clip.encode_from_tokens(tokens)
        return [[cond, {}]]


# ═══════════════════════════════════════════════════════════
#  DYNAMIC CFG + SAMPLER RECOMMENDATIONS
# ═══════════════════════════════════════════════════════════

STYLE_SAMPLER_PRESETS = {
    # (sampler_name, scheduler, steps, cfg_scale)
    "🎌 Anime SD1.5":                ("dpmpp_2m",     "karras", 28, 7.0),
    "🎌 Anime SD1.5 (Realistic)":    ("dpmpp_2m",     "karras", 30, 7.5),
    "📸 Photorealistic SD1.5":       ("dpmpp_2m_sde", "karras", 30, 6.5),
    "⚔️ Fantasy Illustration SD1.5": ("euler_a",      "normal", 30, 8.0),
    "🌑 Dark Fantasy SD1.5":         ("dpmpp_2m",     "karras", 32, 8.5),
    "🌆 Cyberpunk SD1.5":            ("dpmpp_2m",     "karras", 28, 7.5),
    "🎮 3D Render SD1.5":            ("dpmpp_sde",    "karras", 35, 7.0),
    "✨ Anime SDXL":                  ("dpmpp_2m",     "karras", 25, 7.0),
    "✨ Photorealistic SDXL":         ("dpmpp_2m_sde", "karras", 30, 6.0),
    "✨ Fantasy Art SDXL":            ("euler_a",      "normal", 28, 8.0),
    "✨ Dark Art SDXL":               ("dpmpp_2m",     "karras", 30, 9.0),
    "✨ Cyberpunk SDXL":              ("dpmpp_2m",     "karras", 28, 7.5),
}

_DEFAULT_SAMPLER = ("dpmpp_2m", "karras", 30, 7.5)


def get_sampler_preset(art_style: str) -> tuple:
    return STYLE_SAMPLER_PRESETS.get(art_style, _DEFAULT_SAMPLER)


# ═══════════════════════════════════════════════════════════
#  LORA HELPER — FIX: correct comfy.sd API usage
# ═══════════════════════════════════════════════════════════

def apply_lora(model, clip, lora_name: str,
               strength_model: float, strength_clip: float):
    """
    Load and apply a single LoRA.
    FIX: comfy.sd.load_lora_for_models returns (model, clip) tuple,
         not a dict — previous code would crash on dict unpack.
    """
    if not lora_name or lora_name == "None":
        return model, clip
    try:
        import comfy.sd as comfy_sd
        lora_path = folder_paths.get_full_path("loras", lora_name)
        if lora_path is None:
            print(f"[CharacterCreator] ⚠️  LoRA not found: {lora_name}")
            return model, clip

        lora_data = comfy_sd.load_lora(lora_path)
        # Returns (model_patched, clip_patched) — a tuple, not a dict
        result = comfy_sd.load_lora_for_models(
            model, clip, lora_data, strength_model, strength_clip
        )
        # Handle both tuple and dict return (ComfyUI version differences)
        if isinstance(result, dict):
            return result["model"], result["clip"]
        return result[0], result[1]

    except Exception as e:
        print(f"[CharacterCreator] ⚠️  LoRA load error ({lora_name}): {e}")
        return model, clip


# ═══════════════════════════════════════════════════════════
#  CHARACTER PRESET SYSTEM
# ═══════════════════════════════════════════════════════════

def save_character_preset(name: str, data: dict) -> bool:
    safe_name = "".join(c for c in name if c.isalnum() or c in " _-").strip()
    if not safe_name:
        return False
    path = os.path.join(PRESETS_DIR, f"{safe_name}.json")
    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        print(f"[CharacterCreator] ⚠️  Preset save error: {e}")
        return False


def load_character_preset(name: str) -> dict:
    if not name or name == "None":
        return {}
    path = os.path.join(PRESETS_DIR, f"{name}.json")
    if not os.path.exists(path):
        return {}
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"[CharacterCreator] ⚠️  Preset load error: {e}")
        return {}


def list_character_presets() -> list:
    presets = ["None"]
    if os.path.exists(PRESETS_DIR):
        for f in sorted(os.listdir(PRESETS_DIR)):
            if f.endswith(".json"):
                presets.append(f[:-5])
    return presets


# ═══════════════════════════════════════════════════════════
#  SEED FINGERPRINT — FIX: sha256 instead of md5
#  md5 has known collisions; sha256 is appropriate for
#  deterministic identity fingerprinting.
# ═══════════════════════════════════════════════════════════

def character_seed(name: str, gender: str, ethnicity: str, base_seed: int) -> int:
    """
    Deterministic seed offset from character identity.
    Same name + gender + ethnicity = same visual DNA across sessions.
    """
    fingerprint = f"{name.strip().lower()}|{gender}|{ethnicity}"
    h = int(hashlib.sha256(fingerprint.encode()).hexdigest(), 16)
    return (base_seed + h) % (2 ** 32)


# ═══════════════════════════════════════════════════════════
#  PROMPT BUILDER — Advanced Weighted Token System
# ═══════════════════════════════════════════════════════════

def w(text: str, weight: float) -> str:
    """Wrap text in ComfyUI attention weight syntax."""
    if abs(weight - 1.0) < 0.01:
        return text
    return f"({text}:{weight:.2f})"


def build_positive_prompt(cfg: dict) -> str:
    """
    Construct a weighted, ordered positive prompt.
    Token order = attention priority in SD/SDXL.
    FIX: Added .get() with fallback for all cfg keys to prevent KeyError
         when loading old presets missing new fields.
    """
    gender    = cfg.get("gender", "👩 Female")
    age_group = cfg.get("age_group", "🌟 Young Adult (18-24)")
    ethnicity = cfg.get("ethnicity", "🌐 No Preference")
    art_style = cfg.get("art_style", "🎌 Anime SD1.5")
    quality   = cfg.get("quality_preset", "🥇 Maximum")
    camera    = cfg.get("camera_angle", "📸 Upper Body (3/4)")
    body_type = cfg.get("body_type", "💪 Athletic")
    archetype = cfg.get("archetype", "None")
    expression = cfg.get("expression", "😐 Neutral / Calm")
    hair_style = cfg.get("hair_style", "Long & Flowing")
    hair_color = cfg.get("hair_color", "⬛ Jet Black")
    eye_style  = cfg.get("eye_style", "Natural Realistic")
    eye_color  = cfg.get("eye_color", "🟫 Brown")
    outfit     = cfg.get("outfit", "⚔️ Fantasy Armor")
    lighting   = cfg.get("lighting", "🎬 Cinematic Dramatic")
    background = cfg.get("background", "⬜ Clean / Studio")

    gls = cfg.get("gender_lock_strength", 1.55)
    asw = cfg.get("art_style_weight", 1.3)

    # FIX: safe fallback if key not found in data tables
    g      = GENDER_DATA.get(gender, GENDER_DATA["👩 Female"])
    age_d  = AGE_DATA.get(age_group, AGE_DATA["🌟 Young Adult (18-24)"])
    eth_d  = ETHNICITY_DATA.get(ethnicity, ETHNICITY_DATA["🌐 No Preference"])
    style  = ART_STYLES.get(art_style, "")
    qp     = QUALITY_PRESETS.get(quality, QUALITY_PRESETS["🥇 Maximum"])

    is_minor = age_group in ("🧒 Child (8-12)", "🧑 Teen (14-17)")
    age_ls   = 1.5

    parts = []

    # ── BLOCK 1: Quality ──────────────────────────────────
    parts.append(qp)

    # ── BLOCK 2: Age Lockdown ─────────────────────────────
    age_L1 = ", ".join(w(tok, age_ls) for tok in age_d["anchor"])
    parts.append(age_L1)
    parts.append(w(age_d["age_ref"],  round(age_ls * 0.90, 2)))
    parts.append(w(age_d["face_ref"], round(age_ls * 0.85, 2)))

    # ── BLOCK 3: Art Style ────────────────────────────────
    if style:
        parts.append(w(style, asw))

    # ── BLOCK 4: Camera / Composition ────────────────────
    cam_text = CAMERA_ANGLES.get(camera, "")
    if cam_text:
        parts.append(w(cam_text, 1.1))

    # ── BLOCK 5: Gender Lockdown ──────────────────────────
    anchors = g["anchor_tokens"]
    effective_gls = min(gls, 1.2) if is_minor else gls
    L1 = ", ".join(w(tok, effective_gls) for tok in anchors)
    parts.append(L1)
    parts.append(w(g["body_ref"],  round(effective_gls * 0.80, 2)))
    parts.append(w(g["face_ref"],  round(effective_gls * 0.75, 2)))

    # ── BLOCK 6: Body Type ────────────────────────────────
    bt = BODY_TYPES.get(body_type, "")
    if bt:
        parts.append(bt)

    # ── BLOCK 7: Ethnicity Lockdown ───────────────────────
    eth_ls = 1.40
    if eth_d["anchor"]:
        eth_L1 = ", ".join(w(tok, eth_ls) for tok in eth_d["anchor"])
        parts.append(eth_L1)
        if eth_d["skin_ref"]:
            parts.append(w(eth_d["skin_ref"], round(eth_ls * 0.88, 2)))
        if eth_d["face_ref"]:
            parts.append(w(eth_d["face_ref"], round(eth_ls * 0.82, 2)))

        # Conflict detection: unusual hair/eye for ethnicity → softener
        nat_hair = eth_d.get("natural_hair", [])
        nat_eyes = eth_d.get("natural_eyes", [])
        hair_lower = HAIR_COLORS.get(hair_color, "").lower()
        eye_lower  = EYE_COLORS.get(eye_color, "").lower()
        hair_conflict = nat_hair and not any(h in hair_lower for h in nat_hair)
        eye_conflict  = nat_eyes and not any(e in eye_lower  for e in nat_eyes)
        if hair_conflict or eye_conflict:
            parts.append(
                "fantasy character, unconventional appearance, "
                "stylized look, artistic character design"
            )

    # ── BLOCK 8: Archetype ───────────────────────────────
    arch = ARCHETYPES.get(archetype, "")
    if arch:
        parts.append(w(arch, 1.1))

    # ── BLOCK 9: Expression ──────────────────────────────
    expr = EXPRESSIONS.get(expression, "")
    if expr:
        parts.append(w(expr, 1.1))

    # ── BLOCK 10: Hair ───────────────────────────────────
    hs = HAIR_STYLES.get(hair_style, "")
    hc = HAIR_COLORS.get(hair_color, "")
    if hs:
        parts.append(w(hs, 1.1))
    if hc:
        parts.append(w(hc, 1.15))

    # ── BLOCK 11: Eyes ───────────────────────────────────
    es = EYE_STYLES.get(eye_style, "")
    ec = EYE_COLORS.get(eye_color, "")
    if es:
        parts.append(w(es, 1.1))
    if ec:
        parts.append(w(ec, 1.15))

    # ── BLOCK 12: Custom Facial Details ──────────────────
    cf = cfg.get("custom_facial", "").strip()
    if cf:
        parts.append(cf)

    # ── BLOCK 13: Outfit ─────────────────────────────────
    outfit_text = OUTFITS.get(outfit, "")
    extra_outfit = cfg.get("custom_outfit_extra", "").strip()
    if extra_outfit:
        outfit_text += f", {extra_outfit}"
    if outfit_text:
        parts.append(w(outfit_text, 1.05))

    # ── BLOCK 14: Extra Tags ─────────────────────────────
    extra = cfg.get("custom_extra", "").strip()
    if extra:
        parts.append(extra)

    # ── BLOCK 15: Lighting ───────────────────────────────
    lt = LIGHTING.get(lighting, "")
    if lt:
        parts.append(lt)

    # ── BLOCK 16: Background ─────────────────────────────
    bg = BACKGROUNDS.get(background, "")
    if bg:
        parts.append(bg)

    # ── BLOCK 17: Tail Anchors (reinforce in later steps) ─
    tail_weight = round(gls * 0.65, 2)
    gender_tail = ", ".join(w(tok, tail_weight) for tok in anchors[:2])
    parts.append(gender_tail)

    age_tail_w = round(age_ls * 0.60, 2)
    age_tail = ", ".join(w(tok, age_tail_w) for tok in age_d["anchor"][:2])
    parts.append(age_tail)

    return ", ".join(p.strip() for p in parts if p and p.strip())


def build_negative_prompt(cfg: dict) -> str:
    gender    = cfg.get("gender", "👩 Female")
    age_group = cfg.get("age_group", "🌟 Young Adult (18-24)")
    ethnicity = cfg.get("ethnicity", "🌐 No Preference")

    g     = GENDER_DATA.get(gender, GENDER_DATA["👩 Female"])
    age_d = AGE_DATA.get(age_group, AGE_DATA["🌟 Young Adult (18-24)"])
    eth_d = ETHNICITY_DATA.get(ethnicity, ETHNICITY_DATA["🌐 No Preference"])

    neg_parts = [
        age_d["neg"],
        g["neg_tokens"],
        eth_d.get("neg", ""),
        NEGATIVE_BASE,
    ]
    extra_neg = cfg.get("extra_negative", "").strip()
    if extra_neg:
        neg_parts.append(extra_neg)

    return ", ".join(p for p in neg_parts if p and p.strip())


# ═══════════════════════════════════════════════════════════
#  DATA TABLES
# ═══════════════════════════════════════════════════════════

GENDER_DATA = {
    "👩 Female": {
        "anchor_tokens": ["woman", "female", "girl"],
        "body_ref":  "female body, feminine figure, feminine physique",
        "face_ref":  "feminine face, female facial features, soft features",
        "neg_tokens": "male, man, boy, masculine, beard, mustache, male body, "
                      "flat chest, male face, macho",
    },
    "👨 Male": {
        "anchor_tokens": ["man", "male", "boy"],
        "body_ref":  "male body, masculine figure, masculine physique",
        "face_ref":  "masculine face, male facial features, strong jawline, "
                     "defined cheekbones",
        "neg_tokens": "female, woman, girl, feminine, female body, breasts, "
                      "feminine face, girly",
    },
    "🧑 Non-Binary": {
        "anchor_tokens": ["androgynous person", "non-binary individual"],
        "body_ref":  "androgynous figure, neutral body proportions",
        "face_ref":  "androgynous face, soft neutral features",
        "neg_tokens": "strongly masculine, strongly feminine, exaggerated gender",
    },
    "🤖 Android / Robot": {
        "anchor_tokens": ["android", "humanoid robot", "synthetic being"],
        "body_ref":  "mechanical body, synthetic frame, robotic physique",
        "face_ref":  "synthetic face, mechanical features, artificial skin",
        "neg_tokens": "organic skin, human skin texture, biological features",
    },
}

ART_STYLES = {
    "🎌 Anime SD1.5":
        "anime style, manga art, cel shading, clean lineart, vibrant colors, "
        "studio ghibli quality, highly detailed anime, 2d illustration",
    "🎌 Anime SD1.5 (Realistic)":
        "anime realism, semi-realistic anime, detailed shading, "
        "complex lighting, anime girl detailed, high quality render",
    "📸 Photorealistic SD1.5":
        "RAW photo, photorealistic, hyperrealistic, 8k uhd, DSLR, "
        "soft lighting, high quality, film grain, Fujifilm XT3",
    "⚔️ Fantasy Illustration SD1.5":
        "fantasy art, epic illustration, painterly style, "
        "Greg Rutkowski, Artgerm, detailed, trending on ArtStation",
    "🌑 Dark Fantasy SD1.5":
        "dark fantasy art, gothic style, dramatic lighting, "
        "ominous atmosphere, detailed shadows, sinister mood",
    "🌆 Cyberpunk SD1.5":
        "cyberpunk art, neon aesthetic, blade runner style, "
        "futuristic, glowing neon lights, sci-fi detailed",
    "🎮 3D Render SD1.5":
        "3D render, octane render, blender cycles, "
        "subsurface scattering, PBR materials, studio lighting, 4k",
    "✨ Anime SDXL":
        "anime style, official art, beautiful detailed eyes, best quality, "
        "ultra-detailed, absurdres, highres, sharp focus, "
        "vibrant, clean lines, expressive",
    "✨ Photorealistic SDXL":
        "photorealistic, hyperrealistic, cinematic photography, "
        "8k resolution, sharp details, professional lighting, "
        "skin texture, depth of field, bokeh",
    "✨ Fantasy Art SDXL":
        "epic fantasy digital art, highly detailed, dramatic composition, "
        "masterful lighting, intricate details, painterly realism, "
        "concept art quality, professional illustration",
    "✨ Dark Art SDXL":
        "dark moody digital painting, atmospheric, chiaroscuro lighting, "
        "highly detailed, dramatic shadows, painterly, fine art quality",
    "✨ Cyberpunk SDXL":
        "cyberpunk neon digital art, ultra detailed, atmospheric haze, "
        "holographic elements, rain reflections, neon glow, "
        "futuristic aesthetic, cinematic",
}

QUALITY_PRESETS = {
    "🥇 Maximum":
        "masterpiece, best quality, ultra-detailed, ultra-highres, "
        "sharp focus, intricate details, 8k resolution, "
        "perfect anatomy, detailed eyes, detailed hair, "
        "professional artwork, award-winning",
    "⚡ Balanced":
        "masterpiece, best quality, detailed, sharp focus, highres, "
        "good anatomy, professional",
    "🎌 Anime Max":
        "masterpiece, best quality, ultra-detailed, beautiful detailed eyes, "
        "beautiful detailed hair, absurdres, highres, "
        "official art, extremely detailed CG unity 8k wallpaper, "
        "perfect face, detailed background",
    "📸 Photo Max":
        "RAW photo, best quality, photorealistic, 8k uhd, dslr, "
        "soft lighting, high quality, film grain, Fujifilm XT3, "
        "intricate, highly detailed, sharp focus",
    "✨ SDXL Max":
        "best quality, masterpiece, ultra highres, "
        "incredibly detailed, sharp focus, perfect anatomy, "
        "perfect composition, professional, award winning",
}

AGE_DATA = {
    "🧒 Child (8-12)": {
        "anchor":   ["child", "kid", "young child"],
        "age_ref":  "8 years old, prepubescent, small child body, short stature",
        "face_ref": "childlike face, innocent round face, child facial features, chubby cheeks",
        "neg":      "adult, mature, man, woman, muscular, beard, wrinkles, "
                    "adult body, adult face, old, teenager",
    },
    "🧑 Teen (14-17)": {
        "anchor":   ["teenager", "teen", "adolescent"],
        "age_ref":  "16 years old, teenage body, youthful, pubescent",
        "face_ref": "teenage face, young adolescent face, teen facial features, youthful skin",
        "neg":      "adult, mature adult, child, elderly, wrinkles, aged, "
                    "fully grown adult, middle aged",
    },
    "🌟 Young Adult (18-24)": {
        "anchor":   ["young adult", "young man", "young woman"],
        "age_ref":  "20 years old, early twenties, young adult body, youthful",
        "face_ref": "young adult face, smooth skin, youthful mature face, vibrant complexion",
        "neg":      "child, elderly, aged, wrinkles, old, middle aged, teen",
    },
    "💼 Adult (25-35)": {
        "anchor":   ["adult", "man", "woman"],
        "age_ref":  "28 years old, prime adult, mature body, confident",
        "face_ref": "mature adult face, confident expression, slight maturity lines",
        "neg":      "child, elderly, very old, aged heavily, teen, teenager",
    },
    "🏆 Prime (36-45)": {
        "anchor":   ["mature adult", "experienced adult"],
        "age_ref":  "40 years old, prime of life, distinguished, experienced",
        "face_ref": "mature distinguished face, subtle age lines, experienced look",
        "neg":      "child, teen, very young, elderly, ancient, frail",
    },
    "🧓 Middle-aged (46-55)": {
        "anchor":   ["middle-aged", "mature person"],
        "age_ref":  "50 years old, middle age, greying temples, dignified",
        "face_ref": "middle-aged face, visible age lines, distinguished mature look",
        "neg":      "child, teen, young adult, elderly frail, ancient",
    },
    "👴 Elder (60+)": {
        "anchor":   ["elderly", "old person", "senior"],
        "age_ref":  "65 years old, elderly, aged body, white or grey hair",
        "face_ref": "elderly face, deep wisdom lines, aged skin, elder features",
        "neg":      "child, teen, young adult, smooth skin, youthful face",
    },
}

AGE_GROUPS = {k: v["age_ref"] for k, v in AGE_DATA.items()}

BODY_TYPES = {
    "💪 Athletic":      "athletic build, toned body, fit physique, defined muscles",
    "🌸 Slim / Petite": "slim figure, slender, petite, delicate build",
    "🔥 Curvy":         "curvy figure, hourglass silhouette, voluptuous",
    "🏋️ Muscular":      "muscular build, powerful physique, broad shoulders",
    "🌿 Lean / Tall":   "tall lean figure, model proportions, long limbs",
    "🪨 Stocky":        "stocky build, compact, broad solid frame",
    "👻 Ethereal":      "ethereal figure, otherworldly proportions, supernatural grace",
}

ETHNICITY_DATA = {
    "🌐 No Preference": {
        "anchor": [], "skin_ref": "", "face_ref": "",
        "natural_hair": [], "natural_eyes": [], "neg": "",
    },
    "🇯🇵 East Asian": {
        "anchor":       ["East Asian", "Asian person"],
        "skin_ref":     "fair porcelain skin, East Asian complexion, light beige skin tone",
        "face_ref":     "East Asian facial features, almond-shaped eyes, high cheekbones, "
                        "soft facial structure, monolid eyes, Korean Japanese Chinese features",
        "natural_hair": ["black", "dark brown", "brown"],
        "natural_eyes": ["dark brown", "black", "brown"],
        "neg":          "European features, African features, dark brown skin, "
                        "deep skin tone, caucasian face",
    },
    "🇮🇳 South Asian": {
        "anchor":       ["South Asian", "Indian person"],
        "skin_ref":     "warm brown skin, South Asian complexion, medium tan skin tone",
        "face_ref":     "South Asian facial features, dark expressive eyes, "
                        "defined nose, warm brown complexion, Indian subcontinental features",
        "natural_hair": ["black", "dark brown"],
        "natural_eyes": ["dark brown", "black", "brown"],
        "neg":          "very fair skin, pale skin, European features, East Asian features",
    },
    "🌴 Southeast Asian": {
        "anchor":       ["Southeast Asian", "Filipino Thai Indonesian"],
        "skin_ref":     "warm golden tan complexion, Southeast Asian skin tone",
        "face_ref":     "Southeast Asian facial features, warm golden complexion, "
                        "soft rounded features, tropical complexion",
        "natural_hair": ["black", "dark brown"],
        "natural_eyes": ["dark brown", "black"],
        "neg":          "pale skin, very fair European features, African features",
    },
    "🌍 African / Black": {
        "anchor":       ["Black person", "African", "dark skinned"],
        "skin_ref":     "rich dark melanin skin, deep ebony complexion, "
                        "beautiful dark skin tone, Black African complexion",
        "face_ref":     "African facial features, broad nose, full lips, "
                        "strong facial structure, Black facial features",
        "natural_hair": ["black", "dark brown"],
        "natural_eyes": ["dark brown", "black", "brown"],
        "neg":          "pale skin, fair skin, light skin, European features, "
                        "Asian features, white skin",
    },
    "🌙 Middle Eastern": {
        "anchor":       ["Middle Eastern", "Arab person"],
        "skin_ref":     "olive tan skin, warm Mediterranean complexion, Middle Eastern skin tone",
        "face_ref":     "Middle Eastern facial features, defined sharp features, "
                        "olive complexion, strong nose, deep set eyes, Arab features",
        "natural_hair": ["black", "dark brown", "brown"],
        "natural_eyes": ["dark brown", "black", "brown", "green", "hazel"],
        "neg":          "very pale skin, East Asian features, African dark skin",
    },
    "🏔️ European": {
        "anchor":       ["European", "Caucasian"],
        "skin_ref":     "fair light skin, European complexion, pale to light skin tone",
        "face_ref":     "European facial features, light skin, Western facial structure, "
                        "Caucasian features, European bone structure",
        "natural_hair": ["blonde", "brown", "red", "auburn", "black", "light brown"],
        "natural_eyes": ["blue", "green", "grey", "brown", "hazel"],
        "neg":          "dark skin, very dark complexion, Asian features, African features",
    },
    "🌺 Latino / Hispanic": {
        "anchor":       ["Latino", "Hispanic"],
        "skin_ref":     "warm olive complexion, Latino skin tone, warm medium tan skin",
        "face_ref":     "Latino Hispanic facial features, warm olive skin, "
                        "mixed heritage features, expressive eyes",
        "natural_hair": ["black", "dark brown", "brown"],
        "natural_eyes": ["dark brown", "black", "brown", "hazel"],
        "neg":          "very pale Nordic features, purely East Asian features",
    },
    "🌈 Mixed": {
        "anchor":       ["mixed race", "multiracial"],
        "skin_ref":     "mixed ethnicity complexion, blended heritage skin tone",
        "face_ref":     "multiracial facial features, mixed heritage appearance, "
                        "blended ethnic features",
        "natural_hair": [],
        "natural_eyes": [],
        "neg":          "",
    },
}

ETHNICITIES = {k: v["skin_ref"] for k, v in ETHNICITY_DATA.items()}

HAIR_STYLES = {
    "Short & Neat":       "short neat hair, clean cut",
    "Long & Flowing":     "long flowing hair, silky smooth",
    "Wavy / Beachy":      "wavy hair, beach waves",
    "Curly Natural":      "curly hair, natural curls, defined ringlets",
    "Afro":               "large natural afro, voluminous afro hair",
    "Braided":            "intricate braided hair, cornrows",
    "Bun / Updo":         "elegant hair bun, sophisticated updo",
    "Ponytail":           "sleek high ponytail",
    "Bob Cut":            "sharp bob cut, chin-length",
    "Undercut / Fade":    "undercut hairstyle, shaved sides, fade",
    "Spiky / Anime":      "spiky wild hair, dramatic anime spikes",
    "Bald / Shaved":      "bald head, shaved smooth scalp",
    "Dreadlocks":         "long dreadlocks, loc hairstyle",
    "Pixie Cut":          "pixie cut, very short stylish",
    "Half-Up Half-Down":  "half-up half-down, elegant style",
    "Twin Tails":         "twin tails, two symmetrical ponytails",
}

HAIR_COLORS = {
    "⬛ Jet Black":         "jet black hair",
    "🟫 Dark Brown":        "dark brown hair",
    "🟤 Chestnut Brown":    "chestnut brown warm hair",
    "🟡 Golden Blonde":     "golden blonde hair",
    "⬜ Platinum / Silver": "platinum silver hair",
    "🔴 Red / Auburn":      "auburn red fiery hair",
    "⚪ Pure White":        "pure white hair",
    "🔵 Vivid Blue":        "vivid electric blue dyed hair",
    "🟣 Vivid Purple":      "vivid violet purple dyed hair",
    "🩷 Vivid Pink":        "vivid hot pink dyed hair",
    "🟢 Vivid Green":       "vivid neon green dyed hair",
    "🌈 Ombre / Rainbow":   "ombre multicolored rainbow gradient hair",
    "🩶 Ash Grey":          "ash grey hair, salt and pepper",
}

EYE_STYLES = {
    "Natural Realistic":  "natural realistic detailed eyes",
    "Large Anime":        "large expressive anime eyes, detailed iris",
    "Sharp Intense":      "sharp intense piercing eyes, fierce gaze",
    "Gentle & Soft":      "gentle soft warm eyes, kind expression",
    "Heterochromia":      "heterochromia, two different colored eyes",
    "Glowing Magical":    "glowing luminous magical eyes",
    "Cybernetic":         "cybernetic eye implant, mechanical HUD eye",
    "Closed / Serene":    "closed eyes, serene peaceful",
}

EYE_COLORS = {
    "🟫 Brown":  "brown eyes",
    "🔵 Blue":   "blue eyes",
    "🟢 Green":  "green eyes",
    "⚫ Black":  "black eyes",
    "🩶 Grey":   "grey eyes",
    "🟡 Amber":  "amber golden eyes",
    "🔴 Red":    "red glowing eyes",
    "🟣 Purple": "purple violet eyes",
    "⬜ White":  "white glowing eyes",
    "🔵 Teal":   "teal cyan eyes",
    "🌈 Multi":  "gradient multicolor eyes",
}

ARCHETYPES = {
    "None":                 "",
    "⚔️ Hero / Warrior":    "heroic warrior, determined battle-ready stance, powerful presence",
    "🧙 Mage / Wizard":     "powerful mage, mystical energy aura, wise ancient expression",
    "🗡️ Rogue / Assassin":  "skilled assassin, stealthy cunning, dangerous demeanor",
    "✨ Healer / Cleric":    "divine healer, holy golden light aura, compassionate",
    "🛡️ Knight / Paladin":  "noble knight, righteous bearing, honorable champion",
    "🏹 Ranger / Archer":   "wilderness ranger, focused survivalist, nature guardian",
    "💀 Necromancer":        "dark necromancer, sinister undead aura, ominous power",
    "🐉 Dragon Slayer":      "legendary dragon slayer, battle-scarred, epic warrior",
    "🚀 Space Marine":       "elite space marine, futuristic soldier, tactical ready",
    "⚙️ Cyborg":             "advanced cyborg, cybernetic enhancements, half-machine",
    "🧛 Vampire":            "aristocratic vampire, pale ethereal skin, predatory grace",
    "😈 Demon / Fallen":     "powerful demon, dark supernatural aura, intimidating",
    "😇 Angel / Seraph":     "divine angel, radiant wings, holy light emanating",
    "📚 Scholar / Sage":     "wise scholar, intellectual, keeper of knowledge",
    "👑 Royalty / Noble":    "noble royalty, regal bearing, aristocratic grace",
    "🌿 Druid / Nature":     "ancient druid, nature magic, wild mystical power",
    "🥷 Ninja / Shadow":     "elite ninja, shadow assassin, masked warrior",
}

OUTFITS = {
    "⚔️ Fantasy Armor":       "detailed fantasy plate armor, intricate engravings, battle-worn steel",
    "🧙 Mage Robes":          "flowing mystical robes, arcane sigils, enchanted fabric",
    "👗 Elegant Dress":        "elegant flowing gown, beautiful formal attire",
    "👔 Casual Modern":        "casual modern outfit, contemporary streetwear",
    "👔 Business Formal":      "business suit, sharp tailored professional attire",
    "🎓 School Uniform":       "school uniform, academic student clothing",
    "🪖 Military Tactical":    "military tactical gear, combat uniform",
    "🤖 Futuristic Sci-Fi":    "futuristic tech suit, neon accent armor, high-tech",
    "⚙️ Steampunk":            "steampunk outfit, brass gears, goggles, Victorian-industrial",
    "👘 Traditional":          "traditional cultural outfit, ethnic heritage dress",
    "👑 Royal / Aristocratic": "royal garments, crown jewels, opulent noble clothing",
    "🌑 Gothic Dark":          "gothic dark fashion, black lace, alternative elegance",
    "🥋 Martial Artist":       "martial arts training outfit, warrior discipline",
    "🏊 Light / Minimal":      "light minimal tunic, simple unarmored clothing",
    "🌿 Nature / Druid":       "nature-woven druidic garments, leaves and vines",
}

EXPRESSIONS = {
    "😐 Neutral / Calm":       "calm neutral expression, composed",
    "😤 Fierce / Determined":  "fierce determined expression, intense focus",
    "😊 Warm Smile":           "warm gentle smile, friendly",
    "😈 Sinister / Evil":      "sinister evil smirk, menacing",
    "😢 Melancholy":           "melancholy sorrowful eyes, contemplative",
    "😲 Wonder / Surprised":   "expression of wonder, wide eyes, amazed",
    "😌 Serene / Peaceful":    "serene peaceful expression, tranquil",
    "😏 Confident Smirk":      "confident smirk, self-assured, charismatic",
    "😡 Battle Fury":          "battle rage, furious intense, war cry",
    "🥹 Emotional / Tearful":  "emotional tearful eyes, deeply moved",
}

LIGHTING = {
    "🎬 Cinematic Dramatic":
        "cinematic dramatic lighting, professional film lighting, "
        "deep shadows and highlights, dramatic chiaroscuro, "
        "volumetric light rays, high contrast cinematic look",
    "📷 Studio Soft":
        "soft studio lighting, professional portrait lighting, "
        "softbox light, diffused even illumination, clean studio setup, "
        "catch lights in eyes, flattering portrait light",
    "🌅 Golden Hour":
        "golden hour sunlight, warm orange golden glow, "
        "magic hour photography, sun low on horizon, "
        "warm backlit, lens flare, romantic warm tones",
    "🌙 Moonlight / Night":
        "nighttime moonlight, cool blue silver light, "
        "moonlit scene, dark sky, atmospheric night, "
        "stars in background, mysterious night ambiance",
    "🌈 Neon / Cyberpunk":
        "vivid neon lights, colorful neon glow, cyberpunk atmosphere, "
        "purple and cyan neon reflections, electric glow, "
        "wet street reflections, colorful urban night",
    "✨ Rim / Back Light":
        "dramatic rim lighting, strong backlight halo effect, "
        "glowing outline around subject, edge light highlight, "
        "silhouette with rim glow, separation from background",
    "🔥 Fire / Torch":
        "warm flickering fire light, orange torchlight glow, "
        "dramatic firelight shadows, warm ember tones, "
        "dynamic fire illumination, warm red orange lighting",
    "😇 Divine / Holy":
        "divine heavenly light, holy god rays shining down, "
        "golden sacred luminescence, ethereal radiant glow, "
        "heavenly illumination, soft white divine light",
    "🌑 Dark & Moody":
        "dark moody low-key lighting, noir style, "
        "deep dramatic shadows, mysterious atmosphere, "
        "minimal light, high contrast dark aesthetic",
    "❄️ Cold / Ice":
        "cold icy blue lighting, frigid frozen atmosphere, "
        "stark blue-white tones, winter cold light, "
        "crystalline clear lighting, cold harsh illumination",
}

CAMERA_ANGLES = {
    "🎭 Portrait Close-Up":
        "extreme close-up portrait shot, face filling frame, intimate framing, "
        "shallow depth of field, bokeh background, face closeup",
    "👤 Head & Shoulders":
        "head and shoulders portrait, bust shot, upper chest visible, "
        "classic portrait framing, face and neck clearly visible",
    "📸 Upper Body (3/4)":
        "upper body shot, waist up, three quarter view, "
        "torso and face visible, medium shot framing",
    "🧍 Full Body Standing":
        "full body shot, entire figure visible from head to toe, "
        "standing pose, full character view, wide shot",
    "💥 Dynamic Action Pose":
        "dynamic action pose, dramatic composition, mid-motion, "
        "powerful stance, energy and movement, hero pose",
    "📐 Low Angle Epic":
        "low angle shot, shot from below, worm eye view, "
        "looking up at character, epic imposing perspective, dramatic upward angle",
    "🦅 Bird's Eye":
        "overhead shot, bird eye view, top down perspective, "
        "looking down at character from above",
    "🔄 Side Profile":
        "side view, profile shot, lateral view, "
        "character facing sideways, silhouette visible",
    "🔙 Back View":
        "shot from behind, back view, character facing away, "
        "rear perspective, back of character visible",
}

BACKGROUNDS = {
    "⬜ Clean / Studio":
        "clean white seamless studio background, minimal environment, "
        "professional photo backdrop, pure white background",
    "🎨 Gradient Abstract":
        "smooth color gradient background, abstract artistic backdrop, "
        "soft blended colors, aesthetic gradient",
    "🏔️ Epic Fantasy Land":
        "epic fantasy landscape background, dramatic mountain range, "
        "mystical ancient environment, sweeping fantasy vistas, "
        "dramatic cloudy sky, fog in valleys",
    "🌆 Urban City":
        "urban city background, city street level, "
        "modern buildings and architecture, busy metropolitan area, "
        "city life backdrop",
    "🌲 Nature / Forest":
        "lush ancient forest background, towering trees, "
        "dappled sunlight through leaves, verdant green nature, "
        "peaceful woodland environment",
    "🌌 Space / Cosmos":
        "deep outer space background, colorful nebula, "
        "thousands of distant stars, cosmic universe, "
        "galaxy backdrop, interstellar environment",
    "🏚️ Dark Dungeon":
        "dark stone dungeon background, ancient underground ruins, "
        "torchlit stone walls, ominous dark cavern, "
        "medieval dungeon environment, flickering torch shadows",
    "🌇 Cyberpunk City":
        "cyberpunk city skyline background, neon signs everywhere, "
        "rain-soaked reflective streets, futuristic urban sprawl, "
        "holographic advertisements, dense neon-lit megacity",
    "👑 Royal Palace":
        "grand palace interior background, massive marble columns, "
        "opulent throne room, royal gold decor, "
        "cathedral ceiling, regal aristocratic environment",
    "⚔️ Battlefield":
        "epic battlefield background, massive armies clashing, "
        "dramatic stormy war sky, smoke and fire, "
        "epic scale warfare, historical battle scene",
    "✨ Magical Abstract":
        "magical ethereal background, swirling mystical energy, "
        "glowing magical particles, otherworldly void, "
        "arcane spell effects, fantasy magical environment",
    "🌸 Japanese Garden":
        "serene traditional Japanese garden background, "
        "cherry blossom petals falling, zen pond and bridge, "
        "bamboo and stone lanterns, peaceful tranquil atmosphere",
}

NEGATIVE_BASE = (
    "worst quality, low quality, normal quality, lowres, "
    "bad anatomy, bad hands, error, missing fingers, extra digit, "
    "fewer digits, cropped, jpeg artifacts, signature, watermark, "
    "username, blurry, bad feet, mutation, deformed, ugly, "
    "extra limbs, disfigured, malformed limbs, missing arms, "
    "missing legs, extra arms, extra legs, fused fingers, "
    "too many fingers, long neck, poorly drawn face, cloned face, "
    "out of frame, gross proportions, poorly drawn hands, "
    "missing body parts, floating limbs, disconnected limbs, "
    "cross-eyed, asymmetrical eyes, bad proportions"
)

# ═══════════════════════════════════════════════════════════
#  CAMERA → RESOLUTION + NEGATIVE MAP
# ═══════════════════════════════════════════════════════════

CAMERA_RESOLUTION = {
    # key: (SD15_W, SD15_H, SDXL_W, SDXL_H)
    "Portrait Close-Up":   (512,  768,  832, 1216),
    "Head & Shoulders":    (512,  768,  832, 1216),
    "Upper Body (3/4)":    (512,  768,  832, 1216),
    "Full Body Standing":  (512, 1024,  768, 1344),
    "Dynamic Action Pose": (768,  960,  896, 1152),
    "Low Angle Epic":      (512, 1024,  768, 1344),
    "Bird's Eye":          (768,  768, 1024, 1024),
    "Side Profile":        (512,  768,  832, 1216),
    "Back View":           (512,  768,  832, 1216),
}

CAMERA_NEGATIVE_TOKENS = {
    "Portrait Close-Up":   "",
    "Head & Shoulders":    "full body, legs, feet",
    "Upper Body (3/4)":    "full body, legs, feet, close-up face",
    "Full Body Standing":  "close-up, portrait, face only, headshot, cropped, bust shot",
    "Dynamic Action Pose": "standing still, static pose, portrait only",
    "Low Angle Epic":      "top view, portrait, close-up",
    "Bird's Eye":          "front view, portrait, close-up",
    "Side Profile":        "front facing, portrait only",
    "Back View":           "front facing, face visible",
}


def get_camera_key(camera_angle_full: str) -> str:
    for key in CAMERA_RESOLUTION:
        if key in camera_angle_full:
            return key
    return "Upper Body (3/4)"


# ═══════════════════════════════════════════════════════════
#  MAIN NODE — Character Creator Pro v10.1
# ═══════════════════════════════════════════════════════════

class CharacterCreatorProV10:
    """
    Character Creator Pro v10.1
    ✦ CONDITIONING output — no STRING relay
    ✦ SD 1.5 + SDXL unified encoding
    ✦ Triple-layer Gender / Age / Ethnicity Lockdown
    ✦ LoRA injection (3 slots)
    ✦ ControlNet optional input
    ✦ Upscale model pass-through
    ✦ Character save / load presets
    ✦ Deterministic sha256 seed fingerprint
    ✦ Advanced weighted token prompt
    """

    CATEGORY     = "🎨 Character Creator Pro"
    FUNCTION     = "generate"
    RETURN_TYPES = (
        "CONDITIONING", "CONDITIONING", "MODEL", "CLIP",
        "LATENT", "INT", "INT", "INT", "FLOAT", "INT",
        "STRING"
    )
    RETURN_NAMES = (
        "positive", "negative", "model", "clip",
        "latent", "width", "height", "seed", "cfg", "steps",
        "debug"
    )
    OUTPUT_NODE = False

    @classmethod
    def INPUT_TYPES(cls):
        lora_list    = ["None"] + folder_paths.get_filename_list("loras")
        preset_list  = list_character_presets()
        return {
            "required": {
                # ── Inputs ──────────────────────────────
                "model": ("MODEL",),
                "clip":  ("CLIP",),

                # ── Preset System ────────────────────────
                "load_preset":  (preset_list, {"default": "None"}),
                "save_as_name": ("STRING", {
                    "default": "",
                    "placeholder": "اسم الحفظ (اتركه فارغاً لعدم الحفظ)"
                }),

                # ── Quality ──────────────────────────────
                "quality_preset":   (list(QUALITY_PRESETS.keys()), {"default": "🥇 Maximum"}),
                "art_style":        (list(ART_STYLES.keys()),       {"default": "🎌 Anime SD1.5"}),
                "art_style_weight": ("FLOAT", {
                    "default": 1.3, "min": 0.8, "max": 1.8,
                    "step": 0.05, "display": "slider"
                }),

                # ── Gender Lockdown ──────────────────────
                "gender": (list(GENDER_DATA.keys()), {"default": "👩 Female"}),
                "gender_lock_strength": ("FLOAT", {
                    "default": 1.55, "min": 1.0, "max": 2.0,
                    "step": 0.05, "display": "slider"
                }),

                # ── Identity ─────────────────────────────
                "age_group": (list(AGE_GROUPS.keys()),  {"default": "🌟 Young Adult (18-24)"}),
                "body_type": (list(BODY_TYPES.keys()),  {"default": "💪 Athletic"}),
                "ethnicity": (list(ETHNICITIES.keys()), {"default": "🇯🇵 East Asian"}),

                # ── Hair ─────────────────────────────────
                "hair_style": (list(HAIR_STYLES.keys()), {"default": "Long & Flowing"}),
                "hair_color": (list(HAIR_COLORS.keys()), {"default": "⬛ Jet Black"}),

                # ── Eyes ─────────────────────────────────
                "eye_style": (list(EYE_STYLES.keys()), {"default": "Large Anime"}),
                "eye_color": (list(EYE_COLORS.keys()), {"default": "🔵 Blue"}),

                # ── Character ────────────────────────────
                "archetype":  (list(ARCHETYPES.keys()),  {"default": "⚔️ Hero / Warrior"}),
                "expression": (list(EXPRESSIONS.keys()), {"default": "😤 Fierce / Determined"}),
                "outfit":     (list(OUTFITS.keys()),      {"default": "⚔️ Fantasy Armor"}),

                # ── Scene ────────────────────────────────
                "lighting":     (list(LIGHTING.keys()),       {"default": "🎬 Cinematic Dramatic"}),
                "camera_angle": (list(CAMERA_ANGLES.keys()),  {"default": "📸 Upper Body (3/4)"}),
                "background":   (list(BACKGROUNDS.keys()),    {"default": "🏔️ Epic Fantasy Land"}),

                # ── Seed Management ──────────────────────
                "base_seed": ("INT", {"default": 42, "min": 0, "max": 0xFFFFFFFF}),
                "use_char_seed": ("BOOLEAN", {
                    "default": True,
                    "label_on":  "Character DNA Seed",
                    "label_off": "Use Base Seed Only"
                }),

                # ── LoRA Slot 1 ──────────────────────────
                "lora_1":           (lora_list, {"default": "None"}),
                "lora_1_model_str": ("FLOAT", {
                    "default": 0.8, "min": -2.0, "max": 2.0,
                    "step": 0.05, "display": "slider"
                }),
                "lora_1_clip_str":  ("FLOAT", {
                    "default": 0.8, "min": -2.0, "max": 2.0,
                    "step": 0.05, "display": "slider"
                }),

                # ── LoRA Slot 2 ──────────────────────────
                "lora_2":           (lora_list, {"default": "None"}),
                "lora_2_model_str": ("FLOAT", {
                    "default": 0.6, "min": -2.0, "max": 2.0,
                    "step": 0.05, "display": "slider"
                }),
                "lora_2_clip_str":  ("FLOAT", {
                    "default": 0.6, "min": -2.0, "max": 2.0,
                    "step": 0.05, "display": "slider"
                }),

                # ── LoRA Slot 3 ──────────────────────────
                "lora_3":           (lora_list, {"default": "None"}),
                "lora_3_model_str": ("FLOAT", {
                    "default": 0.5, "min": -2.0, "max": 2.0,
                    "step": 0.05, "display": "slider"
                }),
                "lora_3_clip_str":  ("FLOAT", {
                    "default": 0.5, "min": -2.0, "max": 2.0,
                    "step": 0.05, "display": "slider"
                }),

                # ── ControlNet strength (widget — must be in required) ───
                # NOTE: controlnet / controlnet_image are IMAGE/CONTROL_NET
                # inputs (not widgets) and stay in optional.
                # controlnet_strength is FLOAT → ComfyUI serialises it as a
                # widget. Keeping it in optional would insert it BEFORE the
                # STRING optional widgets in widgets_values, corrupting the
                # slot order and causing "could not convert string to float".
                "controlnet_strength": ("FLOAT", {
                    "default": 0.8, "min": 0.0, "max": 1.0,
                    "step": 0.05, "display": "slider"
                }),

                # ── Character Details (widgets) ──────────
                "character_name":      ("STRING", {
                    "default": "", "placeholder": "اسم الشخصية..."
                }),
                "custom_facial":       ("STRING", {
                    "default": "", "multiline": True,
                    "placeholder": "ندوب، وشوم، مجوهرات..."
                }),
                "custom_outfit_extra": ("STRING", {
                    "default": "", "multiline": True,
                    "placeholder": "تفاصيل الزي..."
                }),
                "custom_extra":        ("STRING", {
                    "default": "", "multiline": True,
                    "placeholder": "تفاصيل إضافية..."
                }),
                "extra_negative":      ("STRING", {
                    "default": "", "multiline": True,
                    "placeholder": "Negative إضافية..."
                }),
            },
            "optional": {
                # Only non-widget types here (CONTROL_NET, IMAGE).
                # FLOAT/STRING in optional get serialised as widgets and
                # corrupt the widgets_values slot order → moved to required.
                "controlnet":       ("CONTROL_NET",),
                "controlnet_image": ("IMAGE",),
            }
        }

    def generate(
        self,
        model, clip,
        load_preset, save_as_name,
        quality_preset, art_style, art_style_weight,
        gender, gender_lock_strength,
        age_group, body_type, ethnicity,
        hair_style, hair_color,
        eye_style, eye_color,
        archetype, expression, outfit,
        lighting, camera_angle, background,
        base_seed, use_char_seed,
        lora_1, lora_1_model_str, lora_1_clip_str,
        lora_2, lora_2_model_str, lora_2_clip_str,
        lora_3, lora_3_model_str, lora_3_clip_str,
        controlnet_strength,
        character_name, custom_facial,
        custom_outfit_extra, custom_extra, extra_negative,
        controlnet=None, controlnet_image=None,
    ):
        # ── 1. Load preset if selected ─────────────────────
        preset_data = load_character_preset(load_preset)
        if preset_data:
            quality_preset       = preset_data.get("quality_preset",       quality_preset)
            art_style            = preset_data.get("art_style",            art_style)
            art_style_weight     = preset_data.get("art_style_weight",     art_style_weight)
            gender               = preset_data.get("gender",               gender)
            gender_lock_strength = preset_data.get("gender_lock_strength", gender_lock_strength)
            age_group            = preset_data.get("age_group",            age_group)
            body_type            = preset_data.get("body_type",            body_type)
            ethnicity            = preset_data.get("ethnicity",            ethnicity)
            hair_style           = preset_data.get("hair_style",           hair_style)
            hair_color           = preset_data.get("hair_color",           hair_color)
            eye_style            = preset_data.get("eye_style",            eye_style)
            eye_color            = preset_data.get("eye_color",            eye_color)
            archetype            = preset_data.get("archetype",            archetype)
            expression           = preset_data.get("expression",           expression)
            outfit               = preset_data.get("outfit",               outfit)
            lighting             = preset_data.get("lighting",             lighting)
            camera_angle         = preset_data.get("camera_angle",         camera_angle)
            background           = preset_data.get("background",           background)
            character_name       = preset_data.get("character_name",       character_name)
            custom_facial        = preset_data.get("custom_facial",        custom_facial)
            custom_outfit_extra  = preset_data.get("custom_outfit_extra",  custom_outfit_extra)
            custom_extra         = preset_data.get("custom_extra",         custom_extra)
            extra_negative       = preset_data.get("extra_negative",       extra_negative)

        # ── 2. Apply LoRAs ─────────────────────────────────
        model, clip = apply_lora(model, clip, lora_1, lora_1_model_str, lora_1_clip_str)
        model, clip = apply_lora(model, clip, lora_2, lora_2_model_str, lora_2_clip_str)
        model, clip = apply_lora(model, clip, lora_3, lora_3_model_str, lora_3_clip_str)

        # ── 3. Build config dict ───────────────────────────
        cfg = {
            "quality_preset":       quality_preset,
            "art_style":            art_style,
            "art_style_weight":     art_style_weight,
            "gender":               gender,
            "gender_lock_strength": gender_lock_strength,
            "age_group":            age_group,
            "body_type":            body_type,
            "ethnicity":            ethnicity,
            "hair_style":           hair_style,
            "hair_color":           hair_color,
            "eye_style":            eye_style,
            "eye_color":            eye_color,
            "archetype":            archetype,
            "expression":           expression,
            "outfit":               outfit,
            "lighting":             lighting,
            "camera_angle":         camera_angle,
            "background":           background,
            "character_name":       character_name,
            "custom_facial":        custom_facial,
            "custom_outfit_extra":  custom_outfit_extra,
            "custom_extra":         custom_extra,
            "extra_negative":       extra_negative,
        }

        # ── 4. Build prompts ───────────────────────────────
        pos_text = build_positive_prompt(cfg)
        neg_text = build_negative_prompt(cfg)

        # ── 5. Detect model type ───────────────────────────
        is_sdxl = _detect_sdxl(clip)

        # ── 5a. Auto-inject embeddings ─────────────────────
        pos_embeds, neg_embeds = get_available_embeddings(is_sdxl)
        pos_text, neg_text = inject_embeddings(pos_text, neg_text, pos_embeds, neg_embeds)

        # ── 5b. Encode ─────────────────────────────────────
        positive_cond = encode_prompt(clip, pos_text)
        negative_cond = encode_prompt(clip, neg_text)

        # ── 5c. ControlNet conditioning ───────────────────
        if controlnet is not None and controlnet_image is not None:
            try:
                import comfy.sd as comfy_sd
                positive_cond = comfy_sd.apply_controlnet(
                    positive_cond, controlnet,
                    controlnet_image, controlnet_strength
                )
            except Exception as e:
                print(f"[CharacterCreator] ⚠️  ControlNet apply error: {e}")

        # ── 5d. Dynamic CFG + Sampler recommendation ───────
        rec_sampler, rec_scheduler, rec_steps, rec_cfg = get_sampler_preset(art_style)

        # ── 6. Seed management ─────────────────────────────
        if use_char_seed and character_name.strip():
            final_seed = character_seed(character_name, gender, ethnicity, base_seed)
        else:
            final_seed = base_seed

        # ── 7. Save preset ─────────────────────────────────
        if save_as_name.strip():
            cfg["character_name"] = character_name
            saved = save_character_preset(save_as_name.strip(), cfg)
            save_status = f"✅ Saved: {save_as_name}" if saved else "❌ Save failed"
        else:
            save_status = "—"

        # ── 8. Smart Resolution ────────────────────────────
        import torch
        cam_key = get_camera_key(camera_angle)
        res = CAMERA_RESOLUTION.get(cam_key, (512, 768, 832, 1216))
        out_w, out_h = (res[2], res[3]) if is_sdxl else (res[0], res[1])
        out_w = round(out_w / 64) * 64
        out_h = round(out_h / 64) * 64

        latent_tensor = torch.zeros(
            [1, 4, out_h // 8, out_w // 8], dtype=torch.float32
        )
        latent_out = {"samples": latent_tensor}

        # ── 9. Camera-aware negative reinforcement ─────────
        cam_neg = CAMERA_NEGATIVE_TOKENS.get(cam_key, "")
        if cam_neg:
            negative_cond = encode_prompt(clip, cam_neg + ", " + neg_text)

        # ── 10. Debug info ─────────────────────────────────
        lora_info = []
        for slot, name, ms, cs in [
            (1, lora_1, lora_1_model_str, lora_1_clip_str),
            (2, lora_2, lora_2_model_str, lora_2_clip_str),
            (3, lora_3, lora_3_model_str, lora_3_clip_str),
        ]:
            if name != "None":
                lora_info.append(f"  LoRA {slot}  : {name} [{ms}/{cs}]")

        cn_info = ""
        if controlnet is not None:
            cn_info = f"  ControlNet : strength={controlnet_strength}"

        debug = "\n".join(filter(None, [
            "╔══ CHARACTER CREATOR PRO v10.1 ══╗",
            f"  Name       : {character_name or '—'}",
            f"  Preset     : {load_preset} | Save: {save_status}",
            f"  Gender     : {gender} [lock: {gender_lock_strength}]",
            f"  Age        : {age_group}",
            f"  Ethnicity  : {ethnicity}",
            f"  Style      : {art_style} [w:{art_style_weight}]",
            f"  Archetype  : {archetype}",
            f"  Hair       : {hair_style} / {hair_color}",
            f"  Eyes       : {eye_style} / {eye_color}",
            f"  Outfit     : {outfit}",
            f"  Light      : {lighting}",
            f"  Camera     : {camera_angle}",
            f"  Seed       : {final_seed} {'(DNA sha256)' if use_char_seed else '(base)'}",
            f"  Res        : {out_w}x{out_h} ({'SDXL' if is_sdxl else 'SD1.5'})",
            f"  CFG/Steps  : {rec_cfg} / {rec_steps} ({rec_sampler}/{rec_scheduler})",
            f"  Embeds+    : {pos_embeds or 'none'}",
            f"  Embeds-    : {neg_embeds or 'none'}",
            cn_info,
            *lora_info,
            "  ─────────────────────────────────",
            f"  +Prompt    : {len(pos_text)} chars",
            f"  -Prompt    : {len(neg_text)} chars",
            "╚═════════════════════════════════╝",
        ]))

        return (
            positive_cond, negative_cond, model, clip,
            latent_out, out_w, out_h, final_seed, rec_cfg, rec_steps,
            debug
        )

    @classmethod
    def IS_CHANGED(cls, *args, **kwargs):
        """Hash all widget values — any change = re-run."""
        import hashlib, json
        try:
            state = json.dumps(list(args) + sorted(kwargs.items()), sort_keys=True, default=str)
        except Exception:
            state = str(args) + str(kwargs)
        return hashlib.sha256(state.encode()).hexdigest()


# ═══════════════════════════════════════════════════════════
#  QUICK PRESET NODE v3.1
#  FIX: lora_1_clip_str was using lora_1_str for BOTH model
#       and clip strength — now uses separate parameters.
# ═══════════════════════════════════════════════════════════

QUICK_PRESETS = {
    "⚔️ Epic Female Warrior": {
        "gender": "👩 Female", "gender_lock_strength": 1.6,
        "art_style": "🎌 Anime SD1.5", "art_style_weight": 1.3,
        "quality_preset": "🎌 Anime Max",
        "age_group": "🌟 Young Adult (18-24)", "body_type": "💪 Athletic",
        "ethnicity": "🌐 No Preference",
        "hair_style": "Long & Flowing", "hair_color": "⬛ Jet Black",
        "eye_style": "Large Anime", "eye_color": "🔵 Blue",
        "archetype": "⚔️ Hero / Warrior", "expression": "😤 Fierce / Determined",
        "outfit": "⚔️ Fantasy Armor",
        "lighting": "🎬 Cinematic Dramatic", "camera_angle": "🧍 Full Body Standing",
        "background": "🏔️ Epic Fantasy Land",
        "custom_facial": "light scar on cheek",
    },
    "🧙 Female Dark Mage": {
        "gender": "👩 Female", "gender_lock_strength": 1.6,
        "art_style": "⚔️ Fantasy Illustration SD1.5", "art_style_weight": 1.3,
        "quality_preset": "🥇 Maximum",
        "age_group": "🌟 Young Adult (18-24)", "body_type": "🌸 Slim / Petite",
        "ethnicity": "🌐 No Preference",
        "hair_style": "Long & Flowing", "hair_color": "🟣 Vivid Purple",
        "eye_style": "Glowing Magical", "eye_color": "🔴 Red",
        "archetype": "💀 Necromancer", "expression": "😈 Sinister / Evil",
        "outfit": "🧙 Mage Robes",
        "lighting": "🌑 Dark & Moody", "camera_angle": "📸 Upper Body (3/4)",
        "background": "🏚️ Dark Dungeon",
    },
    "🚀 Male Space Commander": {
        "gender": "👨 Male", "gender_lock_strength": 1.6,
        "art_style": "🎮 3D Render SD1.5", "art_style_weight": 1.2,
        "quality_preset": "🥇 Maximum",
        "age_group": "💼 Adult (25-35)", "body_type": "💪 Athletic",
        "ethnicity": "🌐 No Preference",
        "hair_style": "Short & Neat", "hair_color": "🟫 Dark Brown",
        "eye_style": "Sharp Intense", "eye_color": "🩶 Grey",
        "archetype": "🚀 Space Marine", "expression": "😤 Fierce / Determined",
        "outfit": "🤖 Futuristic Sci-Fi",
        "lighting": "🎬 Cinematic Dramatic", "camera_angle": "📸 Upper Body (3/4)",
        "background": "🌌 Space / Cosmos",
    },
    "🌸 Cute Anime Girl": {
        "gender": "👩 Female", "gender_lock_strength": 1.7,
        "art_style": "🎌 Anime SD1.5", "art_style_weight": 1.4,
        "quality_preset": "🎌 Anime Max",
        "age_group": "🧑 Teen (14-17)", "body_type": "🌸 Slim / Petite",
        "ethnicity": "🇯🇵 East Asian",
        "hair_style": "Twin Tails", "hair_color": "🩷 Vivid Pink",
        "eye_style": "Large Anime", "eye_color": "🔵 Blue",
        "archetype": "None", "expression": "😊 Warm Smile",
        "outfit": "🎓 School Uniform",
        "lighting": "📷 Studio Soft", "camera_angle": "👤 Head & Shoulders",
        "background": "🌸 Japanese Garden",
    },
    "⚙️ Cyberpunk Assassin (F)": {
        "gender": "👩 Female", "gender_lock_strength": 1.6,
        "art_style": "🌆 Cyberpunk SD1.5", "art_style_weight": 1.3,
        "quality_preset": "🥇 Maximum",
        "age_group": "🌟 Young Adult (18-24)", "body_type": "💪 Athletic",
        "ethnicity": "🌐 No Preference",
        "hair_style": "Short & Neat", "hair_color": "⬜ Platinum / Silver",
        "eye_style": "Cybernetic", "eye_color": "🔵 Teal",
        "archetype": "🗡️ Rogue / Assassin", "expression": "😏 Confident Smirk",
        "outfit": "🤖 Futuristic Sci-Fi",
        "lighting": "🌈 Neon / Cyberpunk", "camera_angle": "🧍 Full Body Standing",
        "background": "🌇 Cyberpunk City",
        "custom_outfit_extra": "hood, tactical vest",
    },
    "🧛 Vampire Noble (M)": {
        "gender": "👨 Male", "gender_lock_strength": 1.6,
        "art_style": "🌑 Dark Fantasy SD1.5", "art_style_weight": 1.3,
        "quality_preset": "🥇 Maximum",
        "age_group": "💼 Adult (25-35)", "body_type": "🌿 Lean / Tall",
        "ethnicity": "🏔️ European",
        "hair_style": "Long & Flowing", "hair_color": "⬛ Jet Black",
        "eye_style": "Glowing Magical", "eye_color": "🔴 Red",
        "archetype": "🧛 Vampire", "expression": "😏 Confident Smirk",
        "outfit": "👑 Royal / Aristocratic",
        "lighting": "🌙 Moonlight / Night", "camera_angle": "📸 Upper Body (3/4)",
        "background": "🌇 Cyberpunk City",
        "custom_facial": "vampire fangs, pale ethereal skin",
    },
    "😇 Divine Angel (F)": {
        "gender": "👩 Female", "gender_lock_strength": 1.65,
        "art_style": "⚔️ Fantasy Illustration SD1.5", "art_style_weight": 1.3,
        "quality_preset": "🥇 Maximum",
        "age_group": "🌟 Young Adult (18-24)", "body_type": "👻 Ethereal",
        "ethnicity": "🌐 No Preference",
        "hair_style": "Long & Flowing", "hair_color": "🟡 Golden Blonde",
        "eye_style": "Glowing Magical", "eye_color": "⬜ White",
        "archetype": "😇 Angel / Seraph", "expression": "😌 Serene / Peaceful",
        "outfit": "👗 Elegant Dress",
        "lighting": "😇 Divine / Holy", "camera_angle": "🧍 Full Body Standing",
        "background": "✨ Magical Abstract",
        "custom_facial": "large white feathered wings",
    },
    "🐉 Dragon Slayer (M)": {
        "gender": "👨 Male", "gender_lock_strength": 1.6,
        "art_style": "⚔️ Fantasy Illustration SD1.5", "art_style_weight": 1.3,
        "quality_preset": "🥇 Maximum",
        "age_group": "💼 Adult (25-35)", "body_type": "🏋️ Muscular",
        "ethnicity": "🌐 No Preference",
        "hair_style": "Short & Neat", "hair_color": "🟫 Dark Brown",
        "eye_style": "Sharp Intense", "eye_color": "🟡 Amber",
        "archetype": "🐉 Dragon Slayer", "expression": "😤 Fierce / Determined",
        "outfit": "⚔️ Fantasy Armor",
        "lighting": "🌅 Golden Hour", "camera_angle": "💥 Dynamic Action Pose",
        "background": "⚔️ Battlefield",
        "custom_facial": "battle scars, rough beard stubble",
    },
}


class CharacterQuickPresetV3:
    """
    Quick Preset v3.1
    FIX: lora_1_clip_str now has its own parameter (was using lora_1_str twice).
    """

    CATEGORY     = "🎨 Character Creator Pro"
    FUNCTION     = "load"
    RETURN_TYPES = ("CONDITIONING", "CONDITIONING", "MODEL", "CLIP", "STRING")
    RETURN_NAMES = ("positive",     "negative",     "model",  "clip",  "info")
    OUTPUT_NODE  = False

    @classmethod
    def INPUT_TYPES(cls):
        lora_list = ["None"] + folder_paths.get_filename_list("loras")
        return {
            "required": {
                "model":  ("MODEL",),
                "clip":   ("CLIP",),
                "preset": (list(QUICK_PRESETS.keys()),),
                "lora_1":           (lora_list, {"default": "None"}),
                "lora_1_model_str": ("FLOAT", {
                    "default": 0.8, "min": -2.0, "max": 2.0,
                    "step": 0.05, "display": "slider"
                }),
                "lora_1_clip_str":  ("FLOAT", {   # FIX: was missing, used lora_1_model_str for both
                    "default": 0.8, "min": -2.0, "max": 2.0,
                    "step": 0.05, "display": "slider"
                }),
            },
            "optional": {
                "append_positive": ("STRING", {
                    "default": "", "multiline": True,
                    "placeholder": "إضافة للـ positive..."
                }),
                "append_negative": ("STRING", {
                    "default": "", "multiline": True,
                    "placeholder": "إضافة للـ negative..."
                }),
            }
        }

    def load(self, model, clip, preset, lora_1, lora_1_model_str, lora_1_clip_str,
             append_positive="", append_negative=""):
        cfg = dict(QUICK_PRESETS[preset])

        # Ensure all optional keys exist with safe defaults
        for key in ("custom_facial", "custom_outfit_extra", "custom_extra",
                    "extra_negative", "character_name"):
            cfg.setdefault(key, "")

        pos_text = build_positive_prompt(cfg)
        neg_text = build_negative_prompt(cfg)

        if append_positive.strip():
            pos_text += f", {append_positive.strip()}"
        if append_negative.strip():
            neg_text += f", {append_negative.strip()}"

        # FIX: pass separate model/clip strengths
        model, clip = apply_lora(model, clip, lora_1, lora_1_model_str, lora_1_clip_str)

        pos_cond = encode_prompt(clip, pos_text)
        neg_cond = encode_prompt(clip, neg_text)

        info = (
            f"Preset: {preset} | "
            f"LoRA: {lora_1} [{lora_1_model_str}/{lora_1_clip_str}] | "
            f"+{len(pos_text)}c / -{len(neg_text)}c"
        )

        return (pos_cond, neg_cond, model, clip, info)


# ═══════════════════════════════════════════════════════════
#  REGISTRATION
# ═══════════════════════════════════════════════════════════

NODE_CLASS_MAPPINGS = {
    "CharacterCreatorPro":  CharacterCreatorProV10,
    "CharacterQuickPreset": CharacterQuickPresetV3,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "CharacterCreatorPro":  "🎨 Character Creator Pro v10.1",
    "CharacterQuickPreset": "⚡ Character Quick Preset v10.1",
}

# ─────────────────────────────────────────────────────────
#  __init__.py content (place in same folder as this file):
#
#  from .character_creator_pro_v10 import NODE_CLASS_MAPPINGS, NODE_DISPLAY_NAME_MAPPINGS
#  __all__ = ["NODE_CLASS_MAPPINGS", "NODE_DISPLAY_NAME_MAPPINGS"]
# ─────────────────────────────────────────────────────────
