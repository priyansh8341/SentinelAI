from pathlib import Path
from difflib import unified_diff
import os
import threading
from fastapi import FastAPI,HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel,ConfigDict,Field
from agent import reason_over_changes,ModelUnavailable,model_name
from storage import SnapshotStore,RevisionConflict
from observer import detect_change

app=FastAPI(title='SentinelAI Snapshot Comparison',version='0.2.0')
store=SnapshotStore(os.getenv('SENTINEL_DB_PATH',str(Path(__file__).resolve().parents[1]/'data/sentinel.db')))
update_lock=threading.Lock()
class UpdateIn(BaseModel):
    model_config=ConfigDict(extra='forbid',str_strip_whitespace=True)
    snapshot:str=Field(min_length=1,max_length=6000)

@app.get('/health')
def health():return {'ok':True,'version':'0.2.0','model':model_name(),'storage':'SQLite','mode':'manual snapshot comparison'}

def state(changed=False):
    row=store.latest()
    return {'insight':row['insight'] if row else '', 'last_updated':row['created'] if row else None,
            'snapshot':row['snapshot'] if row else '', 'history':store.history(), 'changed':changed,
            'mode':row['mode'] if row else 'empty','diff':row['diff'] if row else '',
            'revision':row['id'] if row else None,'model':model_name()}

@app.get('/state')
def current_state():return state()

@app.get('/export')
def export_latest():
    row=store.latest()
    if not row:raise HTTPException(404,'No snapshot has been saved.')
    return row

