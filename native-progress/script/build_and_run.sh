#!/usr/bin/env bash
set -euo pipefail
MODE="${1:-run}"
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"
APP_NAME=IndexerProgress
BUNDLE_ID=local.ariel.IndexerProgress
APP_BUNDLE="$ROOT_DIR/dist/$APP_NAME.app"
pkill -x "$APP_NAME" >/dev/null 2>&1 || true
swift build --jobs 2
BUILD_BINARY="$(swift build --show-bin-path)/$APP_NAME"
mkdir -p "$APP_BUNDLE/Contents/MacOS"
cp "$BUILD_BINARY" "$APP_BUNDLE/Contents/MacOS/$APP_NAME"
cat > "$APP_BUNDLE/Contents/Info.plist" <<PLIST
<?xml version="1.0" encoding="UTF-8"?><!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd"><plist version="1.0"><dict><key>CFBundleExecutable</key><string>$APP_NAME</string><key>CFBundleIdentifier</key><string>$BUNDLE_ID</string><key>CFBundleName</key><string>AI Indexer</string><key>CFBundlePackageType</key><string>APPL</string><key>LSMinimumSystemVersion</key><string>14.0</string><key>NSPrincipalClass</key><string>NSApplication</string><key>NSAppTransportSecurity</key><dict><key>NSAllowsLocalNetworking</key><true/></dict></dict></plist>
PLIST
case "$MODE" in
 --build-only) ;;
 run) /usr/bin/open -n "$APP_BUNDLE" ;;
 --verify) /usr/bin/open -n "$APP_BUNDLE"; sleep 1; pgrep -x "$APP_NAME" >/dev/null ;;
 --debug) lldb -- "$APP_BUNDLE/Contents/MacOS/$APP_NAME" ;;
 --logs|--telemetry) /usr/bin/open -n "$APP_BUNDLE"; /usr/bin/log stream --info --style compact --predicate "process == \"$APP_NAME\"" ;;
 *) echo 'usage: build_and_run.sh [run|--build-only|--verify|--debug|--logs|--telemetry]' >&2; exit 2 ;;
esac
