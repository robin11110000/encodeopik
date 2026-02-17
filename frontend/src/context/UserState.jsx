import React, {
  useCallback,
  useEffect,
  useMemo,
  useState,
  useRef,
} from "react";
import { v4 as uuidv4 } from "uuid";
import { userContext } from "./userContext";

const DOCUMENT_GROUPS = [
  {
    key: "identity_documents",
    title: "Identity Documents",
    description: "Upload your passport to verify the applicant",
    icon: "fa-solid fa-id-card",
    accept: ".pdf,.jpg,.jpeg,.png",
    endpoint: "upload/identity_document",
    formField: "identity_documents",
    successMessage: "Identity documents processed successfully.",
    errorMessage: "Unable to upload identity documents.",
  },
  {
    key: "bank_statements",
    title: "Bank Statements",
    description:
      "Recent bank statements for liquidity verification and cash-flow trends.",
    icon: "fa-solid fa-building-columns",
    accept: ".pdf,.jpg,.jpeg,.png",
    endpoint: "upload/bank_statement",
    formField: "bank_statements",
    successMessage: "Bank statements processed successfully.",
    errorMessage: "Unable to upload bank statements.",
  },
  {
    key: "tax_statements",
    title: "Tax Statements",
    description:
      "Latest tax returns(form 1040) or filings to confirm declared income and obligations.",
    icon: "fa-solid fa-file-invoice-dollar",
    accept: ".pdf,.jpg,.jpeg,.png",
    endpoint: "upload/tax_statement",
    formField: "tax_statements",
    successMessage: "Tax statements processed successfully.",
    errorMessage: "Unable to upload tax statements.",
  },
  {
    key: "credit_reports",
    title: "Credit Reports",
    description:
      "Bureau-rated credit histories to surface existing liabilities and scores.",
    icon: "fa-solid fa-chart-line",
    accept: ".pdf,.jpg,.jpeg,.png",
    endpoint: "upload/credit_report",
    formField: "credit_reports",
    successMessage: "Credit reports processed successfully.",
    errorMessage: "Unable to upload credit reports.",
  },
  {
    key: "income_proof",
    title: "Income Proof",
    description: "Upload your Payslip for income validation.",
    icon: "fa-solid fa-briefcase",
    accept: ".pdf,.jpg,.jpeg,.png",
    endpoint: "upload/income_proof",
    formField: "income_proof",
    successMessage: "Income proof processed successfully.",
    errorMessage: "Unable to upload income proof.",
  },
  {
    key: "utility_bills",
    title: "Utility Bills",
    description: "Monthly invoice of your electricity bill",
    icon: "fa-solid fa-money-bills",
    accept: ".pdf,.jpg,.jpeg,.png",
    endpoint: "upload/utility_bill",
    formField: "utility_bills",
    successMessage: "Utility bills processed successfully.",
    errorMessage: "Unable to upload utility bills.",
  },
];

const createInitialUploadState = () =>
  DOCUMENT_GROUPS.reduce((acc, group) => {
    acc[group.key] = {
      status: "idle",
      error: null,
      response: null,
      filesMeta: [],
      updatedAt: null,
    };
    return acc;
  }, {});

