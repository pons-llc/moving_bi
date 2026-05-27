"""Build the complete flow map HTML by combining template, data, and JS logic."""
import json
from pathlib import Path

BASE = Path(__file__).parent

# Load flow data (inter-prefecture only)
with open('/tmp/flows_mini.json') as f:
    flow_data = json.load(f)

PREF_INFO = {
    "01000": {"name": "北海道",  "coord": [141.347, 43.064]},
    "02000": {"name": "青森県",  "coord": [140.740, 40.824]},
    "03000": {"name": "岩手県",  "coord": [141.152, 39.703]},
    "04000": {"name": "宮城県",  "coord": [140.872, 38.268]},
    "05000": {"name": "秋田県",  "coord": [140.102, 39.718]},
    "06000": {"name": "山形県",  "coord": [140.364, 38.240]},
    "07000": {"name": "福島県",  "coord": [140.468, 37.750]},
    "08000": {"name": "茨城県",  "coord": [140.447, 36.342]},
    "09000": {"name": "栃木県",  "coord": [139.883, 36.565]},
    "10000": {"name": "群馬県",  "coord": [139.061, 36.391]},
    "11000": {"name": "埼玉県",  "coord": [139.649, 35.857]},
    "12000": {"name": "千葉県",  "coord": [140.123, 35.605]},
    "13000": {"name": "東京都",  "coord": [139.692, 35.690]},
    "14000": {"name": "神奈川県","coord": [139.642, 35.448]},
    "15000": {"name": "新潟県",  "coord": [139.023, 37.902]},
    "16000": {"name": "富山県",  "coord": [137.212, 36.695]},
    "17000": {"name": "石川県",  "coord": [136.626, 36.594]},
    "18000": {"name": "福井県",  "coord": [136.221, 35.904]},
    "19000": {"name": "山梨県",  "coord": [138.568, 35.664]},
    "20000": {"name": "長野県",  "coord": [138.181, 36.651]},
    "21000": {"name": "岐阜県",  "coord": [136.722, 35.391]},
    "22000": {"name": "静岡県",  "coord": [138.383, 34.977]},
    "23000": {"name": "愛知県",  "coord": [136.907, 35.180]},
    "24000": {"name": "三重県",  "coord": [136.509, 34.730]},
    "25000": {"name": "滋賀県",  "coord": [136.006, 35.004]},
    "26000": {"name": "京都府",  "coord": [135.768, 35.012]},
    "27000": {"name": "大阪府",  "coord": [135.502, 34.686]},
    "28000": {"name": "兵庫県",  "coord": [134.690, 34.691]},
    "29000": {"name": "奈良県",  "coord": [135.832, 34.685]},
    "30000": {"name": "和歌山県","coord": [135.167, 34.226]},
    "31000": {"name": "鳥取県",  "coord": [134.238, 35.504]},
    "32000": {"name": "島根県",  "coord": [132.546, 35.472]},
    "33000": {"name": "岡山県",  "coord": [133.935, 34.662]},
    "34000": {"name": "広島県",  "coord": [132.459, 34.396]},
    "35000": {"name": "山口県",  "coord": [131.471, 34.186]},
    "36000": {"name": "徳島県",  "coord": [134.558, 34.066]},
    "37000": {"name": "香川県",  "coord": [134.043, 34.340]},
    "38000": {"name": "愛媛県",  "coord": [132.765, 33.842]},
    "39000": {"name": "高知県",  "coord": [133.531, 33.559]},
    "40000": {"name": "福岡県",  "coord": [130.416, 33.607]},
    "41000": {"name": "佐賀県",  "coord": [130.298, 33.249]},
    "42000": {"name": "長崎県",  "coord": [129.873, 32.745]},
    "43000": {"name": "熊本県",  "coord": [130.742, 32.790]},
    "44000": {"name": "大分県",  "coord": [131.612, 33.238]},
    "45000": {"name": "宮崎県",  "coord": [131.424, 31.911]},
    "46000": {"name": "鹿児島県","coord": [130.558, 31.560]},
    "47000": {"name": "沖縄県",  "coord": [127.681, 26.212]},
}

