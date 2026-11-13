# BUNKER 115: Undead Protocol — Game Design & CoD Zombies Research

## 1. Recherche: Aufbau & Kernmechaniken von Call of Duty Zombies

Der klassische Call-of-Duty-Zombies-Modus (entwickelt von Treyarch ab *World at War* über *Black Ops I–III* bis *Cold War / BO6*) basiert auf einem präzise abgestimmten **Survival-Economy-Loop** mit folgenden Säulen:

### 1.1 Runden-System & Skalierungsformeln
- **Startbedingungen**: Spieler startet in **Runde 1** mit **500 Punkten**, einer schwachen Startpistole (**M1911**), einem **Kampfmesser** und **2 Splittergranaten**.
- **Zombie-HP-Formel**:
  - Runde 1: `150 HP`
  - Runden 2–9: `+100 HP` pro Runde (`250, 350, ..., 950 HP` in Runde 9)
  - Ab Runde 10: `HP(n) = round(HP(n-1) * 1.1)` (exponentielle Skalierung: R10 = 1.045, R20 = 2.710, R30 = 7.030, R40 = 18.234 HP)
- **Zombie-Anzahl & Spawn-Limit**:
  - Runde 1 = `6`, Runde 2 = `8`, Runde 3 = `13`, Runde 4 = `18`, Runde 5+ skaliert progressiv.
  - Maximal **24 aktive Zombies gleichzeitig** auf der Karte (Performance + "Train"-Spielgefühl); besiegte Zombies werden aus der Runden-Reserve nachgespawnt.
- **Bewegungs- & Spezialeinheiten**:
  - Runden 1–2: Langsame **Walker**
  - Runden 3–4: Mix aus Walkern und **Runnern**
  - Ab Runde 5: Zunehmender Anteil aggressiver **Sprinter**
  - **Alle 5 Runden (R5, R10, R15...)**: **Hellhound-Runde** — dichter Nebel, schnelles Pack brennender Höllenhunde, Abschluss garantiert einen **Max Ammo**-Drop!
  - **Ab Runde 8 (alle 5 Runden: R8, R13, R18...)**: **Armored Brute** — gepanzerter Hazmat-Mini-Boss mit erhöhter HP, orangenem Visier-Schwachpunkt und garantiertem Power-Up-Drop.

### 1.2 Punkte-Ökonomie (Risiko vs. Ertrag)
Anders als in normalen Shootern erzeugen Treffer selbst Punkte:
- **Nicht-tödlicher Kugeltreffer**: `+10` Punkte (pro Projektil — deshalb sind MP40/Pistole anfangs lukrativer als One-Shot-Waffen!)
- **Tödlicher Körpertreffer**: `+60` Punkte
- **Tödlicher Kopfschuss (Headshot)**: `+100` Punkte
- **Tödlicher Nahkampf (Messer)**: `+130` Punkte (klassisches Runde-1-Optimieren: 4–5 Pistolentreffer + Messer = 170–180 Punkte pro Zombie!)
- **Barrikaden reparieren**: `+10` Punkte pro Holzbrett (mit Runden-Cap, um Endlos-Farming zu verhindern)

### 1.3 Map-Struktur, Zonen, Barrikaden & Strom
Klassische Top-Maps (*Der Riese*, *Kino der Toten*) folgen einem **geschlossenen Kreislauf (Looping Training Route)** mit schrittweiser Progression:
1. **Start-Raum ("Wachposten / Courtyard")**: Beengter Start mit **Quick Revive** (500 Punkte Solo), frühen **Wall-Buys** (M14, Trench Shotgun), 3 verbarrikadierten **Fenster-Barrikaden** und 2 verschlossenen **Türen**.
2. **Seitenflügel (West: "Labor 115" / Ost: "Industrie-Hof")**: Kosten je `750–1000` Punkte, schalten neue Zombie-Spawns, bessere Wandwaffen (**MP40**, **STG-44**), **Mystery-Box-Standorte**, **Elektro-Falle** (`1000` Punkte) und erste Perks frei.
3. **Reaktorhalle ("Power Room")**: Zentraler **Hauptstromschalter (Power Switch)**. Erst wenn der Strom aktiviert ist:
   - Leuchten alle **Perk-a-Cola-Automaten** und werden nutzbar
   - Öffnet sich die Sicherheitsschleuse zum **Pack-a-Punch-Gewölbe** und eine **Shortcut-Tür zurück zum Start-Hof** (perfekter Kreis-Laufweg zum "Trainen" von Horden!)
   - Werden **Elektro-Fallen** aktiv.

