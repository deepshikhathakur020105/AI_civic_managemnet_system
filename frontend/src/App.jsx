import { useEffect, useState } from "react";
import SubmitComplaint from "./SubmitComplaint.jsx";
import Dashboard from "./Dashboard.jsx";
import Login from "./Login.jsx";
import { getSession, logout } from "./api.js";

export default function App() {
  const [session, setSession] = useState(getSession());
  const [tab, setTab] = useState("submit");

  // api.js fires this when the server rejects the token (expired or invalid).
  useEffect(() => {
    const onLogout = () => setSession(null);
    window.addEventListener("civic-logout", onLogout);
    return () => window.removeEventListener("civic-logout", onLogout);
  }, []);

  const isOfficer = session && (session.role === "officer" || session.role === "admin");

  return (
    <div className="app">
      <header>
        <h1>AI Assisted Civic Management</h1>
        {session && (
          <nav>
            <button className={tab === "submit" ? "active" : ""} onClick={() => setTab("submit")}>
              Report an issue
            </button>
            {isOfficer && (
              <button className={tab === "dash" ? "active" : ""} onClick={() => setTab("dash")}>
                Officer dashboard
              </button>
            )}
            <button onClick={() => { logout(); setSession(null); setTab("submit"); }}>
              Sign out ({session.email})
            </button>
          </nav>
        )}
      </header>
      <main>
        {!session ? (
          <Login onLogin={setSession} />
        ) : tab === "dash" && isOfficer ? (
          <Dashboard />
        ) : (
          <SubmitComplaint />
        )}
      </main>
    </div>
  );
}
