from __future__ import annotations

import os
import json
from pathlib import Path
from typing import Dict, Any, List

from flask import Flask, request, jsonify, Response
import pandas as pd
import sys
from pathlib import Path

# Make src importable without requiring PYTHONPATH
ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

# Local imports from src (expect PYTHONPATH=src or run via module path)
from fxbot.config import load_config
from fxbot.data.csv_loader import load_ohlcv_csv
from fxbot.strategies.momo_atr import generate_signals
from fxbot.strategies.ai_bridge import generate_signals_from_callable
from fxbot.backtest import run_backtest
from fxbot.report import metrics_from_pnl
from fxbot.risk import position_size_from_atr
from fxbot.walkforward import walk_forward


app = Flask(__name__)

DATA_DIR = ROOT / "data"
DEFAULT_CONFIG = ROOT / "config" / "config.yaml"
ONLINE_ALLOWED = os.environ.get("FXBOT_ALLOW_ONLINE", "0") in ("1", "true", "TRUE", "True")
PREFS_PATH = ROOT / "out" / "webui_prefs.json"

# In-memory storage for last backtest trades (latest 20 shown; export may include all)
_LAST_TRADES: List[Dict[str, Any]] = []
_LAST_WF_FOLDS: List[Dict[str, Any]] = []


def _list_csv_files(base: Path) -> List[str]:
    files = []
    if base.exists():
        for p in sorted(base.rglob("*.csv")):
            # Return Windows-style path string only when on Windows; otherwise posix
            files.append(str(p))
    return files


