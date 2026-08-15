# NOVA Android — نسخه مستقل موبایل

این پروژه کاملاً **جدا** از `nova_desktop` (نسخه ویندوز) است. هیچ فایلی از نسخه ویندوز
تغییر نکرده و این پوشه هیچ وابستگی‌ای به آن ندارد — روی گوشی، بدون لپ‌تاپ، مستقل اجرا می‌شود.

## چرا Kivy و نه PyQt5 یا Flutter؟

- **PyQt5** (نسخه ویندوز) اصلاً روی اندروید کار نمی‌کند — Qt for Android وجود دارد ولی
  PyQt5 پکیج‌بندی رسمی برای اندروید ندارد و ساخت APK از آن عملاً پشتیبانی نمی‌شود.
- **Flutter** گزینه‌ی خوبی است ولی یعنی کل منطق (state machine، دستورها) باید از پایتون به
  Dart بازنویسی شود — با توجه به خواسته‌ی شما («نسخه اول ساده باشد»)، این کار غیرضروری بود.
- **Kivy + Buildozer** انتخاب شد چون:
  - کد پایتون تقریباً مستقیم قابل استفاده است (همان معماری، همان `state.py`/`commands.py`)،
  - رندر Canvas آن (`kivy.graphics`) برای ربات هولوگرافیک procedural کاملاً مناسب است،
  - انیمیشن نرم با `kivy.animation.Animation` (بدون Teleport) بومی پشتیبانی می‌شود،
  - `python-for-android` (بدون واسطه‌ی Buildozer یا Android Studio) مستقیماً یک پروژه‌ی
    Gradle می‌سازد و با Android SDK/NDK آن را کامپایل می‌کند — ساده‌ترین مسیر استاندارد
    برای v1 (جزئیات در بخش «ساخت APK» پایین‌تر).

## معماری (همان الگوی نسخه ویندوز)

```
main.py
  └─ NovaCore            (nova/core/nova_core.py)   -- state, memory, plugin registry
       └─ NovaBridge      (nova/core/bridge.py)       -- STT callbacks → NovaCore
       └─ UI (main.py + nova/ui/robot_widget.py)       -- Robot + Chat + Mic Button
              └─ RobotWidget   -- رندر procedural + انیمیشن (بدون Teleport)
```

دقیقاً مثل نسخه ویندوز: `NovaCore` هیچ‌وقت مستقیم با ویجت‌ها کار ندارد، فقط State و
پیام‌های گفتاری را مدیریت می‌کند. این یعنی بعداً برای اضافه‌کردن:

