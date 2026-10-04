import React, { useEffect, useMemo, useState } from "react";
import { MapContainer, TileLayer, CircleMarker, Popup, Marker } from "react-leaflet";
import { LineChart, Line, XAxis, YAxis, Tooltip, CartesianGrid, ResponsiveContainer, BarChart, Bar, Legend } from "recharts";
import { api } from "./api";

const fmt = (n) => Number(n ?? 0).toLocaleString();

function Stat({ label, value, sub }) {
  return <div className="stat"><div className="stat-label">{label}</div><div className="stat-value">{value}</div>{sub && <div className="stat-sub">{sub}</div>}</div>;
}

function StatusPill({ children, tone = "demo" }) {
  return <span className={`status-pill ${tone}`}>{children}</span>;
}

function MapView({ zones, chargers, recommendations }) {
  return <div className="map-wrap">
    <MapContainer center={[22.8, 79]} zoom={5} className="map">
      <TileLayer attribution="&copy; OpenStreetMap contributors" url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png" />
      {zones.map((z, i) => <CircleMarker key={`z${i}`} center={[z.latitude, z.longitude]} radius={7}
        pathOptions={{ color: z.gap_level === "Critical" ? "#ef4444" : z.gap_level === "High" ? "#f59e0b" : "#2563eb", fillOpacity: .7 }}>
        <Popup><b>{z.district}, {z.state}</b><br />EVs: {fmt(z.ev_count)}<br />Chargers: {z.chargers}<br />EV/charger: {Number(z.ev_per_charger).toFixed(1)}<br />Gap: {z.charger_gap}<br />Gap score: {z.gap_score}<br />Level: {z.gap_level}</Popup>
      </CircleMarker>)}
      {chargers.slice(0, 2500).map((c, i) => <CircleMarker key={`c${i}`} center={[c.latitude, c.longitude]} radius={2.5} pathOptions={{ color: "#111827", fillOpacity: .5 }} />)}
      {recommendations.slice(0, 10).map((r, i) => <Marker key={`r${i}`} position={[r.latitude, r.longitude]}>
        <Popup><b>#{r.rank} {r.district}, {r.state}</b><br />Priority: {r.site_score}<br /><b>Why:</b> {(r.why_here || []).join(" • ")}<br />Additional chargers: {r.additional_chargers}</Popup>
      </Marker>)}
    </MapContainer>
    <div className="legend"><span><i className="dot critical" /> Critical</span><span><i className="dot high" /> High</span><span><i className="dot normal" /> Other zones</span><span><i className="dot charger" /> Charger</span></div>
  </div>;
}