@app.get("/")
def index() -> Response:
    html = f"""
<!doctype html>
<html lang=\"ja\">
<head>
  <meta charset=\"utf-8\" />
  <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\" />
  <title>FX Local-First — Web UI</title>
  <style>
    body {{ font-family: system-ui, -apple-system, Segoe UI, Roboto, sans-serif; margin: 16px; }}
    header {{ margin-bottom: 16px; }}
    label {{ display:block; margin: 8px 0 4px; }}
    input, select {{ padding: 6px 8px; min-width: 260px; }}
    button {{ padding: 8px 12px; margin-top: 12px; }}
    .row {{ display:flex; gap:16px; flex-wrap: wrap; align-items: flex-end; }}
    .card {{ border:1px solid #ddd; border-radius:8px; padding:12px; margin-top:12px; }}
    .metrics span {{ display:inline-block; min-width: 160px; margin-right: 8px; }}
    canvas {{ max-width: 100%; height: 360px; }}
    footer {{ margin-top: 24px; color: #666; font-size: 12px; }}
  </style>
  <style>
    :root {{ --bg:#ffffff; --fg:#0a0a0a; --muted:#6b7280; --card:#f7f7f7; --border:#e5e7eb; --accent:#f97316; --accent-2:#06b6d4; }}
    body.dark {{ --bg:#0b0c0f; --fg:#e6e6e6; --muted:#9aa0a6; --card:#13151a; --border:#2a2d33; --accent:#ff6f00; --accent-2:#00bcd4; }}
    body {{ background: var(--bg); color: var(--fg); }}
    input, select, textarea {{ color: var(--fg); background: var(--bg); border-color: var(--border); }}
    button {{ background: var(--card); color: var(--fg); border-color: var(--border); }}
    .btn--primary {{ background: var(--accent); color: #fff; border-color: var(--accent); }}
    button:hover {{ filter: brightness(1.05); }}
    .card h3 {{ margin: 0 0 8px; font-weight: 600; }}
    .card h3::after {{ content:''; display:block; width:56px; height:2px; background: var(--accent); margin-top:6px; opacity:.85; }}
    .muted {{ color: var(--muted); }}
    #toast {{ position: fixed; right: 16px; bottom: 16px; display:flex; flex-direction:column; gap:8px; z-index: 9999; }}
    .toast {{ background: var(--card); border:1px solid var(--border); padding:8px 10px; border-radius:8px; min-width: 220px; box-shadow: 0 2px 10px rgba(0,0,0,.15); }}
    .toast--err {{ border-color:#c62828; }}
  </style>
  <script src=\"https://cdn.jsdelivr.net/npm/chart.js\"></script>
  <script src=\"https://cdn.jsdelivr.net/npm/chartjs-plugin-zoom@^2\"></script>
  <script>
    function applyTheme() {{
      const t = localStorage.getItem('theme') || 'dark';
      document.body.classList.toggle('dark', t==='dark');
      const btn = document.getElementById('theme'); if (btn) btn.textContent = (t==='dark') ? '☀️ 明るく' : '🌙 暗く';
    }}
    function toggleTheme() {{ const t = localStorage.getItem('theme') || 'dark'; localStorage.setItem('theme', t==='dark'?'light':'dark'); applyTheme(); }}
    function notify(msg, kind='info', timeout=3000) {{
      const box = document.getElementById('toast'); if (!box) return;
      const el = document.createElement('div'); el.className = 'toast' + (kind==='error'?' toast--err':''); el.textContent = msg; box.appendChild(el);
      setTimeout(()=>{{ el.remove(); }}, timeout);
    }}
    function downsample(labels, values, maxPoints=1200) {{
      const n = values.length; if (n <= maxPoints) return {{ labels, values }};
      const step = Math.ceil(n / maxPoints);
      const dsL = [], dsV = [];
      for (let i=0; i<n; i+=step) {{ dsL.push(labels[i]); dsV.push(values[i]); }}
      return {{ labels: dsL, values: dsV }};
    }}
    function getAccent() {{
      try {{ return getComputedStyle(document.body).getPropertyValue('--accent').trim() || '#ff6f00'; }} catch(e) {{ return '#ff6f00'; }}
    }}
    const PRESETS = {{
      conservative: {{ ema_fast: 30, ema_slow: 80, atr_window: 20, atr_k: 2.5, atr_min_pct: 0.02 }},
      standard:     {{ ema_fast: 20, ema_slow: 60, atr_window: 14, atr_k: 2.0, atr_min_pct: 0.01 }},
      aggressive:   {{ ema_fast: 10, ema_slow: 40, atr_window: 10, atr_k: 1.5, atr_min_pct: 0.0 }},
    }};
    function applyPreset(name) {{
      const p = PRESETS[name]; if (!p) return;
      const set = (id, v) => {{ const el = document.getElementById(id); if (el) el.value = v; }};
      set('p_ema_fast', p.ema_fast); set('p_ema_slow', p.ema_slow);
      set('p_atr_window', p.atr_window); set('p_atr_k', p.atr_k); set('p_atr_min_pct', p.atr_min_pct);
    }}
    async function loadFiles() {{
      const res = await fetch('/api/files');
      const data = await res.json();
      const sel = document.getElementById('csv');
      sel.innerHTML = '';
      data.files.forEach(f => {{
        const opt = document.createElement('option');
        opt.value = f; opt.textContent = f; sel.appendChild(opt);
      }});
    }}

    async function runBacktest() {{
      const runBtn = document.getElementById('run');
      if (runBtn) {{ runBtn.disabled = true; runBtn.textContent = '実行中…'; }}
      const payload = {{
        csv: document.getElementById('csv').value,
        pair: document.getElementById('pair').value || 'USDJPY',
        start: document.getElementById('start').value || null,
        end: document.getElementById('end').value || null,
      }};
      // Strategy params (when AI not provided)
      const getNum = (id, defv) => {{ const el = document.getElementById(id); const v = parseFloat(el && el.value); return isNaN(v) ? defv : v; }};
      payload.params = {{
        ema_fast: getNum('p_ema_fast', 20),
        ema_slow: getNum('p_ema_slow', 60),
        atr_window: getNum('p_atr_window', 14),
        atr_k: getNum('p_atr_k', 2.0),
        atr_min_pct: getNum('p_atr_min_pct', 0.0),
      }};
      // Memory saver (max bars)
      const mb = parseInt((document.getElementById('max_bars')||{{value:''}}).value, 10);
      if (!Number.isNaN(mb) && mb > 0) payload.max_bars = mb;
      // AI callable (optional)
      const aiEl = document.getElementById('ai_callable');
      if (aiEl) {{
        const aiPath = aiEl.value.trim();
        if (aiPath) {{
          payload.ai_callable = aiPath;
          const thRaw = (document.getElementById('ai_threshold')||{{value:'0.5'}}).value;
          const th = parseFloat(thRaw);
          payload.ai_threshold = isNaN(th) ? 0.5 : th;
        }}
      }}
      // Client-side validation
      const errs = [];
      if (!(payload.params.ema_fast > 0)) errs.push('EMA Fast は1以上');
      if (!(payload.params.ema_slow > payload.params.ema_fast)) errs.push('EMA Slow は Fast より大きく');
      if (!(payload.params.atr_window >= 5)) errs.push('ATR Window は5以上');
      if (!(payload.params.atr_k >= 0.5 && payload.params.atr_k <= 5.0)) errs.push('ATR k は 0.5〜5.0');
      if (!(payload.params.atr_min_pct >= 0.0 && payload.params.atr_min_pct <= 0.2)) errs.push('Vol下限 は 0.0〜0.2');
      if (payload.start && payload.end && (new Date(payload.start) > new Date(payload.end))) errs.push('開始は終了より前');
      if (errs.length) { alert('入力を確認してください:\n- ' + errs.join('\n- ')); return; }
      // Optional column mapping
      const cols = ['timestamp','open','high','low','close','volume'];
      const colMap = {}; let hasMap = false;
      cols.forEach(k => {{
        const el = document.getElementById('col_'+k);
        if (el) {{
          const v = el.value.trim();
          if (v) {{ colMap[k] = v; hasMap = true; }}
        }}
      }});
      if (hasMap) payload.columns = colMap;
      const res = await fetch('/api/backtest', {{ method: 'POST', headers: {{ 'Content-Type': 'application/json' }}, body: JSON.stringify(payload) }});
      if (!res.ok) {{
        const txt = await res.text();
        notify('エラー: ' + txt, 'error', 6000);
        if (runBtn) {{ runBtn.disabled = false; runBtn.textContent = '実行'; }}
        return;
      }}
      const data = await res.json();
      // Metrics
      const m = data.summary || {{}};
      const fmt = (x) => (x===null||x===undefined) ? '-' : (typeof x==='number' ? x.toFixed(4) : x);
      document.getElementById('m_tr').textContent = fmt(m.total_return);
      document.getElementById('m_sh').textContent = fmt(m.sharpe_approx);
      document.getElementById('m_dd').textContent = fmt(m.max_drawdown);
      document.getElementById('m_nt').textContent = fmt(m.num_trades);
      document.getElementById('m_wr').textContent = fmt(m.win_rate);
      // Chart equity
      const ctx = document.getElementById('equity').getContext('2d');
      const labels = data.equity.map(p => p.t);
      const values = data.equity.map(p => p.v);
      const ds = downsample(labels, values, 1200);
      if (window._chart) window._chart.destroy();
      window._chart = new Chart(ctx, {{
        type: 'line',
        data: {{ labels: ds.labels, datasets: [{{ label: 'Equity', data: ds.values, borderColor: getAccent(), fill: false, tension: 0.1 }}] }},
        options: {{ responsive:true, interaction:{{mode:'index', intersect:false}}, plugins: {{ zoom: {{ zoom: {{ wheel: {{enabled:true}}, pinch: {{enabled:true}}, mode:'x' }}, pan: {{enabled:true, mode:'x'}} }} }}, scales: {{ x: {{ ticks: {{ maxTicksLimit: 8 }} }}, y: {{ beginAtZero: false }} }} }}
      }});
      // Trades table
      const tbody = document.querySelector('#trades tbody');
      tbody.innerHTML = '';
      (data.trades||[]).forEach(tr => {{
        const trEl = document.createElement('tr');
        const cells = [tr.entry_time||'-', tr.exit_time||'-',
                       tr.entry!=null? Number(tr.entry).toFixed(5):'-',
                       tr.exit!=null? Number(tr.exit).toFixed(5):'-',
                       tr.size!=null? Number(tr.size).toFixed(4):'-',
                       tr.pnl!=null? Number(tr.pnl).toFixed(2):'-',
                       tr.hold_min!=null? Number(tr.hold_min).toFixed(1):'-',
                       tr.ret_pct!=null? (Number(tr.ret_pct)*100).toFixed(2)+'%':'-'];
        cells.forEach(v => {{ const td=document.createElement('td'); td.textContent=String(v); trEl.appendChild(td); }});
        tbody.appendChild(trEl);
      }});
      notify('バックテスト完了');
      if (runBtn) {{ runBtn.disabled = false; runBtn.textContent = '実行'; }}
    }}

    async function loadPrefs() {{
      try {{
        const r = await fetch('/api/prefs');
        if (!r.ok) return;
        const p = await r.json();
        if (p.csv) document.getElementById('csv').value = p.csv;
        if (p.pair) document.getElementById('pair').value = p.pair;
        if (p.start) document.getElementById('start').value = p.start;
        if (p.end) document.getElementById('end').value = p.end;
        if (p.max_bars) document.getElementById('max_bars').value = p.max_bars;
        if (p.params) {{
          const q = p.params; const set = (id, v) => {{ if (v!==undefined) document.getElementById(id).value = v; }};
          set('p_ema_fast', q.ema_fast); set('p_ema_slow', q.ema_slow);
          set('p_atr_window', q.atr_window); set('p_atr_k', q.atr_k); set('p_atr_min_pct', q.atr_min_pct);
        }}
        if (p.ai_callable) document.getElementById('ai_callable').value = p.ai_callable;
        if (p.ai_threshold) document.getElementById('ai_threshold').value = p.ai_threshold;
        if (p.columns) {{
          const c = p.columns; const set = (k) => {{ if (c[k]) document.getElementById('col_'+k).value = c[k]; }};
          ['timestamp','open','high','low','close','volume'].forEach(set);
        }}
      }} catch (e) {{ /* ignore */ }}
    }}

    async function savePrefs() {{
      const payload = {{
        csv: document.getElementById('csv').value,
        pair: document.getElementById('pair').value,
        start: document.getElementById('start').value,
        end: document.getElementById('end').value,
        max_bars: (document.getElementById('max_bars')||{{value:''}}).value,
        params: {{
          ema_fast: document.getElementById('p_ema_fast').value,
          ema_slow: document.getElementById('p_ema_slow').value,
          atr_window: document.getElementById('p_atr_window').value,
          atr_k: document.getElementById('p_atr_k').value,
          atr_min_pct: document.getElementById('p_atr_min_pct').value,
        }},
        ai_callable: document.getElementById('ai_callable').value,
        ai_threshold: document.getElementById('ai_threshold').value,
        columns: {{
          timestamp: (document.getElementById('col_timestamp')||{{value:''}}).value,
          open: (document.getElementById('col_open')||{{value:''}}).value,
          high: (document.getElementById('col_high')||{{value:''}}).value,
          low: (document.getElementById('col_low')||{{value:''}}).value,
          close: (document.getElementById('col_close')||{{value:''}}).value,
          volume: (document.getElementById('col_volume')||{{value:''}}).value,
        }}
      }};
      const r = await fetch('/api/prefs', {{ method:'POST', headers: {{'Content-Type':'application/json'}}, body: JSON.stringify(payload) }});
      if (!r.ok) alert('設定の保存に失敗しました');
    }}

    window.addEventListener('DOMContentLoaded', async () => {{
      applyTheme();
      await loadFiles();
      applyPreset('standard');
      await loadPrefs();
      document.getElementById('run').addEventListener('click', runBacktest);
      const ps = document.getElementById('preset'); if (ps) ps.addEventListener('change', (e) => applyPreset(e.target.value));
      const bsave = document.getElementById('btn_save'); if (bsave) bsave.addEventListener('click', savePrefs);
      const dlt = document.getElementById('download_trades'); if (dlt) dlt.addEventListener('click', () => {{ window.location.href = '/api/export/trades'; }});
      // Snapshot list
      const loadSnaps = async () => {{
        const r = await fetch('/api/snapshots'); if (!r.ok) {{ alert('履歴取得に失敗'); return; }}
        const data = await r.json();
        const tb = document.querySelector('#snaps tbody'); if (!tb) return; tb.innerHTML = '';
        (data.items||[]).forEach(it => {{
          const tr = document.createElement('tr');
          const btn = `<button data-name="${{it.name}}" class="btn_run_snap">再実行</button>`;
          const cells = [it.name, it.inputs?.pair||'-', (it.inputs?.start||'-')+' ~ '+(it.inputs?.end||'-'),
                        (it.summary?.sharpe_approx??'-'), (it.summary?.total_return??'-'), btn];
          cells.forEach(v => {{ const td=document.createElement('td'); td.innerHTML=String(v); tr.appendChild(td); }});
          tb.appendChild(tr);
        }});
        document.querySelectorAll('.btn_run_snap').forEach(b => {{ b.addEventListener('click', async (ev) => {{
          const name = ev.target.getAttribute('data-name');
          const r2 = await fetch('/api/snapshots/run', {{ method:'POST', headers:{{'Content-Type':'application/json'}}, body: JSON.stringify({{ name }}) }});
          if (!r2.ok) {{ alert(await r2.text()); return; }}
          const res = await r2.json();
          const m = res.summary||{{}}; const fmt=(x)=> (x==null?'-':(typeof x==='number'?x.toFixed(4):x));
          document.getElementById('m_tr').textContent = fmt(m.total_return);
          document.getElementById('m_sh').textContent = fmt(m.sharpe_approx);
          document.getElementById('m_dd').textContent = fmt(m.max_drawdown);
          document.getElementById('m_nt').textContent = fmt(m.num_trades);
          document.getElementById('m_wr').textContent = fmt(m.win_rate);
          const ctx = document.getElementById('equity').getContext('2d');
          const labels = res.equity.map(p => p.t); const values = res.equity.map(p => p.v);
          const ds = (typeof downsample==='function') ? downsample(labels, values, 1200) : {{ labels, values }};
          if (window._chart) window._chart.destroy();
          window._chart = new Chart(ctx, {{ type:'line', data: {{ labels: ds.labels, datasets:[{{ label:'Equity', data: ds.values, borderColor:getAccent(), fill:false, tension:0.1 }}] }}, options: {{ responsive:true, plugins: {{ zoom: {{ zoom: {{ wheel: {{ enabled:true }}, pinch: {{ enabled:true }}, mode:'x' }}, pan: {{ enabled:true, mode:'x' }} }} }} }} }});
        }}); }});
      }}
      const btnSnaps = document.getElementById('btn_load_snaps'); if (btnSnaps) btnSnaps.addEventListener('click', loadSnaps);

      // Batch run
      const btnBatch = document.getElementById('btn_run_batch'); if (btnBatch) btnBatch.addEventListener('click', async () => {{
        const area = document.getElementById('batch_csvs'); if (!area) return; const txt = (area.value||'').trim(); if (!txt) {{ alert('CSVを入力してください'); return; }}
        const payload = {{
          csvs: txt.split(/\r?\n/).map(s=>s.trim()).filter(Boolean),
          start: document.getElementById('start').value || null,
          end: document.getElementById('end').value || null,
          params: {{
            ema_fast: document.getElementById('p_ema_fast').value,
            ema_slow: document.getElementById('p_ema_slow').value,
            atr_window: document.getElementById('p_atr_window').value,
            atr_k: document.getElementById('p_atr_k').value,
            atr_min_pct: document.getElementById('p_atr_min_pct').value,
          }}
        }};
        const cols = ['timestamp','open','high','low','close','volume']; const colMap={{}}; let hasMap=false;
        cols.forEach(k=>{{ const el=document.getElementById('col_'+k); if(el&&el.value.trim()){{ colMap[k]=el.value.trim(); hasMap=true; }} }});
        if (hasMap) payload.columns = colMap;
        const r = await fetch('/api/batch', {{ method:'POST', headers:{{'Content-Type':'application/json'}}, body: JSON.stringify(payload) }});
        if (!r.ok) {{ alert(await r.text()); return; }}
        const data = await r.json();
        const tb = document.querySelector('#batch_tbl tbody'); if (!tb) return; tb.innerHTML='';
        (data.results||[]).forEach(it => {{
          const tr=document.createElement('tr');
          const cells=[it.pair||it.name||'-', it.summary?.sharpe_approx??'-', it.summary?.total_return??'-', it.summary?.num_trades??'-'];
          cells.forEach(v=>{{ const td=document.createElement('td'); td.textContent=String(v); tr.appendChild(td); }});
          tb.appendChild(tr);
        }});
      }});
      const wfbtn = document.getElementById('run_wf'); if (wfbtn) wfbtn.addEventListener('click', async () => {{
        const payload = {{
          csv: document.getElementById('csv').value,
          pair: document.getElementById('pair').value || 'USDJPY',
          start: document.getElementById('start').value || null,
          end: document.getElementById('end').value || null,
          train_bars: parseInt(document.getElementById('wf_train').value||'2000',10),
          test_bars: parseInt(document.getElementById('wf_test').value||'500',10),
          step_bars: parseInt(document.getElementById('wf_step').value||'0',10),
          ppyear: parseInt(document.getElementById('wf_ppy').value||'6048',10),
          ef: (document.getElementById('wf_ef').value||'10,20,30'),
          es: (document.getElementById('wf_es').value||'50,80,120'),
          aw: (document.getElementById('wf_aw').value||'10,14,20'),
          ak: (document.getElementById('wf_ak').value||'1.5,2.0,2.5'),
          av: (document.getElementById('wf_av').value||'0.0,0.01,0.02'),
        }};
        const cols = ['timestamp','open','high','low','close','volume'];
        const colMap = {}; let hasMap = false;
        cols.forEach(k => {{ const el = document.getElementById('col_'+k); if (el && el.value.trim()) {{ colMap[k]=el.value.trim(); hasMap=true; }} }});
        if (hasMap) payload.columns = colMap;
        const res = await fetch('/api/walkforward', {{ method:'POST', headers:{{'Content-Type':'application/json'}}, body: JSON.stringify(payload) }});
        if (!res.ok) {{ alert(await res.text()); return; }}
        const data = await res.json();
        document.getElementById('wf_n').textContent = (data.folds||[]).length;
        const s = data.summary||{{}};
        const fmt = (x) => (x===null||x===undefined) ? '-' : (typeof x==='number' ? x.toFixed(4) : x);
        document.getElementById('wf_sh').textContent = fmt(s.sharpe_approx);
        document.getElementById('wf_tr').textContent = fmt(s.total_return);
      }});
      const dlf = document.getElementById('dl_wf'); if (dlf) dlf.addEventListener('click', () => {{ window.location.href = '/api/export/wf'; }});
      // Paper trade controls
      const refresh = async () => {{
        const r = await fetch('/api/paper/status');
        if (r.ok) {{
          const s = await r.json();
          document.getElementById('pt_pos').textContent = s.ptr;
          document.getElementById('pt_total').textContent = s.total;
          document.getElementById('pt_position').textContent = (s.position||0).toFixed(4);
          document.getElementById('pt_entry').textContent = (s.entry_price!==null && s.entry_price!==undefined) ? s.entry_price.toFixed(5) : '-';
          document.getElementById('pt_equity').textContent = (s.equity!==null && s.equity!==undefined) ? s.equity.toFixed(2) : '-';
        }}
      }}
      document.getElementById('pt_init').addEventListener('click', async () => {{
        const payload = {{
          csv: document.getElementById('csv').value,
          pair: document.getElementById('pair').value || 'USDJPY',
        }};
        const ai = document.getElementById('ai_callable').value.trim();
        if (ai) {{ payload.ai_callable = ai; payload.ai_threshold = parseFloat(document.getElementById('ai_threshold').value || '0.5'); }}
        const cols = ['timestamp','open','high','low','close','volume'];
        const colMap = {}; let hasMap = false;
        cols.forEach(k => {{ const el = document.getElementById('col_'+k); if (el && el.value.trim()) {{ colMap[k]=el.value.trim(); hasMap=true; }} }});
        if (hasMap) payload.columns = colMap;
        const r = await fetch('/api/paper/config', {{ method:'POST', headers:{{'Content-Type':'application/json'}}, body: JSON.stringify(payload) }});
        if (!r.ok) {{ alert(await r.text()); return; }}
        await refresh();
      }});
      document.getElementById('pt_step').addEventListener('click', async () => {{
        const r = await fetch('/api/paper/step', {{ method:'POST' }});
        if (!r.ok) {{ alert(await r.text()); return; }}
        await refresh();
      }});
      let timer = null;
      document.getElementById('pt_auto').addEventListener('click', async (e) => {{
        if (timer) {{ clearInterval(timer); timer=null; e.target.textContent='自動開始'; return; }}
        e.target.textContent='自動停止';
        timer = setInterval(async () => {{
          const r = await fetch('/api/paper/step', {{ method:'POST' }});
          if (!r.ok) {{ clearInterval(timer); timer=null; e.target.textContent='自動開始'; return; }}
          await refresh();
        }}, 800);
      }});
      await refresh();
    }});
  </script>
  </head>
<body>
  <header>
    <h2>FX Local-First — Web UI</h2>
    <div>
      <div>ローカルCSVでバックテストし、エクイティ曲線と指標を表示します。</div>
      <div class=\"muted\" style=\"margin-top:6px\">オンラインAPI: <strong>{'許可' if ONLINE_ALLOWED else '禁止'}</strong></div>
    </div>
    <div>
      <button id=\"theme\" class=\"btn--primary\" onclick=\"toggleTheme()\">🌙 暗く</button>
    </div>
  </header>
  <div id=\"toast\"></div>

  <div class=\"card\"> 
    <div class=\"row\"> 
      <div>
        <label>プリセット</label>
        <select id=\"preset\">
          <option value=\"standard\">標準</option>
          <option value=\"conservative\">保守</option>
          <option value=\"aggressive\">攻め</option>
        </select>
      </div>
      <div>
        <label>CSVファイル（data/）</label>
        <select id=\"csv\"></select>
      </div>
      <div>
        <label>ペア</label>
        <input id=\"pair\" value=\"USDJPY\" />
      </div>
      <div>
        <label>開始</label>
        <input id=\"start\" placeholder=\"YYYY-MM-DD\" />
      </div>
      <div>
        <label>終了</label>
        <input id=\"end\" placeholder=\"YYYY-MM-DD\" />
      </div>
      <div>
        <label>最大バー数（省メモリ）</label>
        <input id=\"max_bars\" type=\"number\" placeholder=\"例: 50000\" />
      </div>
      <div>
        <button id=\"run\">実行</button>
      </div>
      <div>
        <button id=\"btn_save\">設定保存</button>
      </div>
      <div>
        <button id=\"download_trades\">トレードCSVダウンロード</button>
      </div>
    </div>
    <details style=\"margin-top:8px\"><summary>戦略パラメータ（AI未指定時に有効）</summary>
      <div class=\"row\" style=\"margin-top:8px\">
        <div><label>EMA Fast</label><input id=\"p_ema_fast\" type=\"number\" value=\"20\" style=\"width:120px\" /></div>
        <div><label>EMA Slow</label><input id=\"p_ema_slow\" type=\"number\" value=\"60\" style=\"width:120px\" /></div>
        <div><label>ATR Window</label><input id=\"p_atr_window\" type=\"number\" value=\"14\" style=\"width:120px\" /></div>
        <div><label>ATR k (Stop)</label><input id=\"p_atr_k\" type=\"number\" step=\"0.1\" value=\"2.0\" style=\"width:120px\" /></div>
        <div><label>Vol 下限（相対ATR）</label><input id=\"p_atr_min_pct\" type=\"number\" step=\"0.005\" value=\"0.0\" style=\"width:140px\" /></div>
      </div>
    </details>
    <details style=\"margin-top:8px\"><summary>AIシグナル（任意）</summary>
      <div class=\"row\" style=\"margin-top:8px\">
        <div><label>Pythonコーラブル（module:func）</label><input id=\"ai_callable\" placeholder=\"例: scripts.ai_example:momentum_score\" style=\"min-width:340px\" /></div>
        <div><label>しきい値</label><input id=\"ai_threshold\" type=\"number\" step=\"0.01\" value=\"0.5\" style=\"width:120px\" /></div>
      </div>
    </details>
    <details style=\"margin-top:8px\"><summary>列名マッピング（任意・空で自動推測）</summary>
      <div class=\"row\" style=\"margin-top:8px\">
        <div><label>Timestamp列</label><input id=\"col_timestamp\" placeholder=\"例: Date\" /></div>
        <div><label>Open列</label><input id=\"col_open\" placeholder=\"例: Open\" /></div>
        <div><label>High列</label><input id=\"col_high\" placeholder=\"例: High\" /></div>
        <div><label>Low列</label><input id=\"col_low\" placeholder=\"例: Low\" /></div>
        <div><label>Close列</label><input id=\"col_close\" placeholder=\"例: Close\" /></div>
        <div><label>Volume列（任意）</label><input id=\"col_volume\" placeholder=\"例: Volume\" /></div>
      </div>
    </details>
  </div>

  <div class=\"card\">
    <h3>指標</h3>
    <div class=\"metrics\">
      <span>総リターン: <strong id=\"m_tr\">-</strong></span>
      <span>シャープ: <strong id=\"m_sh\">-</strong></span>
      <span>最大DD: <strong id=\"m_dd\">-</strong></span>
      <span>取引数: <strong id=\"m_nt\">-</strong></span>
      <span>勝率: <strong id=\"m_wr\">-</strong></span>
    </div>
  </div>

  <div class=\"card\"> 
    <h3>エクイティ曲線</h3>
    <canvas id=\"equity\"></canvas>
  </div>

  <div class=\"card\"> 
    <h3>トレード一覧（最新20件）</h3>
    <div style=\"overflow:auto\">
      <table id=\"trades\" border=\"1\" cellpadding=\"4\" cellspacing=\"0\" style=\"border-collapse:collapse; min-width:980px\">
        <thead><tr>
          <th>Entry Time</th><th>Exit Time</th><th>Entry</th><th>Exit</th><th>Size</th><th>PnL</th><th>Hold(min)</th><th>Ret%</th>
        </tr></thead>
        <tbody></tbody>
      </table>
    </div>
  </div>

  <div class=\"card\">
    <h3>Walk-Forward</h3>
    <div class=\"row\">
      <div><label>Train Bars</label><input id=\"wf_train\" type=\"number\" value=\"2000\" style=\"width:140px\" /></div>
      <div><label>Test Bars</label><input id=\"wf_test\" type=\"number\" value=\"500\" style=\"width:140px\" /></div>
      <div><label>Step Bars</label><input id=\"wf_step\" type=\"number\" value=\"0\" style=\"width:140px\" /></div>
      <div><label>ppyear</label><input id=\"wf_ppy\" type=\"number\" value=\"6048\" style=\"width:140px\" /></div>
    </div>
    <details style=\"margin-top:8px\"><summary>パラメータ候補（リスト、カンマ区切り）</summary>
      <div class=\"row\" style=\"margin-top:8px\">
        <div><label>EMA Fast</label><input id=\"wf_ef\" value=\"10,20,30\" style=\"min-width:220px\" /></div>
        <div><label>EMA Slow</label><input id=\"wf_es\" value=\"50,80,120\" style=\"min-width:220px\" /></div>
        <div><label>ATR Window</label><input id=\"wf_aw\" value=\"10,14,20\" style=\"min-width:220px\" /></div>
        <div><label>ATR k</label><input id=\"wf_ak\" value=\"1.5,2.0,2.5\" style=\"min-width:220px\" /></div>
        <div><label>Vol下限</label><input id=\"wf_av\" value=\"0.0,0.01,0.02\" style=\"min-width:220px\" /></div>
      </div>
    </details>
    <div class=\"row\" style=\"margin-top:8px\">
      <div><button id=\"run_wf\">WF実行</button></div>
      <div><button id=\"dl_wf\">Folds CSVダウンロード</button></div>
      <div style=\"margin-left:8px\">Folds: <strong id=\"wf_n\">-</strong>, Sharpe: <strong id=\"wf_sh\">-</strong>, Return: <strong id=\"wf_tr\">-</strong></div>
    </div>
  </div>
 
  <div class=\"card\"> 
    <h3>ペーパートレード</h3>
    <div class=\"row\"> 
      <div><button id=\"pt_init\">初期化</button></div>
      <div><button id=\"pt_step\">1バー進める</button></div>
      <div>
        <button id=\"pt_auto\">自動開始</button>
        <span id=\"pt_status\" style=\"margin-left:8px\"></span>
      </div>
    </div>
    <div style=\"margin-top:8px\"> 
      <div>バー位置: <span id=\"pt_pos\">-</span> / <span id=\"pt_total\">-</span></div>
      <div>ポジション: <span id=\"pt_position\">0</span> @ <span id=\"pt_entry\">-</span></div>
      <div>エクイティ: <span id=\"pt_equity\">-</span></div>
    </div>
  </div>

  <footer>
    <div>設定は <code>config/config.yaml</code> を使用（戦略パラメータ）。</div>
  </footer>
</body>
</html>
"""
    return Response(html, mimetype="text/html")


