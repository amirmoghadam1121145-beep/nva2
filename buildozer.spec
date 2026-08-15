[app]

title = NOVA
package.name = nova
package.domain = org.nova.assistant

source.dir = .
source.include_exts = py,png,jpg,kv,atlas,ttf

version = 0.1.0

# python3,kivy: the app itself
# plyer: battery / text-to-speech
# pyjnius, android: direct Android API access (speech recognizer, intents)
requirements = python3,kivy==2.3.0,plyer==2.1.0,pyjnius,android

orientation = portrait
fullscreen = 0

# No custom icon/presplash for v1 -- Buildozer uses its default Kivy
# icon so the very first build can't fail over a missing image file.
# Add icon.filename / presplash.filename here later once you have real
# artwork (see README.md "افزودن آیکون بعداً").

# Microphone for voice input, internet for TTS/STT engine data if the
# device needs to fetch a language pack, camera for the "camera" command.
android.permissions = RECORD_AUDIO, INTERNET, CAMERA, MODIFY_AUDIO_SETTINGS

android.api = 34
android.minapi = 23
android.ndk = 25b
android.archs = arm64-v8a, armeabi-v7a
android.allow_backup = True

# Keep the app running only in the foreground for v1 (simple + battery
# friendly); a persistent background service can be added later.
android.wakelock = False

[buildozer]
log_level = 2
warn_on_root = 1
