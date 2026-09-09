# Contributing

Use Python 3.10 or newer. Install the package and run tests:

```bash
python -m pip install -e ".[dev]"
python -m pytest -q
```

Use generated synthetic databases, never real backup samples. Keep source
access read-only, avoid filename-only matching, and add regression tests for
path resolution and schema changes. New format support must include explicit
limitations and a reproducible synthetic fixture.

Do not claim a real-device compatibility result without recording the tested
backup format and schema. Do not attach personal identifiers to issues.
