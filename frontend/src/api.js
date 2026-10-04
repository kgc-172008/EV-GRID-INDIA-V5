const API = import.meta.env.VITE_API_URL || "http://localhost:8000/api";

async function get(path) {
  const r = await fetch(`${API}${path}`);
  if (!r.ok) throw new Error(await r.text());
  return r.json();
}

async function post(path, body) {
  const r = await fetch(`${API}${path}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body)
  });
  if (!r.ok) throw new Error(await r.text());
  return r.json();
}

export const api = {
  health: () => get("/health"),
  summary: (target) => get(`/summary?target=${target}`),
  zones: (target, state) => get(`/zones?target=${target}&state=${encodeURIComponent(state)}`),
  chargers: () => get("/chargers"),
  recommendations: (target) => get(`/recommendations?target=${target}&limit=10`),
  dsa: (target) => get(`/dsa-analysis?target=${target}&limit=10`),
  clusters: (target) => get(`/clusters?target=${target}&n_clusters=4`),
  forecast: (body) => post("/forecast", body),
  scenario: (body) => post("/scenario", body),
  quality: () => get("/quality"),
  loadPrediction: (q) => get(`/load-prediction?${new URLSearchParams(q)}`)
};
