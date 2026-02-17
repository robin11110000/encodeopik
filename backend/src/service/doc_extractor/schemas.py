from pydantic import BaseModel, Field
from typing import List, Optional, Dict
from datetime import date
class TransactionRow(BaseModel):
    date: str = Field(description="Date of the transaction, if available")
    description: str = Field(description="Description or details of the transaction")
    amount: str = Field(description="Amount involved in the transaction")
    type: str = Field(description="Type of transaction such as Credit(Deposits), Debit(Withdrawals), or Transfer. Do not include 'Balance' column")

class Account(BaseModel):
    account_holder_name: str = Field(description="Name of the account holder as mentioned in the document")
    bank_name: str = Field(description="Name of the bank")
    account_number_masked: str = Field(description="Account number as shown in the document")
    transactions_table: list[TransactionRow] = Field(description="Table of transactions extracted from the document")

class IdentityDocument(BaseModel):
    full_name: str = Field(description="Full name of the passport holder as mentioned in the document")
    date_of_birth: str = Field(description="Date of birth of the passport holder")
    address: str = Field(description="Residential address of the passport holder")
    passport_number: str = Field(description="Unique passport number assigned to the holder")
    expiry_date: str = Field(description="Passport expiry date")
    issuing_country: str = Field(description="Country that issued the passport")


class ExtractionMetadata(BaseModel):
    """Metadata details captured during document extraction"""
    page_number: Optional[int] = Field(None, description="Page number where the value was found")
    bounding_box: Optional[List[float]] = Field(
        None, description="Bounding box coordinates [x_min, y_min, x_max, y_max] for the extracted text"
    )
    confidence: Optional[float] = Field(None, description="Model confidence score (0-1)")
    raw_text: Optional[str] = Field(None, description="Original text snippet extracted from the document")


class EmployerEntry(BaseModel):
    """Details of each employer in the tax statement"""
    employer_name: Optional[str] = Field(None, description="Name of the employer")
    employer_ein: Optional[str] = Field(None, description="Employer Identification Number (EIN)")
    employer_address: Optional[str] = Field(None, description="Employer address")
    annual_wages: Optional[str] = Field(None, description="Total annual wages or salary reported by this employer")
    tax_withheld: Optional[str] = Field(None, description="Tax amount withheld by this employer")
    ytd_income: Optional[str] = Field(None, description="Year-to-date income reported by this employer")
    metadata: Optional[ExtractionMetadata] = None


class Dependent(BaseModel):
    """Dependent details listed in the tax statement"""
    name: Optional[str] = Field(None, description="Dependent's full name")
    ssn: Optional[str] = Field(None, description="Dependent's SSN")
    relationship: Optional[str] = Field(None, description="Relationship with the taxpayer")
    qualifies_for_credit: Optional[bool] = Field(None, description="Whether the dependent qualifies for child tax credit")


class BankAccountInfo(BaseModel):
    """Bank account information for refund or payment"""
    routing_number: Optional[str] = Field(None, description="Bank routing number (9 digits)")
    account_number: Optional[str] = Field(None, description="Bank account number")
    account_type: Optional[str] = Field(None, description="Type of bank account (Checking/Savings)")
    metadata: Optional[ExtractionMetadata] = None


class TaxSummary(BaseModel):
    """Summarized tax details"""
    total_income: Optional[str] = Field(None, description="Total income reported on the tax return")
    adjusted_gross_income: Optional[str] = Field(None, description="Adjusted Gross Income (AGI)")
    taxable_income: Optional[str] = Field(None, description="Taxable income for the tax year")
    total_tax: Optional[str] = Field(None, description="Total tax liability for the tax year")
    total_refund: Optional[str] = Field(None, description="Total refund amount, if any")
    amount_owed: Optional[str] = Field(None, description="Amount owed, if any")
    metadata: Optional[ExtractionMetadata] = None

