import React from "react";
import "./styling/about.css";

const About = ({ prop }) => {
  const showAlert = prop?.showAlert;

  const pipelineSteps = [
    {
      title: "Upload",
      description: "Borrower files arrive via drag-and-drop",
      icon: "fa-cloud-arrow-up",
    },
    {
      title: "Extract",
      description:
        "Reads data from documents and checks for accuracy and fraud.",
      icon: "fa-robot",
    },
    {
      title: "Analyze",
      description: "Evaluates borrower’s eligibility for approval",
      icon: "fa-magnifying-glass",
    },
    {
      title: "Decision",
      description: "Determines final outcome as Approved or Rejected",
      icon: "fa-clipboard-check",
    },
    {
      title: "Summarize",
      description: "Creates a simple summary of all documents and results.",
      icon: "fa-rectangle-list",
    },
  ];

  const features = [
    {
      icon: "fa-comments",
      title: "Interactive Chat Assistant",
      description:
        "An intelligent chat assistant guides users through the loan process, answering queries instantly and simplifying every step.",
    },
    {
      icon: "fa-shield-halved",
      title: "Advanced Fraud Detection",
      description:
        "AI-powered checks detect inconsistencies and ensure every application is verified, secure, and trustworthy.",
    },
  ];
  const documentTypes = [
    "Identity proofs (Passport)",
    "Income proofs (payslip)",
    "Bank statements",
    "Tax returns(form 1040)",
    "Credit bureau reports",
    "Utility Bills (Electricity bill)",
  ];

  return (
    <div className="bg-light" id="about">
      <section className="py-5 text-white bg-dark">
        <div className="container py-4">
          <span className="badge bg-warning text-dark text-uppercase mb-3">
            About 0xnavi AI
          </span>
          <h1 className="display-5 fw-bold">
            The document intelligence workspace for smarter lending
          </h1>
          <p className="lead text-white-50 mt-3 col-lg-8 px-0">
            Your Virtual Underwriter - From Documents to Decisions – Instantly
            Powered by Landing AI and AWS Bedrock
          </p>
        </div>
      </section>

      <section className="container py-5">
        <div className="row g-4 align-items-center">
          <div className="col-12 col-lg-6">
            <h2 className="fw-bold mb-3">What the platform does</h2>
            <p className="text-muted">
              0xnavi AI is an intelligent, end-to-end underwriting assistant
              that automates financial document analysis, fraud detection, and
              credit decisioning with speed, accuracy, and transparency.
            </p>
            <ul className="list-unstyled text-muted">
              <li className="mb-2">
                <i className="fa-solid fa-file text-primary me-2"></i>
                Extracts data using Landing AI ADE from PDFs and images
              </li>
              <li className="mb-2">
                <i className="fa-solid fa-chart-simple text-primary me-2"></i>
                Calculates KPIs on documents and loan metrics to decide the
                final outcome
              </li>
              <li>
                <i className="fa-solid fa-person-chalkboard text-primary me-2"></i>
                AWS Bedrock powered Natural language interface for reviewers
                enables question answering.
              </li>
            </ul>
          </div>
          <div className="col-12 col-lg-6">
            <div className="card border-0 shadow-sm">
              <div className="card-body">
                <h5 className="text-uppercase text-muted mb-3">
                  Document types handled
                </h5>
                <div className="row g-3">
                  {documentTypes.map((doc) => (
                    <div className="col-12 col-sm-6" key={doc}>
                      <div className="p-3 bg-light border rounded-3 h-100">
                        <i className="fa-solid fa-file-lines text-primary me-2"></i>
                        {doc}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      <section className="py-5 bg-white border-top border-bottom">
        <div className="container">
          <h2 className="fw-bold text-center mb-2">Pipeline flow</h2>
          <p className="text-muted text-center col-lg-8 mx-auto mb-5">
            A seamless workflow from document upload to decision.
          </p>
          <div className="p-4 bg-light rounded-4 shadow-sm">
            <div className="row gy-4 gx-0 align-items-center text-center text-md-start">
              {pipelineSteps.map((step, index) => (
                <>
                  <React.Fragment key={step.title}>
                    <div className="col-12 col-md">
                      <div className="h-100 px-3 step-card transition-all">
                        <div className="d-inline-flex align-items-center justify-content-center rounded-circle bg-primary-subtle text-primary fs-4 px-3 py-3">
                          <i className={`fa-solid ${step.icon}`}></i>
                        </div>
                        <h6 className="fw-semibold mt-3">{step.title}</h6>
                        <p className="small text-muted mb-0">
                          {step.description}
                        </p>
                      </div>
                    </div>
                    {index !== pipelineSteps.length - 1 && (
                      <div className="col-auto d-none d-md-flex justify-content-center">
                        <i className="fa-solid fa-arrow-right-long text-secondary fs-5 mx-2 opacity-75"></i>
                      </div>
                    )}
                  </React.Fragment>
                </>
              ))}
            </div>
          </div>
          <div className="text-center mb-2 mt-4">
            <p className="text-muted mb-0">
              Smart chat assistance and fraud detection ensure a seamless and
              secure lending experience.
            </p>
          </div>
        </div>
      </section>
    </div>
  );
};

export default About;