### 1.4 Kernelemente & Automaten
- **Fenster-Barrikaden**: Zombies reißen Holzbretter einzeln ab (`6` Bretter pro Fenster), bevor sie einsteigen; Spieler kann Bretter gedrückt halten (`[E]`) und wieder zunageln.
- **Wall-Buys**: Kreidezeichnungen an Wänden zum Sofortkauf fester Waffen; Munitions-Nachkauf kostet `50%` des Waffenpreises (bzw. `4500` Punkte für Pack-a-Punch-Munition).
- **Mystery Box (`950` Punkte)**: Eisenbeschlagene Holzkiste mit vertikalem Himmels-Lichtstrahl; rotiert zufällige Waffen inklusive exklusiver Waffen (**MG42**, **Ray Gun**); nach mehreren Zügen erscheint der **Teddybär** und teleportiert die Kiste zu einem der 3 Standorte.
- **Pack-a-Punch (`5000` Punkte)**: Steampunk-Schmiedeofen; rüstet gehaltene Waffe auf (**2x–3x Schaden**, **2x Magazin & Reserve**, animierte glühende Runen-Tarnung, höherenergetischer Schussklang & Mündungsfeuer; M1911 wird zur explosiven **Mustang & Sally**!).
- **Perk-a-Colas**:
  - **Quick Revive** (`500` Pkt Solo, Blau): Selbst-Wiederbelebung aus *Last Stand* (max. 3x pro Spiel)
  - **Juggernog** (`2500` Pkt, Rot): Erhöht Max-HP von `100` auf `250` (5–6 statt 2–3 Treffer)
  - **Speed Cola** (`3000` Pkt, Grün): `2x` schnelleres Nachladen & `2x` schnelleres Barrikaden-Reparieren
  - **Double Tap II** (`2000` Pkt, Gelb/Amber): `+33%` Feuerrate & `2x` Kugelschaden / Doppel-Projektil
  - **Stamin-Up** (`2000` Pkt, Orange): `+25%` Sprinttempo & doppelte Ausdauer-Regeneration
- **Power-Up-Drops** (30 Sekunden Dauer bzw. Soforteffekt):
  - **Max Ammo**: Füllt Magazine & Reserve aller Waffen + Granaten auf
  - **Insta-Kill**: Jeder Treffer (auch Messer!) tötet normale Zombies sofort (30s)
  - **Double Points**: Verdoppelt alle verdienten Punkte (30s)
  - **Nuke**: Tötet alle aktiven Zombies auf der Map + `+400` Punkte
  - **Carpenter**: Repariert alle Barrikaden auf der Map sofort + `+200` Punkte
  - **Fire Sale**: Aktiviert alle Mystery-Box-Standorte gleichzeitig für je nur `10` Punkte (30s)

---

## 2. Visuelle Inspiration & Blender-Pipeline

Als visuelle Stilreferenz wurden 4 hochauflösende Concept-Sheets generiert (`assets_src/concept_art/`):
1. `concept_facility_courtyard_*.jpg`: Mondbeschienener Regen-Innenhof, feuchte Pflastersteine, warm-orangene Bunker-Notlichter vs. cyan leuchtende Element-115-Kristalle, verbarrikadierte Fenster mit Mondlicht-Strahlen und zerstörtem Panzer im Hof.
2. `concept_weapons_packapunch_*.jpg`: M1911, Trench Shotgun, MP40, STG-44, Element-115 Ray Gun und Pack-a-Punch Chrome-Runen-Veredelung.
3. `concept_perks_mysterybox_*.jpg`: 1950er-Vintage-Perk-Automaten mit Leuchtkuppeln, Mystery Box mit golden-cyan Lichtsäule und Pack-a-Punch-Schmiede mit Zahnrädern & Plasmaspulen.
4. `concept_zombies_enemies_*.jpg`: Verrottete Wehrmachts-Zombies, Labor-Wissenschaftler, gepanzerte Hazmat-Brutes und glühende Magma-Höllenhunde.

Alle 3D-Assets werden reproduzierbar über **Blender 4.2.9 LTS (`bpy`)** unter `tools/blender/` erzeugt, als echte `.blend`-Dateien unter `assets_src/blend/` gesichert und als optimierte PBR-`.glb`-Modelle (inkl. Skelett-Rigs und Animationen für Zombies & Höllenhunde) nach `assets/models/` exportiert.