@app.get("/api/files")
def api_files():
    files = _list_csv_files(DATA_DIR)
    return jsonify({"files": files})


@app.post("/api/backtest")
def api_backtest():
    try:
        payload = request.get_json(force=True) or {}
        csv_path = payload.get("csv")
        pair = payload.get("pair") or "USDJPY"
        start = payload.get("start")
        end = payload.get("end")
        colmap = payload.get("columns") if isinstance(payload.get("columns"), dict) else None
        p = payload.get("params") or {}
        max_bars = payload.get("max_bars")

        if not csv_path:
            return Response("csv is required", status=400)
        if not Path(csv_path).exists():
            return Response(f"csv not found: {csv_path}", status=404)

        cfg = load_config(str(DEFAULT_CONFIG))
        df = load_ohlcv_csv(str(csv_path), column_map=colmap)
        # Optional slicing
        if start:
            df = df[df.index >= pd.to_datetime(start, utc=True)]  # type: ignore[name-defined]
        if end:
            df = df[df.index <= pd.to_datetime(end, utc=True)]  # type: ignore[name-defined]
        # Memory saver: limit max bars and downcast numerics
        try:
            if max_bars:
                mb = int(max_bars)
                if mb > 0:
                    df = df.tail(mb)
            for c in ["open","high","low","close","volume"]:
                if c in df.columns:
                    df[c] = pd.to_numeric(df[c], errors="coerce").astype("float32")
        except Exception:
            pass

        params = cfg.strategy_params
        # Overrides from UI (if provided)
        ui_ef = int(p.get("ema_fast")) if str(p.get("ema_fast", "")).strip() != "" else int(params.get("ema_fast", 20))
        ui_es = int(p.get("ema_slow")) if str(p.get("ema_slow", "")).strip() != "" else int(params.get("ema_slow", 60))
        ui_aw = int(p.get("atr_window")) if str(p.get("atr_window", "")).strip() != "" else int(params.get("atr_window", 14))
        ui_ak = float(p.get("atr_k")) if str(p.get("atr_k", "")).strip() != "" else float(params.get("atr_k_stop", 2.0))
        ui_av = float(p.get("atr_min_pct")) if str(p.get("atr_min_pct", "")).strip() != "" else float(params.get("vol_filter_min_atr_pct", 0.0))
        # Server-side validation
        if not (ui_ef > 0):
            return Response("EMA Fast must be > 0", status=400)
        if not (ui_es > ui_ef):
            return Response("EMA Slow must be > EMA Fast", status=400)
        if not (ui_aw >= 5):
            return Response("ATR Window must be >= 5", status=400)
        if not (0.5 <= ui_ak <= 5.0):
            return Response("ATR k must be in [0.5, 5.0]", status=400)
        if not (0.0 <= ui_av <= 0.2):
            return Response("Vol min ATR pct must be in [0.0, 0.2]", status=400)
        ai_callable = payload.get("ai_callable")
        if ai_callable and ("ai_gemini" in str(ai_callable)) and not ONLINE_ALLOWED:
            ai_callable = None
        if ai_callable:
            th = float(payload.get("ai_threshold", 0.5))
            sig = generate_signals_from_callable(df, callable_path=str(ai_callable), threshold=th)
        else:
            sig = generate_signals(
                df,
                ema_fast=ui_ef,
                ema_slow=ui_es,
                atr_window=ui_aw,
                vol_filter_min_atr_pct=ui_av,
            )
        res = run_backtest(
            sig,
            start_cash=float(cfg.general.get("start_cash", 1_000_000)),
            atr_k_stop=ui_ak,
            slippage_pct=float(cfg.backtest_params.get("slippage_pct", 0.0)),
            fee_perc_roundturn=float(cfg.backtest_params.get("fee_perc_roundturn", 0.0)),
            per_trade_risk_pct=float(cfg.risk_params.get("per_trade_risk_pct", 0.25)),
            daily_loss_stop_pct=float(cfg.risk_params.get("daily_loss_stop_pct", 1.0)),
        )

        pnl = res.get("pnl_series")
        start_cash = float(res.get("start_cash", 0.0))
        end_cash = float(res.get("end_cash", 0.0))

        # Build equity curve for chart
        equity_points = []
        if pnl is not None:
            csum = pnl.fillna(0.0).cumsum()
            equity = start_cash + csum
            for ts, v in equity.items():
                t = ts.isoformat()
                equity_points.append({"t": t, "v": float(v)})

        summary = metrics_from_pnl(pnl, start_cash, end_cash) if pnl is not None else {}

        # Build trades table (latest 20) and store all for export
        trades = []
        all_trades = []
        for t in res.get("trades", []):
            try:
                entry_time = t.entry_time.isoformat() if hasattr(t, "entry_time") else None
                exit_time = t.exit_time.isoformat() if getattr(t, "exit_time", None) is not None else None
                entry = float(getattr(t, "entry", None)) if getattr(t, "entry", None) is not None else None
                exit_px = float(getattr(t, "exit", None)) if getattr(t, "exit", None) is not None else None
                size = float(getattr(t, "size", None)) if getattr(t, "size", None) is not None else None
                pnl = None
                if entry is not None and exit_px is not None and size is not None:
                    pnl = (exit_px - entry) * size
                # extra columns
                hold_min = None
                try:
                    if entry_time and exit_time:
                        import pandas as _pd
                        et = _pd.to_datetime(entry_time, utc=True)
                        xt = _pd.to_datetime(exit_time, utc=True)
                        hold_min = float((xt - et).total_seconds() / 60.0)
                except Exception:
                    hold_min = None
                ret_pct = None
                if entry is not None and exit_px is not None and size is not None and entry != 0:
                    try:
                        ret_pct = float((exit_px - entry) / entry)
                    except Exception:
                        ret_pct = None
                row = {
                    "entry_time": entry_time,
                    "exit_time": exit_time,
                    "entry": entry,
                    "exit": exit_px,
                    "size": size,
                    "pnl": pnl,
                    "hold_min": hold_min,
                    "ret_pct": ret_pct,
                }
                all_trades.append(row)
            except Exception:
                continue
        trades = all_trades[-20:]

        # Save last trades for export
        global _LAST_TRADES
        _LAST_TRADES = all_trades

        # Save snapshot (inputs + summary)
        try:
            import datetime as _dt
            snap_dir = ROOT / "out" / "snapshots"
            snap_dir.mkdir(parents=True, exist_ok=True)
            tsname = _dt.datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
            snap = {
                "inputs": {
                    "csv": csv_path,
                    "pair": pair,
                    "start": start,
                    "end": end,
                    "params": {"ema_fast": ui_ef, "ema_slow": ui_es, "atr_window": ui_aw, "atr_k": ui_ak, "atr_min_pct": ui_av},
                    "ai_callable": ai_callable,
                    "max_bars": max_bars,
                },
                "summary": summary,
            }
            with open(snap_dir / f"snap_{tsname}.json", "w", encoding="utf-8") as f:
                json.dump(snap, f, ensure_ascii=False, indent=2)
        except Exception:
            pass

        return jsonify({
            "pair": pair,
            "summary": summary,
            "equity": equity_points,
            "trades": trades,
        })
    except Exception as e:
        return Response(str(e), status=500)


