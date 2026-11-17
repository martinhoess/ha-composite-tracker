# Verify-Kontrakt: ha-composite-tracker (Fork)

Fork von `pnbruckner/ha-composite-tracker`, Home-Assistant-Custom-Integration `composite`.
Remotes: `upstream` (pnbruckner), `origin` (martinhoess, sobald der Fork auf GitHub angelegt ist).
Zielzustand: der Fork-Stand liegt als genau ein Commit auf dem Upstream-Tag auf `main`. Gearbeitet wird
auf `feat/…`/`fix/…`, gefaltet wird nach dem Live-Beleg.

## Test

Python 3.14.2 oder neuer kommt von uv. Einmalig:

```
uv venv --python 3.14 && uv sync --group test
```

Prüflauf:

```
uv run pytest -q
```

Erwartet: alle grün, darunter `tests/test_fallback.py`, `tests/test_restore.py`,
`tests/test_config_flow.py`, `tests/test_upstream_compat.py`.

## Rückweg zu Upstream

Optionen des Forks dürfen Upstream nicht brechen. Der Kompatibilitätstest läuft deshalb auch gegen
den Upstream-Tag, auf dem der Fork liegt (`<tag>`, derzeit `4.3.0`):

```
R=$PWD; W=$(mktemp -d) && git worktree add -q --detach "$W" <tag> && cp -r tests pyproject.toml "$W"/ \
  && (cd "$W" && ! grep -q '"version": ".*\.1[0-9][0-9]"' custom_components/composite/manifest.json \
      && UV_PROJECT_ENVIRONMENT="$R/.venv" uv run --no-sync pytest -q tests/test_upstream_compat.py); \
  rc=$?; git worktree remove --force "$W"; (exit $rc)
```

Erwartet: `1 passed`, Exit 0. Die `grep`-Zeile sichert zu, dass im Worktree Upstream-Code liegt
(keine Fork-Version `….1xx`). YAML mit `fallback` oder `fallback_after` lehnt Upstream ab: diese
Schlüssel vor einem Rückweg aus der YAML-Konfiguration entfernen.

## Nach dem Falten

Wird der Branch in einen Commit auf `main` gefaltet, laufen Prüflauf, Rückweg und Versionsprüfung
auf dem gefalteten Commit erneut, bevor getaggt wird.

## Version

Steht in `custom_components/composite/manifest.json` und `pyproject.toml` und muss gleich sein.
Schema `<upstream>.1xx`, derzeit `4.3.0.101`. Der Release-Tag entspricht exakt der Manifest-Version.

```
python3 -c "import json,tomllib;m=json.load(open('custom_components/composite/manifest.json'))['version'];p=tomllib.load(open('pyproject.toml','rb'))['project']['version'];assert m==p,(m,p);print(m)"
```

## Ausrollen

`hacs.json` hat kein `zip_release`: HACS lädt `custom_components/composite` aus dem Release-Tag.
Release = Tag `<version>` plus GitHub-Release im Fork. Installation über HACS als Custom Repository,
danach Neustart von Home Assistant. Der Schutz beim Neustart greift erst ab dem zweiten Neustart nach
der Installation (beim ersten fehlen die gespeicherten Daten je Eingang).

Der Schutz gilt nach einem sauberen Neustart. Nach einem Absturz gilt der letzte periodische Stand
der Restore-Daten (bis 15 min alt).

## Live-Beleg

Geprüft wird die Composite-Entität, nicht die Person. Ein Fahrzeug-Eingang steht unbewegt außerhalb
der Heimzone, das Telefon liegt daheim.

1. Ausrollen, Neustart 1 (noch ohne gespeicherte Daten, beweist nichts).
2. Debug-Log für `custom_components.composite` einschalten.
3. **Restore allein:** Fahrzeug vorübergehend *ohne* Lückenfüller-Häkchen. Vor Neustart 2 in
   `.storage/core.restore_state` nachsehen, dass `extra_data.inputs.<fahrzeug>` mit der aktuellen
   Position existiert; `gps_accuracy` und lat/lon des Fahrzeugs notieren. Neustart 2: Composite bleibt
   `home`, `last_entity_id` ist nicht das Fahrzeug, im Log steht
   `skipping update from <fahrzeug>: not enough movement`. Weichen lat/lon nach dem Start ab, ist das
   im Bericht zu nennen (Fall nicht durch die Tests gedeckt).
4. **Lückenfüller:** Häkchen wieder setzen, Neustart 3: Composite bleibt `home`.
5. Melde-Takt: größte Lücke zwischen `last_updated`-Wechseln des Telefons über eine ruhige Stunde
   daheim (Recorder) liegt unter `fallback_after`.
