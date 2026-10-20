import { useState } from "react";
import SubmitComplaint from "./SubmitComplaint.jsx";
import Dashboard from "./Dashboard.jsx";

export default function App() {
  const [tab, setTab] = useState("submit");
  return (
    <div className="app">
      <header>
        <h1>AI Assisted Civic Management</h1>
        <nav>
          <button className={tab === "submit" ? "active" : ""} onClick={() => setTab("submit")}>
            Report an issue
          </button>
          <button className={tab === "dash" ? "active" : ""} onClick={() => setTab("dash")}>
            Officer dashboard
          </button>
        </nav>
      </header>
      <main>{tab === "submit" ? <SubmitComplaint /> : <Dashboard />}</main>
    </div>
  );
}
