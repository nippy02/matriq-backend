"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

const API_BASE =
  process.env.NEXT_PUBLIC_API_URL?.replace(/\/$/, "") || "http://localhost:8000";

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

export default function RegistryPage() {
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  async function loadSamples() {
    setLoading(true);
    setError("");
    try {
      const res = await fetch(`${API_BASE}/api/samples`, {
        headers: authHeaders(),
        cache: "no-store",
      });
      if (!res.ok) throw new Error(`Failed to load samples (${res.status})`);
      const data = await res.json();
      setItems(Array.isArray(data) ? data : []);
    } catch (err) {
      setError(err.message || "Failed to load registry.");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadSamples();
  }, []);

  return (
    <>
      <div className="page">
        <div className="header">
          <div>
            <h1>Sample Registry</h1>
            <p className="description">All classified and registered samples.</p>
          </div>
          <button className="refresh-btn" onClick={loadSamples}>Refresh</button>
        </div>

        {loading && <div className="card">Loading samples...</div>}
        {!loading && error && <div className="card error">{error}</div>}

        {!loading && !error && (
          <div className="tableWrap">
            <table>
              <thead>
                <tr>
                  <th>Sample ID</th>
                  <th>Client</th>
                  <th>Project</th>
                  <th>Material</th>
                  <th>Status</th>
                  <th>Confidence</th>
                  <th>Decision</th>
                  <th>Model</th>
                  <th></th>
                </tr>
              </thead>
              <tbody>
                {items.map((item) => (
                  <tr key={item.sample_id}>
                    <td>{item.sample_id}</td>
                    <td>{item.client_name || "-"}</td>
                    <td>{item.project_reference || "-"}</td>
                    <td>{item.material_type || item.ai_predicted_label || "-"}</td>
                    <td>{item.current_state || "-"}</td>
                    <td>
                      {typeof item.ai_confidence_score === "number"
                        ? `${Math.round(item.ai_confidence_score * 100)}%`
                        : "-"}
                    </td>
                    <td>{item.decision || "-"}</td>
                    <td>{item.model_version || "-"}</td>
                    <td>
                      <Link href={`/technical/tracking/${item.sample_id}`} className="view-link">
                        View
                      </Link>
                    </td>
                  </tr>
                ))}
                {items.length === 0 && (
                  <tr>
                    <td colSpan={9} className="empty">
                      No samples found.
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        )}
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
          color: #000000 !important; /* Forces black for title */
          font-weight: 800;
        }
        .description {
          margin: 0;
          color: #1a1a1a !important; /* Darker gray/black for subtitle */
        }
        .refresh-btn {
          border: none;
          border-radius: 12px;
          padding: 12px 16px;
          font-weight: 700;
          cursor: pointer;
          background: #14003a;
          color: #ffffff !important;
        }
        .card,
        .tableWrap {
          background: #ffffff;
          border: 1px solid #e7e7ef;
          border-radius: 18px;
          padding: 18px;
          box-shadow: 0 8px 24px rgba(15, 23, 42, 0.05);
        }
        table {
          width: 100%;
          border-collapse: collapse;
        }
        th {
          color: #000000 !important;
          font-size: 12px;
          text-transform: uppercase;
          letter-spacing: 0.04em;
          font-weight: 800;
          padding: 14px 10px;
          border-bottom: 2px solid #ececf4;
        }
        td {
          text-align: left;
          padding: 14px 10px;
          border-bottom: 1px solid #ececf4;
          font-size: 14px;
          color: #000000 !important; /* Explicitly forces row text to black */
          opacity: 1 !important; /* Prevents any transparency issues */
        }
        .view-link {
          color: #14003a !important;
          font-weight: 700;
          text-decoration: underline;
        }
        .empty {
          text-align: center;
          color: #333333 !important;
          padding: 24px;
        }
        .error {
          color: #b91c1c !important;
          border-color: #fecaca;
          background: #fff7f7;
        }
      `}</style>
    </>
  );
}