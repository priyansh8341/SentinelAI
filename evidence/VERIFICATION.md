# SentinelAI 0.2 local verification

22 October 2026. Windows, Python 3.11.9, FastAPI and local Ollama llama3.2:3b.

## Automated checks

11 isolated unittest cases passed. Checks cover a first baseline without a model
request; identical input without a new revision; exact diffs, persistence and JSON
export; model failure retaining the previous baseline; an intervening revision;
a busy comparison; request bounds; empty export; ten-entry history; and model
timeout, configuration and invalid response handling. Tests use temporary SQLite
databases and mocked network requests.

The JavaScript extracted from the served HTML passes Node's syntax check. Git's
whitespace check passes. These checks do not establish browser rendering quality.

## Real model demonstration

`live-demo.json` records one synthetic operations baseline and revision submitted
through the running HTTP API. The comparison completed in 20.117 seconds with the
real installed model. Exact removed/added lines, saved state and unchanged-input
reuse were checked. The baseline and repeated identical input did not call Ollama.
This is one functional demonstration, not a model accuracy or latency benchmark.

## Limits

The model-written brief is unverified free text. An exact diff proves text changes,
not their cause or business impact. The app is a manually operated, single shared
local stream with no authentication or multi-tenant isolation. Browser automation
could not initialise because the desktop browser runtime could not write its
kernel assets; fresh visual and click-through QA was not completed. HTTP API and
JavaScript syntax checks were used without bypassing that browser limitation.

Source packages exclude local databases, virtual environments and Git history.
