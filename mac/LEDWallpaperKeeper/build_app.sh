#!/bin/bash
# 맥에서 실행: ./build_app.sh  →  dist/LEDWallpaperKeeper.app 생성
set -euo pipefail
cd "$(dirname "$0")"
# UNIVERSAL=1 이면 애플실리콘+인텔 겸용(전체 Xcode 필요), 아니면 지금 맥 전용
ARCH_FLAGS=()
if [ "${UNIVERSAL:-0}" = "1" ]; then ARCH_FLAGS=(--arch arm64 --arch x86_64); fi
swift build -c release ${ARCH_FLAGS[@]+"${ARCH_FLAGS[@]}"}
BIN="$(swift build -c release ${ARCH_FLAGS[@]+"${ARCH_FLAGS[@]}"} --show-bin-path)/LEDWallpaperKeeper"
APP="dist/LEDWallpaperKeeper.app"
rm -rf dist
mkdir -p "$APP/Contents/MacOS" "$APP/Contents/Resources"
cp "$BIN" "$APP/Contents/MacOS/LEDWallpaperKeeper"
cp Info.plist "$APP/Contents/Info.plist"
codesign --force --deep --sign - "$APP"
echo "완료: $(pwd)/$APP"
