from datetime import datetime
import pandas as pd

class UtilityKPI:
    """
    Calculate utility-bill underwriting KPIs:
      - Utility Payment Amount
      - Utility Payment Stability Indicator
      - Billing Recency Check
    """

    @staticmethod
    def _parse_amount(val):
        """Convert '$89.14' -> 89.14 safely"""
        try:
            return float(str(val).replace("$", "").replace(",", "").strip()) if val else 0.0
        except Exception:
            return 0.0

    @staticmethod
    def _parse_date(date_str):
        """Try parsing date with multiple possible formats"""
        if not date_str:
            raise ValueError("Missing statement_date in input data")

        for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%m/%d/%Y"):
            try:
                return datetime.strptime(date_str.strip(), fmt)
            except ValueError:
                continue
        raise ValueError(f"Unrecognized date format: {date_str}")

    def calculate(self, data: dict) -> dict:
        # Extract values
        total_due = self._parse_amount(data.get("total_amount_due"))
        prev_balance = self._parse_amount(data.get("amount_due_previous_statement"))
        unpaid_balance = self._parse_amount(data.get("current_unpaid_balance"))
        monthly_billing_history = data.get("monthly_billing_history",[])
        monthly_billing_history_df = pd.DataFrame(monthly_billing_history)
        if monthly_billing_history_df.empty:
            consistency = "No"
        else:
            monthly_billing_history_df['energy_amount'] = (
                monthly_billing_history_df['energy_amount']
                .str.replace('$', '', regex=False)   # remove dollar sign
                .astype(float)                        # convert to numeric
            )
            check = sum(monthly_billing_history_df['energy_amount']>0)>6
            if check:
                consistency ="Yes"
            else:
                consistency ="No"

        # KPI 1 — Utility Payment Amount
        utility_payment_amount = round(total_due, 2)

        # KPI 2 — Payment Stability
        if unpaid_balance == 0 and prev_balance == 0:
            payment_stability = "On-time payer"
        else:
            payment_stability = "Possible late or outstanding balance"

        # KPI 3 — Billing Recency
        bill_date = self._parse_date(data.get("statement_date"))
        days_old = (datetime.today() - bill_date).days
        billing_recency = "Recent bill" if days_old <= 90 else "Old bill — request latest bill"

        return {
            "Utility Payment Amount": utility_payment_amount,
            "Utility Payment Stability Indicator": payment_stability,
            "Billing Recency Check": billing_recency,
            "Consistency":consistency
        }
