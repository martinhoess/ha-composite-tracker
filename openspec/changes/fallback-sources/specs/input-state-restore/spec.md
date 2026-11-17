# Spec Delta

## Purpose

Nach einem Neustart soll die Composite jede Quelle so beurteilen wie vorher, statt die erste Meldung jeder Quelle als neu und bewegt zu behandeln.

## ADDED Requirements

### Requirement: Letzter Stand je Eingang übersteht den Neustart

Die Composite SHALL für jeden GPS-Eingang die letzte gültige Position mit Genauigkeit und den letzten Meldezeitpunkt über einen Neustart retten. Für Eingänge, die nicht mehr konfiguriert sind, SHALL nichts übernommen werden.

#### Scenario: Neustart, Fahrzeug steht woanders (E)
- **WHEN** „Require movement“ an ist, die Composite auf `home` steht, ein Fahrzeug unverändert außerhalb der Heimzone steht und HA neu startet
- **THEN** bleibt die Composite nach dem Start auf `home`, auch wenn das Fahrzeug nach dem Telefon meldet
- Beleg: `tests/test_restore.py::test_restart_vehicle_elsewhere_stays_home`

#### Scenario: Neustart, zu Fuß unterwegs, Fahrzeug daheim (B)
- **WHEN** „Require movement“ an ist, die Composite unterwegs steht, das Fahrzeug unverändert daheim steht und HA neu startet
- **THEN** bleibt die Composite unterwegs
- Beleg: `tests/test_restore.py::test_restart_on_foot_vehicle_home_stays_away`

#### Scenario: Echte Bewegung während des Neustarts
- **WHEN** sich ein Eingang während des Neustarts weiter als die Summe der Genauigkeiten bewegt hat
- **THEN** zählt seine erste Meldung nach dem Start als Bewegung
- Beleg: `tests/test_restore.py::test_restart_real_movement_counts`

#### Scenario: Frist der Lückenfüller nach dem Neustart
- **WHEN** das Telefon kurz vor dem Neustart gemeldet hat und ein Lückenfüller direkt nach dem Start eine Bewegung meldet
- **THEN** gilt das Telefon als frisch, und der Lückenfüller zählt nicht
- Beleg: `tests/test_restore.py::test_restart_fallback_blocked_by_restored_primary`

#### Scenario: Altdaten ohne gespeicherten Stand
- **WHEN** der gespeicherte Zustand aus einer Version ohne diese Daten stammt
- **THEN** startet die Composite wie Upstream ohne Fehler
- Beleg: `tests/test_restore.py::test_restore_without_extra_data`
