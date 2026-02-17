class IncomeKPI:
    """
    Compute income-based underwriting KPIs from parsed 1040 data.
    """

    def __init__(self, effective_tax_rate: float = 0.22):
        # Allow configurable tax assumption
        self.effective_tax_rate = effective_tax_rate

    @staticmethod
    def _to_float(value):
        """Safely convert string/number to float."""
        try:
            if value is None:
                return 0.0
            return float(str(value).replace(",", "").strip())
        except Exception:
            return 0.0

    def calculate(self, data: dict) -> dict:
        # Extract values
        total_income = self._to_float(data.get("total_income"))
        total_wages = self._to_float(data.get("total_wages"))
        taxable_income = self._to_float(data.get("taxable_income"))

        # KPI 1: Gross Monthly Income
        gross_monthly_income = total_income / 12 if total_income > 0 else 0

        # KPI 2: Estimated Take-Home Pay
        estimated_take_home = gross_monthly_income * (1 - self.effective_tax_rate)

        # KPI 3: Income Type
        income_type = "Salaried (W-2)" if total_wages > 0 else "Other / Unknown"

        # KPI 4: Income Stability Indicator
        income_stability = "Stable Income" if total_wages > 0 else "Needs Verification"

        # KPI 5: Taxable-Income Ratio
        taxable_income_ratio = (
            taxable_income / total_income if total_income > 0 else None
        )

        return {
            "Gross Monthly Income": round(gross_monthly_income, 2),
            "Estimated Take-Home Pay": round(estimated_take_home, 2),
            "Income Type": income_type,
            "Income Stability Indicator": income_stability,
            "Taxable-Income Ratio": (
                round(taxable_income_ratio, 2)
                if taxable_income_ratio is not None
                else None
            ),
        }