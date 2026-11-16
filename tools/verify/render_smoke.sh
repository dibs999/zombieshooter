#!/usr/bin/env bash
# Render actual Vulkan/Forward+ images without the cloud Desktop panel.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
RUNTIME="${BUNKER_RUNTIME_DIR:-/workspace/.zombieshooter-runtime}"
GRAPHICS_ROOT="${BUNKER_GRAPHICS_ROOT:-$RUNTIME/graphics/root}"
export XDG_CONFIG_HOME="${XDG_CONFIG_HOME:-$RUNTIME/config}"
export XDG_CACHE_HOME="${XDG_CACHE_HOME:-$RUNTIME/cache}"
export XDG_DATA_HOME="${XDG_DATA_HOME:-$RUNTIME/data}"
mkdir -p "$XDG_CONFIG_HOME" "$XDG_CACHE_HOME" "$XDG_DATA_HOME"
LVP_ICD=""
if [ -f "$GRAPHICS_ROOT/usr/share/vulkan/icd.d/lvp_icd.json" ]; then
    LVP_ICD="$GRAPHICS_ROOT/usr/share/vulkan/icd.d/lvp_icd.json"
elif [ -f "$GRAPHICS_ROOT/usr/share/vulkan/icd.d/lvp_icd.x86_64.json" ]; then
    LVP_ICD="$GRAPHICS_ROOT/usr/share/vulkan/icd.d/lvp_icd.x86_64.json"
fi
export LP_NUM_THREADS="${LP_NUM_THREADS:-4}"
export BUNKER_SHOT_DIR="${BUNKER_SHOT_DIR:-$ROOT/build/verification-shots}"

display_pid=""
cleanup() {
    if [ -n "$display_pid" ]; then
        kill "$display_pid" 2>/dev/null || true
        wait "$display_pid" 2>/dev/null || true
    fi
}
trap cleanup EXIT
if [ -z "${DISPLAY:-}" ]; then
    # Xvfb selects a free display; never kill or reuse another desktop.
    display_file="$(mktemp)"
    xvfb="$(command -v Xvfb || true)"
    if [ -x "$xvfb" ]; then
        "$xvfb" -displayfd 3 -screen 0 1280x720x24 -nolisten tcp 3>"$display_file" >"$RUNTIME/xvfb.log" 2>&1 &
        display_pid=$!
    elif [ -x "$GRAPHICS_ROOT/usr/bin/Xvfb" ]; then
        LD_LIBRARY_PATH="$GRAPHICS_ROOT/usr/lib/x86_64-linux-gnu${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}" \
            "$GRAPHICS_ROOT/usr/bin/Xvfb" -displayfd 3 -screen 0 1280x720x24 -nolisten tcp 3>"$display_file" >"$RUNTIME/xvfb.log" 2>&1 &
        display_pid=$!
    else
        echo "Xvfb is missing; see README.md (software renderer setup)." >&2
        exit 1
    fi
    for attempt in $(seq 1 50); do
        if [ -s "$display_file" ]; then break; fi
        if ! kill -0 "$display_pid" 2>/dev/null; then break; fi
        sleep 0.1
    done
    if [ ! -s "$display_file" ]; then
        cat "$RUNTIME/xvfb.log" >&2
        rm -f "$display_file"
        exit 1
    fi
    export DISPLAY=":$(cat "$display_file")"
    rm -f "$display_file"
fi
export LD_LIBRARY_PATH="$GRAPHICS_ROOT/usr/lib/x86_64-linux-gnu${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}"
if [ -n "$LVP_ICD" ]; then
    export VK_ICD_FILENAMES="$LVP_ICD"
    export VK_DRIVER_FILES="$LVP_ICD"
fi
cd "$ROOT"
export BUNKER_CAPTURE_STARTED_NS="$(python3 -c 'import time; print(time.time_ns())')"
godot --path "$ROOT" --audio-driver Dummy res://tools/verify/capture_shots.tscn
python3 - <<'PY'
import os
from pathlib import Path
from PIL import Image
root = Path(os.environ['BUNKER_SHOT_DIR'])
for index in range(1, 8):
    files = list(root.glob(f'shot_{index}_*.png'))
    if len(files) != 1:
        raise SystemExit(f'Missing/ambiguous screenshot {index}: {files}')
    if files[0].stat().st_mtime_ns < int(os.environ['BUNKER_CAPTURE_STARTED_NS']):
        raise SystemExit(f'Stale screenshot from an earlier run: {files[0]}')
    with Image.open(files[0]) as image:
        image.load()
        if image.size != (1280, 720) or all(lo == hi for lo, hi in image.convert('RGB').getextrema()):
            raise SystemExit(f'Empty or invalid render: {files[0]}')
print('7 nonempty rendered images verified in', root)
PY
