# Contributing

Run focused tests before opening a pull request:

```bash
.venv/bin/python scripts/bootstrap_upstream.py
.venv/bin/python -m pytest -q
.venv/bin/python scripts/generate.py --release --check
.venv/bin/python scripts/verify_upstream.py
```

Each implementation task should end with focused tests and a single commit.
