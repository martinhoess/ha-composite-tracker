# Spec Delta

## Purpose

Eingänge wie Fahrzeug-Tracker sollen Lücken der Hauptgeräte füllen, ohne ein Hauptgerät zu überstimmen, das gerade meldet.

## ADDED Requirements

### Requirement: Lückenfüller je Eingang

Jeder Eingang SHALL als Lückenfüller markiert werden können. Ein nicht markierter Eingang ist ein Hauptgerät. Ohne Markierung SHALL sich die Composite wie Upstream verhalten.

#### Scenario: Keine Markierung
- **WHEN** kein Eingang als Lückenfüller markiert ist
- **THEN** wählt die Composite die Meldungen wie Upstream aus
- Beleg: `tests/test_fallback.py::test_no_fallback_is_upstream_behaviour`

### Requirement: Lückenfüller zählt nur bei schweigenden Hauptgeräten

Eine Meldung eines Lückenfüllers SHALL die Composite nur ändern, wenn seit der Frist kein Hauptgerät gültig gemeldet hat. Maßstab ist der Meldezeitpunkt der Lückenfüller-Meldung, verglichen mit dem jüngsten Meldezeitpunkt aller Hauptgeräte. Hat noch kein Hauptgerät gemeldet, SHALL der Lückenfüller zählen.

#### Scenario: Fremdfahrt, Telefon meldet (F)
- **WHEN** das Telefon vor weniger als der Frist gemeldet hat und das Fahrzeug eine neue, entfernte Position meldet
- **THEN** bleibt die Composite bei der Position des Telefons
- Beleg: `tests/test_fallback.py::test_scenarios[F_other_driver]`

#### Scenario: Ankunft mit dem Fahrzeug, Telefon schweigt (C)
- **WHEN** das Telefon länger als die Frist nicht gemeldet hat und das Fahrzeug in der Heimzone ankommt
- **THEN** übernimmt die Composite die Position des Fahrzeugs und steht auf `home`
- Beleg: `tests/test_fallback.py::test_scenarios[C_arrive_by_vehicle_phone_silent]`

#### Scenario: Telefon meldet wieder
- **WHEN** ein Lückenfüller übernommen hat und das Telefon danach eine Meldung mit Bewegung liefert
- **THEN** übernimmt die Composite wieder das Telefon
- Beleg: `tests/test_fallback.py::test_scenarios[G_phone_returns]`

#### Scenario: Telefon meldet wieder, ohne sich bewegt zu haben
- **WHEN** ein Lückenfüller übernommen hat und das Telefon danach von seiner alten Position meldet
- **THEN** übernimmt die Composite das Telefon trotz „Require movement“, und weitere Lückenfüller-Meldungen zählen wieder erst nach der Frist
- Beleg: `tests/test_fallback.py::test_scenarios[G_phone_returns_unmoved]`

#### Scenario: Kein Hauptgerät bisher
- **WHEN** kein Hauptgerät je gemeldet hat
- **THEN** zählt der Lückenfüller wie ein normaler Eingang
- Beleg: `tests/test_fallback.py::test_fallback_without_primary_counts`

### Requirement: Jede gültige Meldung eines Hauptgeräts hält die Frist

Für die Frist SHALL jede gültige GPS-Meldung eines Hauptgeräts zählen, auch wenn sie wegen „Require movement“ die Position nicht ändert. Eine Nicht-GPS-Meldung SHALL nur zählen, wenn die Composite sie verwenden würde (Zustand `home` oder „Use All States“).

#### Scenario: Telefon liegt still (heutiger Fehler)
- **WHEN** „Require movement“ an ist, das Telefon still daheim liegt und alle 30 s meldet und das Fahrzeug außerhalb der Heimzone eine neue Position meldet
- **THEN** bleibt die Composite auf `home`
- Beleg: `tests/test_fallback.py::test_scenarios[D_vehicle_parked_elsewhere]`

#### Scenario: Ignorierte Nicht-GPS-Meldung
- **WHEN** ein Router-Hauptgerät `not_home` meldet, das die Composite ignoriert, und danach der Lückenfüller eine neue Position meldet
- **THEN** zählt der Lückenfüller, sofern sonst kein Hauptgerät innerhalb der Frist gemeldet hat
- Beleg: `tests/test_fallback.py::test_non_gps_primary_ignored_report_does_not_block`

#### Scenario: Reihenfolge beim Start
- **WHEN** die Composite startet und Hauptgerät und Lückenfüller schon Zustände haben
- **THEN** werden die Hauptgeräte vor den Lückenfüllern ausgewertet, unabhängig von der Reihenfolge in der Konfiguration
- Beleg: `tests/test_restore.py::test_startup_handles_primary_before_fallback`

### Requirement: Frist ist einstellbar

Die Frist SHALL in den Optionen einstellbar sein, Vorgabe 5 Minuten.

#### Scenario: Options-Flow
- **WHEN** der Options-Flow durchlaufen wird
- **THEN** gibt es einen Schritt mit Auswahl der Lückenfüller und der Frist, und beides landet in den Optionen des Eintrags
- Beleg: `tests/test_config_flow.py::test_options_flow_fallback_step`

#### Scenario: YAML
- **WHEN** ein Eingang in YAML `fallback: true` trägt und der Tracker `fallback_after` setzt
- **THEN** übernimmt der Import beides
- Beleg: `tests/test_config_flow.py::test_yaml_import_fallback`

### Requirement: Bewusste Grenze

Bleibt das Telefon daheim und meldet weiter, während die Person mit einem Lückenfüller-Fahrzeug fährt, SHALL die Composite beim Telefon bleiben (Fall I). Das ist gewollt und steht im README.

#### Scenario: Telefon vergessen (I)
- **WHEN** das Telefon daheim weiter meldet und das Fahrzeug wegfährt
- **THEN** bleibt die Composite auf `home`
- Beleg: `tests/test_fallback.py::test_scenarios[I_phone_forgotten]`
