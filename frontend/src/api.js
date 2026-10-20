const BASE = import.meta.env.VITE_API_URL || "/api";

async function handle(res) {
  if (!res.ok) {
    let msg = `Request failed (${res.status})`;
    try {
      const body = await res.json();
      if (body.detail) msg = typeof body.detail === "string" ? body.detail : JSON.stringify(body.detail);
    } catch { /* keep default message */ }
    throw new Error(msg);
  }
  return res.json();
}

export function submitComplaint({ image, lat, lon, description }) {
  const fd = new FormData();
  fd.append("image", image);
  fd.append("lat", lat);
  fd.append("lon", lon);
  fd.append("description", description || "");
  return fetch(`${BASE}/complaints`, { method: "POST", body: fd }).then(handle);
}

export function listComplaints(status) {
  const q = status ? `?status=${encodeURIComponent(status)}` : "";
  return fetch(`${BASE}/complaints${q}`).then(handle);
}

export function updateStatus(id, status) {
  return fetch(`${BASE}/complaints/${id}/status`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ status }),
  }).then(handle);
}
