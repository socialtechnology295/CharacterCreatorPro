🎨 CHARACTER CREATOR PRO v10.1
Professional ComfyUI Custom Node

The Most Advanced Character Generation System for Stable Diffusion

45 Quadrillion+ Unique Combinations
12 Art Styles · SD1.5 + SDXL · 3 LoRA Slots · 8 Quick Presets
Triple Lockdown System — Gender · Age · Ethnicity

1️⃣ What Is Character Creator Pro?

Character Creator Pro هو عقدة احترافية مخصصة لـ ComfyUI تستبدل نظام الـ text prompt التقليدي بالكامل بواجهة مرئية منظمة تعتمد على Dropdowns وSliders.

بدلاً من كتابة Prompts معقدة وموزونة يدويًا، تقوم بتكوين الشخصية عبر واجهة منظمة — والعقدة تبني Prompt متعدد الطبقات وموزون بدقة في الخلفية.

🔒 الابتكار الأساسي: Triple Lockdown System

نظام ثلاثي الطبقات يمنع انجراف النماذج نحو الديموغرافيا الافتراضية:

الطبقة	الموقع داخل الـ Prompt	الوزن	الوظيفة
L1 – Anchor Tokens	Blocks 2, 4, 7	1.20 – 1.65×	تثبيت الهوية الأساسية
L2 – Physical Descriptors	بعد L1 مباشرة	0.85 – 1.40×	تعزيز الصفات الجسدية
L3 – Tail Anchors	نهاية الـ Prompt	0.60 – 0.85×	تعزيز متأخر أثناء الانتشار
Negative Tokens	بداية الـ Negative	—	منع التضارب

gender_lock_strength (1.0 – 2.0) يسمح بالتحكم بقوة الفرض.
للأطفال والمراهقين يتم ضبط الحد الأقصى تلقائيًا عند 1.2× لمنع تشوهات التشريح.

2️⃣ Installation Guide
المتطلبات
المكون	الحد الأدنى	الموصى به
ComfyUI	إصدار حديث	آخر نسخة مستقرة
Python	3.9+	3.10 / 3.11
VRAM	4GB (SD1.5)	8GB+ (SDXL)
PyTorch	2.0+	2.1+ CUDA 12
خطوات التثبيت

1️⃣ انسخ مجلد:

ComfyUI/custom_nodes/CharacterCreatorPro/

يجب أن يكون الهيكل:

CharacterCreatorPro/
├── character_creator_pro_v10.py
├── __init__.py
└── character_presets/

2️⃣ أعد تشغيل ComfyUI بالكامل
3️⃣ ابحث عن:

🎨 Character Creator Pro v10.1

⚡ Character Quick Preset v10.1

4️⃣ حمّل ملف:

character_creator_v10_workflow.json
إضافات موصى بها
الإضافة	طريقة التثبيت	التأثير
ADetailer	ComfyUI Manager	🔴 حدة الوجه
ControlNet	ComfyUI Manager	🟡 تحكم بالوضعية
IP-Adapter	ComfyUI Manager	🔴 ثبات الوجه
4x-UltraSharp	يدوي	🟡 تكبير 4K
EasyNegative / badhandv4	Embeddings	🟢 تحسين الجودة

ضع ملفات Upscale داخل:

ComfyUI/models/upscale_models/

و Embeddings داخل:

ComfyUI/models/embeddings/
3️⃣ Core Capabilities
🎛️ مكتبة الخيارات الكاملة

12 Art Styles

5 Quality Presets

4 Genders

7 Age Groups

7 Body Types

9 Ethnicities

16 Hairstyles

13 Hair Colors

8 Eye Styles

11 Eye Colors

18 Archetypes

15 Outfits

10 Expressions

10 Lighting Modes

9 Camera Angles

12 Backgrounds

📐 Auto-Resolution حسب زاوية الكاميرا
Camera Angle	SD1.5	SDXL
Portrait	512×768	832×1216
Full Body	512×1024	768×1344
Dynamic	768×960	896×1152
Square	768×768	1024×1024
⚙️ Auto-Sampler Recommendations
Style	Sampler	Steps	CFG
Anime SD1.5	DPM++ 2M	28	7.0
Photoreal SD1.5	DPM++ 2M SDE	30	6.5
Dark Fantasy	DPM++ 2M	32	8.5
Anime SDXL	DPM++ 2M	25	7.0
Photoreal SDXL	DPM++ 2M SDE	30	6.0
🧬 DNA Seed System

يعتمد على SHA-256 لاسم الشخصية + الجنس + العرق.
نفس الاسم = نفس DNA البصري دائمًا.

🎨 LoRA System (3 Slots)
Slot	الاستخدام
LoRA 1	أسلوب أساسي أو وجه
LoRA 2	ملابس / ستايل ثانوي
LoRA 3	تفاصيل دقيقة

القيم: -2.0 إلى +2.0
القيم السالبة تقلل التأثير.

💾 نظام Presets

حفظ بصيغة JSON

قابل للنقل بين الأجهزة

تحميل تلقائي لجميع الإعدادات

مثال:

{
  "gender": "👩 Female",
  "age_group": "🌟 Young Adult (18-24)",
  "ethnicity": "🏔️ European",
  "hair_color": "⬛ Jet Black"
}
4️⃣ Inputs & Outputs
المدخلات الأساسية

MODEL

CLIP

المخارج

positive (CONDITIONING)

negative (CONDITIONING)

latent

seed

cfg

steps

width / height

debug

جميعها موصلة تلقائيًا إلى KSampler داخل الـ Workflow.

5️⃣ Workflow Architecture

يتكون من 9 Nodes موزعة على 4 مجموعات:

المجموعة	الوظيفة
Character Setup	بناء الشخصية
Sampling	توليد الصورة
Upscale	تكبير 4K اختياري
Output	حفظ وعرض
6️⃣ Quick Preset Node

8 شخصيات جاهزة مثل:

⚔️ Epic Female Warrior

🧙 Female Dark Mage

🚀 Male Space Commander

🌸 Cute Anime Girl

🧛 Vampire Noble

😇 Divine Angel

🐉 Dragon Slayer

مع إمكانية append إيجابي وسلبي.

7️⃣ Advanced Usage
إنشاء سلسلة شخصية متسقة

اضبط الهوية

فعّل DNA Seed

احفظ Preset

غيّر المشهد فقط

استخدام Face LoRA

lora_1 model_str = 0.7

clip_str = 0.7

فعّل DNA Seed

8️⃣ Troubleshooting
المشكلة	الحل
الجنس خاطئ	ارفع gender_lock_strength
العمر غير دقيق	تحقق من archetype
LoRA لا يعمل	تأكد من المسار وأعد التشغيل
وجه ضبابي	ثبّت ADetailer
خطأ Upscale	ضع 4x-UltraSharp أو عطّل Upscale
9️⃣ Architecture Notes

كشف SDXL تلقائي

SHA-256 للـ seed fingerprint

IS_CHANGED hashing

Auto resolution table

LoRA API compatibility handling

🔄 Changelog v10.1

دعم ControlNet كمدخل اختياري

نقل Upscale إلى UpscaleModelLoader

استبدال MD5 بـ SHA-256

دعم tuple/dict LoRA API

توصيل seed/cfg/steps من العقدة مباشرة

✨ Conclusion

Character Creator Pro v10.1 هو نظام توليد شخصيات احترافي يحوّل ComfyUI إلى منصة تصميم شخصية متقدمة تعتمد على هندسة Prompt ذكية، قفل هوية متعدد الطبقات، ونظام LoRA احترافي.