- **AI Chat** واقعی (به‌جای پیام «I don't know that command yet.»)
- **Memory** واقعی (`core.remember()` / `core.recall()` از قبل آماده است)
- **Camera / Computer Vision**
- **Face Tracking**
- **Plugin System** (`core.register_plugin()` از قبل آماده است)

فقط کافی است یک `attach_xxx()` جدید به `nova/core/bridge.py` اضافه شود — بدون دست‌زدن به
رندر یا Layout، دقیقاً مثل الگوی `attach_voice_engine()` در نسخه ویندوز.

### چیزی که از ویندوز عوض شد (و چرا)

| ویندوز (`nova_desktop`)                          | اندروید (`nova_android`)                                   |
|---------------------------------------------------|--------------------------------------------------------------|
| PyQt5 + QPainter                                   | Kivy + `kivy.graphics` Canvas                                 |
| `SpeechRecognition` + `PyAudio`                    | `android.speech.RecognizerIntent` (STT بومی اندروید)          |
| `pyttsx3`                                          | `plyer.tts` → TextToSpeech بومی اندروید (fallback: pyttsx3)   |
| دستورها: chrome, notepad, calculator, time, hello, stop | دستورها: browser, camera, battery, time, hello, stop (بدون notepad/calculator — معادل اندرویدی معنادار ندارند) |
| ۸ حالت (IDLE/WALKING/…/HAPPY/ALERT)                | ۴ حالت اصلی خواسته‌شده: IDLE / LISTENING / THINKING / SPEAKING |

State machine (`nova/state.py`) و منطق «هیچ‌وقت پروتکتد state قطع نشود مگر force=True»
عیناً از نسخه ویندوز کپی شده — پایه‌ی مشترک هر دو نسخه یکی است.

## ساختار فایل‌ها

```
nova_android/
├── main.py                    ← نقطه‌ی ورود، Layout، اتصال همه‌چیز به هم
├── buildozer.spec             ← تنظیمات ساخت APK
├── requirements.txt           ← وابستگی‌های هاست (تست دسکتاپ + خود buildozer)
├── .github/workflows/build-apk.yml  ← ساخت خودکار APK در فضای ابری (پایین توضیح داده شده)
└── nova/
    ├── config.py               ← رنگ‌ها و زمان‌بندی انیمیشن‌ها
    ├── state.py                ← State machine (framework-independent)
    ├── commands.py             ← جدول دستورها (Android-appropriate)
    ├── platform_actions.py     ← اکشن‌های واقعی اندروید (باز کردن مرورگر/دوربین/باتری)
    ├── core/
    │   ├── nova_core.py        ← منبع حقیقت State + Memory/Plugin scaffold
    │   └── bridge.py           ← اتصال STT به NovaCore
    ├── voice/
    │   ├── tts_service.py      ← Text-to-Speech (بومی اندروید + fallback دسکتاپ)
    │   └── stt_service.py      ← Speech-to-Text (بومی اندروید + fallback دسکتاپ)
    └── ui/
        └── robot_widget.py     ← ربات procedural + انیمیشن (holographic, no teleport)
```

---

## ۱) تست منطق روی لپ‌تاپ (اختیاری ولی توصیه‌شده، قبل از ساخت APK)

```bash
cd nova_android
python -m venv venv
source venv/bin/activate        # ویندوز: venv\Scripts\activate
pip install -r requirements.txt
python main.py
```

روی دسکتاپ، دکمه‌ی میکروفون به‌جای STT واقعی اندروید یک ورودی متنی در ترمینال باز می‌کند
(`[NOVA test-mode] Type what you would say:`) تا کل جریان State/Chat/TTS بدون گوشی
قابل تست باشد — یعنی می‌توانید مطمئن شوید منطق قبل از رفتن سراغ ساخت APK درست کار می‌کند.

---

## ۲) ساخت APK با `build_apk.sh` (python-for-android + Gradle + Android SDK — بدون Buildozer، بدون Android Studio)

این پروژه دیگر از Buildozer استفاده نمی‌کند. اسکریپت `build_apk.sh` مستقیماً از
**python-for-android (p4a)** استفاده می‌کند — همان ابزاری که Buildozer هم زیرِ پوستِ
خودش صدا می‌زد، فقط این‌بار مستقیم و بدون لایه‌ی اضافه. p4a یک پروژه‌ی **Gradle** واقعی
می‌سازد و با **Android SDK + NDK** آن را کامپایل می‌کند — دقیقاً همان توالی استاندارد
Gradle + Android SDK، بدون Buildozer و بدون نیاز به نصب Android Studio.

⚠️ فقط روی **Linux** کار می‌کند (یا **WSL2 (Ubuntu)** روی ویندوز). macOS معمولاً کار
می‌کند ولی رسماً پشتیبانی نمی‌شود.

### نصب پیش‌نیازهای سیستم (Ubuntu / WSL2)

```bash
sudo apt update
sudo apt install -y openjdk-17-jdk python3 python3-pip python3-venv git unzip zip \
    build-essential autoconf automake libtool pkg-config zlib1g-dev \
    libncurses5-dev libffi-dev libssl-dev
```

### ساخت APK

```bash
cd nova_android
chmod +x build_apk.sh
./build_apk.sh
```

اسکریپت به‌ترتیب:

1. Android SDK cmdline-tools را (اگر از قبل نیست) دانلود می‌کند.
2. با `sdkmanager` این‌ها را نصب می‌کند: `platform-tools`، `platforms;android-34`،
   `build-tools;34.0.0`، `ndk;25.2.9519653` (همان نسخه‌هایی که پروژه از اول هدف گرفته بود).
3. `python-for-android` و `Cython` را در یک venv مجزا (`.build-venv/`) نصب می‌کند —
   این‌ها فقط ابزار build هستند، داخل APK نهایی قرار نمی‌گیرند.
4. دستور `p4a apk` را با تنظیمات دقیقاً معادل تنظیمات قبلی (permissions، package name،
   requirements، orientation، minSDK/targetSDK، معماری‌های arm64-v8a و armeabi-v7a) اجرا
   می‌کند — این همان جایی است که p4a پروژه‌ی Gradle را می‌سازد و Gradle را صدا می‌زند.
5. فایل `.apk` نهایی را در `dist/` کپی می‌کند.

نکات مهم:

- **بار اول** دانلود SDK/NDK و کامپایل وابستگی‌ها می‌تواند **۲۰ تا ۴۵ دقیقه** طول بکشد
  (نیاز به اینترنت پایدار). بارهای بعدی خیلی سریع‌تر است چون همه‌چیز کش می‌شود
  (`~/android-sdk`، `.build-venv/`).
- خروجی نهایی در `dist/*.apk` قرار می‌گیرد.
- برای نصب مستقیم روی گوشی متصل با کابل (با USB Debugging فعال):
  ```bash
  adb install -r dist/*.apk
  ```

> فایل `buildozer.spec` هنوز در پروژه نگه داشته شده (فقط برای مرجع/fallback اختیاری —
> باگ escape شدنِ خط‌جدیدهایش هم برطرف شد) ولی مسیر build رسمی و توصیه‌شده همین
> `build_apk.sh` است، نه Buildozer.

---

## ۳) ساخت APK بدون نیاز به Linux محلی (GitHub Actions — پیشنهاد می‌شود)

Workflow موجود در `.github/workflows/build-apk.yml` هم به‌روزرسانی شد و دیگر از Buildozer
استفاده نمی‌کند — دقیقاً همان `p4a apk` بالا را روی یک ماشین اوبونتوی تمیز در فضای ابری
گیت‌هاب (رایگان) اجرا می‌کند. نیازی به نصب هیچ‌چیزی روی سیستم خودتان نیست:

1. یک ریپازیتوری جدید در GitHub بسازید و کل پوشه‌ی `nova_android` را push کنید.
2. به تب **Actions** بروید → روی workflow با نام **Build NOVA APK** کلیک کنید →
   **Run workflow**.
3. حدود ۱۵ تا ۲۵ دقیقه صبر کنید (اجرای اول کندتر است چون SDK/NDK دانلود می‌شود).
4. وقتی اجرا سبز شد، پایین صفحه‌ی همان اجرا بخش **Artifacts** را باز کنید و
   **NOVA-debug-APK** را دانلود کنید — همان فایل `.apk` قابل نصب روی گوشی است.

---

## ۴) نصب APK روی گوشی

1. فایل `.apk` را روی گوشی کپی کنید (کابل، تلگرام به خودتان، گوگل درایو، هرچه راحت‌تر است).
2. روی فایل بزنید → اگر اندروید اجازه‌ی «نصب از منابع ناشناس» خواست، به همان اپلیکیشنی که
   فایل را باز کرده‌اید (فایل‌منیجر/مرورگر) اجازه بدهید.
3. بعد از نصب، اولین اجرا اجازه‌ی **میکروفون (RECORD_AUDIO)** را می‌پرسد — تایید کنید تا
   دکمه‌ی صحبت کار کند.

> این یک Debug APK است (برای تست شخصی امضا شده) — برای انتشار در Google Play باید بعداً
> با `p4a apk --release ...` (بدون `--debug`) و امضای رسمی (keystore) ساخته شود؛ فعلاً
> نیازی به آن نیست.

---

## دستورهای فعلی NOVA روی اندروید

| بگویید/تایپ کنید | NOVA چه می‌کند |
|---|---|
| `hello` | سلام می‌گوید |
| `time` | ساعت فعلی را می‌گوید |
| `browser` یا `chrome` | مرورگر پیش‌فرض گوشی را باز می‌کند |
| `camera` | اپ دوربین گوشی را باز می‌کند |
| `battery` | درصد باتری فعلی را می‌گوید |
| `stop` یا `exit` | خداحافظی می‌کند و برنامه می‌بندد |

هر پیام دیگری فعلاً پاسخ ثابت «I don't know that command yet.» می‌گیرد — این دقیقاً همان
نقطه‌ای است که بعداً یک AI Chat واقعی جایگزینش می‌شود (`commands.dispatch()` در `main.py`).

## گام‌های بعدی (بعد از اینکه v1 روی گوشی سالم اجرا شد)

- افزودن آیکون واقعی: `assets/icon.png` بسازید و دو خط `icon.filename` /
  `presplash.filename` را در `buildozer.spec` برگردانید.
- اتصال به یک AI Chat واقعی به‌جای پاسخ ثابت (نقطه‌ی اتصال در `main.py._handle_text`).
- افزودن حالت‌های بیشتر (HAPPY/ALERT/SLEEPING) — `nova/state.py` و `robot_widget.py`
  از قبل برای این گسترش طراحی شده‌اند.
- Camera / Computer Vision / Face Tracking / Plugin System — طبق معماری موجود فقط با
  یک `attach_xxx()` جدید در `nova/core/bridge.py`.

## محدودیت شناخته‌شده در این نسخه

من (Claude) این پروژه را در یک sandbox بدون دسترسی به اینترنت و بدون Android SDK/NDK/Gradle
نصب‌شده بررسی و آماده کردم، پس **خودم نتوانستم `build_apk.sh` را واقعاً اجرا کنم** و یک
فایل APK آماده برایتان پیوست کنم — چون این کار نیاز به دانلود چند گیگابایت Android SDK/NDK
دارد. تمام فایل‌های Python را با `python3 -m py_compile` از نظر سینتکسی چک کردم (بدون خطا)
و منطق برنامه (که از قبل درست بود) دست‌نخورده مانده است — تغییرات فقط در لایه‌ی build بود
(حذف کامل Buildozer، جایگزینی با `python-for-android` مستقیم که خودش Gradle + Android SDK
را صدا می‌زند).

به همین دلیل روش شماره ۳ (GitHub Actions) را آماده/به‌روزرسانی کردم تا با یک کلیک، بدون
نصب هیچ‌چیزی روی سیستم خودتان، APK واقعی و قابل‌نصب بگیرید — یا می‌توانید `build_apk.sh`
را روی یک ماشین Linux/WSL2 با اینترنت اجرا کنید. توصیه می‌کنم قبل از build اول مرحله‌ی
«تست روی لپ‌تاپ» (بخش ۱) را هم انجام دهید تا هرگونه رفتار غیرمنتظره را زودتر ببینید.
