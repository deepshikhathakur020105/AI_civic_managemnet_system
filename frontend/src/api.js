const BASE = import.meta.env.VITE_API_URL || "/api";
const KEY = "civic_session";

// Session lives in sessionStorage (cleared when the tab closes). It can throw in private
// windows, so every access is wrapped.
export function getSession() {
  try { return JSON.parse(sessionStorage.getItem(KEY)); } catch { return null; }
}
function setSession(s) {
  try { s ? sessionStorage.setItem(KEY, JSON.stringify(s)) : sessionStorage.removeItem(KEY); } catch { /* ignore */ }
}
export function logout() { setSession(null); }

async function handle(res) {
  if (res.status === 401 && getSession()) {
    logout();
    window.dispatchEvent(new Event("civic-logout"));
  }
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

function authHeaders(extra = {}) {
  const s = getSession();
  return s ? { ...extra, Authorization: `Bearer ${s.token}` } : extra;
}

export async function login(email, password) {
  const res = await fetch(`${BASE}/auth/login`, {
    method: "POST",
    headers: { "Content-Type": "application/x-www-form-urlencoded" },
    body: new URLSearchParams({ username: email, password }),
  });
  const data = await handle(res);
  const session = { token: data.access_token, role: data.role, email };
  setSession(session);
  return session;
}

export async function register(email, password) {
  await fetch(`${BASE}/auth/register`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email, password }),
  }).then(handle);
  return login(email, password);
}

export function submitComplaint({ image, lat, lon, description }) {
  const fd = new FormData();
  fd.append("image", image);
  fd.append("lat", lat);
  fd.append("lon", lon);
  fd.append("description", description || "");
  return fetch(`${BASE}/complaints`, { method: "POST", body: fd, headers: authHeaders() }).then(handle);
}

export function listComplaints(status) {
  const q = status ? `?status=${encodeURIComponent(status)}` : "";
  return fetch(`${BASE}/complaints${q}`, { headers: authHeaders() }).then(handle);
}

export function updateStatus(id, status) {
  return fetch(`${BASE}/complaints/${id}/status`, {
    method: "PATCH",
    headers: authHeaders({ "Content-Type": "application/json" }),
    body: JSON.stringify({ status }),
  }).then(handle);
}
