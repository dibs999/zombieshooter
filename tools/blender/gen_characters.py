"""Stream B character generation entrypoint for BUNKER 115 v2:
Generates CC0 UV-aligned textures and exports all 5 zombies, Hellhound, and Panzersoldat Boss.
"""

import os
import subprocess
import sys

sys.path.insert(0, os.path.dirname(__file__))
import chars_common as CC
import chars_zombies as CZ
import chars_hellhound_boss as CHB


def main():
    repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    fetch_script = os.path.join(repo_root, "tools", "assets", "chars_fetch_cc0.py")
    sentinel = os.path.join(CC.TEX_CHARS, "blood_pool_decal.png")
    cache_ok = (
        os.path.exists(CC.EYES_MHCLO)
        and os.path.exists(CHB.WOLF_BLEND)
        and os.path.exists(CHB.HELMET_OBJ)
    )
    if not os.path.exists(sentinel) or not cache_ok:
        subprocess.run([sys.executable, fetch_script], check=True)

    CZ.build_all_zombies()
    CHB.build_all()


if __name__ == "__main__":
    main()