# Walk-Forward API
@app.post("/api/walkforward")
def api_walkforward():
    try:
        payload = request.get_json(force=True) or {}
        csv_path = payload.get("csv")
        if not csv_path:
            return Response("csv is required", status=400)
        if not Path(csv_path).exists():
            return Response(f"csv not found: {csv_path}", status=404)
        colmap = payload.get("columns") if isinstance(payload.get("columns"), dict) else None
        start = payload.get("start")
        end = payload.get("end")

        # Parse lists from strings
        def _parse_list(s: str, cast):
            return [cast(x) for x in str(s).split(',') if str(x).strip()]

        ef = _parse_list(payload.get("ef", "10,20,30"), int)
        es = _parse_list(payload.get("es", "50,80,120"), int)
        aw = _parse_list(payload.get("aw", "10,14,20"), int)
        ak = _parse_list(payload.get("ak", "1.5,2.0,2.5"), float)
        av = _parse_list(payload.get("av", "0.0,0.01,0.02"), float)

        cfg = load_config(str(DEFAULT_CONFIG))
        df = load_ohlcv_csv(str(csv_path), column_map=colmap)
        if start:
            df = df[df.index >= pd.to_datetime(start, utc=True)]
        if end:
            df = df[df.index <= pd.to_datetime(end, utc=True)]

        train_bars = int(payload.get("train_bars", 2000))
        test_bars = int(payload.get("test_bars", 500))
        step_bars = int(payload.get("step_bars", 0))
        step = step_bars if step_bars > 0 else None
        ppyear = int(payload.get("ppyear", 6048))

        result = walk_forward(
            df,
            train_bars=train_bars,
            test_bars=test_bars,
            step_bars=step,
            ema_fast_list=ef,
            ema_slow_list=es,
            atr_window_list=aw,
            atr_k_list=ak,
            vol_filter_min_atr_pct_list=av,
            start_cash=float(cfg.general.get("start_cash", 1_000_000)),
            slippage_pct=float(cfg.backtest_params.get("slippage_pct", 0.0)),
            fee_perc_roundturn=float(cfg.backtest_params.get("fee_perc_roundturn", 0.0)),
            per_trade_risk_pct=float(cfg.risk_params.get("per_trade_risk_pct", 0.25)),
            daily_loss_stop_pct=float(cfg.risk_params.get("daily_loss_stop_pct", 1.0)),
            periods_per_year=ppyear,
        )

        # Save folds for export
        global _LAST_WF_FOLDS
        _LAST_WF_FOLDS = result.get('folds', [])

        return jsonify({
            "summary": result.get("summary", {}),
            "folds": _LAST_WF_FOLDS,
        })
    except Exception as e:
        return Response(str(e), status=500)


