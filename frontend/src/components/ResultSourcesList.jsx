function ResultSourcesList({ citations, sources }) {
  return (
    <section className="panel">
      <div className="panel-header">
        <h3>Source List</h3>
        <span>{sources.length} sources</span>
      </div>
      <div className="source-list">
        {sources.map((source, idx) => {
          const citation = citations.find((item) => item.index === idx + 1);

          return (
            <article key={`${source.url}-${idx}`} id={`source-${idx + 1}`} className="source-card">
              <div className="source-meta">
                <strong>[{idx + 1}]</strong>
                <a href={source.url} target="_blank" rel="noreferrer">
                  {source.title}
                </a>
              </div>
              <p>{source.snippet}</p>
              <div className="metric-row">
                <span>Credibility: {(source.credibility_score * 100).toFixed(1)}%</span>
                <span>Relevance: {(source.relevance_score * 100).toFixed(1)}%</span>
                {citation ? <span>Citation Index: {citation.index}</span> : null}
              </div>
            </article>
          );
        })}
      </div>
    </section>
  );
}

export default ResultSourcesList;
