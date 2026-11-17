# Tasks

## 1. Testumgebung

- [ ] 1.1 `pyproject.toml` mit Dev-Abhängigkeit `pytest-homeassistant-custom-component` (Version passend zu HA ≥ 2026.7), `tests/conftest.py` mit `enable_custom_integrations`. Beleg: `uv run pytest -q` sammelt Tests ohne Fehler.
- [ ] 1.2 `.claude/verify.md` mit Testaufruf, Rückweg-Prüfung, Version und Release-Weg (kein Lint, Upstream hat keinen). Beleg: Datei im selben Commit wie 1.1.

## 2. Stand je Eingang über Neustart

- [ ] 2.1 `extra_restore_state_data` und Übernahme in `_restore_state`/`_process_config_options`. Beleg: `tests/test_restore.py` (alle fünf Szenarien aus `input-state-restore`).

## 3. Lückenfüller

- [ ] 3.1 Konstanten, YAML-Schema (`fallback`, `fallback_after`) und Übernahme in `_process_config_options`. Beleg: `tests/test_config_flow.py::test_yaml_import_fallback`.
- [ ] 3.2 Prüfung in `_entity_updated`. Beleg: `tests/test_fallback.py` (Szenarien A–I als Tabelle, dazu ohne Markierung und ohne Hauptgerät).
- [ ] 3.3 Options-Flow-Schritt `fallback` mit Übersetzung (en; it/nl fallen auf en zurück). Beleg: `tests/test_config_flow.py::test_options_flow_fallback_step`.

## 4. Replay gegen echte Daten

- [ ] 4.1 Replay-Skript außerhalb des Repos (private Daten): Traccar-Positionen 2026 von Telefon und Fahrzeugen, durch die Entscheidungslogik alt und neu, Ausgabe: Zeitpunkte der Zonenwechsel je Fahrt, Abweichungen. Beleg: Bericht mit Zahlen, vor dem Release.

## 5. Abschluss

- [ ] 5.1 README-Abschnitt „Fallback inputs“ und Restore-Verhalten, Version `4.3.0.101` in `manifest.json`. Beleg: Review.
- [ ] 5.2 Rückweg prüfen: Optionen mit `fallback` unter Upstream-Code laden. Beleg: Test `tests/test_config_flow.py::test_upstream_ignores_fallback_keys` oder Prüfschritt in verify.md.
- [ ] 5.3 Review (`ash`), Findings beheben, `mother`, `ripley`. Beleg: Reviews ohne offene 🔴/🟡, verify grün.

## Workflow follow-up

- Fork `martinhoess/ha-composite-tracker` anlegen, Branch pushen, Release `4.3.0.101` (Tag, HACS lädt aus dem Tag, kein Zip).
- Installation über HACS, Neustart, Auto als Lückenfüller zurück in die Composite.
- Live-Beleg: Neustart von HA, während das Auto woanders steht, `person.<name>` bleibt `home`.
- Wiki-Seiten `google-maps` und `area-occupancy` nachziehen, release-watch eintragen.
- In einen Fork-Commit auf `main` falten (Force-Push nur nach Rückfrage).