@app.get("/api/export/wf")
def api_export_wf():
    try:
        if not _LAST_WF_FOLDS:
            return Response("no folds", status=404)
        import io, csv
        buf = io.StringIO()
        # Flatten params + metrics
        fieldnames = [
            "train_start","train_end","test_start","test_end",
            "ema_fast","ema_slow","atr_window","atr_k","vol_filter_min_atr_pct",
            "total_return","sharpe_approx","max_drawdown","num_trades","win_rate","avg_trade","profit_factor",
        ]
        w = csv.DictWriter(buf, fieldnames=fieldnames)
        w.writeheader()
        for f in _LAST_WF_FOLDS:
            row = {
                "train_start": f.get("train_start"),
                "train_end": f.get("train_end"),
                "test_start": f.get("test_start"),
                "test_end": f.get("test_end"),
                "ema_fast": f.get("params",{}).get("ema_fast"),
                "ema_slow": f.get("params",{}).get("ema_slow"),
                "atr_window": f.get("params",{}).get("atr_window"),
                "atr_k": f.get("params",{}).get("atr_k"),
                "vol_filter_min_atr_pct": f.get("params",{}).get("vol_filter_min_atr_pct"),
            }
            m = f.get("metrics", {})
            row.update({
                "total_return": m.get("total_return"),
                "sharpe_approx": m.get("sharpe_approx"),
                "max_drawdown": m.get("max_drawdown"),
                "num_trades": m.get("num_trades"),
                "win_rate": m.get("win_rate"),
                "avg_trade": m.get("avg_trade"),
                "profit_factor": m.get("profit_factor"),
            })
            w.writerow(row)
        data = buf.getvalue()
        return Response(data, mimetype="text/csv", headers={"Content-Disposition": "attachment; filename=walkforward_folds.csv"})
    except Exception as e:
        return Response(str(e), status=500)
