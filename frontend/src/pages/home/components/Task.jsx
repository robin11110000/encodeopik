import React, {
  useEffect,
  useMemo,
  useState,
  useContext,
} from "react";
import { useNavigate, useLocation } from "react-router-dom";
import "../styling/task.css";
import ProcessingBlink from "../../../components/Blink";
import { userContext } from "../../../context/userContext";
import { v4 as uuidv4 } from "uuid";

const DOC_CONFLICT_REGEX = {
  identity_documents: [
    /(bank|statement)/i,
    /(tax|1040|w[-\s]?2)/i,
    /(credit|bureau)/i,
    /(utility|bill)/i,
    /(pay\s?stub|payslip|salary|income)/i,
  ],
  bank_statements: [
    /(identity|passport|license)/i,
    /(tax|1040|w[-\s]?2)/i,
    /(credit|bureau)/i,
    /(utility|bill)/i,
    /(pay\s?stub|payslip|salary|income)/i,
  ],
  tax_statements: [
    /(identity|passport|license)/i,
    /(bank)/i,
    /(credit|bureau)/i,
    /(utility|bill)/i,
    /(pay\s?stub|payslip|salary|income)/i,
  ],
  credit_reports: [
    /(identity|passport|license)/i,
    /(bank|statement)/i,
    /(tax|1040|w[-\s]?2)/i,
    /(utility|bill)/i,
    /(pay\s?stub|payslip|salary|income)/i,
  ],
  income_proof: [
    /(identity|passport|license)/i,
    /(tax|1040|w[-\s]?2)/i,
    /(utility|bill)/i,
    /(credit|bureau)/i,
    /(bank|statement)/i,
  ],
  utility_bills: [
    /(identity|passport|license)/i,
    /(tax|1040|w[-\s]?2)/i,
    /(credit|bureau)/i,
    /(bank|statement)/i,
    /(pay\s?stub|payslip|salary|income)/i,
  ],
};

const Task = ({ prop }) => {
  const { showAlert } = prop;
  const navigate = useNavigate();
  const location = useLocation();

  const {
    uploadStatuses,
    uploadSummary,
    uploadDocumentGroup,
    caseId,
    uploadCount,
    changeUploadCount,
  } = useContext(userContext);

  const [selectedFiles, setSelectedFiles] = useState({});
  const [loader, setLoader] = useState(false);

  const documentGroups = useMemo(
    () => [
      {
        title: "Identity Documents",
        description:
          "Passports, national IDs, or driver’s licenses to verify the applicant.",
        icon: "fa-solid fa-id-card",
        accept: ".pdf,.jpg,.jpeg,.png",
        key: "identity_documents",
      },
      {
        title: "Bank Statements",
        description:
          "Recent bank statements for liquidity verification and cash-flow trends.",
        icon: "fa-solid fa-building-columns",
        accept: ".pdf,.csv,.xlsx",
        key: "bank_statements",
      },
      {
        title: "Tax Statements",
        description:
          "Latest tax returns or filings to confirm declared income.",
        icon: "fa-solid fa-file-invoice-dollar",
        accept: ".pdf",
        key: "tax_statements",
      },
      {
        title: "Credit Reports",
        description:
          "Bureau-rated credit histories and liabilities.",
        icon: "fa-solid fa-chart-line",
        accept: ".pdf",
        key: "credit_reports",
      },
      {
        title: "Income Proof",
        description:
          "Payslips or employment letters for income validation.",
        icon: "fa-solid fa-briefcase",
        accept: ".pdf,.jpg,.jpeg,.png",
        key: "income_proof",
      },
      {
        title: "Utility Bills",
        description:
          "Invoices for electricity, water, gas, etc.",
        icon: "fa-solid fa-money-bills",
        accept: ".pdf,.jpg,.jpeg,.png",
        key: "utility_bills",
      },
    ],
    []
  );

  /* Bootstrap tooltips */
  useEffect(() => {
    if (!window.bootstrap?.Tooltip) return;

    const triggers = document.querySelectorAll(
      '[data-bs-toggle="tooltip"]'
    );

    [...triggers].forEach(
      (el) => new window.bootstrap.Tooltip(el)
    );
  }, [location.pathname]);

  const filesReady = useMemo(() => {
    const values = Object.values(selectedFiles);
    if (values.length !== documentGroups.length) return false;
    return values.every(
      (files) => Array.isArray(files) && files.length > 0
    );
  }, [selectedFiles, documentGroups]);

  const anyUploadInFlight = useMemo(() => {
    return documentGroups.some(
      (group) =>
        uploadStatuses[group.key]?.status === "processing"
    );
  }, [documentGroups, uploadStatuses]);

  const handleFileChange = async (group, event) => {
    const inputEl = event.target;
    const files = Array.from(inputEl.files || []);

    if (!files.length) return;

    const conflictMatchers =
      DOC_CONFLICT_REGEX[group.key] || [];

    const conflictFile = files.find((file) =>
      conflictMatchers.some((rx) => rx.test(file.name))
    );

    if (conflictFile) {
      showAlert(
        <>
          The file <strong>{conflictFile.name}</strong>{" "}
          does not look like{" "}
          <strong>{group.title}</strong>.
        </>,
        "warning"
      );
      inputEl.value = "";
      return;
    }

    try {
      setLoader(true);
      setSelectedFiles((prev) => ({
        ...prev,
        [group.key]: files,
      }));
      changeUploadCount();
      await uploadDocumentGroup(group.key, files);
    } catch (err) {
      console.error(err);
      showAlert("Upload failed.", "danger");
    } finally {
      setLoader(false);
      inputEl.value = "";
    }
  };

  const handleProcessDocuments = () => {
    if (uploadCount !== documentGroups.length) {
      showAlert(
        "Please upload all required documents.",
        "warning"
      );
      return;
    }

    navigate(`/outcomes/${caseId}`, {
      state: { caseId: uploadSummary?.caseId || caseId },
    });
  };

  return (
    <section id="task" className="bg-light">
      <div className="container py-5">
        <div className="text-center mb-5">
          <h2 className="fw-bold">
            Upload Your Lending Documents
          </h2>
          <p className="text-muted">
            Provide documents for 0xnavi analysis.
          </p>
        </div>

        <div className="row g-4">
          {documentGroups.map((item) => {
            const uploadState =
              uploadStatuses[item.key] || {};
            const isUploading =
              uploadState.status === "processing";
            const isCompleted =
              uploadState.status === "completed";
            const hasFiles =
              Array.isArray(uploadState.filesMeta) &&
              uploadState.filesMeta.length > 0;

            return (
              <div key={item.key} className="col-md-6 col-lg-4">
                <div className="upload-card h-100">
                  <h5>{item.title}</h5>
                  <p className="text-muted">
                    {item.description}
                  </p>

                  <input
                    type="file"
                    accept={item.accept}
                    multiple
                    onChange={(e) =>
                      handleFileChange(item, e)
                    }
                  />

                  {isUploading && (
                    <ProcessingBlink tag="Processing" />
                  )}
                  {isCompleted && (
                    <small className="text-success">
                      Processed
                    </small>
                  )}
                </div>
              </div>
            );
          })}
        </div>

        <div className="text-center mt-5">
          <button
            className="btn btn-primary btn-lg"
            disabled={!filesReady || anyUploadInFlight}
            onClick={handleProcessDocuments}
            data-bs-toggle="tooltip"
            title="Process uploaded documents"
          >
            See Results
          </button>
        </div>
      </div>
    </section>
  );
};

export default Task;
