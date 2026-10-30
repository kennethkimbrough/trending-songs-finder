// Renders site/chart.json, written by `python main.py export`. All the comparisons are
// computed (and tested) in Python; this file only draws them.

const $ = (s) => document.querySelector(s);
const esc = (s) => String(s ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" })[c]);
const fmtDate = (iso) => new Date(iso.length > 10 ? iso : `${iso}T12:00:00Z`)
  .toLocaleDateString("en-US", { month: "short", day: "numeric", year: "numeric", timeZone: "UTC" });

let data;
try {
  const res = await fetch("chart.json", { cache: "no-cache" });
  if (!res.ok) throw new Error(res.statusText);
  data = await res.json();
} catch (e) {
  $("#status").textContent = `Could not load the chart (${e.message}).`;
  throw e;
}

const entries = data.entries;
const compared = Boolean(data.previous_fetched_at);
const SOURCE = { apple: "Apple Music Top Songs", spotify: "Spotify New Releases" }[data.source] ?? data.source;

$("#status").textContent = `${SOURCE} · ${data.market} · updated ${fmtDate(data.fetched_at)} · ${data.run_count} day${data.run_count === 1 ? "" : "s"} recorded since ${fmtDate(data.first_fetched_at)}`;
if (!compared) {
  $("#note").innerHTML = `<p class="note">This is the first recorded chart, so there is nothing to compare with yet. Movement, new entries and drop-offs appear from the next daily run.</p>`;
}

const moves = entries.map((e) => (e.previous == null ? 0 : e.previous - e.position));
const newCount = entries.filter((e) => e.new).length;
const biggest = entries.reduce((best, e, i) => (moves[i] > (best?.m ?? 0) ? { e, m: moves[i] } : best), null);
const longest = [...entries].sort((a, b) => b.runs - a.runs || a.position - b.position)[0];
$("#tiles").innerHTML = [
  [entries[0] ? esc(entries[0].name) : "–", entries[0] ? `No. 1, by ${esc(entries[0].artists)}` : "No. 1", true],
  [compared ? newCount : "–", compared ? "new entries since the last run" : "new entries (from the next run)"],
  [biggest ? `+${biggest.m}` : "–", biggest ? `biggest climb: ${esc(biggest.e.name)}` : "biggest climb"],
  [`${longest.runs}`, `days on the chart, the most: ${esc(longest.name)}`],
].map(([v, k, small]) => `<div class="tile"><div class="v"${small ? ' style="font-size:1.15rem;line-height:1.3"' : ""}>${v}</div><div class="k">${k}</div></div>`).join("");

$("#chart-sub").textContent = compared
  ? `Movement is against ${fmtDate(data.previous_fetched_at)}. Peak and days are over the whole history. The line shows the last ${data.history_dates.length} days (higher is better).`
  : "Peak and days count from the first recorded chart.";

function moveBadge(e, m) {
  if (!compared) return `<span class="move same">–</span>`;
  if (e.new) return `<span class="move new" title="New since the previous run">NEW</span>`;
  if (m > 0) return `<span class="move up" title="Up ${m}">▲${m}</span>`;
  if (m < 0) return `<span class="move down" title="Down ${-m}">▼${-m}</span>`;
  return `<span class="move same" title="No change">=</span>`;
}

function spark(history) {
  const n = history.length;
  if (n < 2) return "";
  const W = 84, H = 28, max = 100;
  const x = (i) => (i / (n - 1)) * (W - 4) + 2;
  const y = (p) => 2 + ((p - 1) / (max - 1)) * (H - 4);
  let d = "", pen = false;
  history.forEach((p, i) => {
    if (p == null) { pen = false; return; }
    d += `${pen ? "L" : "M"}${x(i).toFixed(1)},${y(p).toFixed(1)}`; pen = true;
  });
  const last = history[n - 1];
  return `<svg class="spark" viewBox="0 0 ${W} ${H}" aria-hidden="true"><path d="${d}" fill="none" stroke="var(--accent)" stroke-width="1.8" stroke-linejoin="round"/>${last != null ? `<circle cx="${x(n - 1)}" cy="${y(last)}" r="2.4" fill="var(--accent)"/>` : ""}</svg>`;
}

function renderChart() {
  const q = $("#q").value.trim().toLowerCase(), show = $("#show").value;
  const rows = entries.map((e, i) => [e, moves[i]])
    .filter(([e]) => !q || `${e.name} ${e.artists}`.toLowerCase().includes(q))
    .filter(([e, m]) => !show || (show === "new" ? e.new : show === "up" ? m > 0 && !e.new : m < 0));
  $("#chart").innerHTML = rows.length ? rows.map(([e, m]) => `<li class="row">
      <span class="pos">${e.position}</span>${moveBadge(e, m)}
      <div style="min-width:0"><div class="title">${e.url ? `<a href="${esc(e.url)}" rel="noopener">${esc(e.name)}</a>` : esc(e.name)}</div>
        <div class="meta">${esc(e.artists)}${e.genre ? ` · ${esc(e.genre)}` : ""}</div></div>
      <div class="stats"><span>peak<b>${e.peak}</b></span><span>days<b>${e.runs}</b></span>${spark(e.history)}</div>
    </li>`).join("") : `<li class="muted" style="padding:.6rem 0">No songs match.</li>`;
}
$("#q").addEventListener("input", renderChart);
$("#show").addEventListener("input", renderChart);
renderChart();

const genres = new Map();
for (const e of entries) { const g = e.genre || "Not stated"; genres.set(g, (genres.get(g) ?? 0) + 1); }
const gs = [...genres].sort((a, b) => b[1] - a[1]);
$("#genres").innerHTML = gs.map(([g, n]) => `<div class="bar"><span class="name">${esc(g)}</span><span class="track"><span class="fill" style="display:block;width:${(n / gs[0][1]) * 100}%"></span></span><span class="n">${n}</span></div>`).join("");

if (!compared) {
  $("#dropped-sub").textContent = "Appears from the next daily run.";
} else {
  $("#dropped-sub").textContent = `${data.dropped.length} song${data.dropped.length === 1 ? "" : "s"} on the ${fmtDate(data.previous_fetched_at)} chart that are gone today.`;
  $("#dropped").innerHTML = data.dropped.map((d) => `<li>${esc(d.name)} <span class="muted">${esc(d.artists)} · was No. ${d.position}</span></li>`).join("") || `<li class="muted">None.</li>`;
}
