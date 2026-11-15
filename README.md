# BUNKER 115: Undead Protocol

A **Call of Duty Zombies**-inspired 3D survival first-person shooter built in **Godot 4 (`4.7.2-stable`, Forward+)**, featuring **CC0 Poly Haven / MPFB2 / OpenGameArt assets refined and rigged in Blender 4.2.9 LTS (`bpy`)**, triplanar scanned PBR shaders, 2K night HDRIs, volumetric atmosphere, 5 interconnected facility zones, **5 animated zombie variants with dismemberment & gore**, the **Panzersoldat Boss**, **Wunderwaffe DG-2**, **9 Perk-a-Colas + Der Wunderfizz**, **Operation Element 115** main Easter Egg quest, and **46+ layered spatial audio cues**.

- Full CC0 Asset & Audio Attributions: [CREDITS.md](CREDITS.md)
- Development History & Design Notes: [ZOMBIES_ROADMAP.md](ZOMBIES_ROADMAP.md) · [DESIGN.md](DESIGN.md)

---

## Core Gameplay Mechanics (CoD Zombies Loop)

- **Endless Wave Escalation & Formulas** ([`RoundDirector`](scripts/systems/round_director.gd), [`GameManager`](scripts/autoload/game_manager.gd)):
  - Start in **Round 1** with **500 points**, **M1911**, **Combat Knife**, and **2 Frag Grenades**.
  - **Zombie Health**: `150 HP` (Round 1), `+100 HP` per round through Round 9 (`950 HP`), then exponential `× 1.1` scaling from Round 10 onward.
  - **Max 24 active zombies** simultaneously, evolving from Walkers to Runners (R3+) and Sprinters (R4+), with 5 MPFB2 anatomical variants (**Soldier, Scientist, Brute, Worker, Crawler**), detachable limbs/head gore, and dynamic Crawler leg-sever transitions.
  - **Hellhound Rounds (every 5th round: R5, R10, ...)**: Crimson ember fog settles in, packs of burning wolf Hellhounds hunt the player, and the final kill guarantees a **Max Ammo** drop.
  - **Panzersoldat Boss (every 8th non-dog round: R8, R16, ...)**: Heavily armored juggernaut (`1400+ HP`) with 4 individually shatterable armor plates (Visor, Chest, Left/Right Shoulder exposing glowing weakpoints), claw slams, a medium-range flamethrower burst, `+1500 pts` kill bounty, and guaranteed **Max Ammo** drop.
- **Classic Points Economy & Barricades**:
  - Non-lethal hit: `+10 pts` | Body kill: `+60 pts` | Headshot kill: `+100 pts` | Melee knife kill: `+130 pts`
  - **Window Barricade Repairs** ([`WindowBarricade`](scripts/interactables/window_barricade.gd)): Zombies tear down 6 wooden planks per entry window before vaulting inside; hold `[E]`/`[F]` to rebuild planks for `+10 pts` (capped per round).
