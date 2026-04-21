"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

const API_BASE =
  process.env.NEXT_PUBLIC_API_URL?.replace(/\/$/, "") || "http://localhost:8000";

function authHeaders() {
  const token =
    typeof window !== "undefined"
      ? localStorage.getItem("access_token") ||
        localStorage.getItem("technician-token")
      : null;

  return {
    "Content-Type": "application/json",
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
            <p>All classified and registered samples.</p>
          </div>
          <button onClick={loadSamples}>Refresh</button>
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
                      <Link href={`/technical/tracking/${item.sample_id}`}>
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
        }
        p {
          margin: 0;
          color: #000000;
        }
        button {
          border: none;
          border-radius: 12px;
          padding: 12px 16px;
          font-weight: 700;
          cursor: pointer;
          background: #14003a;
          color: #fff;
        }
        .card,
        .tableWrap {
          background: #fff;
          border: 1px solid #e7e7ef;
          border-radius: 18px;
          padding: 18px;
          box-shadow: 0 8px 24px rgba(15, 23, 42, 0.05);
        }
        .error {
          color: #b91c1c;
          border-color: #fecaca;
          background: #fff7f7;
        }
        table {
          width: 100%;
          border-collapse: collapse;
        }
        th,
        td {
          text-align: left;
          padding: 14px 10px;
          border-bottom: 1px solid #ececf4;
          font-size: 14px;
        }
        th {
          color: #666;
          font-size: 12px;
          text-transform: uppercase;
          letter-spacing: 0.04em;
        }
        a {
          color: #14003a;
          font-weight: 700;
          text-decoration: none;
        }
        .empty {
          text-align: center;
          color: #777;
          padding: 24px;
        }
      `}</style>
    </>
  );
}