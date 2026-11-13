# BUNKER 115 — Entwicklungsrichtung und Iterationen

## Ziel und Recherche-Status

Gewünscht ist eine Mischung: die knappe Rundenökonomie der klassischen
Zombies-Spiele mit gezielten Komfort- und Progressionssystemen aus neueren
Teilen. Eigene Blender-Assets, zusammenhängende Art Direction und überprüfbare
Spielmechanik gehen vor einer langen Liste halbfertiger Features.

**Webabgleich noch offen:** Am 13.11.2026 blockiert die Cloud-Netzwerkregel den
Abruf von `www.callofduty.com` (CONNECT 403). Diese Einordnung basiert auf
allgemeinem Vorwissen und Codeanalyse, nicht auf abgeschlossener aktueller
Internetrecherche. Zahlen in DESIGN.md sind Projektregeln und keine universellen
Originalwerte aller CoD-Titel.

Offizielle Einstiegsquelle für den noch ausstehenden Abgleich:
https://www.callofduty.com/blog
Die angefragte, nicht abrufbare Referenz-URL war:
https://www.callofduty.com/blog/2024/08/call-of-duty-black-ops-6-zombies-terminus-gameplay-guide
URL und Inhalt sind noch zu verifizieren. Die Domains `callofduty.com`,
`www.callofduty.com` und `images.contentstack.io` sind im Umgebungsentwurf
vorgeschlagen. Nach Speichern: offizielle Gameplay-Erklärungen und Screenshots
zu Terminus/Liberty Falls, danach klassische Karten als Vergleich ansehen.
Mechaniken immer dem konkreten Titel zuordnen; Hit-Punkte, Kill-Punkte,
Rüstung, Salvage, Waffenrarität und GobbleGums sind kein einheitliches System.

## Vorläufiger Vergleich und Prioritäten

| Bereich | Klassischer Schwerpunkt | Moderne Ergänzung | Stand / nächste Arbeit |
| --- | --- | --- | --- |
| Runden | Wellen, Munition, Laufwege, Spezialrunden | skalierte Spezialgegner und optionale Ziele | Vorhanden; längere Spieltests fehlen |
| Ökonomie | Punkte, Türen, Wandwaffen, Box, Perks, Pack-a-Punch | Rarität, Salvage, Rüstung als getrennte Ressourcen | Klassischer Kern vorhanden; moderne Systeme einzeln balancieren |
| Überleben | Barrikaden, Training-Routen, Fallen, Wiederbelebung | Evakuierung, Field Upgrade, bessere Informationen | Solo-Revive und Falle vorhanden; Notfalltransfer in Iteration 1 |
| Waffen | Silhouetten, Rückstoß, Nachladen, ADS | differenzierte Aufwertung und Feedback | Modelle vorhanden; Hände, Timing und Feedback prüfen |
| Karten | Strom als Meilenstein, Loop-Abkürzungen, Geheimnisse | mehrteilige Hauptaufgabe und optionale Aufgaben | Vier Zonen vorhanden; Stromroute visuell deutlicher |
| Koop | Rettungen, gemeinsames Überleben | Join/Leave, abgestimmte Progression | Nicht implementiert; separate Netzwerk-Etappe |

## Visuelle Leitlinien (Bildreferenzabgleich offen)

- Lesbare Dunkelheit: kaltes Mondlicht, warme Leuchten, einzelne grünliche
  Laborakzente; kein gleichmäßig schwarzes Bild und kein Dauer-Neon.
- Funktion und Geschichte: Rohrführung, Wartungstechnik, verschlissene Schotts,
  Raumkennzeichnung und erkennbare Stromzustände.
- Großformen zuerst: Türrahmen, Raumproportionen und Hauptobjekte; danach
  Materialabnutzung, kleine Trümmer und Oberflächendetails.
- Keine Dekoration in Türöffnungen oder Laufwegen; Interaktionsanzeigen müssen
  von Hintergrund und Nebel unterscheidbar bleiben.
- Blender als Quelle: `.blend` und gezielter Generator, `.glb` als Laufzeitasset.
  Wiederverwendbare Geometrie statt vieler zusätzlicher dynamischer Lichter.
