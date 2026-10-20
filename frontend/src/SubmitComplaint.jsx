import { useState } from "react";
import { submitComplaint } from "./api.js";

const ALLOWED = ["image/jpeg", "image/png"];
const MAX_MB = 8;

export default function SubmitComplaint() {
  const [image, setImage] = useState(null);
  const [preview, setPreview] = useState(null);
  const [coords, setCoords] = useState({ lat: "", lon: "" });
  const [description, setDescription] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [result, setResult] = useState(null);

  function onFile(e) {
    const f = e.target.files[0];
    setError("");
    if (!f) return;
    if (!ALLOWED.includes(f.type)) return setError("Please choose a JPEG or PNG image.");
    if (f.size > MAX_MB * 1024 * 1024) return setError(`Image must be under ${MAX_MB} MB.`);
    setImage(f);
    setPreview(URL.createObjectURL(f));
  }

  function useMyLocation() {
    setError("");
    if (!navigator.geolocation) return setError("Geolocation is not supported by this browser.");
    navigator.geolocation.getCurrentPosition(
      (p) => setCoords({ lat: p.coords.latitude.toFixed(6), lon: p.coords.longitude.toFixed(6) }),
      () => setError("Could not get your location. Enter coordinates manually."),
      { enableHighAccuracy: true, timeout: 10000 }
    );
  }

  async function onSubmit(e) {
    e.preventDefault();
    setError("");
    setResult(null);
    if (!image) return setError("Add a photo of the issue.");
    if (coords.lat === "" || coords.lon === "") return setError("Location is required.");
    setBusy(true);
    try {
      setResult(await submitComplaint({ image, ...coords, description }));
    } catch (err) {
      setError(err.message);
    } finally {
      setBusy(false);
    }
  }

  return (
    <form className="card" onSubmit={onSubmit}>
      <h2>Report a civic issue</h2>
      <label>
        Photo
        <input type="file" accept="image/jpeg,image/png" capture="environment" onChange={onFile} />
      </label>
      {preview && <img className="preview" src={preview} alt="Selected issue" />}

      <div className="row">
        <label>
          Latitude
          <input value={coords.lat} onChange={(e) => setCoords({ ...coords, lat: e.target.value })} inputMode="decimal" />
        </label>
        <label>
          Longitude
          <input value={coords.lon} onChange={(e) => setCoords({ ...coords, lon: e.target.value })} inputMode="decimal" />
        </label>
      </div>
      <button type="button" className="secondary" onClick={useMyLocation}>Use my location</button>

      <label>
        Description (optional)
        <textarea rows="3" value={description} onChange={(e) => setDescription(e.target.value)} />
      </label>

      {error && <p className="error">{error}</p>}
      <button type="submit" disabled={busy}>{busy ? "Analysing…" : "Submit complaint"}</button>

      {result && (
        <div className="result">
          <h3>Complaint #{result.id} received</h3>
          <ul>
            <li>Category: <b>{result.category}</b> ({Math.round(result.confidence * 100)}% confidence)</li>
            <li>Department: <b>{result.department}</b></li>
            <li>Priority: <b>{result.priority}</b></li>
            <li>Status: <b>{result.status}</b></li>
            {result.duplicate_of && <li>Already reported as #{result.duplicate_of}; your report adds support.</li>}
          </ul>
        </div>
      )}
    </form>
  );
}
