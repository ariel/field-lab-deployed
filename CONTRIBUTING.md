# Contributing

Develop in a source checkout, never in an installed release. Keep the application, downloaded models, durable deployment state, and media projects separate. Do not commit media, model weights, databases, logs containing operator data, credentials or a machine's config.json.

Use the pinned bootstrap to prepare a disposable installation. Tests create temporary fixtures and must not open production project databases or change desktop app settings:

```sh
/path/to/prepared/release/.venv/bin/python -m unittest discover -s tests -v
npm ci --prefix search
cd viewer
npm ci
npm test
npm run build
```

`tests/test_deploy.py`, `test_bootstrap.py`, `test_field.py`, `test_offshoot_setup.py` and `test_generation_assets.py` cover failure boundaries without live app mutation. `test_durability.py` includes real process kills against disposable SQLite fixtures. Live model inference and physical OffShoot/CCC acceptance remain separate steps in `docs/SMOKE-TEST.md`.

For a release, record the exact Git commit, source release ID, platform and dependency/model locks; review changes to model profiles and database compatibility. Publish a tag only after the automated tests and own-media offline inference check pass. Give field operators that exact tag or commit. A SHA256 calculated on downloaded source establishes integrity against the selected source, not publisher authenticity. Review upstream source before promotion.

Updates must not silently erase footage, metadata, queue records, transfer receipts or identity corrections. Use atomic writes and existing SQLite transaction/audit paths. Build candidates separately and validate before activation; keep prior releases and pre-update metadata backups. Schema changes need compatibility or an explicit migration/recovery plan. Do not automatically restore old databases after operators may have made new edits.

Historical development scripts under `development/` are archived experiments; some require old fixtures or manual path adaptation. They are not part of the current test command or deployment flow.
