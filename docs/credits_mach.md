# Stream D – Machines, Traps, Perks & Easter Egg Credits

## Poly Haven CC0 1.0 Textures (1K JPG, packed into Blender-exported GLBs)
- **Rusty Painted Metal** (`rusty_painted_metal`) — Author: Amal Kumar — Source: https://polyhaven.com/a/rusty_painted_metal — License: CC0 1.0
  - Used for weathered enamel machine housing trims (`perk_mulekick.glb`, `perk_deadshot.glb`, `perk_phdflopper.glb`, `perk_electriccherry.glb`, `quest_terminal.glb`).
- **Metal Plate 02** (`metal_plate_02`) — Author: Rob Tuytel — Source: https://polyhaven.com/a/metal_plate_02 — License: CC0 1.0
  - Used for industrial cabinetry and machine chassis surfaces (`der_wunderfizz.glb`, `fire_trap.glb`, `quest_terminal.glb`, `quest_canister.glb`).
- **Metal Grate Rusty** (`metal_grate_rusty`) — Authors: Rob Tuytel, Dimitrios Savva — Source: https://polyhaven.com/a/metal_grate_rusty — License: CC0 1.0
  - Used for the 6.2m trench grating on `fire_trap_burner.glb`.
- **Rusty Metal 02** (`rusty_metal_02`) — Author: Rob Tuytel — Source: https://polyhaven.com/a/rusty_metal_02 — License: CC0 1.0
  - Used for heavy cast iron plinths, cradles, and collars (`der_wunderfizz.glb`, `fire_trap.glb`, `fire_trap_burner.glb`, `quest_resonator.glb`, `quest_canister.glb`).

## Poly Haven CC0 1.0 3D Models (1K glTF, processed via Blender `tools/blender/gen_machines.py`)
- **Propane Tank** (`propane_tank`) — Author: Slinc — Source: https://polyhaven.com/a/propane_tank — License: CC0 1.0
  - Integrated into `fire_trap.glb` fuel cradle feeding the trench burner manifold.
- **Retro Multimeter** (`retro_multimeter`) — Author: elli moeller — Source: https://polyhaven.com/a/retro_multimeter — License: CC0 1.0
  - Integrated onto the workstation surface of `quest_terminal.glb`.

## Original Project Textures & Audio (CC0 / Project-Owned)
- `tools/textures/generate_mach_textures.py` -> Perk UI icons (`perk_mulekick.png`, `perk_deadshot.png`, `perk_phdflopper.png`, `perk_electriccherry.png`), machine marquee plates (`marquee_{mulekick,deadshot,phdflopper,electriccherry,wunderfizz,quest}.png`), Fire Trap dial/placard/flame sprites (`fire_trap_panel.png`, `fire_trap_gauge.png`, `fire_flame_sprite.png`).
- `tools/audio/mach_sfx.py` -> Synthesized Easter Egg song (`assets/audio/ui/ee_song_115.wav`, D-minor 158 BPM tribute track).
