# BUNKER 115: Undead Protocol

Development direction and iteration status: [ZOMBIES_ROADMAP.md](ZOMBIES_ROADMAP.md).
The facility also includes an Emergency Teleporter console in the Reactor: turn on power, use its console for 500 points to return to the courtyard, then wait 45 seconds before another transfer.

### Cloud graphical verification without Desktop

On the Debian amd64 cloud image, prepare a user-owned Xvfb/Mesa installation:

```bash
bash tools/verify/bootstrap_renderer.sh
bash tools/verify/render_smoke.sh
```

Import resources first using the environment setup instructions. The renderer uses Vulkan/Forward+ with Mesa software rendering and saves seven 1280×720 PNGs in `build/verification-shots/`. Neither command needs the shared Desktop panel (`BUNKER_RUNTIME_DIR`, `BUNKER_GRAPHICS_ROOT`, and `BUNKER_SHOT_DIR` allow overrides).

A **Call of Duty Zombies**-inspired 3D survival first-person shooter built in **Godot 4** (`Forward+`), with **49 custom 3D models sculpted, rigged, and animated in Blender 4.2.9 LTS** (`bpy`), procedural PBR materials/textures, and synthesized 3D spatial audio.

> Further mechanics & design research notes: [DESIGN.md](DESIGN.md)

---

## Core Gameplay Mechanics (CoD Zombies Loop)

- **Endless Wave Escalation & Formulas** ([`RoundDirector`](scripts/systems/round_director.gd), [`GameManager`](scripts/autoload/game_manager.gd)):
  - Start in **Round 1** with **500 points**, **M1911**, **Combat Knife**, and **2 Frag Grenades**.
  - **Zombie Health**: `150 HP` (Round 1), `+100 HP` per round through Round 9 (`950 HP`), then exponential `× 1.1` scaling from Round 10 onward.
  - **Max 24 active zombies** on the map simultaneously, replenishing from the round quota, transitioning from slow Walkers to Runners (Round 3+) and Sprinters (Round 4+).
  - **Hellhound Rounds (every 5th round: R5, R10, ...)**: Dense ember fog settles in, packs of burning Hellhounds hunt the player, and the final kill guarantees a **Max Ammo** drop.
  - **Armored Brute Mini-Boss (every 5th round from R8: R8, R13, ...)**: `2.6×` health with heavy torso armor (`0.65×` body damage resistance), glowing orange visor weakpoint, and a guaranteed Power-Up drop.
- **Classic Points Economy**:
  - Non-lethal bullet hit: `+10 pts` | Body kill: `+60 pts` | Headshot kill: `+100 pts` | Melee knife kill: `+130 pts`
  - **Window Barricade Repairs** ([`WindowBarricade`](scripts/interactables/window_barricade.gd)): Zombies tear down 6 wooden planks per entry window before vaulting inside; hold `[E]`/`[F]` to rebuild planks for `+10 pts` (capped per round).
- **Power Switch & Looping Facility Zones** ([`GameWorld`](scripts/systems/game_world.gd)):
  - **Spawn Courtyard** (Quick Revive, M14 & Kar98k Wall-Buys, Tank centerpiece, Element 115 crystals)
  - **West Bio-Lab** (`Lab Bio-Lock` door, `1000 pts` -> Bio-containment pods, MP40 Wall-Buy, Speed Cola, Mystery Box relocation site)
  - **East Industrial Courtyard** (`Courtyard Gate` door, `750 pts` -> Trench Shotgun & STG-44 Wall-Buys, **Electro-Shock Trap** (`1000 pts`), Double Tap II, starting active **Mystery Box**)
  - **Reactor Hall** (`Containment North` / `Reactor Access` doors `1250 pts`, plus automatic **Emergency Vault Shortcut** when power is turned on -> **Main Power Switch**, **Pack-a-Punch** forge, Stamin-Up, Juggernog, Teleporter Pad, third Mystery Box site)

---

## Arsenal, Pack-a-Punch, Perks & Power-Ups

### Weapons & Pack-a-Punch (`5000 pts`)
| Weapon | Acquisition | Base Name | Pack-a-Punch (`★`) | Special Effect |
| :--- | :--- | :--- | :--- | :--- |
| Pistol | Starter | **M1911** | **Mustang & Sally** | Becomes explosive! |
| Rifle | Wall (`500 pts`) / Box | **M14** | **Mnemosyne** | High headshot multiplier (`2.6×`) |
| Bolt Sniper | Wall (`800 pts`) / Box | **Kar98k Scoped** | **Armageddon** | Massive precision damage (`3.5×` HS) |
| Shotgun | Wall (`1000 pts`) / Box | **M1897 Trench Gun** | **Gut Shot** | 8 pellets per blast |
| SMG | Wall (`1000 pts`) / Box | **MP40** | **The Afterburner** | High sustained mobility/economy |
| Assault Rifle | Wall (`1200 pts`) / Box | **STG-44** | **Spatz-447+** | Balanced full-auto workhorse |
| LMG | Mystery Box (`950 pts`) | **MG42** | **Barracuda FU-A11** | `920 RPM`, 100/150-round belt |
| Wonder Weapon | Mystery Box (`950 pts`) | **Ray Gun** | **Porter's X2 Ray Gun** | Element-115 splash plasma (`750` -> `1650`) |

