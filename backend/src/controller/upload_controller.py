from typing import List, Optional
from fastapi import Form, File, UploadFile, APIRouter
from opik import track
from src.model.Response import Response
from src.service.utils.upload_file_utils import persist_file_in_local
from src.service.summariser_module.get_summary import get_markdown, get_document_data, check_for_fraud_image
from src.service.main import process_documents
from src.service.loan_core.utils import get_document_files,save_json_to_file,get_image_file_paths
from src.service.loan_core.document_kpi_logic.bank_statement_kpi import BankStatementKPIs
from src.service.loan_core.document_kpi_logic.credit_report_kpi import CreditReportKPIs
from src.service.loan_core.document_kpi_logic.salary_kpi import PaystubSimpleKPIs
from src.service.loan_core.document_kpi_logic.tax_statement_1040_kpi import IncomeKPI
from src.service.loan_core.document_kpi_logic.utility_bill_kpi import UtilityKPI
from src.service.loan_core.document_kpi_logic.identity_verification_kpi import calculate_identity_verification_kpis
from src.service.summary_service.report_summarizer import Summarizer
from src.service.loan_core.image_fraud_engine import PassportFraudDetector,PassportFraudAnalyzer
from src.service.summary_service.summarizer_prompt import(BANK_STATEMENT_SUMMARIZER_HUMAN_PROMPT,BANK_STATEMENT_SUMMARIZER_SYSTEM_PROMPT,
                                                          IDENTITY_REPORT_SUMMARIZER_HUMAN_PROMPT,IDENTITY_REPORT_SUMMARIZER_SYSTEM_PROMPT,
                                                          INCOME_PROOF_REPORT_SUMMARIZER_HUMAN_PROMPT,INCOME_PROOF_REPORT_SUMMARIZER_SYSTEM_PROMPT,
                                                          TAX_STATEMENT_REPORT_SUMMARIZER_HUMAN_PROMPT,TAX_STATEMENT_REPORT_SUMMARIZER_SYSTEM_PROMPT,
                                                          UTILITY_BILL_REPORT_SUMMARIZER_HUMAN_PROMPT,UTILITY_BILLS_REPORT_SUMMARIZER_SYSTEM_PROMPT,
                                                          CREDIT_REPORT_SUMMARIZER_HUMAN_PROMPT,CREDIT_REPORT_SUMMARIZER_SYSTEM_PROMPT)

router = APIRouter()
bankstatement_kpi = BankStatementKPIs()
creditreportkpis  = CreditReportKPIs()
salaryslipkpis = PaystubSimpleKPIs()
incomekpis = IncomeKPI()
utilitykpis  = UtilityKPI()
summary_module = Summarizer()
passport_fraud_detector  = PassportFraudDetector()
passport_analyzer = PassportFraudAnalyzer()


@router.post("/bank_statement", response_model=Response)
async def upload_bank_statement(
    metadata: Optional[str] = Form(None),
    bank_statements: Optional[UploadFile] = File(None)
) -> Response:

    folder_id, folder_name = await persist_file_in_local(metadata, bank_statements, "bank_statements")
    result, folder_id, document_type, base_path = process_documents(folder_id, folder_name)
    files = get_document_files(
                                document_type=document_type,
                                base_path=base_path
                                )
    statement_json = files['json']
    bank_statement_kpis = bankstatement_kpi.calculate(statement_json)
    save_json_to_file(bank_statement_kpis,base_path,document_type)
    summary_output_path  = f"{base_path}/{document_type}/output"
    input_path = f"{base_path}/{document_type}/output/{document_type}_kpis.json"
    summary_module.save_summary(input_path,BANK_STATEMENT_SUMMARIZER_SYSTEM_PROMPT,BANK_STATEMENT_SUMMARIZER_HUMAN_PROMPT,summary_output_path ,document_type)


    # folder_id = "0eb98f46-908a-4734-a4e5-645b6d7db032"
    
    markdown = get_document_data(folder_id, folder_name)

    return Response(
        status=200,
        message="Documents uploaded successfully.",
        data={
            "folderId": folder_id,
            "content": markdown
        },
        errors=None,
    )


@router.post("/identity_document", response_model=Response)
async def upload_identity_document(
    metadata: Optional[str] = Form(None),
    identity_documents: Optional[UploadFile] = File(None)
) -> Response:

    folder_id, folder_name = await persist_file_in_local(metadata, identity_documents, "identity_documents")
    result, folder_id, document_type, base_path = process_documents(folder_id, folder_name)
    files = get_document_files(
                                document_type=document_type,
                                base_path=base_path
                                )
    statement_json = files['json']
    identity_kpis = calculate_identity_verification_kpis(statement_json)
    save_json_to_file(identity_kpis,base_path,document_type)
    summary_output_path  = f"{base_path}/{document_type}/output"
    input_path = f"{base_path}/{document_type}/output/{document_type}_kpis.json"
    summary_module.save_summary(input_path,IDENTITY_REPORT_SUMMARIZER_SYSTEM_PROMPT,IDENTITY_REPORT_SUMMARIZER_HUMAN_PROMPT,summary_output_path ,document_type)
    # folder_id = "0eb98f46-908a-4734-a4e5-645b6d7db032"
    markdown = get_document_data(folder_id, folder_name)
    image_path = get_image_file_paths(f"{base_path}/{document_type}")
    image_output_path = f"{summary_output_path}/{document_type}_components_analyze.jpg" 
    passport_detection_result = passport_fraud_detector.detect_all_components(image_path[0],image_output_path)
    passport_analysis = passport_analyzer.analyze_passport(passport_detection_result[0],passport_detection_result[1])
    passport_analyzer.save_fraud_result_as_json(passport_analysis,summary_output_path)
    return Response(
        status=200,
        message="Documents uploaded successfully.",
        data={
            "folderId": folder_id,
            "content": markdown
        },
        errors= check_for_fraud_image(folder_id,folder_name),
    )


