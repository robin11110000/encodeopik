import os
import json
from pathlib import Path
from src.service.loan_core.utils import (
    get_document_kpis_files,
    save_responses_to_folder,
    load_json
)
import json, ast
from src.service.loan_core.loan_metrics import LoanUnderwritingScorerSimple
from src.service.loan_core.decision import DecisionEngine
from src.service.doc_extractor.logger import get_logger
from src.service.rag_service.agent import RAGAgent
from src.service.loan_core.fraud_engine import FraudDetectionEngine
from src.service.opik_tracing import track_with_error_context, track_performance, track_business_metrics

# Initialize logger for this module
logger = get_logger(__name__)

loan_metrics = LoanUnderwritingScorerSimple()
decision_engine = DecisionEngine()



@track_with_error_context("document_evaluation")
@track_performance
@track_business_metrics("document_evaluation")
def evaluate(folder_id):
    base_path = str((Path(__file__).parent.parent / "resources" / folder_id).resolve())
    base_path = base_path.replace("/src/service", "")

    bank_statements = get_document_kpis_files("bank-statements", base_path) or {}
    logger.info(f"The bank statement is  {bank_statements }")
    identity_documents = get_document_kpis_files("identity-documents", base_path) or {}
    credit_reports = get_document_kpis_files("credit-reports", base_path) or {}
    income_proof = get_document_kpis_files("income-proof", base_path) or {}
    tax_statements = get_document_kpis_files("tax-statements", base_path) or {}
    utility_bills = get_document_kpis_files("utility-bills", base_path) or {}

    fraud_json_path  = f"{base_path}/identity-documents/output/identity-documents_fraud_report.json"
    fraud_json = load_json(fraud_json_path)
    fraud_json = json.loads(fraud_json)
    # --- Combine all safely ---
    combined_flat = {
        **credit_reports,
        **bank_statements,
        **identity_documents,
        **income_proof,
        **tax_statements,
        **utility_bills,
    }
    logger.info(f"The combined kpis dict is- {combined_flat}")
    response_dict = loan_metrics.score(combined_flat)
    fraud_engine  = FraudDetectionEngine(base_path)
    summary, save_path = fraud_engine.save_fraud_summary()
    summary= ast.literal_eval(summary)
    # Ensure output folder exists
    os.makedirs(os.path.dirname(save_path), exist_ok=True)
    with open(save_path, "w") as f:
        json.dump(summary, f, indent=4)

    final_descision = decision_engine.make_decision(final_score=response_dict,fraud_result=fraud_json,text_fraud_result=summary)
    save_responses_to_folder(response_dict, final_descision, base_path)


    ## Build RAG index after evaluation
    agent = RAGAgent(case_id=folder_id)
    try:
        agent.ingest()
    except Exception as e:
        logger.error(f"Error during RAG ingestion: {e}")

    return str(final_descision["status"]), summary
