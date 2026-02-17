from datetime import datetime

class PaystubSimpleKPIs:
    """
    Extract minimal underwriting KPIs from a paystub JSON:
    - Gross Monthly Income
    - Paystub Recency (days)
    - Total Deductions (current period)
    - Recency Check
    - Income Stability Flag (based on YTD vs current consistency)
    """

    @staticmethod
    def _amt(val):
        if not val:
            return 0.0
        try:
            return float(str(val).replace("$", "").replace(",", "").strip())
        except:
            return 0.0

    @staticmethod
    def _parse_date(s):
        if not s:
            return None
        for fmt in ["%m/%d/%Y", "%Y-%m-%d"]:
            try:
                return datetime.strptime(s, fmt)
            except:
                pass
        return None

    def calculate(self, data: dict) -> dict:
        # Income values
        gross_cur = self._amt(data.get("gross_earnings_current"))
        net_cur = self._amt(data.get("net_pay_current"))
        ded_cur = self._amt(data.get("total_deductions_current"))
        gross_ytd = self._amt(data.get("gross_earnings_ytd"))

        # Gross monthly income (assuming paystub shows monthly pay)
        gross_monthly_income = round(gross_cur, 2)

        # Recency calculation
        pay_dt = self._parse_date(data.get("pay_date"))
        today = datetime.today()
        days_old = (today - pay_dt).days if pay_dt else None
        recency_check = "Recent paystub" if days_old is not None and days_old <= 90 else "Old paystub — request newer"

        # Income stability check (simple: compare current vs YTD average)
        stability_flag = "unknown"
        if gross_ytd > 0 and gross_cur > 0:
            months_inferred = gross_ytd / gross_cur
            if 0.5 <= months_inferred <= 12:  # sanity check
                ytd_avg = gross_ytd / months_inferred
                variance = abs(gross_cur - ytd_avg) / ytd_avg
                stability_flag = "stable" if variance <= 0.10 else "variable"

        return {
            "Gross Monthly Income": gross_monthly_income,
            "paystub_recency_days": days_old,
            "total_deductions": round(ded_cur, 2),
            "recency_check": recency_check,
            "stability_flag": stability_flag
        }