@app.get("/", response_class=HTMLResponse)
def home():
    return r"""
<!doctype html>
<html>
<head>
  <meta charset="utf-8"/>
  <meta name="viewport" content="width=device-width,initial-scale=1"/>
  <title>SentinelAI – Snapshot Comparison</title>
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
    *{box-sizing:border-box} .wrap,.card,.cardBody{min-width:0} .top{flex-wrap:wrap} .out{overflow-wrap:anywhere} button:disabled{opacity:.5;cursor:wait} a.btn{text-decoration:none;display:inline-block} button:focus-visible,textarea:focus-visible,select:focus-visible,a:focus-visible{outline:2px solid #7bd0ff;outline-offset:3px}
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
        <div class="title">SentinelAI – Snapshot Comparison</div>
        <div class="sub">Save a baseline → compare a revision → review evidence and a model-written brief</div>
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
          <div class="hint">First submission saves a baseline. Revised snapshots produce an exact text diff and a model-written comparison.</div>
        </div>
        <div class="row">
          <select id="preset" aria-label="Snapshot preset">
            <option value="0">Operations baseline</option>
            <option value="1">Operations revision</option>
            <option value="2">Release baseline</option>
            <option value="3">Release revision</option>
          </select>
          <button class="btn btnGhost" id="loadPreset">Load</button>
          <button class="btn btnGhost" id="clear">Clear</button>
          <button class="btn btnPrimary" id="run">Save / Compare</button>
        </div>
      </div>

      <div class="cardBody">
        <textarea id="snapshot" aria-label="Snapshot text" maxlength="6000" placeholder="Paste a snapshot here (news, KPIs, incidents, risk memo)…"></textarea>

        <div class="kpiRow">
          <div class="kpi">
            <div class="label">Input length</div>
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
          <h3>Comparison Brief</h3>
          <div class="hint">Model-written brief for human review. Inspect the exact diff below; model interpretations can be wrong.</div>
        </div>
        <div class="row">
          <button class="btn btnGhost" id="copy">Copy Output</button><a class="btn btnGhost" href="/export" download="sentinel-report.json">Export JSON</a>
        </div>
      </div>

      <div class="cardBody">
        <div id="out" class="out">Save a baseline, then submit a revised snapshot.</div>

        <details style="margin-top:14px"><summary>Exact text changes</summary><pre id="diff" style="white-space:pre-wrap;overflow-wrap:anywhere;line-height:1.7"></pre></details>
<div style="margin-top:12px">
          <h3 style="margin:0 0 8px 0; font-size:14px">Run Timeline</h3>
          <div id="timeline" class="timeline"></div>
        </div>
      </div>
    </div>
  </div>

  <div class="footer">
    Manual local prototype · SQLite history · no automated feeds, forecasting or external actions
  </div>
</div>

<script>
const $ = (id)=>document.getElementById(id);

const PRESETS = [
`Operations status
Open incidents: 2
API error rate: 0.5%
Order backlog: 18
Owner: operations`,
`Operations status
Open incidents: 5
API error rate: 1.8%
Order backlog: 33
Owner: operations`,
`Release status
Version: 1.4
Passed checks: 18
Failed checks: 0
Rollback prepared: yes`,
`Release status
Version: 1.5
Passed checks: 16
Failed checks: 2
Rollback prepared: yes`
];

function setStatus(t){ $("status").textContent = t; }
function setStamp(t){ $("stamp").textContent = t; }

function updateMiniKPIs(text){
  const len = text.trim().length;
  $("qScore").textContent = len < 200 ? "Short" : (len < 600 ? "Medium" : "Long");
  const s = text.toLowerCase();
  $("theme").textContent =
    s.includes("inflation") || s.includes("yields") || s.includes("usd") ? "Macro / Rates" :
    s.includes("earnings") || s.includes("guidance") ? "Earnings" :
    s.includes("shipping") || s.includes("supply") || s.includes("freight") ? "Supply Chain" :
    s.includes("crypto") || s.includes("btc") || s.includes("regulator") ? "Crypto / Reg" :
    "General";
  $("nextAction").textContent = "Save baseline / compare revision";
}

function renderTimeline(items){
  const root = $("timeline");
  root.innerHTML = "";
  if(!items.length){
    root.innerHTML = '<div class="tItem"><div class="topline"><div class="tag">No runs yet</div><div class="when">—</div></div></div>';
    return;
  }
  for(const it of items.slice(0,10)){
    const div = document.createElement("div");
    div.className = "tItem";
    const title=document.createElement('div');title.className='topline';
    const tag=document.createElement('span');tag.textContent=it.tag;
    const when=document.createElement('span');when.className='when';when.textContent=it.when;
    title.append(tag,when);const note=document.createElement('div');note.className='when';note.textContent=it.note;
    div.append(title,note);
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

async function applyState(data){
  $('out').textContent=data.insight||'Save a baseline to begin.';
  $('diff').textContent=data.diff||'No recorded diff yet.';
  setStamp(data.last_updated||'—');renderTimeline(data.history||[]);
}
async function runAgent(){
  const snap=$('snapshot').value.trim();if(!snap){$('out').textContent='Paste a snapshot first.';return;}
  $('run').disabled=true;setStatus('Working…');
  try{
    const response=await fetch('/update',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({snapshot:snap})});
    const data=await response.json();if(!response.ok)throw new Error(typeof data.detail==='string'?data.detail:'Invalid input or comparison failed.');
    await applyState(data);setStatus(data.mode==='unchanged'?'Unchanged · no model call':data.mode==='baseline'?'Baseline saved':'Compared');
  }catch(error){setStatus('Error');$('out').textContent=error.message;}
  finally{$('run').disabled=false;}
}
async function restore(){
  try{const response=await fetch('/state');if(!response.ok)throw new Error('Could not load saved history.');const data=await response.json();if(data.snapshot)$('snapshot').value=data.snapshot;await applyState(data);updateMiniKPIs($('snapshot').value);}
  catch(error){setStatus('History unavailable');}
}
$("run").onclick = runAgent;

// load a preset by default
$("preset").value = "0";
$("snapshot").value = PRESETS[0];
updateMiniKPIs($("snapshot").value);
renderTimeline([]);
restore();
</script>
</body>
</html>
"""

@app.post('/update')
def update(payload:UpdateIn):
    if not update_lock.acquire(blocking=False):raise HTTPException(409,'A comparison is already running. Wait for it to finish.')
    try:
        previous=store.latest()
        if previous and not detect_change(previous['snapshot'],payload.snapshot):
            result=state();result['mode']='unchanged';return result
        diff='\n'.join(unified_diff((previous['snapshot'] if previous else '').splitlines(),payload.snapshot.splitlines(),fromfile='previous',tofile='current',lineterm=''))
        if previous:
            insight=reason_over_changes(previous['snapshot'],payload.snapshot);mode='model'
        else:
            insight='Baseline saved. Submit a revised snapshot to compare changes. No model call was made.';mode='baseline'
        store.save(previous['id'] if previous else None,payload.snapshot,insight,diff,mode,model_name() if previous else 'not called')
        return state(changed=previous is not None)
    except ModelUnavailable as exc:raise HTTPException(503,str(exc)) from exc
    except RevisionConflict as exc:raise HTTPException(409,'Another update changed the baseline. Refresh and compare again.') from exc
    finally:update_lock.release()
