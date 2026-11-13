#!/usr/bin/env bash
set -euo pipefail
BLENDER="${BLENDER_BIN:-/home/antigravity/.local/bin/blender}"
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
cd "$ROOT"

python3 tools/textures/generate_textures.py
python3 tools/audio/generate_sfx.py
"$BLENDER" --background --python-exit-code 1 --python tools/blender/gen_weapons.py
"$BLENDER" --background --python-exit-code 1 --python tools/blender/gen_characters.py
"$BLENDER" --background --python-exit-code 1 --python tools/blender/gen_machines.py
"$BLENDER" --background --python-exit-code 1 --python tools/blender/gen_props.py
"$BLENDER" --background --python-exit-code 1 --python tools/blender/gen_facility_details.py
echo "All textures, audio, .blend sources, and .glb models built!"