- **Power Switch & 5 Looping Facility Zones** ([`GameWorld`](scripts/systems/game_world.gd)):
  1. **Spawn Courtyard** (Quick Revive, M14 & Kar98k Wall-Buys, Sherman Tank centerpiece, Element 115 crystals)
  2. **West Bio-Lab** (`Lab Bio-Lock` door, `1000 pts` -> Bio-containment pods, MP40 Wall-Buy, Speed Cola, Deadshot Daiquiri alcove, Mystery Box site, Song Teddy #3)
  3. **East Industrial Courtyard** (`Courtyard Gate` door, `750 pts` -> Trench Shotgun & STG-44 Wall-Buys, **Electro-Shock Trap** (`1000 pts`), Double Tap II, starting active **Mystery Box**, Song Teddy #1)
  4. **Reactor Hall** (`Containment North` / `Reactor Access` doors `1250 pts`, plus automatic **Emergency Vault Shortcut** when Power turns on -> **Main Power Switch**, **Pack-a-Punch** forge, Stamin-Up, Juggernog, **Der Wunderfizz** (`1500 pts`), **Emergency Teleporter** console (`500 pts` transfer to Spawn Courtyard, `45s` cooldown))
  5. **North Motorpool Yard (Zone 5)** (`Motorpool Bulkhead` door, `1500 pts` -> **Fire Trap** (`1000 pts`), **Mule Kick**, **PhD Flopper**, **Electric Cherry**, **Operation Element 115 Terminal**, Song Teddy #2)

---

## Arsenal, Pack-a-Punch, Perks, Traps & Easter Egg

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
| Wonder Weapon | Mystery Box (`950 pts`) / Quest | **Wunderwaffe DG-2** | **Wunderwaffe DG-3 JZ** | Arcs chain lightning across `10` -> `24` zombies |

All Pack-a-Punched weapons feature animated cyan-magenta glowing runic camouflage ([`pap_camo.gdshader`](assets/shaders/pap_camo.gdshader)) and upgraded higher-energy audio. Repeated **Mystery Box** rolls risk pulling the **Teddy Bear**, refunding points and relocating the active box!

### Perk-a-Cola Machines (4-Perk Limit by Default — Unlock 9/9 via Easter Egg)
- **Quick Revive** (`500 pts`, Blue): Automatic self-revive from *Last Stand* with shockwave blast (up to 3 uses Solo, works before Power).
- **Juggernog** (`2500 pts`, Red): Increases Max HP from `100` to `250`.
- **Speed Cola** (`3000 pts`, Green): `2×` faster weapon reloads & barrier repairs.
- **Double Tap II** (`2000 pts`, Yellow): `+33%` fire rate and `2×` bullet damage.
- **Stamin-Up** (`2000 pts`, Orange): `+25%` sprint speed and faster stamina recovery.
- **Mule Kick** (`4000 pts`, Emerald): Grants a **3rd primary weapon slot** (drops cleanly if perks are lost).
- **Deadshot Daiquiri** (`1500 pts`, Gold): Tightens hipfire spread and snaps ADS onto nearby zombie heads.
- **PhD Flopper** (`2000 pts`, Purple): Full immunity to explosive & Fire Trap damage; triggers a **Nuke shockwave** at the end of a sprint-slide or ≥2.2 m drop.
- **Electric Cherry** (`2000 pts`, Cyan): Unleashes an electric stun/damage arc burst around the player on every reload.
- **Der Wunderfizz** (`1500 pts`, Reactor Hall): Spins through Perk orbs and dispenses a random unowned Perk-a-Cola (respects `4/4` cap until Operation Element 115 is completed).

### Traps & Easter Eggs
- **Electro-Shock Trap** (`1000 pts`, East Courtyard) & **Fire Trap** (`1000 pts`, North Motorpool Yard): Activate hazardous energy barriers (Fire Trap instakills regular zombies, deals heavy DoT to Panzersoldat Bosses, burns unprotected players unless wearing PhD Flopper).
- **Operation Element 115 (Main Quest)** ([`EasterEggQuest`](scripts/interactables/easter_egg_quest.gd)): Activate the Quest Terminal in North Yard → turn on Power → shoot 4 glowing Element-115 Resonators → fill 3 Soul Canisters with nearby zombie kills (5 souls each) → defeat the Containment Panzersoldat Boss → execute Final Extraction Override to unlock **all 9 Perk slots + all 9 Perks**, equip **Wunderwaffe DG-3 JZ (PaP)**, and earn `+5000 pts`.
- **Musical Easter Egg**: Activate all **3 hidden Teddy Bears** (`East Courtyard`, `North Motorpool Shelf`, `West Bio-Lab Desk`) to trigger the custom D-minor tribute track (`ee_song_115.wav`) and `+1150 pts`.

### Power-Up Drops
- **Max Ammo**: Refills all weapons and frag grenades.
- **Insta-Kill** (`30s`): Instant kill on normal zombies with any hit or melee.
- **Double Points** (`30s`): Doubles all points earned.
- **Nuke**: Eliminates active regular zombies & Hellhounds and chunks Boss armor (`+400 pts`).
- **Carpenter**: Repairs every window barricade immediately (`+200 pts`).
- **Fire Sale** (`30s`): Activates all 3 Mystery Boxes simultaneously for `10 pts` per spin.

---

## Controls

| Action | Keys / Input |
| :--- | :--- |
| Move | `W A S D` |
| Look / Aim / Fire | Mouse / Right-Click (ADS) / Left-Click |
| Sprint / Crouch / Jump | `Left Shift` / `C` or `Left Ctrl` / `Space` |
| **Sprint-Slide** | Press `C` or `Left Ctrl` while sprinting |
| Interact / Repair Barrier | `E` or `F` (Hold to board windows) |
| Reload | `R` |
| Switch Weapons | `Q`, `Mouse Wheel`, `1`, `2`, `3` |
| Melee (Combat Knife) | `V` |
| Throw Frag Grenade | `G` |
| Pause & Settings | `Esc` |

---

## Blender 3D Asset & Procedural Media Pipeline

All 3D models, scanned CC0 textures, rigs, animations, and layered WAV audio assets are tracked reproducibly under [`tools/`](tools/):
- **Sources (`.blend`) & Exports (`.glb`)**: [`assets_src/blend/`](assets_src/blend/) → [`assets/models/`](assets/models/)
- **Blender `bpy` Generators**: [`tools/blender/`](tools/blender/) (`env_cc0_pipeline.py`, `chars_zombies.py`, `chars_hellhound_boss.py`, `wpn_weapons.py`, `wpn_hands.py`, `gen_machines.py`, `gen_props.py`, `gen_facility_details.py`)
- **Texture & Audio Generators**: [`tools/textures/`](tools/textures/), [`tools/audio/`](tools/audio/)

Rebuild core procedural textures, audio, `.blend` files, and `.glb` models:
```bash
bash tools/blender/build_all.sh
```

---

## Running, CI/CD & Downloads

### Prebuilt Binaries (Windows, Linux, macOS via GitHub Actions)
Every push to `main` and every `v*` tag automatically runs the full headless verification suite and exports standalone builds via [ci-cd.yml](.github/workflows/ci-cd.yml) + [export_presets.cfg](export_presets.cfg):
- **Windows (`x86_64`)**: `Bunker115-Windows-x86_64.zip` → extract and run `Bunker115.exe`
- **Linux (`x86_64`)**: `Bunker115-Linux-x86_64.tar.gz` → extract and run `./Bunker115.x86_64`
- **macOS (`Universal`)**: `Bunker115-macOS-Universal.zip` → extract and open `Bunker115.app` (unsigned: Right-click → Open or `xattr -cr Bunker115.app`)

Downloads are published under **GitHub Releases** (`latest` / `v*`) and as GitHub Actions build artifacts.

### Play from Source in Godot 4 (`4.7.2-stable`)
```bash
godot --path /home/antigravity/dibs999/zombieshooter
```
Or open `project.godot` in the Godot editor (`scenes/main_menu.tscn` is the entry scene).

### Headless Test Suite & Cloud Graphical Verification
```bash
godot --headless --path /home/antigravity/dibs999/zombieshooter --editor --quit
godot --headless --path /home/antigravity/dibs999/zombieshooter res://tools/verify/test_runner.tscn
```
[`test_runner.gd`](tools/verify/test_runner.gd) executes the unified automated verification suite across all subsystems:
- Core game math, MainMenu diorama, Zone 1–4 NavMesh bridges, Emergency Teleporter, WindowBarricades, MysteryBox Teddy relocation, Game Over & Pause states
- [`TestsJitter`](tools/verify/tests_jitter.gd) (exponential frame-rate-independent camera/viewmodel smoothing & 144Hz/0.12s spike regression checks)
- [`tests_env.gd`](tools/verify/tests_env.gd) (Stream A HDRIs, AgX environment, ReflectionProbes, Decals, GPUParticles, 28 CC0 props, Zone 5 `north_yard` & NavMesh)
- [`TestsChars`](tools/verify/tests_chars.gd) (Stream B 5 MPFB2 zombie variants, dismemberment/crawlers, Hellhound, Panzersoldat Boss armor plates & drops)
- [`TestsWpn`](tools/verify/tests_wpn.gd) (Stream C animated weapon nodes, shell casings, decals, Layer-16 quest pass-through, Wunderwaffe 10/24-chain lightning, Mule Kick/Deadshot/PhD Flopper/Electric Cherry, 9-perk HUD)
- [`TestsMach`](tools/verify/tests_mach.gd) (Stream D 10 new props, 4-perk cap, Der Wunderfizz, Fire Trap, end-to-end Operation Element 115 Easter Egg & 3 Song Teddies)

On the Debian amd64 cloud image without a GPU/Desktop panel, Vulkan/Forward+ verification renders can be captured via [`bootstrap_renderer.sh`](tools/verify/bootstrap_renderer.sh) + [`render_smoke.sh`](tools/verify/render_smoke.sh).