const UserState = ({ children, prop }) => {
  const showAlert = prop?.showAlert;
  const showToast = prop?.showToast;
  const host = prop?.host;
  const [uploads, setUploads] = useState(() => createInitialUploadState());
  const [uploadCount, setUploadCount] = useState(0);
  const [processedCount, setProcessedCount] = useState(0);
  const [finalVerdict, setFinalVerdict] = useState({
    status: "idle",
    data: null,
    error: null,
    lastFetched: null,
    uuid: null,
  });

  const changeUploadCount = (value = 10) => {
    if (value != 10) {
      setUploadCount(value);
    } else {
      setUploadCount((prevCount) => prevCount + 1);
    }
  };

  const [summary, setSummary] = useState({
    completed: 0,
    total: DOCUMENT_GROUPS.length,
    lastUpdated: null,
    caseId: null,
  });
  const caseIdRef = useRef(uuidv4());

  const resetUploads = useCallback(() => {
    caseIdRef.current = uuidv4();
    setUploads(createInitialUploadState());
    setSummary({
      completed: 0,
      total: DOCUMENT_GROUPS.length,
      lastUpdated: null,
      caseId: caseIdRef.current,
    });
    setProcessedCount(0);
    setFinalVerdict({
      status: "idle",
      data: null,
      error: null,
      lastFetched: null,
      uuid: null,
    });
  }, []);

  const uploadDocumentGroup = useCallback(
    async (groupKey, filesOrFile) => {
      const fileList = Array.isArray(filesOrFile)
        ? filesOrFile
        : filesOrFile
        ? [filesOrFile]
        : [];

      if (fileList.length === 0) {
        return;
      }
      const group = DOCUMENT_GROUPS.find((item) => item.key === groupKey);
      if (!group) {
        console.warn(
          `Unknown document group "${groupKey}" supplied to upload.`
        );
        return;
      }

      const [primaryFile] = fileList;
      const filesMeta = [
        {
          name: primaryFile.name,
          size: primaryFile.size,
        },
      ];

      // const filesMeta = fileList.map((file) => ({
      //   name: file.name,
      //   size: file.size,
      //   type: file.type,
      //   lastModified: file.lastModified,
      // }));

      setUploads((prev) => ({
        ...prev,
        [groupKey]: {
          ...prev[groupKey],
          status: "processing",
          error: null,
          filesMeta,
          updatedAt: Date.now(),
        },
      }));

      const fd = new FormData();

      const formField = group.formField || group.key;
      fd.append(formField, primaryFile, primaryFile.name);
      const meta = {
        n_docs: fileList.length,
        caseId: caseIdRef.current,
        documentType: group.key,
        source: "react-ui",
      };
      fd.append("metadata", JSON.stringify(meta));
      try {
        const response = await fetch(`${host}/${group.endpoint}`, {
          method: "POST",
          body: fd,
        });

        if (!response.ok) {
          const errorText = await response.text();
          throw new Error(errorText || "Upload failed");
        }

        const data = await response.json().catch(() => ({}));

        setUploads((prev) => ({
          ...prev,
          [groupKey]: {
            ...prev[groupKey],
            status: "completed",
            error: null,
            response: data,
            updatedAt: Date.now(),
          },
        }));

        if (data?.data?.caseId && caseIdRef.current !== data.data.caseId) {
          caseIdRef.current = data.data.caseId;
        }

        showToast(group.successMessage, false, group.successMessage, "success");
        setProcessedCount((prev) => prev + 1);
        return data;
      } catch (error) {
        console.error(`Upload error for ${group.key}:`, error);

        setUploads((prev) => ({
          ...prev,
          [groupKey]: {
            ...prev[groupKey],
            status: "error",
            error: error.message || "Unknown error",
            updatedAt: Date.now(),
          },
        }));
        showAlert(group.errorMessage, "danger");
        throw error;
      }
    },
    [showAlert]
  );

  const getFinalVerdict = useCallback(
    async (uuid) => {
      const targetUuid = uuid || caseIdRef.current;

      if (!targetUuid) {
        const error = new Error("Case ID is required to fetch verdict.");
        setFinalVerdict((prev) => ({
          ...prev,
          status: "error",
          error: error.message,
          lastFetched: Date.now(),
          uuid: null,
        }));
        throw error;
      }

      setFinalVerdict((prev) => ({
        ...prev,
        status: "loading",
        error: null,
        uuid: targetUuid,
      }));

      try {
        const response = await fetch(
          `${host}/evaluate/evaluate-doc?uuid=${encodeURIComponent(targetUuid)}`
        );

        if (!response.ok) {
          const errorText = await response.text();
          throw new Error(
            errorText || "Failed to retrieve final verdict from server."
          );
        }

        const payload = await response.json().catch(() => ({}));
        const verdictData = payload?.data ?? null;
        const errors = payload?.errors || null;

        setFinalVerdict({
          status: "success",
          data: verdictData,
          error: errors,
          lastFetched: Date.now(),
          uuid: targetUuid,
        });

        return verdictData;
      } catch (error) {
        console.error("Error fetching final verdict:", error);

        setFinalVerdict({
          status: "error",
          data: null,
          error: error.message || "Unknown error",
          lastFetched: Date.now(),
          uuid: targetUuid,
        });

        if (typeof showAlert === "function") {
          showAlert("Unable to fetch final verdict.", "danger");
        }

        throw error;
      }
    },
    [showAlert]
  );

  useEffect(() => {
    const completed = Object.values(uploads).filter(
      (item) => item.status === "completed"
    ).length;

    const lastUpdated = Object.values(uploads).reduce((latest, item) => {
      if (!item.updatedAt) {
        return latest;
      }
      if (!latest || item.updatedAt > latest) {
        return item.updatedAt;
      }
      return latest;
    }, null);

    setSummary((prev) => ({
      ...prev,
      completed,
      lastUpdated,
      caseId: caseIdRef.current,
    }));
  }, [uploads]);

  const value = useMemo(
    () => ({
      documentGroups: DOCUMENT_GROUPS,
      uploadStatuses: uploads,
      uploadSummary: summary,
      uploadDocumentGroup,
      resetUploads,
      caseId: caseIdRef.current,
      uploadCount: uploadCount,
      processedCount,
      changeUploadCount,
      finalVerdict,
      getFinalVerdict,
    }),
    [
      uploads,
      summary,
      uploadDocumentGroup,
      resetUploads,
      uploadCount,
      processedCount,
      changeUploadCount,
      finalVerdict,
      getFinalVerdict,
    ]
  );

  return <userContext.Provider value={value}>{children}</userContext.Provider>;
};

export default UserState;
