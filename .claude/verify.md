# Verify-Kontrakt: ha-composite-tracker (Fork)

Fork von `pnbruckner/ha-composite-tracker`, Home-Assistant-Custom-Integration `composite`.
Remotes: `upstream` (pnbruckner), `origin` (martinhoess). Der Fork-Stand liegt als genau ein Commit
auf dem Upstream-Tag auf `main`, gearbeitet wird auf `feat/…`/`fix/…`.

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
W=$(mktemp -d) && git worktree add -q --detach "$W" <tag> && cp -r tests pyproject.toml "$W"/ \
  && (cd "$W" && UV_PROJECT_ENVIRONMENT="$OLDPWD/.venv" uv run --no-sync pytest -q tests/test_upstream_compat.py); \
  git worktree remove --force "$W"
```

Erwartet: `1 passed`.

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

## Live-Beleg

Nach dem Ausrollen, mit einem Eingang als Lückenfüller, der außerhalb der Heimzone steht:
zweimal neu starten, nach jedem Start bleibt die Person `home`, und `last_entity_id` der Composite
zeigt nicht auf den Lückenfüller.
