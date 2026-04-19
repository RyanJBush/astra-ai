import { useEffect, useState } from "react";

import { getResearchHistory, listSources } from "../services/api";

function DashboardPage() {
  const [stats, setStats] = useState({ runs: 0, sources: 0 });

  useEffect(() => {
    async function loadData() {
      const [history, sources] = await Promise.all([getResearchHistory(), listSources(100)]);
      setStats({ runs: history.length, sources: sources.length });
    }

    loadData();
  }, []);

  return (
    <section>
      <header className="page-header">
        <h2>Dashboard</h2>
        <p>Track your research workflows, source quality, and report generation output.</p>
      </header>

      <div className="stats-grid">
        <article className="stat-card">
          <h3>Research Runs</h3>
          <p>{stats.runs}</p>
        </article>
        <article className="stat-card">
          <h3>Validated Sources</h3>
          <p>{stats.sources}</p>
        </article>
      </div>

      <section className="panel">
        <h3>Workflow</h3>
        <ol>
          <li>Submit a research query.</li>
          <li>Review structured summary with linked citations.</li>
          <li>Inspect source evidence and scoring.</li>
          <li>Re-open historical runs in History.</li>
        </ol>
      </section>
    </section>
  );
}

export default DashboardPage;
