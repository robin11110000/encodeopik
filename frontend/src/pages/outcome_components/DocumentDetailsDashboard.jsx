import React, { useMemo } from "react";
import { FileText, Info, ListChecks } from "lucide-react";
import Markdown from "./Markdown";

const TITLES = {
  identity_documents: "Identity Document Insights",
  credit_reports: "Credit Report Insights",
  income_proof: "Income Proof Insights",
  utility_bills: "Utility Bill Insights",
};

const HUMAN_LABEL_OVERRIDES = {
  ssn: "SSN",
};

const humanize = (value) => {
  if (!value) {
    return "";
  }
  if (HUMAN_LABEL_OVERRIDES[value]) {
    return HUMAN_LABEL_OVERRIDES[value];
  }
  return value
    .toString()
    .replace(/[_-]+/g, " ")
    .replace(/\s+/g, " ")
    .trim()
    .replace(/\b\w/g, (char) => char.toUpperCase());
};

const formatValue = (value) => {
  if (value === null || value === undefined || value === "") {
    return "Not available";
  }
  if (typeof value === "boolean") {
    return value ? "Yes" : "No";
  }
  if (typeof value === "number") {
    const isInt = Number.isInteger(value);
    return value.toLocaleString(undefined, {
      minimumFractionDigits: isInt ? 0 : 2,
      maximumFractionDigits: isInt ? 0 : 2,
    });
  }
  if (Array.isArray(value)) {
    return value.length
      ? value.map((item) => formatValue(item)).join(", ")
      : "Not available";
  }
  if (typeof value === "object") {
    return Object.entries(value)
      .map(([key, val]) => `${humanize(key)}: ${formatValue(val)}`)
      .join("\n");
  }

  return value;
};

const buildSections = (data) => {
  if (!data || typeof data !== "object") {
    return [];
  }

  const overview = [];
  const sections = [];

  Object.entries(data).forEach(([key, value]) => {
    if (value === null || value === undefined || value === "") {
      return;
    }

    if (Array.isArray(value)) {
      if (value.length === 0) {
        return;
      }
      const hasNestedObjects = value.some(
        (item) => item && typeof item === "object" && !Array.isArray(item)
      );
      if (!hasNestedObjects) {
        sections.push({
          key,
          title: humanize(key),
          entries: [
            {
              key,
              label: "Values",
              value: formatValue(value),
              type: "text",
            },
          ],
        });
      } else {
        sections.push({
          key,
          title: humanize(key),
          entries: value.map((item, index) => ({
            key: `${key}-${index}`,
            label: `${humanize(key)} ${index + 1}`,
            value: formatValue(item),
            type: "multiline",
          })),
        });
      }
      return;
    }

    if (typeof value === "object") {
      const nestedEntries = Object.entries(value)
        .filter(
          ([, nestedValue]) =>
            nestedValue !== null &&
            nestedValue !== undefined &&
            nestedValue !== ""
        )
        .map(([nestedKey, nestedValue]) => ({
          key: `${key}-${nestedKey}`,
          label: humanize(nestedKey),
          value: formatValue(nestedValue),
        }));

      if (nestedEntries.length > 0) {
        sections.push({
          key,
          title: humanize(key),
          entries: nestedEntries,
        });
      }
      return;
    }

    overview.push({
      key,
      label: humanize(key),
      value: formatValue(value),
    });
  });

  const orderedSections = [];
  if (overview.length > 0) {
    orderedSections.push({
      key: "overview",
      title: "Overview",
      entries: overview,
    });
  }
  orderedSections.push(...sections);
  return orderedSections;
};

const DocumentDetailsDashboard = ({
  data = {},
  summary,
  documentKey,
  title,
}) => {
  const sections = useMemo(() => buildSections(data), [data]);

  const summaryParagraphs = useMemo(() => {
    if (!summary || typeof summary !== "string") {
      return [];
    }
    return summary
      .split(/\n+/)
      .map((line) => line.trim())
      .filter(Boolean);
  }, [summary]);

  const heading = title || TITLES[documentKey] || "Document Insights";

  const hasSections = sections.some((section) => section.entries.length > 0);

  return (
    <div className="min-vh-100 py-4 px-3">
      <div className="container" style={{ maxWidth: "1100px" }}>
        <div className="card shadow-sm mb-4 border-0 border-top border-info border-5">
          <div className="card-body p-4 p-md-5">
            <div className="d-flex align-items-start justify-content-between flex-wrap gap-3">
              <div>
                <h1 className="h3 fw-bold text-dark mb-1">{heading}</h1>
                <p className="text-muted small mb-0">
                  Showing the data points extracted from the uploaded document.
                </p>
              </div>
              <div className="text-info">
                <ListChecks size={28} />
              </div>
            </div>
          </div>
        </div>

        {hasSections ? (
          sections.map((section) => (
            <div className="card shadow-sm mb-4" key={section.key}>
              <div className="card-body p-4">
                <div className="d-flex justify-content-between align-items-center mb-3">
                  <h2 className="h6 fw-bold text-dark mb-0">{section.title}</h2>
                  <Info size={18} className="text-muted" />
                </div>
                <div className="row row-cols-1 row-cols-md-2 row-cols-lg-3 g-3">
                  {section.entries.map((entry) => (
                    <div className="col" key={entry.key}>
                      <div className="border rounded-3 h-100 p-3">
                        <p className="text-muted small mb-1">{entry.label}</p>
                        {entry.type === "multiline" ? (
                          <pre className="mb-0 small text-break">
                            {entry.value}
                          </pre>
                        ) : (
                          <p className="fw-semibold mb-0 text-break">
                            {entry.value}
                          </p>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          ))
        ) : (
          <div
            className="alert alert-info d-flex align-items-center"
            role="alert"
          >
            <Info className="me-2" size={18} />
            <span>No structured data was available for this document.</span>
          </div>
        )}

        {summaryParagraphs.length > 0 && (
          <div className="card shadow-sm">
            <div className="card-body p-4">
              <div className="d-flex justify-content-between align-items-center mb-3">
                <h2 className="h6 fw-bold text-dark mb-0">Summary</h2>
                <FileText size={18} className="text-info" />
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
  );
};

export default DocumentDetailsDashboard;
