from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from agent import reason_over_changes
from datetime import datetime

app = FastAPI()

STATE = {
    "previous": "",
    "current": "",
    "last_insight": "",
    "last_updated": None,
    "history": []  # store last runs
}

class UpdateIn(BaseModel):
    snapshot: str

@app.get("/health")
def health():
    return {"ok": True}

@app.get("/", response_class=HTMLResponse)
def home():
    return """
<!doctype html>
<html>
<head>
  <meta charset="utf-8"/>
  <meta name="viewport" content="width=device-width,initial-scale=1"/>
  <title>SentinelAI – Autonomous Intelligence Agent</title>
  <style>
    :root{
      --bg0:#070b14;
      --bg1:#0b1220;
      --card: rgba(255,255,255,.06);
      --card2: rgba(255,255,255,.04);
      --border: rgba(255,255,255,.10);
      --text: #e6eaf2;
      --muted: rgba(230,234,242,.68);
      --accent:#2ee59d;
      --accent2:#7bd0ff;
      --warn:#ffcc66;
      --danger:#ff6b6b;
    }
    *{box-sizing:border-box}
    body{
      margin:0;
      font-family: ui-sans-serif, system-ui, -apple-system, Segoe UI, Roboto, Arial;
      background: radial-gradient(900px 500px at 15% 10%, rgba(123,208,255,.14), transparent 60%),
                  radial-gradient(900px 500px at 80% 20%, rgba(46,229,157,.12), transparent 55%),
                  linear-gradient(180deg, var(--bg0), var(--bg1));
      color:var(--text);
      min-height:100vh;
    }
    .wrap{max-width:1300px;margin:0 auto;padding:18px 18px 26px}
    .top{
      display:flex;justify-content:space-between;align-items:center;gap:12px;
      padding:16px 16px;border-radius:18px;
      background: linear-gradient(180deg, rgba(255,255,255,.08), rgba(255,255,255,.05));
      border:1px solid var(--border);
      box-shadow: 0 10px 40px rgba(0,0,0,.35);
    }
    .brand{display:flex;align-items:center;gap:12px}
    .dot{
      width:11px;height:11px;border-radius:50%;
      background:var(--accent);
      box-shadow:0 0 20px rgba(46,229,157,.65);
    }
    .title{font-weight:900;font-size:18px;letter-spacing:.2px}
    .sub{margin-top:2px;color:var(--muted);font-size:13px}
    .rightMeta{display:flex;gap:10px;align-items:center;flex-wrap:wrap;justify-content:flex-end}
    .pill{
      font-size:12px;padding:7px 10px;border-radius:999px;
      border:1px solid var(--border);
      background: rgba(255,255,255,.05);
      color:var(--muted);
    }
    .pill b{color:var(--text)}
    .statusDot{display:inline-block;width:7px;height:7px;border-radius:99px;margin-right:6px;background:var(--accent)}
    .grid{
      display:grid;
      grid-template-columns: 1.15fr .85fr;
      gap:14px;
      margin-top:14px;
      align-items:stretch;
    }
    @media(max-width:1100px){
      .grid{grid-template-columns:1fr}
    }
    .card{
      border-radius:18px;
      background: linear-gradient(180deg, rgba(255,255,255,.07), rgba(255,255,255,.04));
      border:1px solid var(--border);
      box-shadow: 0 10px 35px rgba(0,0,0,.30);
      overflow:hidden;
    }
    .cardHead{
      padding:14px 14px 10px;
      display:flex;justify-content:space-between;align-items:flex-start;gap:12px;
      border-bottom:1px solid rgba(255,255,255,.08);
    }
    h3{margin:0;font-size:15px}
    .hint{margin-top:4px;color:var(--muted);font-size:12px}
    .cardBody{padding:14px}
    .row{display:flex;gap:10px;flex-wrap:wrap;align-items:center}
    .btn{
      padding:11px 12px;border-radius:14px;
      border:1px solid var(--border);
      background: rgba(255,255,255,.08);
      color:var(--text);
      font-weight:800;
      cursor:pointer;
      transition: transform .06s ease, background .15s ease;
    }
    .btn:hover{background: rgba(255,255,255,.12)}
    .btn:active{transform: translateY(1px)}
    .btnPrimary{
      background: rgba(46,229,157,.14);
      border-color: rgba(46,229,157,.25);
    }
    .btnPrimary:hover{background: rgba(46,229,157,.18)}
    .btnGhost{
      background: rgba(255,255,255,.05);
    }
    select, input{
      height:40px;border-radius:14px;border:1px solid var(--border);
      background: rgba(255,255,255,.06);
      color:var(--text);
      padding:0 12px; outline:none;
    }
    .split{
      display:grid;
      grid-template-columns: 1fr;
      gap:12px;
    }
    textarea{
      width:100%;
      min-height: 360px; /* BIGGER */
      border-radius:18px;
      border:1px solid rgba(255,255,255,.12);
      background: rgba(0,0,0,.18);
      color:var(--text);
      padding:14px;
      outline:none;
      resize: vertical;
      font-size: 13.5px;
      line-height: 1.4;
      font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, "Liberation Mono", monospace;
    }
    .out{
      min-height: 560px; /* BIGGER */
      border-radius:18px;
      border:1px solid rgba(255,255,255,.12);
      background: rgba(0,0,0,.22);
      padding:14px;
      white-space: pre-wrap;
      line-height: 1.45;
      font-size: 13.5px;
      font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, "Liberation Mono", monospace;
      overflow:auto;
    }
    .kpiRow{
      display:grid;
      grid-template-columns: repeat(3, 1fr);
      gap:10px;
      margin-top:12px;
    }
    @media(max-width:720px){ .kpiRow{grid-template-columns:1fr} }
    .kpi{
      padding:12px;border-radius:16px;
      background: rgba(255,255,255,.04);
      border:1px solid rgba(255,255,255,.08);
    }
    .kpi .label{color:var(--muted);font-size:12px}
    .kpi .value{margin-top:6px;font-weight:900}
    .timeline{
      display:flex;flex-direction:column;gap:10px;
      max-height: 240px;
      overflow:auto;
      padding-right:4px;
    }
    .tItem{
      padding:10px 12px;border-radius:16px;
      background: rgba(255,255,255,.04);
      border:1px solid rgba(255,255,255,.08);
    }
    .tItem .topline{display:flex;justify-content:space-between;gap:10px}
    .tItem .when{color:var(--muted);font-size:12px}
    .tItem .tag{font-size:12px;color:var(--muted)}
    .footer{
      margin-top:12px;
      color:var(--muted);
      font-size:12px;
      opacity:.95;
      text-align:center;
    }
  </style>
</head>
<body>
<div class="wrap">

  <div class="top">
    <div class="brand">
      <div class="dot"></div>
      <div>
        <div class="title">SentinelAI – Autonomous Business Intelligence Agent</div>
        <div class="sub">Observe → Reason → Report (local LLM via Ollama) • Snapshot-driven agent demo</div>
      </div>
    </div>

    <div class="rightMeta">
      <div class="pill"><span class="statusDot"></span><b id="status">Idle</b></div>
      <div class="pill">Last run: <b id="stamp">—</b></div>
      <div class="pill">Mode: <b>Analyst Brief</b></div>
    </div>
  </div>

  <div class="grid">
    <!-- LEFT: INPUT -->
    <div class="card">
      <div class="cardHead">
        <div>
          <h3>New Snapshot</h3>
          <div class="hint">Pick a preset (professional examples) or paste your own. The agent compares against the previous snapshot.</div>
        </div>
        <div class="row">
          <select id="preset">
            <option value="0">Preset 1 — Macro Risk (Rates/FX)</option>
            <option value="1">Preset 2 — Earnings Shock (Tech)</option>
            <option value="2">Preset 3 — Supply Chain (Oil/Shipping)</option>
            <option value="3">Preset 4 — Crypto + Regulation</option>
          </select>
          <button class="btn btnGhost" id="loadPreset">Load</button>
          <button class="btn btnGhost" id="clear">Clear</button>
          <button class="btn btnPrimary" id="run">Run Agent</button>
        </div>
      </div>

      <div class="cardBody">
        <textarea id="snapshot" placeholder="Paste a snapshot here (news, KPIs, incidents, risk memo)…"></textarea>

        <div class="kpiRow">
          <div class="kpi">
            <div class="label">Snapshot Quality</div>
            <div class="value" id="qScore">—</div>
          </div>
          <div class="kpi">
            <div class="label">Detected Theme</div>
            <div class="value" id="theme">—</div>
          </div>
          <div class="kpi">
            <div class="label">Next Action</div>
            <div class="value" id="nextAction">—</div>
          </div>
        </div>
      </div>
    </div>

    <!-- RIGHT: OUTPUT -->
    <div class="card">
      <div class="cardHead">
        <div>
          <h3>Agent Output</h3>
          <div class="hint">Structured insight (changes, impact, risks, what to monitor). This is what you show HR.</div>
        </div>
        <div class="row">
          <button class="btn btnGhost" id="copy">Copy Output</button>
        </div>
      </div>

      <div class="cardBody">
        <div id="out" class="out">Click “Run Agent” to generate an analyst brief.</div>

        <div style="margin-top:12px">
          <h3 style="margin:0 0 8px 0; font-size:14px">Run Timeline</h3>
          <div id="timeline" class="timeline"></div>
        </div>
      </div>
    </div>
  </div>

  <div class="footer">
    Pro tip: In the interview say “This is snapshot-based autonomy: observe → reason → report; not a reactive chatbot.”
  </div>
</div>

<script>
const $ = (id)=>document.getElementById(id);

const PRESETS = [
`MACRO SNAPSHOT (NEW):
- US yields spike after hotter-than-expected inflation print; rate-cut odds repriced lower.
- USD strengthens broadly; EM FX under pressure; liquidity thinner into month-end.
- Equities wobble; defensives bid; volatility up; credit spreads inch wider.

TASK:
Produce an analyst brief for tomorrow: market impact, risk flags, and what to watch next.`,

`EARNINGS SNAPSHOT (NEW):
- Megacap tech reports earnings: revenue beat but guidance comes in cautious due to margin pressure.
- Buyback increased, but commentary signals slower enterprise demand next quarter.
- Sell-side notes: mixed tone, target revisions likely; options market pricing elevated move.

TASK:
Produce a trader-style brief: bull/bear cases, key numbers, and next catalysts.`,

`SUPPLY CHAIN SNAPSHOT (NEW):
- Crude oil rises on supply disruption headlines; shipping risk premium increasing.
- Freight rates jump; insurers adjust premiums; lead times widen for critical components.
- Industrials and airlines react; input costs likely to flow through in 2–6 weeks.

TASK:
Write an operations + market impact brief: second-order effects, risks, and indicators to monitor.`,

`CRYPTO + REGULATION SNAPSHOT (NEW):
- Major regulator signals stricter exchange compliance timeline; enforcement rhetoric increases.
- BTC/ETH volatile; funding rates flip; stablecoin flows spike between venues.
- Risk appetite sensitive to headlines; correlation with tech returns.

TASK:
Produce a concise brief: what changed, why it matters, risks, and tomorrow checklist.`
];

function setStatus(t){ $("status").textContent = t; }
function setStamp(t){ $("stamp").textContent = t; }

function updateMiniKPIs(text){
  const len = text.trim().length;
  $("qScore").textContent = len < 200 ? "Low (add detail)" : (len < 600 ? "Good" : "Strong");
  const s = text.toLowerCase();
  $("theme").textContent =
    s.includes("inflation") || s.includes("yields") || s.includes("usd") ? "Macro / Rates" :
    s.includes("earnings") || s.includes("guidance") ? "Earnings" :
    s.includes("shipping") || s.includes("supply") || s.includes("freight") ? "Supply Chain" :
    s.includes("crypto") || s.includes("btc") || s.includes("regulator") ? "Crypto / Reg" :
    "General";
  $("nextAction").textContent = "Run agent → review risks";
}

function renderTimeline(items){
  const root = $("timeline");
  root.innerHTML = "";
  if(!items.length){
    root.innerHTML = '<div class="tItem"><div class="topline"><div class="tag">No runs yet</div><div class="when">—</div></div></div>';
    return;
  }
  for(const it of items.slice(0,6)){
    const div = document.createElement("div");
    div.className = "tItem";
    div.innerHTML = `
      <div class="topline">
        <div class="tag">${it.tag}</div>
        <div class="when">${it.when}</div>
      </div>
      <div class="when" style="margin-top:6px">${it.note}</div>
    `;
    root.appendChild(div);
  }
}

$("loadPreset").onclick = () => {
  const i = parseInt($("preset").value, 10);
  $("snapshot").value = PRESETS[i];
  updateMiniKPIs($("snapshot").value);
};

$("clear").onclick = () => {
  $("snapshot").value = "";
  updateMiniKPIs("");
};

$("snapshot").addEventListener("input", ()=>updateMiniKPIs($("snapshot").value));

$("copy").onclick = async () => {
  try{
    await navigator.clipboard.writeText($("out").textContent || "");
    setStatus("Copied");
    setTimeout(()=>setStatus("Idle"), 800);
  }catch(e){
    alert("Copy failed (browser permission).");
  }
};

async function runAgent(){
  const snap = $("snapshot").value.trim();
  if(!snap){
    $("out").textContent = "Paste a snapshot or load a preset first.";
    return;
  }

  setStatus("Thinking…");
  $("out").textContent = "Running agent…";

  const res = await fetch("/update", {
    method:"POST",
    headers: {"Content-Type":"application/json"},
    body: JSON.stringify({snapshot: snap})
  });

  const data = await res.json();

  if(!res.ok || data.error){
    setStatus("Error");
    $("out").textContent = "Error: " + (data.error || "Request failed");
    return;
  }

  $("out").textContent = data.insight || "(no output)";
  setStamp(data.last_updated || "—");
  renderTimeline(data.history || []);
  setStatus("Done");
  setTimeout(()=>setStatus("Idle"), 1200);
}

$("run").onclick = runAgent;

// load a preset by default
$("preset").value = "0";
$("snapshot").value = PRESETS[0];
updateMiniKPIs($("snapshot").value);
renderTimeline([]);
</script>
</body>
</html>
"""

@app.post("/update")
def update(payload: UpdateIn):
    try:
        prev = STATE["current"]
        curr = payload.snapshot

        insight = reason_over_changes(prev, curr)

        STATE["previous"] = prev
        STATE["current"] = curr
        STATE["last_insight"] = insight
        STATE["last_updated"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # simple history tag
        tag = "Run"
        low = curr.lower()
        if "inflation" in low or "yields" in low or "usd" in low: tag = "Macro"
        elif "earnings" in low or "guidance" in low: tag = "Earnings"
        elif "shipping" in low or "supply" in low or "freight" in low: tag = "Supply"
        elif "crypto" in low or "btc" in low or "regulator" in low: tag = "Crypto"

        STATE["history"].insert(0, {
            "when": STATE["last_updated"],
            "tag": tag,
            "note": (curr.strip().splitlines()[0][:80] + "…") if curr.strip() else "—"
        })
        STATE["history"] = STATE["history"][:10]

        return {
            "insight": insight,
            "last_updated": STATE["last_updated"],
            "history": STATE["history"]
        }
    except Exception as e:
        return {"error": str(e)}
