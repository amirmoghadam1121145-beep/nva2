#!/usr/bin/env bash
#
# NOVA Android -- APK build script.
#
# Builds the APK using python-for-android (p4a) DIRECTLY -- NOT Buildozer,
# NOT Android Studio. p4a generates a real Gradle Android project and
# invokes Gradle + the Android SDK/NDK to compile it, which is exactly
# the standard toolchain (Gradle + Android SDK) requested.
#
# What this script does, step by step:
#   1) checks/install system prerequisites (Java 17, python3, unzip, git)
#   2) downloads Android cmdline-tools (SDK) if not already present
#   3) uses sdkmanager to install: platform-tools, platform 34, build-tools 34,
#      and NDK 25b (same versions the project was already targeting)
#   4) pip-installs python-for-android + Cython (build-time only, NOT bundled)
#   5) runs `p4a apk` with flags equivalent to the old buildozer.spec
#   6) copies the resulting .apk into ./dist/
#
# Requirements: Linux (native or WSL2). macOS mostly works too but is
# not officially supported by p4a for NDK toolchains as reliably.
#
# Usage:
#   chmod +x build_apk.sh
#   ./build_apk.sh
#
# Re-running is safe and fast after the first run (SDK/NDK/pip caches persist).

set -euo pipefail

# ---- configurable versions (kept identical to the project's original targets) ----
ANDROID_API=34
ANDROID_MINAPI=23
ANDROID_BUILD_TOOLS=34.0.0
ANDROID_NDK_VERSION=25b
ANDROID_NDK_PKG="25.2.9519653"     # sdkmanager package id for NDK 25b
CMDLINE_TOOLS_VERSION=11076708      # Android cmdline-tools version (stable)

APP_TITLE="NOVA"
PACKAGE_NAME="nova"
PACKAGE_DOMAIN="org.nova.assistant"
APP_VERSION="0.1.0"

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SDK_DIR="${ANDROID_SDK_ROOT:-$HOME/android-sdk}"
NDK_DIR="$SDK_DIR/ndk/$ANDROID_NDK_PKG"

echo "== NOVA APK build (python-for-android + Gradle + Android SDK, no Buildozer) =="
echo "Project dir : $ROOT_DIR"
echo "SDK dir     : $SDK_DIR"
echo

# ---- 1) system prerequisites -------------------------------------------------
missing=()
command -v java   >/dev/null 2>&1 || missing+=("openjdk-17-jdk")
command -v python3 >/dev/null 2>&1 || missing+=("python3")
command -v pip3   >/dev/null 2>&1 || missing+=("python3-pip")
command -v git    >/dev/null 2>&1 || missing+=("git")
command -v unzip  >/dev/null 2>&1 || missing+=("unzip")
command -v zip    >/dev/null 2>&1 || missing+=("zip")

if [ ${#missing[@]} -ne 0 ]; then
  echo "Missing system packages: ${missing[*]}"
  echo "Install them first, e.g. on Ubuntu/WSL2:"
  echo "  sudo apt update && sudo apt install -y openjdk-17-jdk python3 python3-pip python3-venv git unzip zip \\"
  echo "       build-essential autoconf automake libtool pkg-config zlib1g-dev libncurses5-dev libffi-dev libssl-dev"
  exit 1
fi

JAVA_VER="$(java -version 2>&1 | head -1)"
echo "Java found: $JAVA_VER"
echo

# ---- 2) Android SDK cmdline-tools --------------------------------------------
if [ ! -x "$SDK_DIR/cmdline-tools/latest/bin/sdkmanager" ]; then
  echo "-- Downloading Android cmdline-tools (SDK) --"
  mkdir -p "$SDK_DIR/cmdline-tools"
  TMP_ZIP="$(mktemp)"
  curl -fsSL -o "$TMP_ZIP" \
    "https://dl.google.com/android/repository/commandlinetools-linux-${CMDLINE_TOOLS_VERSION}_latest.zip"
  unzip -q -o "$TMP_ZIP" -d "$SDK_DIR/cmdline-tools/_tmp"
  rm -rf "$SDK_DIR/cmdline-tools/latest"
  mv "$SDK_DIR/cmdline-tools/_tmp/cmdline-tools" "$SDK_DIR/cmdline-tools/latest"
  rm -rf "$SDK_DIR/cmdline-tools/_tmp" "$TMP_ZIP"
else
  echo "Android cmdline-tools already present, skipping download."
fi

export ANDROID_SDK_ROOT="$SDK_DIR"
export ANDROID_HOME="$SDK_DIR"
export PATH="$SDK_DIR/cmdline-tools/latest/bin:$SDK_DIR/platform-tools:$PATH"

echo "-- Installing SDK platform/build-tools/NDK (only what's missing) --"
yes | sdkmanager --licenses >/dev/null 2>&1 || true
sdkmanager \
  "platform-tools" \
  "platforms;android-${ANDROID_API}" \
  "build-tools;${ANDROID_BUILD_TOOLS}" \
  "ndk;${ANDROID_NDK_PKG}"

export ANDROIDSDK="$SDK_DIR"
export ANDROIDNDK="$NDK_DIR"
export ANDROIDAPI="$ANDROID_API"
export ANDROIDMINAPI="$ANDROID_MINAPI"

echo
echo "SDK ready at:  $SDK_DIR"
echo "NDK ready at:  $NDK_DIR"
echo

# ---- 3) python-for-android (build tool only, not bundled into the APK) ------
echo "-- Installing/upgrading python-for-android + Cython in a venv --"
VENV_DIR="$ROOT_DIR/.build-venv"
if [ ! -d "$VENV_DIR" ]; then
  python3 -m venv "$VENV_DIR"
fi
source "$VENV_DIR/bin/activate"
pip install --upgrade pip
pip install --upgrade "python-for-android" "cython==0.29.37" "sh"

echo
echo "python-for-android version: $(p4a --version)"
echo

# ---- 4) build the APK with p4a directly (this is what invokes Gradle) -------
echo "-- Building APK with p4a (this drives Gradle + the Android SDK/NDK) --"
cd "$ROOT_DIR"

p4a apk \
  --private "$ROOT_DIR" \
  --package="${PACKAGE_DOMAIN}.${PACKAGE_NAME}" \
  --name="$APP_TITLE" \
  --version="$APP_VERSION" \
  --bootstrap=sdl2 \
  --requirements=python3,kivy==2.3.0,plyer==2.1.0,pyjnius,android \
  --orientation=portrait \
  --permission=RECORD_AUDIO \
  --permission=INTERNET \
  --permission=CAMERA \
  --permission=MODIFY_AUDIO_SETTINGS \
  --android-api="$ANDROID_API" \
  --minsdk="$ANDROID_MINAPI" \
  --ndk-api="$ANDROID_MINAPI" \
  --arch=arm64-v8a \
  --arch=armeabi-v7a \
  --dist-name="${PACKAGE_NAME}_dist" \
  --debug

echo
echo "-- Collecting the built APK into ./dist --"
mkdir -p "$ROOT_DIR/dist"
find "$ROOT_DIR" -maxdepth 4 -name "*-debug.apk" -newer "$ROOT_DIR/build_apk.sh" -exec cp -v {} "$ROOT_DIR/dist/" \;

echo
echo "== Done. Your APK should be in: $ROOT_DIR/dist/ =="
echo "Install it on a phone with USB debugging enabled via:"
echo "  adb install -r dist/*.apk"
