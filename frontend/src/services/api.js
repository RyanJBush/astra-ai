const API_BASE = import.meta.env.VITE_API_BASE ?? "http://localhost:8000/api/v1";

async function request(path, options = {}) {
  const response = await fetch(`${API_BASE}${path}`, options);

  if (!response.ok) {
    const message = await response.text();
    throw new Error(message || `Request failed with status ${response.status}`);
  }

  return response.json();
}

export async function runResearch(query, maxSources = 5) {
  return request("/research", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ query, max_sources: maxSources })
  });
}

export async function getResearchHistory() {
  return request("/research");
}

export async function getResearchResult(runId) {
  return request(`/research/${runId}`);
}

export async function listSources(limit = 25) {
  return request(`/sources?limit=${limit}`);
}
