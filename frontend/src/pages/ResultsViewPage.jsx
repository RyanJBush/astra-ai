import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";

import CitationSummary from "../components/CitationSummary";
import ResultSourcesList from "../components/ResultSourcesList";
import { getResearchResult } from "../services/api";

function ResultsViewPage() {
  const { runId } = useParams();
  const [result, setResult] = useState(null);
  const [error, setError] = useState("");

  useEffect(() => {
    async function loadResult() {
      try {
        const response = await getResearchResult(runId);
        setResult(response);
      } catch (loadError) {
        setError(loadError.message);
      }
    }

    loadResult();
  }, [runId]);

  if (error) {
    return <p className="error-text">{error}</p>;
  }

  if (!result) {
    return <p>Loading research result...</p>;
  }

  return (
    <section>
      <header className="page-header">
        <h2>Results View</h2>
        <p>{result.query}</p>
      </header>

      <CitationSummary summary={result.summary} citations={result.citations} />
      <ResultSourcesList citations={result.citations} sources={result.sources} />

      <div className="inline-actions">
        <Link to="/research">Run another query</Link>
        <Link to="/history">Open history</Link>
      </div>
    </section>
  );
}

export default ResultsViewPage;
