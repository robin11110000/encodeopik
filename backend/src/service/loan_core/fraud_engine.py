import json
import pandas as pd
import collections
from pathlib import Path
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

# 🔹 Opik tracing
from src.service.opik_tracing import trace_service_call
from opik import track
import opik


class FraudDetectionEngine:
    def __init__(self, base_path):
        self.base_path = base_path
        self.bank_statement_path = base_path + "/bank-statements/output/bank-statements.json"
        self.credit_report_path = base_path + "/credit-reports/output/credit-reports.json"
        self.identity_doc_path = base_path + "/identity-documents/output/identity-documents.json"
        self.income_proof_path = base_path + "/income-proof/output/income-proof.json"
        self.tax_statement_path = base_path + "/tax-statements/output/tax-statements.json"
        self.utility_bills_path = base_path + "/utility-bills/output/utility-bills.json"

    def load_json(self, file_path):
        with open(Path(file_path), "r") as f:
            return json.load(f)

    def pairwise_similarity(self, docs):
        with opik.start_as_current_span(name="tfidf_similarity") as span:
            vectorizer = TfidfVectorizer()
            tfidf_matrix = vectorizer.fit_transform(docs)
            cosine_sim_matrix = cosine_similarity(tfidf_matrix)

            span.metadata = {
                "documents_compared": len(docs)
            }

        doc_labels = [
            "bank statement",
            "credit report",
            "identity document",
            "income document",
            "tax document",
            "utility bills"
        ]

        df = pd.DataFrame(cosine_sim_matrix, columns=doc_labels, index=doc_labels)

        mismatch = []
        for col in df.columns:
            mismatch.extend(df[col][df[col] < 0.95].index.values.tolist())

        collections_dict = collections.Counter(mismatch)

        if not collections_dict:
            return []

        min_value = min(collections_dict.values())
        mismatch_items = [
            item for item, count in collections_dict.items()
            if count > min_value
        ]

        return mismatch_items

    # ------------------------------------------------------------------
    # MAIN FRAUD DETECTION
    # ------------------------------------------------------------------
    @track(name="fraud_detection", capture_input=False, capture_output=True)
    def fraud_detection(self):
        """
        Compare names across documents using TF-IDF similarity.
        """

        # ----------------------------
        # LOAD DOCUMENTS
        # ----------------------------
        with opik.start_as_current_span(name="load_documents") as span:
            bank_json = self.load_json(self.bank_statement_path)
            credit_json = self.load_json(self.credit_report_path)
            identity_json = self.load_json(self.identity_doc_path)
            income_json = self.load_json(self.income_proof_path)
            tax_json = self.load_json(self.tax_statement_path)
            utility_json = self.load_json(self.utility_bills_path)

            span.metadata = {
                "documents_loaded": 6
            }

        # ----------------------------
        # EXTRACT NAMES
        # ----------------------------
        with opik.start_as_current_span(name="extract_names") as span:
            name_in_bank = bank_json["account_holder_name"]
            name_in_credit = credit_json["full_name"]
            name_in_identity = identity_json["full_name"]
            name_in_income = income_json["employee_name"]
            name_in_tax = (
                tax_json["taxpayer_first_name"] +
                " " +
                tax_json["taxpayer_last_name"]
            )
            name_in_utility = utility_json["customer_name"]

            similarity_search_docs = [
                name_in_bank,
                name_in_credit,
                name_in_identity,
                name_in_income,
                name_in_tax,
                name_in_utility
            ]

            span.metadata = {
                "names_extracted": len(similarity_search_docs)
            }

        # ----------------------------
        # SIMILARITY ANALYSIS
        # ----------------------------
        with opik.start_as_current_span(name="name_similarity_analysis") as span:
            mismatch_items = self.pairwise_similarity(similarity_search_docs)

            span.metadata = {
                "mismatch_count": len(mismatch_items)
            }

        # ----------------------------
        # BUILD FRAUD RESULT
        # ----------------------------
        if len(mismatch_items) > 0:
            mismatch_message = {
                "type": "Warning",
                "text": "\n".join(
                    f"- {item.capitalize()}" for item in mismatch_items
                ),
                "message": (
                    "Name inconsistencies detected across documents. "
                    "Please expand the section below to view the documents "
                    "with mismatched names."
                )
            }
        else:
            mismatch_message = {
                "type": "Authentic",
                "message": "",
                "text": ""
            }

        return mismatch_message

    # ------------------------------------------------------------------
    # SAVE FRAUD SUMMARY
    # ------------------------------------------------------------------
    @track(name="save_fraud_summary", capture_input=False, capture_output=False)
    def save_fraud_summary(self):
        summary = str(self.fraud_detection())
        save_path = f"{self.base_path}/final_output/fraud_report.json"
        return summary, save_path
