import { Link, useLocation } from "react-router-dom";

const navItems = [
  { to: "/", label: "Dashboard" },
  { to: "/research", label: "Research Query" },
  { to: "/sources", label: "Source Viewer" },
  { to: "/history", label: "History" }
];

function AppLayout({ children }) {
  const location = useLocation();

  return (
    <div className="shell">
      <aside className="sidebar">
        <div className="brand">
          <h1>Astra AI</h1>
          <p>Research Dashboard</p>
        </div>
        <nav>
          {navItems.map((item) => (
            <Link
              key={item.to}
              to={item.to}
              className={location.pathname === item.to ? "active" : ""}
            >
              {item.label}
            </Link>
          ))}
        </nav>
      </aside>
      <main className="content">{children}</main>
    </div>
  );
}

export default AppLayout;