- Bilder mit dem echten Godot-Renderer kontrollieren. Software-Rendering ist
  ein Bildtest, kein Leistungsnachweis auf Zielhardware.

## Iteration 1 — Orientierung und Notfalltransfer

- Drei neue Blender-Assets: `containment_arch`, `service_pipes`,
  `teleporter_console`, jeweils mit `.blend`, `.glb` und reproduzierbarem Script.
- Schott-Rahmen und Kennzeichnungen an fünf Durchgängen, Rohrgruppen an
  Wänden; keine neuen Hindernisse im Navigationsmesh.
- Dekorative Reaktor-Teleporterplatte wird zum Einweg-Fluchtweg in den Starthof:
  Strom erforderlich, 500 Punkte, 45 Sekunden Abklingzeit; gesperrt während
  Last Stand und Game Over. Kein Schutz vor Gegnern am Ziel. Position und Kosten
  müssen in tatsächlichen Spieltests bewertet werden.
- Tests für Stromsperre, Zahlung, Zielposition, zurückgesetzte Geschwindigkeit,
  Cooldown, fehlende Punkte und Downed-Sperre.
- Siebte Kameraperspektive für den Transferbereich; eingefrorene Spielerphysik
  macht die Aufnahme unabhängig von der Rendergeschwindigkeit.
- Nach tatsächlicher Bildkontrolle: überwiegend raue Pflastersteine mit
  begrenzten feuchten Stellen, schwächere Lichtkegel und neutraleres Fülllicht.

### Validierung dieser Iteration

- Godot 4.6.3: Asset-Import und **85 Prüfungen bestanden**, keine fehlgeschlagen.
  Die bereits vor dieser Iteration beobachteten ObjectDB-/Ressourcenmeldungen
  beim Beenden sind weiter vorhanden; Exitcode der Suite ist 0.
- Drei neue Assets mit Blender 4.3.2 erzeugt; Generator lief erfolgreich.
- `bootstrap_renderer.sh` ausgeführt und wiederholt, ohne Root-Rechte.
- `render_smoke.sh` lief mit Vulkan Forward+ / Mesa llvmpipe: sieben aktuelle,
  nicht leere PNGs mit 1280×720 erzeugt und geprüft. Menü, Hof, Kampf, Osthof,
  Labor, Reaktor und Transferbereich wurden tatsächlich gerendert. Mehrere
  Ansichten einschließlich Hof und Konsole wurden visuell kontrolliert.
- Kein interaktiver Durchlauf und kein GPU-Leistungstest. Die Sichtprüfung zeigt
  weiterhin einfache Figuren und Waffen, fehlende Hände, zu starke Emission der
  aufgewerteten Waffe und aus der Ferne kleine Raumbeschriftungen. Das ist ein
  früher Prototyp, noch nicht die gewünschte finale grafische Qualität.

## Nächste Iterationen

1. Referenzrecherche abschließen: offizielle Texte und Bilder abrufen, Quellen
   mit titelbezogenen Feststellungen erfassen. Noch keine behauptete visuelle
   Übereinstimmung mit dem Original.
2. Gunplay: Spielerhände und Reload-Animationen aus Blender, Waffenprofile,
   Gegnerreaktionen und räumliches Audio; im Spiel prüfen.
3. Art-Pass: beschädigte Mauersegmente, Materialvarianten, Trümmer an Randzonen,
   Silhouetten und Bildkomposition verbessern.
4. Moderne Progression: genau ein vollständiges System, z.B. Salvage und
   Rüstung mit klaren Kosten, UI und Balanceprüfungen.
5. Ziele: mehrteilige Reaktoraufgabe, optionaler Evakuierungsabschluss,
   danach eigene Spezialgegner.
6. Koop: Architektur, Synchronisation und Wiederbelebung gemeinsam entwickeln.

Pro Runde: spielbarer Umfang → Logiktests → gerenderte Bilder → visuelle Kritik
→ Korrektur → Spieltest und dokumentierter Stand. Vorhandene Mechaniken müssen
dabei weiterhin funktionieren.
