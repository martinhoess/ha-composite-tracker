# Design

## Context

`CompositeDeviceTracker._entity_updated` prüft jede Meldung der Reihe nach: gültig, Bewegung (nur bei „Require movement“, und nur wenn es eine alte Position der Quelle gibt), neuer als die zuletzt übernommene Meldung. Der Stand je Quelle (`EntityData.seen`, `EntityData.data`) liegt nur im Speicher. `_restore_state` stellt nur den Zustand der Composite selbst wieder her (`last_seen`, Position). Nach einem Start ist `old_data` deshalb für jede Quelle leer, und die Bewegungsprüfung greift nicht.

Quellen ohne `last_seen`-Attribut (z. B. Traccar) liefern `last_updated` als Meldezeitpunkt.

## Goals / Non-Goals

**Goals:**
- Lückenfüller-Regel als zusätzliche Prüfung in `_entity_updated`, ohne den bestehenden Ablauf umzubauen
- Stand je Quelle über `RestoreEntity.extra_restore_state_data` retten

**Non-Goals:**
- Motion- oder Speed-Sensoren der Quellen auswerten (unzuverlässig, siehe Proposal)
- Gepufferte Altpositionen von Quellen ohne `last_seen` erkennen
- Prioritäten mit mehr als zwei Stufen

## Decisions

**Prüfung an einer Stelle.** Die Lückenfüller-Prüfung sitzt direkt vor „Is this newer info than last update?“. Damit gilt sie für GPS- und Nicht-GPS-Eingänge gleich, und `entity.good(...)` ist für die Frist schon gelaufen. Alternative wäre eine eigene Vorauswahl über alle Eingänge gewesen. Das widerspricht dem ereignisgetriebenen Aufbau, den Upstream bewusst gewählt hat.

**Frist gegen den Meldezeitpunkt, nicht gegen die Uhr.** Verglichen wird `last_seen` der Lückenfüller-Meldung mit dem größten `seen` aller Hauptgeräte. Das ist deterministisch, testbar und im Replay identisch zum Live-Verhalten. Mit `utcnow()` würde eine verspätet zugestellte Meldung anders bewertet als im Replay.

**Frische zählt ohne Bewegung.** `entity.good(...)` setzt `seen` vor der Bewegungsprüfung. Genau dieser Wert dient als Meldezeitpunkt des Hauptgeräts. So hält ein stillliegendes Telefon die Frist.

**Restore über `extra_restore_state_data`.** Gespeichert wird je Eingang `{entity_id: {seen, lat, lon, acc}}` nur für GPS-Daten. HA schreibt die Daten selbst regelmäßig und beim Stopp. `_restore_state` liest sie in ein Wörterbuch, `_process_config_options` übernimmt sie beim Anlegen der `EntityData`. Gespeichert wird nichts davon in Attributen, damit der Recorder nicht wächst. Alternative wären Attribute der Composite gewesen. Sie würden bei jeder Meldung in der Datenbank landen.

**Neu gesetztes `seen` nach dem Restore.** Startet eine Quelle mit `last_updated` als Meldezeitpunkt, ist dieser nach dem Neustart neuer als der gerettete Wert. „last_seen went backwards“ greift deshalb nicht fälschlich.

**Options-Flow.** Neuer Schritt `fallback` nach `all_states`, mit Mehrfachauswahl der Eingänge und `DurationSelector` für die Frist. In YAML: `fallback: true` je Eingang, `fallback_after` je Tracker oder in `default_options`.

## Risks / Trade-offs

- [Ein Hauptgerät meldet ständig, aber mit veralteter Position] → Der Lückenfüller springt nie ein. Das ist dieselbe Lage wie heute ohne Fahrzeug. Bewusst hingenommen.
- [Fall I: Telefon vergessen] → steht als Grenze im README.
- [Der gerettete Stand ist alt (HA war Tage aus)] → Die Bewegungsprüfung vergleicht trotzdem korrekt. Ein Gerät, das sich bewegt hat, meldet eine entfernte Position und zählt.
- [Upstream ändert `_entity_updated`] → Fork-Commit klein halten, Tests fangen Rebase-Fehler.

## Migration Plan

Installation über HACS aus dem Fork, Neustart. Beim ersten Start fehlen die Restore-Daten. Die Composite verhält sich dann einmal wie Upstream, ab dem zweiten Neustart greift der Schutz. Rückweg: Upstream-Version über HACS. Upstream liest in den Optionen nur die eigenen Schlüssel, die zusätzlichen bleiben liegen und stören nicht (Beleg: Test mit Upstream-Code vor dem Ausrollen, Aufgabe 5.2). YAML mit `fallback` lehnt Upstream dagegen ab, deshalb dort vorher entfernen.