class TaxStatement(BaseModel):
    # Basic taxpayer info
    taxpayer_first_name: Optional[str] = Field(None, description="Taxpayer's first name as shown on the return")
    taxpayer_last_name: Optional[str] = Field(None, description="Taxpayer's last name as shown on the return")
    taxpayer_ssn: Optional[str] = Field(None, description="Taxpayer's Social Security Number")
    address_line: Optional[str] = Field(None, description="Street address or home address of the taxpayer")
    city: Optional[str] = Field(None, description="City of residence")
    state: Optional[str] = Field(None, description="State of residence")
    zip_code: Optional[str] = Field(None, description="ZIP code of residence")

    # Income details
    total_wages: Optional[str] = Field(None, description="Total wages or salary reported on line 1a (Form W-2, Box 1)")
    total_income: Optional[str] = Field(None, description="Total income reported on the return")
    adjusted_gross_income: Optional[str] = Field(None, description="Adjusted Gross Income (AGI)")
    standard_deduction: Optional[str] = Field(None, description="Standard deduction amount claimed")
    taxable_income: Optional[str] = Field(None, description="Taxable income after deductions")
    total_tax: Optional[str] = Field(None, description="Total tax owed")
    total_payments: Optional[str] = Field(None, description="Total payments and credits applied")
    refund_or_amount_owed: Optional[str] = Field(None, description="Amount owed or overpaid/refund amount")

    # Bank info
    routing_number: Optional[str] = Field(None, description="Bank routing number for refund/payment")

    # Other info
    occupation: Optional[str] = Field(None, description="Taxpayer's occupation as written on the return")
    signature_date: Optional[str] = Field(None, description="Date of signature on the tax form")

class CreditReport(BaseModel):
    # ==============================
    # Basic Identity Information
    # ==============================
    full_name: Optional[str] = Field(
        None, description="Consumer's full name as listed on the credit report."
    )
    ssn: Optional[str] = Field(
        None, description="Social Security Number (SSN) of the consumer."
    )
    date_of_birth: Optional[str] = Field(
        None, description="Consumer's date of birth."
    )
    file_pulled_date: Optional[str] = Field(
        None, description="Date on which this credit report was pulled or generated."
    )
    user_id: Optional[str] = Field(
        None, description="User or Member ID assigned by Equifax."
    )

    # ==============================
    # Address and Contact Information
    # ==============================
    current_address: Optional[str] = Field(
        None, description="Current address of the consumer as reported on the credit file."
    )
    address_reported_date: Optional[str] = Field(
        None, description="Date when the current address was last reported."
    )

    # ==============================
    # SSN Verification Information
    # ==============================
    ssn_status: Optional[str] = Field(
        None, description="Status of SSN verification, such as 'Verified'."
    )
    ssn_issue_state: Optional[str] = Field(
        None, description="State where the SSN was issued, e.g., 'GA'."
    )
    ssn_issue_date: Optional[str] = Field(
        None, description="Approximate date or period when SSN was issued, if available."
    )
    ssn_match_flags: Optional[str] = Field(
        None, description="Flags indicating the SSN match confidence or indicators."
    )

    # ==============================
    # Account Summary
    # ==============================
    total_accounts: Optional[str] = Field(
        None, description="Total number of accounts reported in the credit summary."
    )
    revolving_accounts: Optional[str] = Field(
        None, description="Number of revolving accounts, such as credit cards."
    )
    installment_accounts: Optional[str] = Field(
        None, description="Number of installment accounts, such as loans."
    )
    mortgage_accounts: Optional[str] = Field(
        None, description="Number of mortgage accounts listed."
    )
    line_of_credit_accounts: Optional[str] = Field(
        None, description="Number of open line of credit accounts, if any."
    )
    other_accounts: Optional[str] = Field(
        None, description="Count of other account types."
    )
    account_length: Optional[str] = Field(
        None, description="Total credit history length (e.g., '8 years and 9 months')."
    )
    average_account_age: Optional[str] = Field(
        None, description="Average age of all open accounts (e.g., '5 years and 8 months')."
    )
    oldest_open_account: Optional[str] = Field(
        None, description="Name or type of the oldest open account (e.g., 'STUDENT LOAN (09/2010)')."
    )
    most_recent_account: Optional[str] = Field(
        None, description="Most recent account opened, e.g., 'Auto Loan (06/2023)'."
    )

    # ==============================
    # Scores
    # ==============================
    insight_score: Optional[str] = Field(
        None, description="Equifax Insight Score based on credit factors."
    )
    vantage_score_3_0: Optional[str] = Field(
        None, description="VantageScore 3.0 credit score as displayed in the report."
    )

    # ==============================
    # Potential Negative Info
    # ==============================
    thirty_day_delinquencies: Optional[str] = Field(
        None, description="Number of 30-day delinquencies reported."
    )
    sixty_day_delinquencies: Optional[str] = Field(
        None, description="Number of 60-day delinquencies reported."
    )
    ninety_day_delinquencies: Optional[str] = Field(
        None, description="Number of 90-day delinquencies reported."
    )
    bankruptcies: Optional[str] = Field(
        None, description="Number of bankruptcies reported."
    )
    collections: Optional[str] = Field(
        None, description="Number of collection accounts reported."
    )

    # ==============================
    # Employment and Income
    # ==============================
    employer_name: Optional[str] = Field(
        None, description="Current employer’s name as listed under 'The Work Number Income & Employment Information'."
    )
    employment_status: Optional[str] = Field(
        None, description="Employment status (e.g., Active)."
    )
    job_title: Optional[str] = Field(
        None, description="Job title or designation of the consumer."
    )
    total_time_with_employer: Optional[str] = Field(
        None, description="Total duration with the current employer (e.g., '6 years, 4 months')."
    )
    employer_pay_amount: Optional[str] = Field(
        None, description="Pay amount reported by employer (e.g., '$2850.00')."
    )
    pay_cycle: Optional[str] = Field(
        None, description="Pay frequency, e.g., 'Biweekly'."
    )
    most_recent_start_date: Optional[str] = Field(
        None, description="Most recent employment start date."
    )

    # ==============================
    # DataX Report Summary
    # ==============================
    current_tradelines: Optional[str] = Field(
        None, description="Number of tradelines currently active, as shown in the DataX report summary."
    )
    maximum_total_principal: Optional[str] = Field(
        None, description="Maximum total principal amount reported in the DataX section."
    )
    paid_off_last_payment: Optional[str] = Field(
        None, description="Most recent paid-off amount reported."
    )
    current_principal: Optional[str] = Field(
        None, description="Total current principal balance."
    )
    application_inquiries_180_days: Optional[str] = Field(
        None, description="Number of credit application inquiries in the last 180 days."
    )
    charges_offs_1_year: Optional[str] = Field(
        None, description="Charge-offs reported in the last one year."
    )