JS_LOGIC = r"""
// ============================================================
// MAP
// ============================================================
const map = new maplibregl.Map({
  container: 'map',
  style: {
    version: 8,
    sources: {
      gsi: {
        type: 'raster',
        tiles: ['https://cyberjapandata.gsi.go.jp/xyz/blank/{z}/{x}/{y}.png'],
        tileSize: 256,
        attribution: '<a href="https://maps.gsi.go.jp/development/ichiran.html" target="_blank">国土地理院</a>'
      }
    },
    layers: [{id:'gsi',type:'raster',source:'gsi',minzoom:0,maxzoom:18}]
  },
  center: [136.5, 37.0],
  zoom: 4.5,
  minZoom: 3,
  maxZoom: 12
});
map.addControl(new maplibregl.NavigationControl(), 'bottom-left');
map.addControl(new maplibregl.ScaleControl({unit:'metric'}), 'bottom-left');

// ============================================================
// CANVAS
// ============================================================
const cvs = document.getElementById('flow-canvas');
const ctx = cvs.getContext('2d');

function resizeCvs() {
  const c = map.getContainer();
  cvs.width = c.offsetWidth * (window.devicePixelRatio || 1);
  cvs.height = c.offsetHeight * (window.devicePixelRatio || 1);
  cvs.style.width = c.offsetWidth + 'px';
  cvs.style.height = c.offsetHeight + 'px';
  ctx.scale(window.devicePixelRatio || 1, window.devicePixelRatio || 1);
}
window.addEventListener('resize', resizeCvs);
map.on('resize', resizeCvs);

// ============================================================
// STATE
// ============================================================
let selPref = '13000';
let selYear = 'all';
let excludeTokyo = false;
let particles = [];
let activeFlows = [];

// ============================================================
// HELPERS
// ============================================================
function project(lngLat) {
  const p = map.project(lngLat);
  return {x: p.x, y: p.y};
}

function ctrlPt(p0, p2) {
  const mx = (p0.x+p2.x)/2, my = (p0.y+p2.y)/2;
  const dx = p2.x-p0.x, dy = p2.y-p0.y;
  const len = Math.sqrt(dx*dx+dy*dy)||1;
  const off = len*0.28;
  return {x: mx-(dy/len)*off, y: my+(dx/len)*off};
}

function bezPt(t, p0, p1, p2) {
  const m=1-t;
  return {x:m*m*p0.x+2*m*t*p1.x+t*t*p2.x, y:m*m*p0.y+2*m*t*p1.y+t*t*p2.y};
}

function fmt(n) { return n.toLocaleString('ja-JP')+'人'; }

// ============================================================
// DATA AGGREGATION  — net flows per other prefecture
// ============================================================
function getFlows() {
  const years = selYear==='all' ? ['2020','2021','2022','2023','2024','2025'] : [selYear];
  const ins = {}, outs = {};
  for (const yr of years) {
    for (const f of (FD[yr]||[])) {
      if (f.to===selPref && f.from!==selPref) ins[f.from]=(ins[f.from]||0)+f.count;
      else if (f.from===selPref && f.to!==selPref) outs[f.to]=(outs[f.to]||0)+f.count;
    }
  }
  const all = new Set([...Object.keys(ins), ...Object.keys(outs)]);
  return [...all].map(o=>({
    other: o,
    in: ins[o]||0,
    out: outs[o]||0,
    net: (ins[o]||0)-(outs[o]||0)
  })).filter(f=>f.net!==0 && !(excludeTokyo && f.other==='13000'));
}

function updateStats(flows) {
  const si = flows.reduce((s,f)=>s+f.in,0);
  const so = flows.reduce((s,f)=>s+f.out,0);
  const net = si-so;
  document.getElementById('si').textContent = fmt(si);
  document.getElementById('so').textContent = fmt(so);
  const el = document.getElementById('sn');
  el.textContent = (net>=0?'+':'')+net.toLocaleString('ja-JP')+'人';
  el.style.color = net>=0?'#1565C0':'#C62828';
  // Ranking
  const sorted = [...flows].sort((a,b)=>b.net-a.net);
  renderRank('rank-in',  sorted.filter(f=>f.net>0).slice(0,6), true);
  renderRank('rank-out', sorted.filter(f=>f.net<0).sort((a,b)=>a.net-b.net).slice(0,6), false);
}

function renderRank(id, flows, isIn) {
  const el = document.getElementById(id);
  if (!el||!flows.length) { if(el) el.innerHTML='<div style="color:#bbb;font-size:11px">データなし</div>'; return; }
  const maxAbs = Math.abs(flows[0].net);
  el.innerHTML = flows.map(f=>{
    const pct = Math.round(Math.abs(f.net)/maxAbs*100);
    const col = isIn?'#0A64E6':'#D21414';
    const nm = (PI[f.other]||{}).name||f.other;
    const sign = isIn?'+':'';
    return `<div style="margin-bottom:5px">
      <div style="display:flex;justify-content:space-between;font-size:11px;margin-bottom:2px">
        <span style="font-weight:500">${nm}</span>
        <span style="color:${col};font-weight:bold">${sign}${f.net.toLocaleString('ja-JP')}</span>
      </div>
      <div style="height:4px;background:#eee;border-radius:2px">
        <div style="width:${pct}%;height:4px;background:${col};border-radius:2px;transition:width .3s"></div>
      </div>
    </div>`;
  }).join('');
}

// ============================================================
// PARTICLES
// ============================================================
const MAX_P = 700;

function rebuildParticles(flows) {
  particles = [];
  if (!flows.length) { activeFlows=flows; return; }
  const total = flows.reduce((s,f)=>s+Math.abs(f.net),0);
  const mapped = flows.map(f=>({...f, np: Math.max(1, Math.round(Math.abs(f.net)/total*MAX_P))}));
  let sum = mapped.reduce((s,f)=>s+f.np,0);
  if (sum > MAX_P) { const r=MAX_P/sum; mapped.forEach(f=>f.np=Math.max(1,Math.round(f.np*r))); }
  activeFlows = flows;
  mapped.forEach((f,fi) => {
    for (let j=0;j<f.np;j++) particles.push({fi, t:j/f.np, spd:0.0012+Math.random()*0.0008});
  });
}

// ============================================================
// DRAWING
// ============================================================
function drawFrame() {
  const W = cvs.clientWidth, H = cvs.clientHeight;
  ctx.clearRect(0, 0, W, H);
  if (!activeFlows.length) return;

  const maxN = Math.max(...activeFlows.map(f=>Math.abs(f.net)));
  // 1. Lines — one arrow per other-pref showing net direction
  for (const f of activeFlows) {
    if (!PI[f.other]||!PI[selPref]) continue;
    const isIn = f.net > 0;
    // arrow travels FROM source TO destination
    const fp = isIn ? project(PI[f.other].coord) : project(PI[selPref].coord);
    const tp = isIn ? project(PI[selPref].coord) : project(PI[f.other].coord);
    const cp = ctrlPt(fp, tp);
    const absN = Math.abs(f.net);
    const w = 0.8 + (absN/maxN)*8;
    const a = 0.45 + (absN/maxN)*0.5;
    const col = isIn ? `rgba(10,100,230,${a})` : `rgba(210,20,20,${a})`;
    ctx.beginPath();
    ctx.moveTo(fp.x, fp.y);
    ctx.quadraticCurveTo(cp.x, cp.y, tp.x, tp.y);
    ctx.strokeStyle = col;
    ctx.lineWidth = w;
    ctx.lineCap = 'round';
    ctx.stroke();
    // arrowhead at tp
    const adx=tp.x-cp.x, ady=tp.y-cp.y, al=Math.sqrt(adx*adx+ady*ady)||1;
    const ax=adx/al, ay=ady/al;
    const as=Math.max(4,w*2.8), ang=Math.PI/6;
    ctx.beginPath();
    ctx.moveTo(tp.x, tp.y);
    ctx.lineTo(tp.x-as*(ax*Math.cos(ang)-ay*Math.sin(ang)), tp.y-as*(ay*Math.cos(ang)+ax*Math.sin(ang)));
    ctx.lineTo(tp.x-as*(ax*Math.cos(ang)+ay*Math.sin(ang)), tp.y-as*(ay*Math.cos(ang)-ax*Math.sin(ang)));
    ctx.closePath();
    ctx.fillStyle = col;
    ctx.fill();
  }

  // 2. Markers (other prefs)
  for (const f of activeFlows) {
    if (!PI[f.other]) continue;
    const pt = project(PI[f.other].coord);
    const r = 3 + (Math.abs(f.net)/maxN)*5;
    ctx.beginPath();
    ctx.arc(pt.x, pt.y, r, 0, Math.PI*2);
    ctx.fillStyle = f.net>0 ? 'rgba(10,100,230,0.9)' : 'rgba(210,20,20,0.9)';
    ctx.strokeStyle = 'rgba(255,255,255,0.9)';
    ctx.lineWidth = 1.2;
    ctx.fill();
    ctx.stroke();
  }

  // 3. Selected pref marker
  if (PI[selPref]) {
    const sp = project(PI[selPref].coord);
    ctx.beginPath();
    ctx.arc(sp.x, sp.y, 11, 0, Math.PI*2);
    ctx.fillStyle = 'rgba(255,215,0,0.95)';
    ctx.strokeStyle = '#333';
    ctx.lineWidth = 2;
    ctx.fill();
    ctx.stroke();
    ctx.fillStyle = '#333';
    ctx.font = 'bold 9px sans-serif';
    ctx.textAlign = 'center';
    ctx.textBaseline = 'middle';
    const nm = PI[selPref].name;
    ctx.fillText(nm.length>3 ? nm.slice(0,-1) : nm, sp.x, sp.y);
  }

  // 4. Particles — flow along net direction
  for (const p of particles) {
    const f = activeFlows[p.fi];
    if (!f||!PI[f.other]||!PI[selPref]) continue;
    const isIn = f.net > 0;
    const fp = isIn ? project(PI[f.other].coord) : project(PI[selPref].coord);
    const tp = isIn ? project(PI[selPref].coord) : project(PI[f.other].coord);
    const cp = ctrlPt(fp, tp);
    const pos = bezPt(p.t, fp, cp, tp);
    const sz = 1.5 + (Math.abs(f.net)/maxN)*2.5;
    ctx.beginPath();
    ctx.arc(pos.x, pos.y, sz, 0, Math.PI*2);
    ctx.fillStyle = isIn ? '#1976D2' : '#C62828';
    ctx.fill();
  }
}

// ============================================================
// ANIMATION LOOP
// ============================================================
function loop() {
  requestAnimationFrame(loop);
  for (const p of particles) { p.t+=p.spd; if(p.t>1)p.t-=1; }
  drawFrame();
}

// ============================================================
// TOOLTIP
// ============================================================
const tip = document.getElementById('tip');
document.getElementById('map').addEventListener('mousemove', e => {
  const r = e.currentTarget.getBoundingClientRect();
  const mx = e.clientX-r.left, my = e.clientY-r.top;
  let best=null, bestD=22;
  // Check selected pref marker
  if (PI[selPref]) {
    const sp = project(PI[selPref].coord);
    const d = Math.hypot(sp.x-mx, sp.y-my);
    if (d<18) {
      const flows = getFlows();
      const si2 = flows.filter(f=>f.isInflow).reduce((s,f)=>s+f.count,0);
      const so2 = flows.filter(f=>!f.isInflow).reduce((s,f)=>s+f.count,0);
      tip.innerHTML=`<strong>${PI[selPref].name}</strong><br>転入: <span style="color:#4FC3F7">${fmt(si2)}</span><br>転出: <span style="color:#FF8A65">${fmt(so2)}</span>`;
      tip.style.display='block';
      tip.style.left=(e.clientX+14)+'px'; tip.style.top=(e.clientY-10)+'px';
      document.body.style.cursor='pointer';
      return;
    }
  }
  for (const f of activeFlows) {
    if (!PI[f.other]) continue;
    const pt = project(PI[f.other].coord);
    const d = Math.hypot(pt.x-mx, pt.y-my);
    if (d<bestD) { bestD=d; best=f; }
  }
  if (best) {
    const f = best;
    const nm = PI[f.other].name;
    const yrLabel = selYear==='all'?'2020-2025累計':selYear+'年';
    const isIn = f.net>0;
    const dir = isIn ? `${nm} → ${PI[selPref].name}` : `${PI[selPref].name} → ${nm}`;
    const col = isIn?'#4FC3F7':'#FF8A65';
    const sign = isIn?'+':'';
    tip.innerHTML=`<strong>${nm}</strong><br>
      <span style="color:#aaa;font-size:11px">${dir}</span><br>
      転入超過: <span style="color:${col};font-weight:bold">${sign}${f.net.toLocaleString('ja-JP')}人</span><br>
      <span style="color:#999;font-size:10px">転入 ${f.in.toLocaleString('ja-JP')} / 転出 ${f.out.toLocaleString('ja-JP')} (${yrLabel})</span>`;
    tip.style.display='block';
    tip.style.left=(e.clientX+14)+'px'; tip.style.top=(e.clientY-10)+'px';
    document.body.style.cursor='default';
  } else {
    tip.style.display='none';
    document.body.style.cursor='';
  }
});
document.getElementById('map').addEventListener('mouseleave', ()=>{ tip.style.display='none'; });

// Click on map: select clicked prefecture
document.getElementById('map').addEventListener('click', e => {
  const r = e.currentTarget.getBoundingClientRect();
  const mx = e.clientX-r.left, my = e.clientY-r.top;
  let best=null, bestD=25;
  for (const code of Object.keys(PI)) {
    const pt = project(PI[code].coord);
    const d = Math.hypot(pt.x-mx, pt.y-my);
    if (d<bestD) { bestD=d; best=code; }
  }
  if (best && best!==selPref) {
    selPref=best;
    document.getElementById('ps').value=best;
    refresh();
  }
});

// ============================================================
// UI
// ============================================================
const ps = document.getElementById('ps');
Object.entries(PI).sort((a,b)=>a[0].localeCompare(b[0])).forEach(([code,info])=>{
  const o=document.createElement('option');
  o.value=code; o.textContent=info.name;
  if(code===selPref)o.selected=true;
  ps.appendChild(o);
});
ps.addEventListener('change', ()=>{ selPref=ps.value; refresh(); });

document.querySelectorAll('.yb').forEach(b=>b.addEventListener('click',()=>{
  document.querySelectorAll('.yb').forEach(x=>x.classList.remove('on'));
  b.classList.add('on'); selYear=b.dataset.y; refresh();
}));

document.getElementById('ex-tokyo').addEventListener('change', e=>{
  excludeTokyo = e.target.checked; refresh();
});


// ============================================================
// REFRESH & INIT
// ============================================================
function refresh() {
  const flows = getFlows();
  updateStats(flows);
  rebuildParticles(flows);
}

map.on('load', ()=>{ resizeCvs(); refresh(); loop(); });
"""