# Preferences save/load
@app.get("/api/prefs")
def api_get_prefs():
    try:
        if PREFS_PATH.exists():
            with open(PREFS_PATH, "r", encoding="utf-8") as f:
                return jsonify(json.load(f))
        return jsonify({})
    except Exception as e:
        return Response(str(e), status=500)


@app.post("/api/prefs")
def api_post_prefs():
    try:
        payload = request.get_json(force=True) or {}
        PREFS_PATH.parent.mkdir(parents=True, exist_ok=True)
        with open(PREFS_PATH, "w", encoding="utf-8") as f:
            json.dump(payload, f, ensure_ascii=False, indent=2)
        return jsonify({"ok": True, "path": str(PREFS_PATH)})
    except Exception as e:
        return Response(str(e), status=500)


# Export last trades as CSV
@app.get("/api/export/trades")
def api_export_trades():
    try:
        if not _LAST_TRADES:
            return Response("no trades", status=404)
        import io, csv
        buf = io.StringIO()
        w = csv.DictWriter(buf, fieldnames=["entry_time","exit_time","entry","exit","size","pnl"])
        w.writeheader()
        for r in _LAST_TRADES:
            w.writerow(r)
        data = buf.getvalue()
        return Response(
            data,
            mimetype="text/csv",
            headers={"Content-Disposition": "attachment; filename=trades.csv"},
        )
    except Exception as e:
        return Response(str(e), status=500)