All Pack-a-Punched weapons feature animated cyan-magenta glowing runic camouflage ([`pap_camo.gdshader`](assets/shaders/pap_camo.gdshader)) and upgraded higher-energy audio. Repeated **Mystery Box** rolls risk pulling the **Teddy Bear**, refunding points and relocating the active box!

### Perk-a-Cola Machines (Requires Power, except Quick Revive Solo)
- **Quick Revive** (`500 pts`, Blue): Automatic self-revive from *Last Stand* with shockwave blast (up to 3 uses Solo).
- **Juggernog** (`2500 pts`, Red): Increases Max HP from `100` to `250`.
- **Speed Cola** (`3000 pts`, Green): `2×` faster weapon reloads & barrier repairs.
- **Double Tap II** (`2000 pts`, Yellow): `+33%` fire rate and `2×` bullet damage.
- **Stamin-Up** (`2000 pts`, Orange): `+25%` sprint speed and faster stamina recovery.

### Power-Up Drops
- **Max Ammo**: Refills all weapons and frag grenades.
- **Insta-Kill** (`30s`): Instant kill on normal zombies with any hit or melee.
- **Double Points** (`30s`): Doubles all points earned.
- **Nuke**: Eliminates all active enemies (`+400 pts`).
- **Carpenter**: Repairs every window barricade immediately (`+200 pts`).
- **Fire Sale** (`30s`): Activates all 3 Mystery Boxes simultaneously for `10 pts` per spin.

---

## Controls

| Action | Keys / Input |
| :--- | :--- |
| Move | `W A S D` |
| Look / Aim / Fire | Mouse / Right-Click (ADS) / Left-Click |
| Sprint / Crouch / Jump | `Left Shift` / `C` or `Left Ctrl` / `Space` |
| Interact / Repair Barrier | `E` or `F` (Hold to board windows) |
| Reload | `R` |
| Switch Weapons | `Q`, `Mouse Wheel`, `1`, `2` |
| Melee (Combat Knife) | `V` |
| Throw Frag Grenade | `G` |
| Pause & Settings | `Esc` |

---

## Blender 3D Asset & Procedural Media Pipeline

Visual styling was guided by 4 generated concept-art sheets in [`assets_src/concept_art/`](assets_src/concept_art/), and **all 49 3D models** (weapons, first-person arms/hands, rigged/animated zombies & hellhound, perk machines, Mystery Box, Pack-a-Punch, power-up drops, blast doors, containment bulkheads, overhead gantry, pipe manifolds, teleporter console, traps, props, and tank) are built reproducibly via **Blender `bpy`** scripts in [`tools/blender/`](tools/blender/):
- Source `.blend` files: [`assets_src/blend/`](assets_src/blend/)
- Exported glTF `.glb` assets: [`assets/models/`](assets/models/)
- Procedural PBR textures, chalk drawings, marquees, Perk UI icons: [`tools/textures/generate_textures.py`](tools/textures/generate_textures.py)
- Synthesized 2D/3D weapon, zombie, and UI WAV SFX + ambience: [`tools/audio/generate_sfx.py`](tools/audio/generate_sfx.py)

Rebuild all textures, audio, `.blend` files, and `.glb` models in one command:
```bash
bash tools/blender/build_all.sh
```

---

## Running, CI/CD & Downloads

### Prebuilt Binaries (Windows, Linux, macOS via GitHub Actions)
Every push to `main` and every `v*` tag automatically runs the headless verification suite and exports standalone builds via [ci-cd.yml](.github/workflows/ci-cd.yml) + [export_presets.cfg](export_presets.cfg):
- **Windows (`x86_64`)**: `Bunker115-Windows-x86_64.zip` -> extract and run `Bunker115.exe`
- **Linux (`x86_64`)**: `Bunker115-Linux-x86_64.tar.gz` -> extract and run `./Bunker115.x86_64`
- **macOS (`Universal`)**: `Bunker115-macOS-Universal.zip` -> extract and open `Bunker115.app` (unsigned: Right-click → Open or `xattr -cr Bunker115.app`)

Downloads are published under **GitHub Releases** (`latest` / `v*`) and as GitHub Actions build artifacts.

### Play from Source in Godot 4 (`4.3+`, verified on `v4.7.2.stable`)
```bash
godot --path /home/antigravity/dibs999/zombieshooter
```
Or open `project.godot` in the Godot editor (`scenes/main_menu.tscn` is the entry scene).

### Headless Test Suite & Asset Reimport Check
```bash
godot --headless --path /home/antigravity/dibs999/zombieshooter --editor --quit
godot --headless --path /home/antigravity/dibs999/zombieshooter res://tools/verify/test_runner.tscn
```
`tools/verify/test_runner.tscn` ([`test_runner.gd`](tools/verify/test_runner.gd)) verifies round HP/count math, WeaponDB Pack-a-Punch transforms, MainMenu 3D diorama loading, multi-zone NavMesh baking & dynamic door navigation bridges, Power Switch shortcut activation, Perk dependencies, Quick Revive self-revive & Game Over states, WindowBarricade planks & ballistic gaps, Mystery Box Teddy Bear relocation & Fire Sale, Zombie Soldier/Scientist/Brute rig loading & headshot areas, Hellhound & Nuke clearing, FragGrenade splash detonation, ElectroTrap activation, PauseMenu, and SettingsManager.