HTML_TEMPLATE = '''<!DOCTYPE html>
<html lang="ja">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>都道府県間 転出・転入フローマップ</title>
<link href="https://unpkg.com/maplibre-gl@4.1.2/dist/maplibre-gl.css" rel="stylesheet">
<script src="https://unpkg.com/maplibre-gl@4.1.2/dist/maplibre-gl.js"></script>
<style>
*{margin:0;padding:0;box-sizing:border-box}
body{font-family:'Hiragino Kaku Gothic ProN','Meiryo','Yu Gothic',sans-serif;overflow:hidden}
#map{width:100vw;height:100vh}
#flow-canvas{position:absolute;top:0;left:0;pointer-events:none;z-index:1}
#controls{position:absolute;top:14px;left:14px;background:rgba(255,255,255,.96);border-radius:12px;padding:15px 16px;min-width:235px;box-shadow:0 2px 14px rgba(0,0,0,.15);z-index:10}
#title{font-size:14px;font-weight:bold;color:#1a1a2e;margin-bottom:0;line-height:1.5;border-bottom:1px solid #eee;padding-bottom:9px;display:flex;justify-content:space-between;align-items:flex-start;cursor:pointer;user-select:none}
#ctrl-body{margin-top:12px}
.chev{font-size:12px;color:#aaa;flex-shrink:0;margin-left:8px;margin-top:2px}
.cg{margin-bottom:10px}
.cl{font-size:10px;color:#888;font-weight:bold;text-transform:uppercase;letter-spacing:.6px;margin-bottom:4px}
select#ps{width:100%;padding:6px 9px;border:1.5px solid #ddd;border-radius:7px;font-size:13px;background:#fff;cursor:pointer;outline:none}
select#ps:focus{border-color:#5b80c4}
.yb-wrap{display:flex;gap:3px;flex-wrap:wrap}
.yb{flex:1;min-width:38px;padding:5px 4px;border:1.5px solid #ddd;border-radius:6px;font-size:11px;background:#fff;cursor:pointer;text-align:center;transition:all .12s;color:#555}
.yb.on{background:#1a1a2e;color:#fff;border-color:#1a1a2e}
.yb:hover:not(.on){background:#f5f5f5}
#controls{max-height:calc(100vh - 30px);overflow-y:auto}
#stats{margin-top:10px;padding-top:10px;border-top:1px solid #eee;font-size:12px}
.sr{display:flex;justify-content:space-between;align-items:center;margin-bottom:4px}
.sl{color:#777}
.si{color:#1565C0;font-weight:bold;font-size:13px}
.so{color:#C62828;font-weight:bold;font-size:13px}
.sn{font-weight:bold;font-size:13px}
#legend{position:absolute;bottom:36px;right:14px;background:rgba(255,255,255,.95);border-radius:10px;padding:11px 14px;font-size:11px;box-shadow:0 2px 8px rgba(0,0,0,.12);z-index:10;min-width:170px}
.lt{font-weight:bold;color:#333;margin-bottom:0;font-size:12px;display:flex;justify-content:space-between;align-items:center;cursor:pointer;user-select:none}
#leg-body{margin-top:7px}
.li{display:flex;align-items:center;margin-bottom:5px;gap:7px;color:#444}
.ll{height:3px;border-radius:2px}
.ld{width:8px;height:8px;border-radius:50%;flex-shrink:0}
#tip{position:fixed;background:rgba(20,20,40,.9);color:#fff;border-radius:8px;padding:8px 12px;font-size:12px;pointer-events:none;z-index:30;display:none;line-height:1.7;max-width:220px;backdrop-filter:blur(4px)}
</style>
</head>
<body>
<div id="map"></div>
<canvas id="flow-canvas"></canvas>
<div id="controls">
  <div id="title" onclick="toggleCtrl()">
    <span>都道府県間<br>転出・転入フローマップ</span>
    <span class="chev" id="ctrl-chevron">▲</span>
  </div>
  <div id="ctrl-body">
    <div class="cg">
      <div class="cl">都道府県</div>
      <select id="ps"></select>
    </div>
    <div class="cg">
      <div class="cl">年度</div>
      <div class="yb-wrap">
        <button class="yb on" data-y="all">全期間</button>
        <button class="yb" data-y="2020">2020</button>
        <button class="yb" data-y="2021">2021</button>
        <button class="yb" data-y="2022">2022</button>
        <button class="yb" data-y="2023">2023</button>
        <button class="yb" data-y="2024">2024</button>
        <button class="yb" data-y="2025">2025</button>
      </div>
    </div>
    <div class="cg">
      <label style="display:flex;align-items:center;gap:8px;cursor:pointer;font-size:13px;color:#333">
        <input type="checkbox" id="ex-tokyo" style="width:15px;height:15px;cursor:pointer;accent-color:#1a1a2e">
        東京都を除外する
      </label>
    </div>
    <div id="stats">
      <div class="sr"><span class="sl">転入合計</span><span class="si" id="si">-</span></div>
      <div class="sr"><span class="sl">転出合計</span><span class="so" id="so">-</span></div>
      <div class="sr"><span class="sl">転入超過数</span><span class="sn" id="sn">-</span></div>
    </div>
    <div class="cg" style="margin-top:12px;padding-top:10px;border-top:1px solid #eee">
      <div class="cl" style="color:#1565C0">転入超過 上位</div>
      <div id="rank-in"></div>
    </div>
    <div class="cg">
      <div class="cl" style="color:#C62828">転出超過 上位</div>
      <div id="rank-out"></div>
    </div>
  </div>
</div>
<div id="legend">
  <div class="lt" onclick="toggleLeg()">
    <span>凡例</span>
    <span class="chev" id="leg-chevron">▲</span>
  </div>
  <div id="leg-body">
    <div class="li"><div class="ll" style="width:30px;background:#0A64E6"></div>転入超過（差分がプラス）</div>
    <div class="li"><div class="ll" style="width:30px;background:#D21414"></div>転出超過（差分がマイナス）</div>
    <div class="li">
      <div style="display:flex;align-items:center;gap:1px">
        <div style="width:2px;height:5px;background:#888;border-radius:1px"></div>
        <div style="width:4px;height:5px;background:#888;border-radius:1px"></div>
        <div style="width:7px;height:5px;background:#888;border-radius:1px"></div>
      </div>
      線の太さ＝人数規模
    </div>
    <div class="li"><div class="ld" style="background:#4FC3F7"></div>転入粒子</div>
    <div class="li"><div class="ld" style="background:#FF8A65"></div>転出粒子</div>
    <div class="li"><div class="ld" style="background:#FFD700;border:1px solid #888"></div>選択中の都道府県</div>
    <div style="margin-top:8px;padding-top:8px;border-top:1px solid #eee;font-size:10px;color:#aaa">
      出典: 総務省住民基本台帳人口移動報告<br>
      e-Stat API / 国土地理院地図タイル
    </div>
  </div>
</div>
<div id="tip"></div>

<div id="modal-overlay" style="position:fixed;inset:0;background:rgba(0,0,0,.45);z-index:100;display:flex;align-items:center;justify-content:center;backdrop-filter:blur(3px)">
  <div style="background:#fff;border-radius:14px;padding:32px 36px;max-width:420px;width:90%;box-shadow:0 8px 32px rgba(0,0,0,.18);line-height:1.7">
    <div style="font-size:17px;font-weight:bold;color:#1a1a2e;margin-bottom:14px">都道府県間 転出・転入フローマップ</div>
    <div style="font-size:13px;color:#444;margin-bottom:18px">
      本アプリは<strong>デモ目的</strong>で作成されています。<br>
      データは <a href="https://www.e-stat.go.jp/" target="_blank" style="color:#0A64E6">e-Stat（政府統計の総合窓口）</a> の
      住民基本台帳人口移動報告（2020〜2025年）を使用していますが、
      データの加工・集計における正確性は保証しません。
      意思決定等への利用はお控えください。
    </div>
    <div style="font-size:12px;color:#888;margin-bottom:22px;padding-top:14px;border-top:1px solid #eee">
      Powered by <a href="https://www.pons-llc.com/" target="_blank" style="color:#1a1a2e;font-weight:bold">合同会社 Pons</a>
    </div>
    <button onclick="document.getElementById('modal-overlay').style.display='none'"
      style="width:100%;padding:10px;background:#1a1a2e;color:#fff;border:none;border-radius:8px;font-size:14px;cursor:pointer;font-weight:bold">
      同意して使用する
    </button>
  </div>
</div>
<script>
function toggleCtrl(){var b=document.getElementById('ctrl-body'),c=document.getElementById('ctrl-chevron'),o=b.style.display!=='none';b.style.display=o?'none':'';c.textContent=o?'▼':'▲';}
function toggleLeg(){var b=document.getElementById('leg-body'),c=document.getElementById('leg-chevron'),o=b.style.display!=='none';b.style.display=o?'none':'';c.textContent=o?'▼':'▲';}
if(window.innerWidth<640){document.getElementById('ctrl-body').style.display='none';document.getElementById('ctrl-chevron').textContent='▼';document.getElementById('leg-body').style.display='none';document.getElementById('leg-chevron').textContent='▼';}
</script>
<script>
const PI={PREF_INFO_JSON};
const FD=FLOW_DATA_JSON;
MAIN_JS
</script>
</body>
</html>
'''

pref_json = json.dumps(PREF_INFO, ensure_ascii=False, separators=(',', ':'))
# Remove outer braces since we embed inline
pref_json = pref_json[1:-1]  # strip { }

flow_json = json.dumps(flow_data, ensure_ascii=False, separators=(',', ':'))

html = HTML_TEMPLATE.replace('PREF_INFO_JSON', pref_json)
html = html.replace('FLOW_DATA_JSON', flow_json)
html = html.replace('MAIN_JS', JS_LOGIC)

out = BASE / 'build' / 'index.html'
out.parent.mkdir(exist_ok=True)
out.write_text(html, encoding='utf-8')
print(f'Written: {out} ({out.stat().st_size:,} bytes)')
