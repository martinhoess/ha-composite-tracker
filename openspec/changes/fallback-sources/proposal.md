# Proposal

## Why

Die Composite übernimmt immer die neueste Meldung. Ein abgestelltes Fahrzeug mit eigenem GPS-Tracker kann dadurch ein Telefon überstimmen, das die Person tatsächlich bei sich trägt. Am deutlichsten passiert das nach einem Neustart von Home Assistant. Dann zählt die erste Meldung jeder Quelle als Bewegung, weil die letzte Position je Quelle verloren ist. Steht das Fahrzeug außerhalb der Heimzone, springt die Person auf „unterwegs“. Mit „Require movement“ bleibt das so, bis sich das Telefon bewegt, denn ein stillliegendes Telefon zählt nicht als Bewegung.

## What Changes

- Neue Eingangsoption **Lückenfüller** je Eingang. Ein Lückenfüller zählt nur, wenn seit einer einstellbaren Frist (Vorgabe 5 min) kein anderer Eingang gemeldet hat.
- Neue globale Option **Frist für Lückenfüller**.
- Als Meldung für die Frist zählt jede gültige Meldung eines Hauptgeräts, auch eine ohne Bewegung.
- Die letzte Position und der letzte Meldezeitpunkt je Eingang überstehen einen Neustart. „Require movement“ vergleicht danach mit dieser Position statt die erste Meldung durchzulassen. Das gilt für alle Eingänge, nicht nur für Lückenfüller.
- Neuer Schritt „Lückenfüller“ im Options-Flow nach „Use All States“.
- Ohne gesetztes Häkchen verhält sich die Integration wie Upstream. Keine Option ändert sich, nichts ist **BREAKING**.

## Capabilities

### New Capabilities

- `fallback-inputs`: Eingänge, die nur einspringen, wenn die Hauptgeräte länger schweigen.
- `input-state-restore`: Letzte Position und letzter Meldezeitpunkt je Eingang überstehen einen Neustart.

### Modified Capabilities

(keine, im Repo gibt es noch keine Specs)

## Impact

- `custom_components/composite/device_tracker.py`: Auswahl der Meldungen, Restore-Daten
- `custom_components/composite/config_flow.py`, `config.py`, `const.py`, `translations/*.json`: neue Optionen
- Neu: `tests/` mit `pytest-homeassistant-custom-component`, `.claude/verify.md`
- README: Abschnitt zu den neuen Optionen
