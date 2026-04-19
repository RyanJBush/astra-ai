import { useEffect, useMemo, useState } from "react";

import { listSources } from "../services/api";

function SourceViewerPage() {
  const [sources, setSources] = useState([]);
  const [filter, setFilter] = useState("");

  useEffect(() => {
    listSources(100).then(setSources);
  }, []);

  const filteredSources = useMemo(() => {
    if (!filter) {
      return sources;
    }

    const lowered = filter.toLowerCase();
    return sources.filter(
      (source) =>
        source.title.toLowerCase().includes(lowered) || source.url.toLowerCase().includes(lowered)
    );
  }, [sources, filter]);

  return (
    <section>
      <header className="page-header">
        <h2>Source Viewer</h2>
        <p>Inspect validated source metadata and scoring.</p>
      </header>

      <input
        className="search-input"
        value={filter}
        onChange={(event) => setFilter(event.target.value)}
        placeholder="Filter by title or URL"
      />

      <div className="source-list">
        {filteredSources.map((source, idx) => (
          <article key={`${source.url}-${idx}`} className="source-card">
            <a href={source.url} target="_blank" rel="noreferrer">
              {source.title}
            </a>
            <p>{source.snippet}</p>
            <div className="metric-row">
              <span>Credibility: {(source.credibility_score * 100).toFixed(1)}%</span>
              <span>Relevance: {(source.relevance_score * 100).toFixed(1)}%</span>
            </div>
          </article>
        ))}
      </div>
    </section>
  );
}

export default SourceViewerPage;