@router.post("/credit_report", response_model=Response)
async def upload_credit_report(
    metadata: Optional[str] = Form(None),
    credit_reports: Optional[UploadFile] = File(None)
) -> Response:

    folder_id, folder_name = await persist_file_in_local(metadata, credit_reports, "credit_reports")
    result, folder_id, document_type, base_path = process_documents(folder_id, folder_name)
 

    files = get_document_files(
                                document_type=document_type,
                                base_path=base_path
                                )
    statement_json = files['json']
    credit_kpis = creditreportkpis.calculate(statement_json)
    save_json_to_file(credit_kpis,base_path,document_type)
    summary_output_path  = f"{base_path}/{document_type}/output"
    input_path = f"{base_path}/{document_type}/output/{document_type}_kpis.json"
    summary_module.save_summary(input_path,CREDIT_REPORT_SUMMARIZER_SYSTEM_PROMPT,CREDIT_REPORT_SUMMARIZER_HUMAN_PROMPT,summary_output_path ,document_type)
   
    # folder_id = "0eb98f46-908a-4734-a4e5-645b6d7db032"
    markdown = get_document_data(folder_id, folder_name)

    return Response(
        status=200,
        message="Documents uploaded successfully.",
        data={
            "folderId": folder_id,
            "content": markdown
        },
        errors=None,
    )


@router.post("/income_proof", response_model=Response)
async def upload_income_proof(
    metadata: Optional[str] = Form(None),
    income_proof: Optional[UploadFile] = File(None)
) -> Response:

    folder_id, folder_name = await persist_file_in_local(metadata, income_proof, "income_proof")
    result, folder_id, document_type, base_path = process_documents(folder_id, folder_name)

    files = get_document_files(
                                document_type=document_type,
                                base_path=base_path
                                )
    statement_json = files['json']
    salary_kpis = salaryslipkpis.calculate(statement_json)
    save_json_to_file(salary_kpis ,base_path,document_type)
    summary_output_path  = f"{base_path}/{document_type}/output"
    input_path = f"{base_path}/{document_type}/output/{document_type}_kpis.json"
    summary_module.save_summary(input_path,INCOME_PROOF_REPORT_SUMMARIZER_SYSTEM_PROMPT,INCOME_PROOF_REPORT_SUMMARIZER_HUMAN_PROMPT,summary_output_path ,document_type)
   
    # folder_id = "0eb98f46-908a-4734-a4e5-645b6d7db032"
    markdown = get_document_data(folder_id, folder_name)

    return Response(
        status=200,
        message="Documents uploaded successfully.",
        data={
            "folderId": folder_id,
            "content": markdown
        },
        errors=None,
    )


@router.post("/tax_statement", response_model=Response)
async def upload_tax_statement(
    metadata: Optional[str] = Form(None),
    tax_statements: Optional[UploadFile] = File(None)
) -> Response:

    folder_id, folder_name = await persist_file_in_local(metadata, tax_statements, "tax_statements")
    result, folder_id, document_type, base_path = process_documents(folder_id, folder_name)

    files = get_document_files(
                                document_type=document_type,
                                base_path=base_path
                                )
    statement_json = files['json']
    income_kpis = incomekpis.calculate(statement_json)
    save_json_to_file(income_kpis ,base_path,document_type)
    summary_output_path  = f"{base_path}/{document_type}/output"
    input_path = f"{base_path}/{document_type}/output/{document_type}_kpis.json"
    summary_module.save_summary(input_path,TAX_STATEMENT_REPORT_SUMMARIZER_SYSTEM_PROMPT,TAX_STATEMENT_REPORT_SUMMARIZER_HUMAN_PROMPT,summary_output_path ,document_type)
   
    # folder_id = "0eb98f46-908a-4734-a4e5-645b6d7db032"
    markdown = get_document_data(folder_id, folder_name)


    return Response(
        status=200,
        message="Documents uploaded successfully.",
        data={
            "folderId": folder_id,
            "content": markdown
        },
        errors=None,
    )


@router.post("/utility_bill", response_model=Response)
async def upload_utility_bill(
    metadata: Optional[str] = Form(None),
    utility_bills: Optional[UploadFile] = File(None)
) -> Response:

    folder_id, folder_name = await persist_file_in_local(metadata, utility_bills, "utility_bills")
    result, folder_id, document_type, base_path = process_documents(folder_id, folder_name)

    files = get_document_files(
                                document_type=document_type,
                                base_path=base_path
                                )
    statement_json = files['json']
    utility_kpis = utilitykpis.calculate(statement_json)
    save_json_to_file(utility_kpis ,base_path,document_type)
    summary_output_path  = f"{base_path}/{document_type}/output"
    input_path = f"{base_path}/{document_type}/output/{document_type}_kpis.json"
    summary_module.save_summary(input_path,UTILITY_BILLS_REPORT_SUMMARIZER_SYSTEM_PROMPT,UTILITY_BILL_REPORT_SUMMARIZER_HUMAN_PROMPT,summary_output_path ,document_type)
   
    # folder_id = "0eb98f46-908a-4734-a4e5-645b6d7db032"
    markdown = get_document_data(folder_id, folder_name)


    return Response(
        status=200,
        message="Documents uploaded successfully.",
        data={
            "folderId": folder_id,
            "content": markdown
        },
        errors=None,
    )

