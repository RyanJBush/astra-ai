import { useEffect, useState } from "react";

import { listMemory } from "../services/api";

function MemoryPage() {
  const [items, setItems] = useState([]);

  useEffect(() => {
    listMemory().then(setItems);
  }, []);

  return (
    <section>
      <h2>Memory</h2>
      <ul>
        {items.map((item) => (
          <li key={item.id}>
            <strong>{item.topic}</strong>: {item.content}
          </li>
        ))}
      </ul>
    </section>
  );
}

export default MemoryPage;
