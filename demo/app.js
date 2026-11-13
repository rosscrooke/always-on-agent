(() => {
'use strict';

const TRACK = [
  [37.7955,-122.3937],[37.7990,-122.3972],[37.8030,-122.4010],[37.8016,-122.4040],
  [37.8024,-122.4058],[37.8008,-122.4098],[37.7983,-122.4076],[37.7976,-122.4066],
  [37.7955,-122.4060],[37.7941,-122.4078],[37.7908,-122.4058],[37.7880,-122.4075]
];
const CLAY = '#D97757', GOLD = '#F5C26B';
const $ = (s) => document.querySelector(s);
const esc = (s) => String(s).replace(/[&<>"']/g, (c) => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const buddyImg = () => '<img src="buddy.png" alt="BTW Buddy">';

let walk = null, stops = [], idx = -1, token = 0;
let speechOn = false, autoTimer = null, hintTimer = null;
let map, youMarker, routeDone, routeRest, radiusCircle, pinLayer;

/* ---------- stage scaling ---------- */
const stage = $('#stage');
let scale = 1;
function fit() {
  scale = Math.min(innerWidth / 1440, innerHeight / 810);
  const x = (innerWidth - 1440 * scale) / 2, y = (innerHeight - 810 * scale) / 2;
  stage.style.transform = `translate(${x}px,${y}px) scale(${scale})`;
  updateConnector();
}

/* ---------- data ---------- */
async function load() {
  let sample = false;
  try {
    const r = await fetch('walk.json', { cache: 'no-store' });
    if (!r.ok) throw new Error(r.status);
    walk = await r.json();
  } catch (e) {
    const r = await fetch('walk.sample.json');
    walk = await r.json();
    sample = true;
  }
  stops = walk.stops.slice();
  if (sample) badge('sample data');
}
function badge(text, cls, id) {
  let el = id && document.getElementById(id);
  if (!el) {
    el = document.createElement('div');
    el.className = 'badge'; if (id) el.id = id;
    $('#badges').appendChild(el);
  }
  if (cls) el.classList.add(cls);
  el.innerHTML = text;
  return el;
}
const timeFor = (seq) => {
  const m = 13 * 60 + seq * 25, h = Math.floor(m / 60) % 24;
  return `${h % 12 || 12}:${String(m % 60).padStart(2, '0')} ${h >= 12 ? 'PM' : 'AM'}`;
};
const trackIndex = (stop) => {
  const i = TRACK.findIndex((p) => Math.abs(p[0] - stop.lat) < 1e-5 && Math.abs(p[1] - stop.lon) < 1e-5);
  return i >= 0 ? i : Math.min(Math.max(stop.seq, 0), TRACK.length - 1);
};

/* ---------- map ---------- */
const ZOOM = 16;
function initMap() {
  map = L.map('map', {
    zoomControl: false, attributionControl: true, dragging: false, scrollWheelZoom: false,
    doubleClickZoom: false, boxZoom: false, keyboard: false, touchZoom: false, zoomSnap: 0.5
  });
  map.attributionControl.setPrefix(false);
  // Esri Dark Gray Canvas: no API key needed (CARTO basemaps now require one). Max zoom 16.
  L.tileLayer('https://services.arcgisonline.com/ArcGIS/rest/services/Canvas/World_Dark_Gray_Base/MapServer/tile/{z}/{y}/{x}', {
    attribution: 'Tiles &copy; Esri &mdash; Esri, HERE, Garmin, &copy; OpenStreetMap contributors',
    maxZoom: 16
  }).addTo(map);
  const first = stops[0];
  map.setView([first.lat, first.lon], ZOOM, { animate: false });
  routeRest = L.polyline(TRACK, { color: CLAY, weight: 3, opacity: .35, dashArray: '6 8' }).addTo(map);
  routeDone = L.polyline([], { color: CLAY, weight: 4, opacity: .95 }).addTo(map);
  radiusCircle = L.circle([first.lat, first.lon], { radius: walk.radius_m || 500, color: GOLD, weight: 1.5, dashArray: '6 6', fillColor: GOLD, fillOpacity: .03, interactive: false }).addTo(map);
  pinLayer = L.layerGroup().addTo(map);
  youMarker = L.marker([first.lat, first.lon], {
    icon: L.divIcon({ className: '', iconSize: [0, 0], html: '<div class="you"><div class="halo"></div><div class="dot"></div><div class="lbl">You</div></div>' }),
    interactive: false, zIndexOffset: 1000
  }).addTo(map);
  map.on('move zoom moveend', updateConnector);
}

const COMPASS = { N: 0, NE: 45, E: 90, SE: 135, S: 180, SW: 225, W: 270, NW: 315 };
function offsetLatLon(lat, lon, m, dir) {
  const a = ((COMPASS[dir] ?? 0) * Math.PI) / 180;
  return [lat + (m * Math.cos(a)) / 111320, lon + (m * Math.sin(a)) / (111320 * Math.cos((lat * Math.PI) / 180))];
}
const distText = (p) => (p.direction === 'here' ? 'right here' : `${p.distance_m} m ${p.direction}`);

const PIN_SVG = '<svg class="pin" width="24" height="32" viewBox="0 0 24 32"><path d="M12 1C6 1 1.5 5.4 1.5 11c0 7.6 10.5 19.5 10.5 19.5S22.5 18.6 22.5 11C22.5 5.4 18 1 12 1z" fill="#F5C26B" stroke="#0E1117" stroke-width="1.5"/><circle cx="12" cy="11" r="4" fill="#0E1117"/></svg>';

// Lay out label chips so close pins don't overlap: chips go right of pins east of you and left
// of pins west of you, and chips on the same side are pushed apart to at least CHIP_GAP px.
const CHIP_GAP = 30;
function chipLayout(stop, lls) {
  const you = map.latLngToContainerPoint([stop.lat, stop.lon]);
  const items = lls.map((ll, i) => {
    const pt = map.latLngToContainerPoint(ll);
    return { i, pt, side: pt.x >= you.x ? 'right' : 'left', y: pt.y - 16 };
  });
  const out = [];
  ['right', 'left'].forEach(side => {
    const col = items.filter(it => it.side === side).sort((a, b) => a.y - b.y);
    for (let k = 1; k < col.length; k++) col[k].y = Math.max(col[k].y, col[k - 1].y + CHIP_GAP);
    col.forEach(it => { out[it.i] = [side, [side === 'right' ? 12 : -12, Math.round(it.y - it.pt.y)]]; });
  });
  return out;
}

function dropPins(stop, tk) {
  pinLayer.clearLayers();
  const places = stop.places || [];
  const lls = places.map(p => (p.lat == null || p.lon == null)
    ? offsetLatLon(stop.lat, stop.lon, p.distance_m || 0, p.direction) : [p.lat, p.lon]);
  const layout = chipLayout(stop, lls);
  places.forEach((p, i) => {
    setTimeout(() => {
      if (tk !== token) return;
      const ll = lls[i];
      const m = L.marker(ll, {
        icon: L.divIcon({ className: '', html: PIN_SVG, iconSize: [24, 32], iconAnchor: [12, 30] }),
        interactive: false, zIndexOffset: 500
      });
      const [dir, off] = layout[i];
      m.bindTooltip(`<span class="t">${esc(p.title)}</span> · <em>${esc(distText(p))}</em>`, { permanent: true, direction: dir, offset: off, className: 'chip' });
      m.addTo(pinLayer);
    }, 350 * i);
  });
}

function updateMap(stop, first) {
  const ti = trackIndex(stop);
  routeDone.setLatLngs(TRACK.slice(0, ti + 1));
  radiusCircle.setLatLng([stop.lat, stop.lon]);
  radiusCircle.setRadius(walk.radius_m || 500);
  youMarker.setLatLng([stop.lat, stop.lon]);
  pinLayer.clearLayers();
  const tk = ++token;
  if (first) { map.setView([stop.lat, stop.lon], ZOOM, { animate: false }); setTimeout(() => dropPins(stop, tk), 600); return; }
  let done = false;
  const go = () => { if (done || tk !== token) return; done = true; dropPins(stop, tk); };
  map.once('moveend', () => setTimeout(go, 150));
  setTimeout(go, 2600);
  map.flyTo([stop.lat, stop.lon], ZOOM, { duration: 1.8 });
}

/* ---------- inset ---------- */
function renderInset(stop) {
  const W = 210, H = 130, pad = 14;
  const lats = TRACK.map((p) => p[0]), lons = TRACK.map((p) => p[1]);
  const minLa = Math.min(...lats), maxLa = Math.max(...lats), minLo = Math.min(...lons), maxLo = Math.max(...lons);
  const k = Math.cos(((minLa + maxLa) / 2) * Math.PI / 180);
  const w = (maxLo - minLo) * k, h = maxLa - minLa;
  const s = Math.min((W - 2 * pad) / w, (H - 2 * pad) / h);
  const ox = (W - w * s) / 2, oy = (H - h * s) / 2;
  const pt = (p) => [(ox + (p[1] - minLo) * k * s).toFixed(1), (oy + (maxLa - p[0]) * s).toFixed(1)];
  const ti = trackIndex(stop);
  const line = (arr) => arr.map((p) => pt(p).join(',')).join(' ');
  const cur = pt([stop.lat, stop.lon]);
  $('#inset').innerHTML =
    `<polyline points="${line(TRACK.slice(ti))}" fill="none" stroke="#7b8394" stroke-width="2" stroke-dasharray="4 4" stroke-linecap="round"/>` +
    `<polyline points="${line(TRACK.slice(0, ti + 1))}" fill="none" stroke="${CLAY}" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"/>` +
    `<circle cx="${cur[0]}" cy="${cur[1]}" r="7" fill="#fff" stroke="${CLAY}" stroke-width="3.5"/>`;
}

/* ---------- phone ---------- */
function renderClock(stop) {
  const [t, ap] = (stop.time || '').split(' ');
  $('#clock-time').textContent = t || '';
  $('#clock-ampm').textContent = ap || '';
}
function renderStack(i) {
  const stack = $('#stack');
  const before = {};
  stack.querySelectorAll('[data-i]').forEach((el) => { before[el.dataset.i] = el.getBoundingClientRect().top; });
  const stop = stops[i], p0 = (stop.places || [])[0];
  let html = `<div class="notif new" data-i="${i}">
    <div class="nh"><div class="appicon">${buddyImg()}</div><b>BTW Buddy</b><span>now</span></div>
    <div class="nt">${esc(stop.notification.title)}</div>
    <div class="nb">${esc(stop.notification.body)}</div>
    <div class="btns"><a class="btn read" ${p0 ? `href="${esc(p0.url)}" target="_blank" rel="noopener"` : ''}>Read more</a><button class="btn hear" id="hear">Hear it</button></div>
  </div>`;
  for (let n = 1; n <= 3 && i - n >= 0; n++) {
    const s = stops[i - n], pl = s.places || [];
    const t = pl.length ? (pl.length > 1 ? `${pl[0].title} and ${pl.length - 1} more` : pl[0].title) : s.notification.title;
    html += `<div class="notif old o${n}" data-i="${i - n}" style="opacity:${[0, .9, .62, .36][n]}"><div class="ot">${esc(t)}</div><div class="os">${esc(s.label)} · ${esc(s.time)}</div></div>`;
  }
  stack.innerHTML = html;
  $('#hear').onclick = () => speakStop(stop);
  stack.querySelectorAll('.old').forEach((el) => {
    const prev = before[el.dataset.i];
    if (prev == null) return;
    const d = (prev - el.getBoundingClientRect().top) / scale;
    if (!d) return;
    el.style.transition = 'none'; el.style.transform = `translateY(${d}px)`;
    requestAnimationFrame(() => requestAnimationFrame(() => {
      el.style.transition = 'transform .7s cubic-bezier(.34,1.3,.64,1)'; el.style.transform = '';
    }));
  });
}

/* ---------- connector ---------- */
function updateConnector() {
  const path = $('#conn-path');
  if (!map || !youMarker) return;
  const card = document.querySelector('.notif.new');
  if (!card) { path.classList.add('hide'); return; }
  const sr = stage.getBoundingClientRect();
  const cr = card.getBoundingClientRect();
  // un-animated geometry: use layout position so the spring doesn't wobble the start
  const x1 = (cr.right - sr.left) / scale, y1 = (cr.top - sr.top + cr.height / 2) / scale;
  const mp = map.latLngToContainerPoint(youMarker.getLatLng());
  const x2 = 540 + mp.x, y2 = 28 + mp.y;
  const inside = mp.x > 0 && mp.x < 872 && mp.y > 0 && mp.y < 754;
  path.classList.toggle('hide', !inside);
  const dx = Math.max(40, (x2 - x1) * 0.5);
  path.setAttribute('d', `M${x1.toFixed(1)} ${y1.toFixed(1)} C${(x1 + dx).toFixed(1)} ${y1.toFixed(1)} ${(x2 - dx).toFixed(1)} ${y2.toFixed(1)} ${x2.toFixed(1)} ${y2.toFixed(1)}`);
}
function trackConnector(ms) {
  const end = performance.now() + ms;
  const f = () => { updateConnector(); if (performance.now() < end) requestAnimationFrame(f); };
  f();
}

/* ---------- show stop ---------- */
function showStop(i, opts = {}) {
  if (i < 0 || i >= stops.length) return;
  const first = idx < 0;
  idx = i;
  const stop = stops[i];
  renderClock(stop);
  renderStack(i);
  const ti = trackIndex(stop);
  $('#coords').textContent = `${stop.lat.toFixed(4)}, ${stop.lon.toFixed(4)}`;
  $('#trigmeta').textContent = `${stop.time} · stop ${stop.seq + 1} of ${TRACK.length} · ${(stop.places || []).length} places within ${walk.radius_m || 500} m`;
  renderInset(stop);
  updateMap(stop, first);
  trackConnector(2600);
  if (speechOn && !opts.silent) speakStop(stop);
}
const next = () => { if (idx < stops.length - 1) showStop(idx + 1); else stopAuto(); };
const prev = () => showStop(idx - 1);
const restart = () => { speechSynthesis.cancel(); showStop(0); };

/* ---------- speech ---------- */
function speakStop(stop) {
  if (!('speechSynthesis' in window)) return;
  const p0 = (stop.places || [])[0];
  const u = new SpeechSynthesisUtterance(`${stop.notification.title}. ${p0 ? p0.snippet : stop.notification.body}`);
  const vs = speechSynthesis.getVoices();
  const v = vs.find((x) => x.lang === 'en-US') || vs.find((x) => /^en/i.test(x.lang));
  if (v) { u.voice = v; u.lang = v.lang; } else u.lang = 'en-US';
  speechSynthesis.cancel();
  speechSynthesis.speak(u);
}

/* ---------- autoplay & hint ---------- */
function startAuto() { stopAuto(); autoTimer = setInterval(next, 8000); status(); }
function stopAuto() { if (autoTimer) clearInterval(autoTimer); autoTimer = null; status(); }
function toggleAuto() { autoTimer ? stopAuto() : startAuto(); }
function status() {
  const el = $('#hint'); if (!el) return;
  el.innerHTML = `<kbd>&rarr;</kbd>/<kbd>Space</kbd> next &nbsp; <kbd>&larr;</kbd> back &nbsp; <kbd>A</kbd> autoplay ${autoTimer ? 'ON' : 'off'} &nbsp; <kbd>S</kbd> speech ${speechOn ? 'ON' : 'off'} &nbsp; <kbd>R</kbd> restart`;
  el.classList.remove('gone');
  clearTimeout(hintTimer);
  hintTimer = setTimeout(() => el.classList.add('gone'), 4000);
}
addEventListener('keydown', (e) => {
  if (e.metaKey || e.ctrlKey || e.altKey) return;
  const k = e.key.toLowerCase();
  if (k === 'arrowright' || k === ' ') { e.preventDefault(); next(); }
  else if (k === 'arrowleft') { e.preventDefault(); prev(); }
  else if (k === 'a') toggleAuto();
  else if (k === 's') { speechOn = !speechOn; if (!speechOn) speechSynthesis.cancel(); status(); }
  else if (k === 'r') restart();
});
addEventListener('resize', fit);

/* ---------- live mode (GitHub issue comments) ---------- */
function parseComment(body) {
  const h = body.match(/###\s*.*?Stop\s+(\d+)\s*\/\s*(\d+):\s*(.+)/);
  const lines = body.split(/\r?\n/);
  const places = [];
  for (let n = 0; n < lines.length; n++) {
    const m = lines[n].match(/^\s*-\s*\*\*\[(.+?)\]\((.+?)\)\*\*\s*·\s*(.+?)\s*$/);
    if (!m) continue;
    let snippet = '';
    for (let j = n + 1; j < lines.length; j++) {
      if (!lines[j].trim()) continue;
      if (/^\s*-\s*\*\*\[/.test(lines[j])) break;
      snippet = lines[j].trim().replace(/^[>_*\s]+|[_*\s]+$/g, '');
      break;
    }
    const dm = m[3].match(/(\d+)\s*m\b\s*([NSEW]{1,2})?/i);
    const here = /here/i.test(m[3]) || (dm && !dm[2]);
    places.push({ title: m[1], url: m[2], distance_m: dm ? +dm[1] : 0, direction: here ? 'here' : (dm[2] || '').toUpperCase(), snippet });
  }
  return { label: h ? h[3].trim() : '', places };
}
function startLive(repo, issue) {
  badge('LIVE · from GitHub<small id="live-note"></small>', 'live', 'live-badge');
  let lastK = null;
  const note = (t) => { const n = $('#live-note'); if (n) n.textContent = t; };
  const poll = async () => {
    try {
      const r = await fetch(`https://api.github.com/repos/${repo}/issues/${issue}/comments?per_page=100`);
      if (!r.ok) throw new Error(r.status);
      const cs = await r.json();
      note('');
      for (let n = cs.length - 1; n >= 0; n--) {
        const m = (cs[n].body || '').match(/<!--\s*btw-stop:(\d+)\s*-->/);
        if (!m) continue;
        const K = +m[1];
        if (K !== lastK) { lastK = K; applyLive(K, parseComment(cs[n].body)); }
        break;
      }
    } catch (e) { note('retrying…'); }
  };
  poll(); setInterval(poll, 15000);
}
function applyLive(K, parsed) {
  let i = stops.findIndex((s) => s.seq === K);
  const base = i >= 0 ? stops[i] : { seq: K, label: parsed.label, lat: TRACK[K][0], lon: TRACK[K][1], time: timeFor(K), places: [] };
  const label = parsed.label || base.label;
  const places = parsed.places.map((p) => {
    const w = (base.places || []).find((x) => x.title === p.title);
    return Object.assign({}, p, w && w.lat != null ? { lat: w.lat, lon: w.lon } : {});
  });
  const body = (places[0] && places[0].snippet || base.notification && base.notification.body || '').slice(0, 140);
  const stop = Object.assign({}, base, { label, places: places.length ? places : base.places,
    notification: { title: `By the way, you're at ${label}`, body } });
  if (i < 0) { stops.push(stop); stops.sort((a, b) => a.seq - b.seq); i = stops.indexOf(stop); } else stops[i] = stop;
  showStop(i);
}

/* ---------- boot ---------- */
(async () => {
  fit();
  $('#thinker').innerHTML = buddyImg();
  await load();
  initMap();
  fit();
  const q = new URLSearchParams(location.search);
  const start = Math.max(0, stops.findIndex(s => String(s.seq) === q.get('stop')));
  showStop(start);
  status();
  if (speechSynthesis) speechSynthesis.getVoices();
  if (q.get('repo') && q.get('issue')) startLive(q.get('repo'), q.get('issue'));
})();
})();
