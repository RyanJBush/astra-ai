function CitationSummary({ summary, citations }) {
  const citationMap = new Map(citations.map((citation) => [citation.index, citation]));
  const parts = summary.split(/(\[\d+\])/g);

  return (
    <div className="summary-card">
      <h3>Structured Summary</h3>
      <p>
        {parts.map((part, idx) => {
          const match = part.match(/^\[(\d+)\]$/);
          if (!match) {
            return <span key={`${part}-${idx}`}>{part}</span>;
          }

          const citationNumber = Number(match[1]);
          const citation = citationMap.get(citationNumber);

          if (!citation) {
            return <span key={`${part}-${idx}`}>{part}</span>;
          }

          return (
            <a key={`${part}-${idx}`} className="citation-link" href={`#source-${citationNumber}`}>
              {part}
            </a>
          );
        })}
      </p>
    </div>
  );
}

export default CitationSummary;
