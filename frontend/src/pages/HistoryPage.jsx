import { useEffect, useState } from "react";
import { Link } from "react-router-dom";

import { getResearchHistory } from "../services/api";

function HistoryPage() {
  const [runs, setRuns] = useState([]);

  useEffect(() => {
    getResearchHistory().then(setRuns);
  }, []);

  return (
    <section>
      <header className="page-header">
        <h2>History</h2>
        <p>Browse and reopen previous research runs.</p>
      </header>

      <div className="panel">
        {runs.length === 0 ? <p>No research runs yet.</p> : null}
        {runs.map((run) => (
          <div key={run.id} className="history-row">
            <div>
              <strong>{run.query}</strong>
              <p>{new Date(run.created_at).toLocaleString()}</p>
            </div>
            <Link to={`/results/${run.id}`}>View Results</Link>
          </div>
        ))}
      </div>
    </section>
  );
}

export default HistoryPage;
