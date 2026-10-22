# SentinelAI

A local text-snapshot comparison prototype using FastAPI, SQLite and Ollama.
Save an operational baseline, submit a revision, and inspect an exact line diff
alongside a model-written brief. The user initiates each submission.

## Run locally

Requires Python 3.11+ and an Ollama service with `llama3.2:3b` available.
From the repository root in PowerShell:

```powershell
.\start.ps1
```

Open http://127.0.0.1:8011. The launcher creates a virtual environment and installs
requirements. Alternatively:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m uvicorn server:app --app-dir SentinelAI --host 127.0.0.1 --port 8011
```

## Demonstrate the change workflow

1. Load Operations baseline and choose Save / Compare. This saves a baseline;
   no model call is made.
2. Load Operations revision and submit it. Compare the exact diff with the brief.
3. Submit the identical text again. The app reports unchanged and skips Ollama.
4. Refresh or restart the app. The saved snapshot and last ten history entries return.
5. Export the latest snapshot, diff and brief as JSON.

Snapshots persist in `data/sentinel.db` (ignored by Git). History shows the ten
latest revisions; the database retains earlier revisions. The application is a
single shared local snapshot stream, without accounts or tenant isolation.

## Configuration

Set environment variables before starting; `.env.example` documents the names,
but the application does not automatically load an `.env` file.

```powershell
$env:OLLAMA_MODEL = 'llama3.2:3b'
$env:OLLAMA_URL = 'http://127.0.0.1:11434'
```

`SENTINEL_DB_PATH` can override the database path. Model requests have a connection
and response timeout. Invalid input, a busy comparison or a changed baseline is
reported explicitly. A model failure retains the previous snapshot and brief.

## Tests

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

Tests use temporary databases and mocked model calls; they do not require Ollama.
See `evidence/VERIFICATION.md` for measured local checks.

## Scope and limits

The exact text diff is deterministic. The generated brief is unverified model text
for human review: quotations, hypotheses and interpretations can be wrong. There
is no autonomous monitoring, automatic ingestion, forecasting, execution of model
suggestions or model training. The input-length indicator describes text length,
not factual quality or AI confidence. No public deployment or production claim is
made. Use synthetic input for demos; local history and exports contain submitted text.