class IncomeProof(BaseModel):
    company_name: Optional[str] = Field(
        None, description="Name of the employer or company issuing the payslip, e.g., 'Acme Hospitality LLC'."
    )
    employee_name: Optional[str] = Field(
        None, description="Full name of the employee as mentioned on the payslip."
    )
    employee_id: Optional[str] = Field(
        None, description="Unique employee identification number assigned by the employer."
    )
    department: Optional[str] = Field(
        None, description="Department or business unit where the employee works."
    )
    pay_date: Optional[str] = Field(
        None, description="Date the payment was issued, typically labeled 'Pay Date'."
    )
    pay_period: Optional[str] = Field(
        None, description="Start and end dates for the pay cycle, e.g., '08/01/2023 - 08/31/2023'."
    )
    payment_method: Optional[str] = Field(
        None, description="Mode of salary payment, such as 'Direct Deposit' or 'Cheque'."
    )

    # ==============================
    # Earnings
    # ==============================
    gross_earnings_current: Optional[str] = Field(
        None, description="Gross earnings for the current pay period before deductions."
    )
    gross_earnings_ytd: Optional[str] = Field(
        None, description="Year-to-date (YTD) gross earnings accumulated through the current pay period."
    )

    # ==============================
    # Deductions
    # ==============================
    federal_income_tax_current: Optional[str] = Field(
        None, description="Federal income tax deducted for the current pay period."
    )
    federal_income_tax_ytd: Optional[str] = Field(
        None, description="Cumulative federal income tax deducted year-to-date."
    )
    state_income_tax_current: Optional[str] = Field(
        None, description="State income tax deducted for the current pay period."
    )
    state_income_tax_ytd: Optional[str] = Field(
        None, description="Cumulative state income tax deducted year-to-date."
    )
    fica_social_security_current: Optional[str] = Field(
        None, description="FICA Social Security tax deducted for the current period."
    )
    fica_social_security_ytd: Optional[str] = Field(
        None, description="Cumulative FICA Social Security tax deducted year-to-date."
    )
    fica_medicare_current: Optional[str] = Field(
        None, description="FICA Medicare tax deducted for the current period."
    )
    fica_medicare_ytd: Optional[str] = Field(
        None, description="Cumulative FICA Medicare tax deducted year-to-date."
    )
    total_deductions_current: Optional[str] = Field(
        None, description="Total deductions applied during the current pay period."
    )
    total_deductions_ytd: Optional[str] = Field(
        None, description="Cumulative total deductions for the year-to-date."
    )

    # ==============================
    # Net Pay
    # ==============================
    net_pay_current: Optional[str] = Field(
        None, description="Net pay (take-home pay) for the current period after deductions."
    )
    net_pay_ytd: Optional[str] = Field(
        None, description="Cumulative year-to-date net pay after all deductions."
    )

