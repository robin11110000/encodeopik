import React, { useState, useMemo } from "react";
import { FileText } from "lucide-react";
import Markdown from "./Markdown";

const BankStatementDashboard = ({
  transaction,
  summary = "Unable to get summary",
}) => {
  const [activeView, setActiveView] = useState("transactions");
  const styles = `
    <style>
      .insight-card { border-left: 4px solid; padding-left: 1rem; padding-top: 0.5rem; padding-bottom: 0.5rem; }
      .insight-blue { border-color: #0d6efd; }
      .insight-red { border-color: #dc3545; }
      .insight-amber { border-color: #ffc107; }
      .insight-purple { border-color: #6f42c1; }
      .nav-btn { transition: all 0.3s; }
      .nav-btn:hover { background-color: #e9ecef; }
      .nav-btn.active { background-color: #0d6efd; color: white; }
      .table-hover tbody tr:hover { background-color: #f8f9fa; }
    </style>
  `;

  const transactions = transaction.transactions_table;

  function parseAmount(value) {
    if (typeof value === "string") {
      // Remove commas and extra spaces
      value = value.replace(/,/g, "").trim();
    }
    let num = Number(value);
    return isNaN(num) ? 0 : num;
  }

  function parseTransactionDate(str) {
    const [mon, yr, day] = str.split("-");
    // convert "01" -> 2001
    const fullYear = 2000 + parseInt(yr, 10);
    return new Date(`${mon} ${day}, ${fullYear}`);
  }
  const firstDate = parseTransactionDate(transactions[1].date);
  const lastDate = parseTransactionDate(
    transactions[transactions.length - 1].date
  );
  const startDate = {
    month: firstDate.toLocaleString("en-US", { month: "short" }),
    year: firstDate.getFullYear(),
  };
  const endDate = {
    month: lastDate.toLocaleString("en-US", { month: "short" }),
    year: lastDate.getFullYear(),
  };

  const summaryParagraphs = useMemo(() => {
    if (!summary || typeof summary !== "string") {
      return [];
    }
    return summary
      .split(/\n+/)
      .map((line) => line.trim())
      .filter(Boolean);
  }, [summary]);

  return (
    <>
      <div dangerouslySetInnerHTML={{ __html: styles }} />
      <div className="min-vh-100 py-4 px-3">
        <div className="container" style={{ maxWidth: "1100px" }}>
          {/* Header */}
          <div className="card shadow-sm mb-4 border-0 border-top border-primary border-5">
            <div className="card-body p-4 p-md-5">
              <div className="d-flex justify-content-between align-items-start flex-wrap ">
                <div>
                  <h1 className="h3 fw-bold text-dark mb-3">
                    Bank Statement Analysis
                  </h1>
                  <p className="text-muted mt-1 mb-1">
                    {transaction.account_holder_name} • {transaction.bank_name}
                  </p>
                  <p className="text-muted small mb-0">
                    Account: {transaction.account_number_masked}
                  </p>
                </div>
              </div>
            </div>
          </div>

          {/* Navigation Tabs */}
          <div className="card shadow-sm mb-4">
            <div className="card-body p-2">
              <div className="d-flex gap-2">
                <button
                  onClick={() => setActiveView("transactions")}
                  className={`flex-fill btn fw-medium nav-btn ${
                    activeView === "transactions" ? "active" : "btn-light"
                  }`}
                >
                  Transactions
                </button>
              </div>
            </div>
          </div>

          {activeView === "transactions" && (
            <div className="card shadow-sm">
              <div className="card-body">
                <h3 className="h5 fw-semibold text-dark mb-3">
                  Transaction History
                </h3>
                <div className="table-responsive">
                  <table className="table table-hover align-middle">
                    <thead>
                      <tr className="border-bottom border-2">
                        <th className="text-muted fw-semibold">Date</th>
                        <th className="text-muted fw-semibold">Description</th>
                        <th className="text-muted fw-semibold text-end">
                          Amount($)
                        </th>
                        <th className="text-muted fw-semibold text-center">
                          Type
                        </th>
                      </tr>
                    </thead>
                    <tbody>
                      {transactions.map((t, idx) => (
                        <tr key={idx}>
                          <td className="text-dark">{t.date}</td>
                          <td className="text-dark">{t.description}</td>
                          <td
                            className={`text-end fw-semibold ${
                              t.type === "Credit"
                                ? "text-success"
                                : t.type === "Debit"
                                ? "text-danger"
                                : "text-dark"
                            }`}
                          >
                            {/* {parseAmount(t.amount).toFixed(2)} */}
                            {t.amount}
                          </td>
                          <td className="text-center">
                            {t.type && (
                              <span
                                className={`badge ${
                                  t.type === "Credit"
                                    ? "bg-success-subtle text-success"
                                    : "bg-danger-subtle text-danger"
                                }`}
                              >
                                {t.type}
                              </span>
                            )}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            </div>
          )}
          {summaryParagraphs.length > 0 && (
            <div className="card shadow-sm mb-0 mt-3">
              <div className="card-body p-4">
                <div className="d-flex justify-content-between align-items-center mb-3">
                  <h2 className="h6 fw-bold text-dark mb-0">Summary</h2>
                  <FileText size={18} className="text-primary" />
                </div>
                <div className="text-muted">
                  {summaryParagraphs.map((paragraph, idx) => (
                    <Markdown content={paragraph} />
                  ))}
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </>
  );
};

export default BankStatementDashboard;
