import { useState } from "react";
import { useNavigate } from "react-router-dom";

import { runResearch } from "../services/api";

function ResearchQueryPage() {
  const navigate = useNavigate();
  const [query, setQuery] = useState("");
  const [maxSources, setMaxSources] = useState(5);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  async function handleSubmit(event) {
    event.preventDefault();
    setLoading(true);
    setError("");

    try {
      const response = await runResearch(query, maxSources);
      navigate(`/results/${response.id}`);
    } catch (submissionError) {
      setError(submissionError.message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <section>
      <header className="page-header">
        <h2>Research Query</h2>
        <p>Submit a topic to run planning, retrieval, validation, and summarization.</p>
      </header>

      <form className="query-form" onSubmit={handleSubmit}>
        <label htmlFor="query">Query</label>
        <textarea
          id="query"
          value={query}
          onChange={(event) => setQuery(event.target.value)}
          placeholder="Example: Evaluate latest autonomous agent safety approaches"
          rows={5}
          required
        />

        <label htmlFor="maxSources">Max Sources</label>
        <input
          id="maxSources"
          type="number"
          min={1}
          max={10}
          value={maxSources}
          onChange={(event) => setMaxSources(Number(event.target.value))}
        />

        <button type="submit" disabled={loading}>
          {loading ? "Running..." : "Run Research"}
        </button>
        {error ? <p className="error-text">{error}</p> : null}
      </form>
    </section>
  );
}

export default ResearchQueryPage;
