"use client";

import { useEffect, useMemo, useState } from "react";

const API_BASE =
  process.env.NEXT_PUBLIC_API_URL?.replace(/\/$/, "") || "http://localhost:8000";

const LABEL_OPTIONS = ["Concrete", "Soil Aggregates", "Reinforcing Steel Bar"];

function authHeaders(json = false) {
  const token =
    typeof window !== "undefined"
      ? localStorage.getItem("access_token") || localStorage.getItem("token")
      : null;

  return {
    ...(json ? { "Content-Type": "application/json" } : {}),
    ...(token ? { Authorization: `Bearer ${token}` } : {}),
  };
}

export default function ValidationPage() {
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(true);
  const [submittingId, setSubmittingId] = useState(null);
  const [error, setError] = useState("");
  const [form, setForm] = useState({});

  async function loadReviews() {
    setLoading(true);
    setError("");
    try {
      const res = await fetch(`${API_BASE}/api/reviews`, {
        headers: authHeaders(),
        cache: "no-store",
      });
      if (!res.ok) throw new Error(`Failed to load reviews (${res.status})`);
      const data = await res.json();
      setItems(Array.isArray(data) ? data : []);
    } catch (err) {
      setError(err.message || "Failed to load review queue.");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadReviews();
  }, []);

  const pendingItems = useMemo(
    () => items.filter((x) => x.status !== "Completed"),
    [items]
  );

  async function submitReview(sampleId) {
    const entry = form[sampleId] || {};
    if (!entry.corrected_label || !entry.justification?.trim()) {
      alert("Please select a corrected label and add justification.");
      return;
    }

    setSubmittingId(sampleId);
    try {
      const res = await fetch(`${API_BASE}/api/validate`, {
        method: "POST",
        headers: authHeaders(true),
        body: JSON.stringify({
          sample_id: sampleId,
          corrected_label: entry.corrected_label,
          justification: entry.justification.trim(),
        }),
      });

      if (!res.ok) {
        let detail = `Validation failed (${res.status})`;
        try {
          const data = await res.json();
          detail = JSON.stringify(data);
        } catch {}
        throw new Error(detail);
      }

      await loadReviews();
      alert("Validation submitted successfully.");
    } catch (err) {
      let message = "Validation failed.";

      if (typeof err?.message === "string") {
        try {
          const parsed = JSON.parse(err.message);

          if (Array.isArray(parsed)) {
            message = parsed.map((x) => x.msg || JSON.stringify(x)).join("\n");
          } else if (parsed?.detail) {
            message =
              typeof parsed.detail === "string"
                ? parsed.detail
                : JSON.stringify(parsed.detail, null, 2);
          } else {
            message = JSON.stringify(parsed, null, 2);
          }
        } catch {
          message = err.message;
        }
      }

      alert(message);
    } finally {
      setSubmittingId(null);
    }
  }

  return (
    <>
      <div className="page">
        <div className="header">
          <div>
            <h1>Validation Queue</h1>
            <p className="description">Review manual-review and mandatory-override AI classifications.</p>
          </div>
          <button className="refreshBtn" onClick={loadReviews}>
            Refresh
          </button>
        </div>

        {loading && <div className="card">Loading review queue...</div>}
        {!loading && error && <div className="card error">{error}</div>}
        {!loading && !error && pendingItems.length === 0 && (
          <div className="card empty">No review cases found.</div>
        )}

        <div className="grid">
          {pendingItems.map((item) => {
            const current = form[item.sample_id] || {};
            return (
              <div className="card" key={item.sample_id}>
                <div className="row topRow">
                  <div>
                    <div className="label">Sample ID</div>
                    <div className="value">{item.sample_id}</div>
                  </div>
                  <span
                    className={`badge ${
                      item.status === "Mandatory Override" ? "danger" : "warn"
                    }`}
                  >
                    {item.status}
                  </span>
                </div>

                <div className="twoCol">
                  <div>
                    <div className="label">Client</div>
                    <div className="value">{item.client_name || "-"}</div>
                  </div>
                  <div>
                    <div className="label">Project</div>
                    <div className="value">{item.project_id || "-"}</div>
                  </div>
                  <div>
                    <div className="label">Predicted Label</div>
                    <div className="value">{item.predicted_label || "-"}</div>
                  </div>
                  <div>
                    <div className="label">Confidence</div>
                    <div className="value">
                      {typeof item.confidence_score === "number"
                        ? `${Math.round(item.confidence_score * 100)}%`
                        : "-"}
                    </div>
                  </div>
                  <div>
                    <div className="label">Model Version</div>
                    <div className="value">{item.model_version || "-"}</div>
                  </div>
                  <div>
                    <div className="label">Decision</div>
                    <div className="value">{item.decision || "-"}</div>
                  </div>
                </div>

                <div className="formBlock">
                  <label className="formLabel">Corrected Label</label>
                  <select
                    value={current.corrected_label || ""}
                    onChange={(e) =>
                      setForm((prev) => ({
                        ...prev,
                        [item.sample_id]: {
                          ...prev[item.sample_id],
                          corrected_label: e.target.value,
                        },
                      }))
                    }
                  >
                    <option value="">Select label</option>
                    {LABEL_OPTIONS.map((opt) => (
                      <option key={opt} value={opt}>
                        {opt}
                      </option>
                    ))}
                  </select>

                  <label className="formLabel">Justification</label>
                  <textarea
                    rows={4}
                    placeholder="Explain why the AI result should be corrected..."
                    value={current.justification || ""}
                    onChange={(e) =>
                      setForm((prev) => ({
                        ...prev,
                        [item.sample_id]: {
                          ...prev[item.sample_id],
                          justification: e.target.value,
                        },
                      }))
                    }
                  />

                  <button
                    className="submitBtn"
                    disabled={submittingId === item.sample_id}
                    onClick={() => submitReview(item.sample_id)}
                  >
                    {submittingId === item.sample_id
                      ? "Submitting..."
                      : "Submit Validation"}
                  </button>
                </div>
              </div>
            );
          })}
        </div>
      </div>

      <style jsx>{`
        .page {
          padding: 24px;
          background: #f7f7fb;
          min-height: 100vh;
        }
        .header {
          display: flex;
          justify-content: space-between;
          align-items: flex-start;
          gap: 16px;
          margin-bottom: 20px;
        }
        h1 {
          margin: 0 0 6px;
          font-size: 28px;
          color: #000000 !important;
          font-weight: 800;
        }
        .description {
          margin: 0;
          color: #000000 !important;
          opacity: 1 !important;
        }
        .grid {
          display: grid;
          grid-template-columns: repeat(auto-fit, minmax(360px, 1fr));
          gap: 16px;
        }
        .card {
          background: #fff;
          border: 1px solid #e7e7ef;
          border-radius: 18px;
          padding: 18px;
          box-shadow: 0 8px 24px rgba(15, 23, 42, 0.05);
        }
        .error {
          color: #b91c1c !important;
          border-color: #fecaca;
          background: #fff7f7;
        }
        .empty {
          color: #000000 !important;
          text-align: center;
          padding: 24px;
        }
        .row {
          display: flex;
          justify-content: space-between;
          gap: 12px;
        }
        .topRow {
          align-items: center;
          margin-bottom: 16px;
        }
        .label {
          font-size: 11px;
          color: #000000 !important;
          margin-bottom: 4px;
          text-transform: uppercase;
          letter-spacing: 0.05em;
          font-weight: 700;
          opacity: 1 !important;
        }
        .value {
          font-size: 15px;
          font-weight: 700;
          color: #000000 !important;
          opacity: 1 !important;
        }
        .badge {
          border-radius: 999px;
          padding: 8px 12px;
          font-size: 12px;
          font-weight: 800;
          white-space: nowrap;
        }
        .warn {
          background: #fff7ed;
          color: #c2410c !important;
        }
        .danger {
          background: #fef2f2;
          color: #b91c1c !important;
        }
        .twoCol {
          display: grid;
          grid-template-columns: 1fr 1fr;
          gap: 14px 18px;
          margin-bottom: 18px;
        }
        .formBlock {
          display: grid;
          gap: 10px;
          border-top: 1px solid #ececf4;
          padding-top: 18px;
        }
        .formLabel {
          font-size: 13px;
          font-weight: 800;
          color: #000000 !important;
        }
        select,
        textarea {
          width: 100%;
          border: 1px solid #b3b3cc; /* Darkened border for visibility */
          border-radius: 12px;
          padding: 12px 14px;
          font: inherit;
          background: #fff;
          color: #000000 !important;
        }
        .submitBtn,
        .refreshBtn {
          border: none;
          border-radius: 12px;
          padding: 12px 16px;
          font-weight: 700;
          cursor: pointer;
          background: #14003a;
          color: #ffffff !important;
        }
        .submitBtn:disabled,
        .refreshBtn:disabled {
          opacity: 0.5;
          cursor: not-allowed;
        }
      `}</style>
    </>
  );
}