export default function App() {
  const [target, setTarget] = useState(150);
  const [state, setState] = useState("All India");
  const [summary, setSummary] = useState(null);
  const [zones, setZones] = useState([]);
  const [chargers, setChargers] = useState([]);
  const [recommendations, setRecommendations] = useState([]);
  const [dsa, setDsa] = useState([]);
  const [clusters, setClusters] = useState([]);
  const [forecast, setForecast] = useState(null);
  const [scenarios, setScenarios] = useState([]);
  const [loadPrediction, setLoadPrediction] = useState(null);
  const [quality, setQuality] = useState(null);
  const [tab, setTab] = useState("overview");
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState("");
  const [error, setError] = useState("");

  async function refresh() {
    try {
      setLoading(true); setError("");
      const [s, z, c, r, d, cl, q] = await Promise.all([
        api.summary(target), api.zones(target, state), api.chargers(), api.recommendations(target), api.dsa(target), api.clusters(target), api.quality()
      ]);
      setSummary(s); setZones(z.rows); setChargers(c.rows); setRecommendations(r.rows); setDsa(d.rows); setClusters(cl.rows); setQuality(q);
    } catch (e) { setError(e.message); } finally { setLoading(false); }
  }

  useEffect(() => { refresh(); }, [target, state]);

  async function runForecast() {
    try { setBusy("forecast"); setError(""); const f = await api.forecast({ target_ev_per_charger: target, horizon: 5 }); setForecast(f); setTab("forecast"); }
    catch (e) { setError(e.message); } finally { setBusy(""); }
  }

  async function runScenario() {
    try { setBusy("scenario"); const x = await api.scenario({ target_ev_per_charger: target, years: 5, low_growth: 8, base_growth: 15, high_growth: 22 }); setScenarios(x.rows); }
    catch (e) { setError(e.message); } finally { setBusy(""); }
  }

  async function runLoadPrediction() {
    try { setBusy("load"); const x = await api.loadPrediction({ traffic_index: 70, current_occupancy: 65, arrivals_index: 60 }); setLoadPrediction(x); }
    catch (e) { setError(e.message); } finally { setBusy(""); }
  }

  const states = useMemo(() => [...new Set(zones.map(z => z.state))].sort(), [zones]);
  const filteredDsa = useMemo(() => dsa.filter(x => state === "All India" || x.state === state), [dsa, state]);
  const top = recommendations.slice(0, 5);

  return <div className="app">
    <header className="topbar">
      <div>
        <div className="brand">⚡ EV-GRID INDIA <span className="version">V5</span></div>
        <div className="tagline">EV charging infrastructure decision intelligence</div>
      </div>
      <div className="header-right">
        <StatusPill>DEMO / SYNTHETIC DATA</StatusPill>
        <label>Target EV/charger <input type="number" min="1" max="5000" value={target} onChange={e => setTarget(Number(e.target.value) || 150)} /></label>
        <select value={state} onChange={e => setState(e.target.value)}><option>All India</option>{states.map(s => <option key={s}>{s}</option>)}</select>
      </div>
    </header>

    <div className="notice"><b>Prototype status:</b> planning intelligence only. Demo/synthetic records are used unless verified datasets are supplied; live charger status and verified national road routing are not connected.</div>

    <nav className="tabs">
      {["overview", "map", "gap", "recommendations", "dsa", "forecast", "scenarios", "clusters", "load", "quality"].map(t => <button className={tab === t ? "active" : ""} onClick={() => setTab(t)} key={t}>{t === "dsa" ? "DSA" : t}</button>)}
    </nav>

    {error && <div className="error">{error}</div>}
    {loading && <div className="loading">Loading EV-GRID intelligence…</div>}

    {!loading && summary && <main>
      <section className="stats">
        <Stat label="EV registrations" value={fmt(summary.ev_registrations)} sub={`Latest year ${summary.year}`} />
        <Stat label="Charging points" value={fmt(summary.chargers)} />
        <Stat label="EV / charger" value={summary.ev_per_charger} sub={`Target ${target}`} />
        <Stat label="High/Critical zones" value={summary.high_critical_zones} />
        <Stat label="Estimated gap" value={fmt(summary.estimated_extra_chargers)} />
      </section>

      {tab === "overview" && <>
        <div className="hero-grid">
          <section className="panel hero-panel"><StatusPill>DECISION ENGINE</StatusPill><h1>WHERE + HOW MANY + WHY</h1><p>V5 connects GIS gap analysis, machine learning and transparent DSA scoring to turn EV infrastructure data into planning priorities.</p><div className="engine-flow"><span>EV demand</span><b>→</b><span>Gap analysis</span><b>→</b><span>ML forecast</span><b>→</b><span>DSA ranking</span><b>→</b><strong>Priority</strong></div><button className="primary" onClick={() => setTab("recommendations")}>Open priority locations →</button><button className="secondary" onClick={runForecast}>{busy === "forecast" ? "Running…" : "Run ML forecast"}</button></section>
          <section className="panel"><h2>Top priority zones</h2>{top.map(r => <div className="rank" key={r.rank}><span>#{r.rank}</span><b>{r.district}, {r.state}</b><strong>{r.site_score}</strong></div>)}<button className="link-btn" onClick={() => setTab("dsa")}>See DSA priority ranking →</button></section>
        </div>
        <section className="panel"><h2>How to read this dashboard</h2><div className="guide"><div><b>1. Gap</b><p>Find districts where EV demand is high relative to available chargers.</p></div><div><b>2. Recommendation</b><p>See ranked locations and the reasons they are prioritized.</p></div><div><b>3. Forecast</b><p>Estimate future EV demand and additional charger requirement.</p></div><div><b>4. DSA</b><p>Use KD-tree proximity + priority queue ranking as a transparent prototype accessibility layer.</p></div></div></section>
      </>}

      {tab === "map" && <section className="panel"><div className="section-head"><div><h2>National GIS intelligence</h2><p>Red/orange zones indicate higher infrastructure pressure. Markers show charger points and top recommendations.</p></div><StatusPill>GIS PROTOTYPE</StatusPill></div><MapView zones={zones} chargers={chargers} recommendations={recommendations} /></section>}

      {tab === "gap" && <section className="panel"><div className="section-head"><div><h2>Charging gap intelligence</h2><p>Target is configurable and is a planning assumption, not an official government formula.</p></div><StatusPill>PLANNING MODEL</StatusPill></div><table><thead><tr><th>District</th><th>EVs</th><th>Chargers</th><th>EV/Chg</th><th>Required</th><th>Gap</th><th>Score</th><th>Level</th></tr></thead><tbody>{[...zones].sort((a, b) => b.gap_score - a.gap_score).map(z => <tr key={z.state + z.district}><td>{z.district}, {z.state}</td><td>{fmt(z.ev_count)}</td><td>{z.chargers}</td><td>{Number(z.ev_per_charger).toFixed(1)}</td><td>{z.required_chargers}</td><td><b>{z.charger_gap}</b></td><td>{z.gap_score}</td><td><span className={`badge ${String(z.gap_level).toLowerCase().replace(" ", "-")}`}>{z.gap_level}</span></td></tr>)}</tbody></table></section>}

      {tab === "recommendations" && <section className="panel"><div className="section-head"><div><h2>Explainable priority locations</h2><p>Each recommendation answers <b>why here</b> instead of only giving a score.</p></div><StatusPill>ML + GIS</StatusPill></div>{recommendations.map(r => <div className="recommend" key={r.rank}><div className="ranknum">#{r.rank}</div><div className="recbody"><div className="rec-title"><h3>{r.district}, {r.state}</h3><span className="score">Priority {r.site_score}</span></div><div className="reason-row">{(r.why_here || []).map((x, i) => <span key={i}>{x}</span>)}</div><p>Current charger gap: <b>{r.charger_gap}</b> · Additional chargers: <b>{r.additional_chargers}</b> · Gap score: <b>{r.gap_score}</b></p></div></div>)}</section>}

      {tab === "dsa" && <section className="panel"><div className="section-head"><div><h2>DSA accessibility & priority engine</h2><p><b>KD-tree</b> finds nearest charger points and a <b>priority queue</b> ranks candidates. This is a geographic prototype, not verified road-network routing.</p></div><StatusPill>DSA PROTOTYPE</StatusPill></div><div className="method-cards"><div><b>KD-tree</b><span>Nearest charger search</span></div><div><b>Priority Queue</b><span>Highest final priority first</span></div><div><b>Road graph</b><span>Not connected yet</span></div></div><table><thead><tr><th>#</th><th>District</th><th>Final priority</th><th>Site score</th><th>DSA access</th><th>Nearest charger</th><th>Extra chargers</th></tr></thead><tbody>{filteredDsa.map((r, i) => <tr key={`${r.state}-${r.district}`}><td>{i + 1}</td><td>{r.district}, {r.state}</td><td><b>{r.final_priority}</b></td><td>{r.site_score}</td><td>{r.dsa_access_score}</td><td>{Number(r.nearest_charger_km_dsa || 0).toFixed(1)} km</td><td>{r.additional_chargers}</td></tr>)}</tbody></table></section>}

      {tab === "forecast" && <section className="panel"><div className="section-head"><div><h2>ML EV demand forecast</h2><p>Random Forest with chronological holdout validation. Results are based on the current demo/synthetic dataset.</p></div><button className="primary" onClick={runForecast}>{busy === "forecast" ? "Running…" : "Run / refresh forecast"}</button></div>{!forecast ? <div className="empty">Run the forecast to generate future EV demand and charger requirements.</div> : <><div className="metrics"><Stat label="MAE" value={Math.round(forecast.metrics.MAE).toLocaleString()} /><Stat label="RMSE" value={Math.round(forecast.metrics.RMSE).toLocaleString()} /><Stat label="R²" value={forecast.metrics.R2.toFixed(3)} /><Stat label="Holdout year" value={forecast.metrics.holdout_year} /></div><div className="chart"><ResponsiveContainer width="100%" height={340}><LineChart data={forecast.rows.filter(x => state === "All India" || x.state === state)}><CartesianGrid strokeDasharray="3 3" /><XAxis dataKey="year" /><YAxis /><Tooltip /><Legend /><Line type="monotone" dataKey="predicted_ev" name="Predicted EVs" stroke="#2563eb" strokeWidth={3} /></LineChart></ResponsiveContainer></div><table><thead><tr><th>Year</th><th>District</th><th>Predicted EVs</th><th>Chargers</th><th>Required</th><th>Additional</th></tr></thead><tbody>{forecast.rows.filter(x => state === "All India" || x.state === state).slice(0, 40).map((r, i) => <tr key={i}><td>{r.year}</td><td>{r.district}, {r.state}</td><td>{fmt(r.predicted_ev)}</td><td>{r.chargers}</td><td>{r.required_chargers}</td><td><b>{r.additional_chargers}</b></td></tr>)}</tbody></table></>}</section>}

      {tab === "scenarios" && <section className="panel"><div className="section-head"><div><h2>Scenario planning</h2><p>Compare low, base and high EV-growth assumptions over five years.</p></div><button className="primary" onClick={runScenario}>{busy === "scenario" ? "Calculating…" : "Calculate scenarios"}</button></div>{scenarios.length ? <><div className="chart"><ResponsiveContainer width="100%" height={340}><BarChart data={scenarios}><CartesianGrid strokeDasharray="3 3" /><XAxis dataKey="scenario" /><YAxis /><Tooltip /><Legend /><Bar dataKey="projected_evs" name="Projected EVs" fill="#2563eb" /><Bar dataKey="additional_chargers" name="Additional chargers" fill="#f59e0b" /></BarChart></ResponsiveContainer></div><div className="scenario-grid">{scenarios.map(x => <div className="scenario-card" key={x.scenario}><b>{x.scenario}</b><span>{x.growth_percent}% annual growth</span><strong>{fmt(x.additional_chargers)}</strong><small>additional chargers</small></div>)}</div></> : <div className="empty">Calculate scenarios to compare infrastructure needs.</div>}</section>}

      {tab === "clusters" && <section className="panel"><div className="section-head"><div><h2>Demand clusters</h2><p>K-Means groups districts by EV demand, charger pressure, population, roads and activity.</p></div><StatusPill>ML CLUSTERING</StatusPill></div><div className="cluster-grid">{[0,1,2,3].map(c => { const rows = clusters.filter(x => x.cluster === c); return <div className="cluster-card" key={c}><span>Cluster {c}</span><b>{rows.length}</b><small>districts</small><p>EVs: {fmt(rows.reduce((a, x) => a + Number(x.ev_count || 0), 0))}</p><p>Gap: {fmt(rows.reduce((a, x) => a + Number(x.charger_gap || 0), 0))}</p></div>; })}</div></section>}

      {tab === "load" && <section className="panel"><div className="section-head"><div><h2>Station load prediction</h2><p>Current V5 uses a transparent heuristic because historical station-session data is not connected.</p></div><StatusPill>HEURISTIC</StatusPill></div><div className="load-inputs"><label>Traffic index <input id="traffic" type="range" min="0" max="100" defaultValue="70" /></label><label>Occupancy <input id="occupancy" type="range" min="0" max="100" defaultValue="65" /></label><label>Arrivals index <input id="arrivals" type="range" min="0" max="100" defaultValue="60" /></label></div><button className="primary" onClick={runLoadPrediction}>{busy === "load" ? "Calculating…" : "Estimate peak occupancy"}</button>{loadPrediction && <div className="load-result"><strong>{loadPrediction.predicted_peak_occupancy}%</strong><span>predicted peak occupancy</span><small>{loadPrediction.data_status}</small></div>}</section>}

      {tab === "quality" && <section className="panel"><div className="section-head"><div><h2>Data quality & provenance</h2><p>Use this page before presenting results to judges or decision makers.</p></div><StatusPill>PROVENANCE</StatusPill></div><div className="stats"><Stat label="Registration rows" value={quality.registration_rows} /><Stat label="Charger points" value={quality.charger_points} /><Stat label="Districts" value={quality.districts} /><Stat label="Years" value={quality.years} /></div><div className="quality-box"><b>Data status: {quality.data_status}</b>{(quality.limitations || []).map((x, i) => <p key={i}>• {x}</p>)}</div></section>}
    </main>}
    <footer>EV-GRID INDIA V5 • Planning intelligence, not construction approval.</footer>
  </div>;
}
