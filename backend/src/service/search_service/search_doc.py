import os
from src.service.evaluator_service.evaluator import evaluate
from src.service.summariser_module.get_summary import get_markdown


def search(folder_id):

    folder_id = "bc0f8f34-1933-448b-9259-de05b80a0814"

    base_dir = os.getcwd()
    resource_dir = base_dir + "/resources"
    uuids = [x for x in os.listdir(resource_dir)]
    if folder_id in uuids:

        bank_metadata = get_markdown(folder_id, "bank-statements")
        identity_metadata = get_markdown(folder_id, "identity-documents")
        credit_metadata = get_markdown(folder_id, "credit-reports")
        income_metadata = get_markdown(folder_id, "income-proof")
        tax_metadata = get_markdown(folder_id, "tax-statements")
        utility_metadata = get_markdown(folder_id, "utility-bills")
        evaluate_result = evaluate(folder_id)

        return {"bank_statements": bank_metadata,
                "identity_documents": identity_metadata,
                "credit_reports": credit_metadata,
                "income_proof": income_metadata,
                "tax_statements": tax_metadata,
                "utility_bills": utility_metadata,
                "final_verdict": evaluate_result}

    else:

        return -1
