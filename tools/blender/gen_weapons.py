"""Entrypoint for building all 11 BUNKER 115 weapons + MPFB2 anatomical first-person hands."""

import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
import wpn_hands
import wpn_weapons


if __name__ == "__main__":
    wpn_hands.build_fp_right_hand()
    wpn_hands.build_fp_left_hand()
    wpn_weapons.build_all_weapons()
    print("ALL 11 HIGH-DETAIL WEAPONS + MPFB2 ANATOMICAL FIRST-PERSON HANDS EXPORTED!")