# -------- Paper trading (step-by-step) --------
class PaperEngine:
    def __init__(self, sig_df: pd.DataFrame, *, start_cash: float, atr_k_stop: float, slippage_pct: float, fee_perc_roundturn: float, per_trade_risk_pct: float, daily_loss_stop_pct: float | None):
        self.df = sig_df.copy()
        self.idx = list(sig_df.index)
        self.ptr = 0
        self.start_cash = float(start_cash)
        self.cash = float(start_cash)
        self.equity = float(start_cash)
        self.position = 0.0
        self.entry_price = None
        self.atr_stop = None
        self.atr_k_stop = float(atr_k_stop)
        self.slippage_pct = float(slippage_pct)
        self.fee_perc_roundturn = float(fee_perc_roundturn)
        self.per_trade_risk_pct = float(per_trade_risk_pct)
        self.daily_loss_stop_pct = float(daily_loss_stop_pct) if daily_loss_stop_pct is not None else None
        self.pnl_series = pd.Series(0.0, index=self.df.index)
        self.day_realized = {}

    def step_one(self) -> bool:
        if self.ptr >= len(self.idx):
            return False
        ts = self.idx[self.ptr]
        row = self.df.loc[ts]
        price = float(row["close"])
        sig = int(row.get("signal", 0))
        a = float(row.get("atr", 0.0)) if pd.notna(row.get("atr", float("nan"))) else 0.0

        # Exit
        if self.position > 0:
            stop_px = self.atr_stop if self.atr_stop is not None else -1e18
            exit_now = (sig == 0) or (price <= stop_px)
            if exit_now:
                px = price * (1.0 - self.slippage_pct)
                gross = (px - float(self.entry_price)) * self.position
                fee = abs(px * self.position) * self.fee_perc_roundturn
                trade_pnl = gross - fee
                self.cash += trade_pnl
                self.equity = self.cash
                self.position = 0.0
                self.entry_price = None
                self.atr_stop = None
                self.pnl_series.loc[ts] = trade_pnl
                d = ts.tz_convert("UTC").date() if hasattr(ts, "tzinfo") and ts.tzinfo else ts.date()
                self.day_realized[d] = self.day_realized.get(d, 0.0) + float(trade_pnl)

        # Entry
        if self.position == 0 and sig == 1 and a > 0:
            if self.daily_loss_stop_pct is not None:
                d = ts.tz_convert("UTC").date() if hasattr(ts, "tzinfo") and ts.tzinfo else ts.date()
                realized_today = self.day_realized.get(d, 0.0)
                if realized_today <= -(self.start_cash * (self.daily_loss_stop_pct / 100.0)):
                    self.ptr += 1
                    return True
            units = position_size_from_atr(
                entry_price=price,
                atr_value=a,
                atr_k_stop=self.atr_k_stop,
                equity=self.equity,
                per_trade_risk_pct=self.per_trade_risk_pct,
            )
            if units > 0:
                px = price * (1.0 + self.slippage_pct)
                fee = abs(px * units) * (self.fee_perc_roundturn / 2.0)
                self.entry_price = px
                self.atr_stop = self.entry_price - self.atr_k_stop * a
                self.position = units
                self.cash -= fee
                self.equity = self.cash

        self.ptr += 1
        return True

    def status(self) -> dict:
        last_ts = self.idx[self.ptr - 1] if self.ptr > 0 and self.ptr <= len(self.idx) else None
        start_cash = float(self.start_cash)
        end_cash = float(self.cash)
        summary = metrics_from_pnl(self.pnl_series.iloc[: self.ptr], start_cash, end_cash) if self.ptr > 0 else {}
        return {
            "ptr": self.ptr,
            "total": len(self.idx),
            "last_ts": last_ts.isoformat() if last_ts is not None else None,
            "position": float(self.position),
            "entry_price": float(self.entry_price) if self.entry_price is not None else None,
            "equity": float(self.equity),
            "summary": summary,
        }


_ENGINE: PaperEngine | None = None


@app.post("/api/paper/config")
def api_paper_config():
    try:
        payload = request.get_json(force=True) or {}
        csv_path = payload.get("csv")
        if not csv_path:
            return Response("csv is required", status=400)
        colmap = payload.get("columns") if isinstance(payload.get("columns"), dict) else None
        cfg = load_config(str(DEFAULT_CONFIG))
        df = load_ohlcv_csv(str(csv_path), column_map=colmap)
        params = cfg.strategy_params
        ai_callable = payload.get("ai_callable")
        if ai_callable:
            th = float(payload.get("ai_threshold", 0.5))
            sig = generate_signals_from_callable(df, callable_path=str(ai_callable), threshold=th)
        else:
            sig = generate_signals(
                df,
                ema_fast=int(params.get("ema_fast", 20)),
                ema_slow=int(params.get("ema_slow", 60)),
                atr_window=int(params.get("atr_window", 14)),
                vol_filter_min_atr_pct=float(params.get("vol_filter_min_atr_pct", 0.0)),
            )
        global _ENGINE
        _ENGINE = PaperEngine(
            sig,
            start_cash=float(cfg.general.get("start_cash", 1_000_000)),
            atr_k_stop=float(params.get("atr_k_stop", 2.0)),
            slippage_pct=float(cfg.backtest_params.get("slippage_pct", 0.0)),
            fee_perc_roundturn=float(cfg.backtest_params.get("fee_perc_roundturn", 0.0)),
            per_trade_risk_pct=float(cfg.risk_params.get("per_trade_risk_pct", 0.25)),
            daily_loss_stop_pct=float(cfg.risk_params.get("daily_loss_stop_pct", 1.0)),
        )
        return jsonify({"ok": True})
    except Exception as e:
        return Response(str(e), status=500)


