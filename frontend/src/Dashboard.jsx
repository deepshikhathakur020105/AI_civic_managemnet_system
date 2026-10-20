import { useCallback, useEffect, useRef, useState } from "react";
import L from "leaflet";
import { listComplaints, updateStatus } from "./api.js";

const STATUSES = ["open", "in_progress", "resolved", "needs_review"];
const COLORS = { P1: "#c0392b", P2: "#e67e22", P3: "#f1c40f", P4: "#7f8c8d" };

export default function Dashboard() {
  const [rows, setRows] = useState([]);
  const [filter, setFilter] = useState("");
  const [error, setError] = useState("");
  const mapEl = useRef(null);
  const map = useRef(null);
  const layer = useRef(null);

  const load = useCallback(async () => {
    try {
      setError("");
      setRows(await listComplaints(filter || undefined));
    } catch (e) {
      setError(e.message);
    }
  }, [filter]);

  useEffect(() => { load(); }, [load]);

  useEffect(() => {
    if (!map.current) {
      map.current = L.map(mapEl.current).setView([30.3165, 78.0322], 12);
      L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
        attribution: "&copy; OpenStreetMap contributors",
      }).addTo(map.current);
      layer.current = L.layerGroup().addTo(map.current);
    }
    layer.current.clearLayers();
    rows.forEach((r) => {
      L.circleMarker([r.lat, r.lon], {
        radius: 8, color: COLORS[r.priority] || "#333", fillOpacity: 0.7,
      }).bindPopup(`#${r.id} ${r.category}<br/>${r.priority} · ${r.status}`).addTo(layer.current);
    });
    if (rows.length) {
      map.current.fitBounds(rows.map((r) => [r.lat, r.lon]), { maxZoom: 15, padding: [30, 30] });
    }
  }, [rows]);

  async function change(id, status) {
    try {
      await updateStatus(id, status);
      load();
    } catch (e) {
      setError(e.message);
    }
  }

  return (
    <div>
      <div className="toolbar">
        <h2>Complaints</h2>
        <select value={filter} onChange={(e) => setFilter(e.target.value)}>
          <option value="">All statuses</option>
          {STATUSES.map((s) => <option key={s} value={s}>{s}</option>)}
        </select>
        <button className="secondary" onClick={load}>Refresh</button>
      </div>
      {error && <p className="error">{error}</p>}
      <div ref={mapEl} className="map" />
      <table>
        <thead>
          <tr><th>ID</th><th>Category</th><th>Priority</th><th>Department</th><th>Status</th><th>Duplicate of</th></tr>
        </thead>
        <tbody>
          {rows.map((r) => (
            <tr key={r.id}>
              <td>{r.id}</td>
              <td>{r.category}</td>
              <td><span className="badge" style={{ background: COLORS[r.priority] }}>{r.priority}</span></td>
              <td>{r.department}</td>
              <td>
                <select value={r.status} onChange={(e) => change(r.id, e.target.value)}>
                  {STATUSES.map((s) => <option key={s} value={s}>{s}</option>)}
                </select>
              </td>
              <td>{r.parent_id ?? "—"}</td>
            </tr>
          ))}
          {!rows.length && <tr><td colSpan="6">No complaints yet.</td></tr>}
        </tbody>
      </table>
    </div>
  );
}
