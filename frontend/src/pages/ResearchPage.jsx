import { useState } from "react";

import { runResearch } from "../services/api";

function ResearchPage() {
  const [query, setQuery] = useState("");
  const [result, setResult] = useState(null);

  async function handleSubmit(event) {
    event.preventDefault();
    const response = await runResearch(query);
    setResult(response);
  }

  return (
    <section>
      <h2>Research</h2>
      <form onSubmit={handleSubmit}>
        <input
          value={query}
          onChange={(event) => setQuery(event.target.value)}
          placeholder="Enter a research query"
          required
        />
        <button type="submit">Run</button>
      </form>
      {result ? <pre>{JSON.stringify(result, null, 2)}</pre> : null}
    </section>
  );
}

export default ResearchPage;
