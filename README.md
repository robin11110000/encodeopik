
# 0xnavi – Intelligent Loan Processing and Fraud Detection

*Your Virtual Underwriter — From Documents to Decisions, Instantly*

Powered by [Landing AI](https://landing.ai/) 🚀 and [AWS Bedrock](https://aws.amazon.com/documentation-overview/bedrock/)
Observed & Traced with [Opik](https://www.comet.com/docs/opik)

0xnavi is an intelligent, end-to-end underwriting assistant that automates financial document analysis, fraud detection, KPI computation, and credit decisioning with speed, accuracy, and full auditability.

---

## 🎬 Watch Demo

https://youtu.be/JWxo6Zf9zFk

  Notes: I used duplicate documents for the demo. Please try it with the actual documents since it is built with LandingAI. The chatbot is still on the works.  
 
---

# 🚨 Problem Statement

Manual loan underwriting is:

* Time-consuming
* Error-prone
* Vulnerable to fraud
* Difficult to audit

Financial institutions must accelerate credit decisions while maintaining regulatory compliance and minimizing operational risk. However, fragmented document reviews and inconsistent data interpretation make this challenging.

**0xnavi solves this by combining Agentic Data Extraction (ADE), Agentic Object Detection (AOD), rule-based scoring, fraud intelligence, and full observability tracing into one AI-driven underwriting system.**

---

## 📊 Industry Metrics

* **52%** of loan processing time is spent on manual document verification
* **5%** of applications contain altered or inconsistent documents
* **30%** of creditworthy applicants are rejected due to poor interpretation
* **32%** of lenders struggle with affordability assessment
* **19%** of banks still use semi-automated underwriting
* Nearly **20% of financial fraud complaints** involve identity theft
* Over **60% of fraudulent personal loans** involve first-party manipulation

---

Decision time drops from hours to minutes.

---

# ⚙️ Key Features

| Feature Category                      | Capabilities                                                                           |
| ------------------------------------- | -------------------------------------------------------------------------------------- |
| **Automated Document Ingestion**      | Bank statements, payslips, passports, tax docs, credit reports, utility bills          |
| **Multi-Stream ADE + AOD Extraction** | Structured JSON, bounding boxes, unstructured text                                     |
| **KPI & Loan Metric Engine**          | DTI, credit score, default risk, liquidity, income stability, address stability        |
| **Weighted Credit Decision Engine**   | Score-based approval logic + hard rejection rules                                      |
| **Fraud Detection Agent**             | Salary mismatch detection, name inconsistency, layout tampering, document manipulation |
| **Conversational RAG Interface**      | Case Q&A using LangChain + Vector DB + AWS Bedrock                                     |
| **Observability with Opik**           | End-to-end tracing, LLM call monitoring, KPI debugging                                 |
| **Transparency & Auditability**       | ADE bounding box overlays + Opik trace logs                                            |

---

# 🧠 Architecture Overview

0xnavi is a modular, multi-agent AI underwriting pipeline.

## System Layers

1. **Document Intake Layer**
2. **ADE + AOD Extraction Layer**
3. **Structured KPI Engine**
4. **Credit Decision Engine**
5. **Fraud Detection Agent**
6. **Reviewer Dashboard**
7. **Conversational RAG Layer**
8. **Opik Observability Layer**

---

# 🔄 Workflow

### 1️⃣ Document Ingestion

* Upload PDFs, scanned images, photos
* Stored securely under `backend/resources/<case_id>/`

### 2️⃣ ADE & AOD Parsing

Landing AI produces:

* Structured JSON (for metrics)
* Bounding boxes (for UI traceability)
* Raw extracted text (for fraud analysis)

### 3️⃣ KPI & Loan Metrics

Computed using Python (Pandas, NumPy):

* Debt-to-Income Ratio
* Income Stability
* Account Liquidity
* Default Risk Score
* Address Stability

### 4️⃣ Credit Decision Engine

Two layers:

* **Weighted Scoring Engine**
* **Hard Rejection Rules**

Outcomes:

* Approved
* Warning (Manual Review)
* Rejected

### 5️⃣ Fraud Detection Agent

Detects:

* Salary discrepancy between payslip & bank credit
* Name inconsistency across documents
* Layout manipulation via object detection
* Bounding box irregularities
* Document tampering patterns

### 6️⃣ Reviewer Interface

* Markdown summary view
* KPI dashboard
* Decision status badge
* Chat-based case querying (RAG)
* Opik trace inspection

---

# 🧰 Tech Stack

## Backend

* Python 3.10+
* FastAPI
* Pandas / NumPy
* Custom rule engine
* LangChain
* AWS Bedrock
* Landing AI ADE & AOD
* Opik tracing SDK

## Frontend

* React 19
* Vite
* Bootstrap
* Context API state management

## AI & Intelligence

* Retrieval-Augmented Generation (RAG)
* Vector database
* Embedding models
* AWS Bedrock LLM

## Observability

* Opik (full pipeline tracing)
* LLM call tracking
* Performance monitoring

---

# 🔎 Observability with Opik

0xnavi integrates Opik to provide:

* Document ingestion trace logs
* ADE parsing latency tracking
* KPI engine performance metrics
* Fraud detection decision breakdown
* LLM call monitoring for RAG chatbot
* Full audit trail for every loan case

This ensures:

* Debuggability
* Compliance readiness
* Transparent AI decisioning

---

# 🚀 Getting Started

## Prerequisites

* Python 3.10+
* Node.js 22+
* npm 10+
* Docker & Docker Compose (for Opik)
* Landing AI API key
* AWS Bedrock credentials

---

## Environment Variables

Create `.env` inside `backend/`:

```
VISION_AGENT_API_KEY=""

AWS_ACCESS_KEY_ID=""
AWS_SECRET_ACCESS_KEY=""
AWS_REGION=""

```

---

## 1️⃣ Start Opik

```bash
git clone https://github.com/comet-ml/opik.git
cd opik
./opik.sh
```

Access at:

```
http://localhost:5173
```

---

## 2️⃣ Start Backend

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

uvicorn src.controller.main_controller:app --host 0.0.0.0 --port 8000 --reload
```

---

## 3️⃣ Start Frontend

```bash
cd frontend
npm install
npm run dev
```

Runs on:

```
http://localhost:5173
```

---

## 4️⃣ End-to-End Demo

1. Start Opik
2. Start Backend
3. Start Frontend
4. Upload required documents
5. View outcomes dashboard
6. Inspect traces in Opik

---

# 📂 Project Structure

```
0xnavi/
├── backend/
│   ├── requirements.txt
│   └── src/
│       ├── controller/
│       ├── model/
│       └── service/
├── frontend/
│   ├── package.json
│   └── src/
│       ├── context/
│       ├── components/
│       └── pages/
└── opik/  (cloned from comet-ml/opik)
```