class MonthlyBillingEntry(BaseModel):
    month: str = Field(..., description="MM format e.g. '03'")
    month_name: str = Field(..., description="Short month name e.g. 'Mar'")
    year: str = Field(..., description="YYYY")
    energy_amount: str = Field(..., description="Total energy amount (electric + gas) as string")


class UsagePeriod(BaseModel):
    last_year: Optional[str] = Field(
        None, description="Last year's value as a string"
    )
    last_period: Optional[str] = Field(
        None, description="Last billing period value"
    )
    current_period: Optional[str] = Field(
        None, description="Current billing period value"
    )


class DailyUsageComparison(BaseModel):
    electric_kwh_per_day: Optional[UsagePeriod] = Field(
        None, description="Electricity usage comparison table"
    )
    gas_therms_per_day: Optional[UsagePeriod] = Field(
        None, description="Gas usage comparison table"
    )

class UtilityBill(BaseModel):
    account_number: Optional[str] = Field(
        None,
        description="Unique account number for the PG&E energy account, located in the top right and bottom sections of the bill."
    )
    statement_date: Optional[str] = Field(
        None,
        description="Date the energy statement was issued, labeled as 'Statement Date' near the account number."
    )
    due_date: Optional[str] = Field(
        None,
        description="Payment due date displayed in the lower remittance section, labeled as 'Due Date'."
    )
    total_amount_due: Optional[str] = Field(
        None,
        description="Total amount the customer owes, labeled 'Total Amount Due' in bold at both the top summary section and remittance slip."
    )
    customer_name: Optional[str] = Field(
        None,
        description="Name of the customer receiving the energy bill, shown under 'Service For'."
    )
    service_company: Optional[str] = Field(
        None,
        description="Company name or organization associated with the account, displayed below the customer name."
    )
    service_address: Optional[str] = Field(
        None,
        description="Street address for the service location, as printed under 'Service For'."
    )
    service_city_state_zip: Optional[str] = Field(
        None,
        description="City, state, and ZIP of the service address, as printed on the bill."
    )
    amount_due_previous_statement: Optional[str] = Field(
        None,
        description="Amount due on the previous statement, labeled 'Amount Due on Previous Statement' in 'Your Account Summary'."
    )
    payments_received_since_last_statement: Optional[str] = Field(
        None,
        description="Total of payments received since the last statement period, labeled 'Payment(s) Received Since Last Statement'."
    )
    current_unpaid_balance: Optional[str] = Field(
        None,
        description="Any remaining unpaid balance carried over to this billing cycle, labeled 'Current Unpaid Balance'."
    )
    electric_delivery_charges: Optional[str] = Field(
        None,
        description="Charges related to PG&E's electric delivery service, labeled 'Current PGE Electric Delivery Charges'."
    )
    clean_energy_generation_charges: Optional[str] = Field(
        None,
        description="Charges related to clean energy generation from providers like Silicon Valley Clean Energy, labeled 'Electric Generation'."
    )
    customer_service_phone: Optional[str] = Field(
        None,
        description="PG&E customer service phone number, typically found under 'Questions about your bill?'."
    )
    customer_service_hours: Optional[str] = Field(
        None,
        description="Operating hours for PG&E customer service listed on the bill (e.g., Monday–Friday 7 a.m. to 9 p.m.)."
    )
    customer_service_website: Optional[str] = Field(
        None,
        description="Website URL for PG&E customer service or billing information (e.g., www.pge.com/waysto)."
    )
    company_name: Optional[str] = Field(
        None,
        description="Utility provider company name, e.g., 'PG&E'."
    )
    remittance_address: Optional[str] = Field(
        None,
        description="Mailing address for sending payments, found in the remittance section (e.g., 'P.O. Box 997500, Sacramento, CA 95899-7500')."
    )
    monthly_billing_history: Optional[List[MonthlyBillingEntry]] = Field(
        None,
        description="List of month-wise entries with energy_amount only",
    )

    daily_usage_comparison: Optional[DailyUsageComparison] = Field(
        None,
        description="Structured daily usage comparison from the right-side table"
    )