@app.post("/api/paper/step")
def api_paper_step():
    try:
        global _ENGINE
        if _ENGINE is None:
            return Response("engine not initialized", status=400)
        cont = _ENGINE.step_one()
        return jsonify({"ok": True, "cont": cont})
    except Exception as e:
        return Response(str(e), status=500)


@app.get("/api/paper/status")
def api_paper_status():
    try:
        global _ENGINE
        if _ENGINE is None:
            return jsonify({"ptr": 0, "total": 0, "position": 0.0, "entry_price": None, "equity": None, "summary": {}})
        return jsonify(_ENGINE.status())
    except Exception as e:
        return Response(str(e), status=500)
def main():
    # Flask dev server
    port = int(os.environ.get("PORT", "7860"))
    app.run(host="0.0.0.0", port=port, debug=True)


if __name__ == "__main__":
    # Lazy import to avoid top import cost for pandas in route registration
    import pandas as pd  # noqa: F401
    main()
# Snapshot list and rerun
@app.get("/api/snapshots")
def api_snapshots():
    try:
        snap_dir = ROOT / "out" / "snapshots"
        items = []
        if snap_dir.exists():
            for p in sorted(snap_dir.glob("snap_*.json"), reverse=True):
                try:
                    with open(p, "r", encoding="utf-8") as f:
                        j = json.load(f)
                    items.append({"name": p.name, "inputs": j.get("inputs", {}), "summary": j.get("summary", {})})
                except Exception:
                    continue
        return jsonify({"items": items[:50]})
    except Exception as e:
        return Response(str(e), status=500)


@app.post("/api/snapshots/run")
def api_snapshots_run():
    try:
        payload = request.get_json(force=True) or {}
        name = payload.get("name")
        if not name:
            return Response("name is required", status=400)
        snap_path = ROOT / "out" / "snapshots" / name
        if not snap_path.exists():
            return Response("snapshot not found", status=404)
        with open(snap_path, "r", encoding="utf-8") as f:
            snap = json.load(f)
        inp = snap.get("inputs", {})
        csv_path = inp.get("csv")
        if not csv_path or not Path(csv_path).exists():
            return Response("csv missing or not found", status=400)
        pair = inp.get("pair") or "USDJPY"
        start = inp.get("start")
        end = inp.get("end")
        params = inp.get("params") or {}
        ai_callable = inp.get("ai_callable")

        cfg = load_config(str(DEFAULT_CONFIG))
        df = load_ohlcv_csv(str(csv_path))
        if start:
            df = df[df.index >= pd.to_datetime(start, utc=True)]
        if end:
            df = df[df.index <= pd.to_datetime(end, utc=True)]

        ef = int(params.get("ema_fast", 20)); es = int(params.get("ema_slow", 60)); aw = int(params.get("atr_window", 14))
        ak = float(params.get("atr_k", params.get("atr_k_stop", 2.0)))
        av = float(params.get("atr_min_pct", params.get("vol_filter_min_atr_pct", 0.0)))
        if ai_callable and ("ai_gemini" in str(ai_callable)) and not ONLINE_ALLOWED:
            ai_callable = None
        if ai_callable:
            sig = generate_signals_from_callable(df, callable_path=str(ai_callable), threshold=0.5)
        else:
            sig = generate_signals(df, ema_fast=ef, ema_slow=es, atr_window=aw, vol_filter_min_atr_pct=av)

        res = run_backtest(
            sig,
            start_cash=float(cfg.general.get("start_cash", 1_000_000)),
            atr_k_stop=ak,
            slippage_pct=float(cfg.backtest_params.get("slippage_pct", 0.0)),
            fee_perc_roundturn=float(cfg.backtest_params.get("fee_perc_roundturn", 0.0)),
            per_trade_risk_pct=float(cfg.risk_params.get("per_trade_risk_pct", 0.25)),
            daily_loss_stop_pct=float(cfg.risk_params.get("daily_loss_stop_pct", 1.0)),
        )
        pnl = res.get("pnl_series")
        start_cash = float(res.get("start_cash", 0.0))
        end_cash = float(res.get("end_cash", 0.0))
        equity_points = []
        if pnl is not None:
            csum = pnl.fillna(0.0).cumsum(); equity = start_cash + csum
            for ts, v in equity.items(): equity_points.append({"t": ts.isoformat(), "v": float(v)})
        summary = metrics_from_pnl(pnl, start_cash, end_cash) if pnl is not None else {}
        return jsonify({"summary": summary, "equity": equity_points})
    except Exception as e:
        return Response(str(e), status=500)


# Batch backtest across multiple CSVs
@app.post("/api/batch")
def api_batch():
    try:
        payload = request.get_json(force=True) or {}
        csvs = payload.get("csvs") or []
        if not isinstance(csvs, list) or not csvs:
            return Response("csvs list required", status=400)
        start = payload.get("start"); end = payload.get("end")
        colmap = payload.get("columns") if isinstance(payload.get("columns"), dict) else None
        p = payload.get("params") or {}
        cfg = load_config(str(DEFAULT_CONFIG))
        results = []
        for path in csvs:
            try:
                if not Path(path).exists():
                    results.append({"name": path, "error": "not found"}); continue
                df = load_ohlcv_csv(str(path), column_map=colmap)
                if start: df = df[df.index >= pd.to_datetime(start, utc=True)]
                if end: df = df[df.index <= pd.to_datetime(end, utc=True)]
                ef = int(p.get("ema_fast", 20)); es = int(p.get("ema_slow", 60)); aw = int(p.get("atr_window", 14))
                ak = float(p.get("atr_k", 2.0)); av = float(p.get("atr_min_pct", 0.0))
                sig = generate_signals(df, ema_fast=ef, ema_slow=es, atr_window=aw, vol_filter_min_atr_pct=av)
                res = run_backtest(
                    sig,
                    start_cash=float(cfg.general.get("start_cash", 1_000_000)),
                    atr_k_stop=ak,
                    slippage_pct=float(cfg.backtest_params.get("slippage_pct", 0.0)),
                    fee_perc_roundturn=float(cfg.backtest_params.get("fee_perc_roundturn", 0.0)),
                    per_trade_risk_pct=float(cfg.risk_params.get("per_trade_risk_pct", 0.25)),
                    daily_loss_stop_pct=float(cfg.risk_params.get("daily_loss_stop_pct", 1.0)),
                )
                pnl = res.get("pnl_series"); summ = metrics_from_pnl(pnl, res["start_cash"], res["end_cash"]) if pnl is not None else {}
                pair = Path(path).stem
                results.append({"name": path, "pair": pair, "summary": summ})
            except Exception as e:
                results.append({"name": path, "error": str(e)})
        # sort by sharpe desc
        results.sort(key=lambda x: (x.get("summary",{}).get("sharpe_approx", -1e9)), reverse=True)
        return jsonify({"results": results})
    except Exception as e:
        return Response(str(e), status=500)
