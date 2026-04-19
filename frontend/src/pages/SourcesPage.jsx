import { useEffect, useState } from "react";

import { listSources } from "../services/api";

function SourcesPage() {
  const [sources, setSources] = useState([]);

  useEffect(() => {
    listSources().then(setSources);
  }, []);

  return (
    <section>
      <h2>Sources</h2>
      <ul>
        {sources.map((source) => (
          <li key={source.url}>
            <a href={source.url} target="_blank" rel="noreferrer">
              {source.title}
            </a>{" "}
            ({source.credibility_score})
          </li>
        ))}
      </ul>
    </section>
  );
}

export default SourcesPage;
