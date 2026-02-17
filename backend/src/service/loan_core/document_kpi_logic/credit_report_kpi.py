from __future__ import annotations
from typing import Dict, Any, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime
import json
import re


@dataclass
class ScoreBands:
    excellent_min: int = 750
    good_min: int = 700
    fair_min: int = 650

    def band(self, score: Optional[int]) -> str:
        if score is None:
            return "unknown"
        if score >= self.excellent_min:
            return "excellent"
        if score >= self.good_min:
            return "good"
        if score >= self.fair_min:
            return "fair"
        return "poor"


class CreditReportKPIs:
    """
    Compute underwriting KPIs from a credit report payload,
    EXCLUDING employment and identity.

    Public API:
      - calculate(report: Dict[str, Any], reference_date: Optional[str]) -> Dict[str, Any]

    reference_date:
      ISO date ("YYYY-MM-DD"). If omitted, uses today's date for recency calcs.
    """

    def __init__(self, bands: ScoreBands | None = None) -> None:
        self.bands = bands or ScoreBands()

    # ------------------------
    # Parsing helpers
    # ------------------------
    @staticmethod
    def _to_float(val: Optional[str]) -> Optional[float]:
        if val is None:
            return None
        try:
            cleaned = str(val).replace("$", "").replace(",", "").strip()
            return float(cleaned)
        except ValueError:
            return None

    @staticmethod
    def _to_int(val: Optional[str]) -> Optional[int]:
        if val is None:
            return None
        try:
            cleaned = str(val).replace(",", "").strip()
            return int(float(cleaned))
        except ValueError:
            return None

    @staticmethod
    def _parse_age_to_months(text: Optional[str]) -> Optional[int]:
        """
        Parse strings like "8 years and 9 months" or "5 years 8 months" to total months.
        """
        if not text:
            return None
        s = text.lower()
        years = 0
        months = 0
        y_match = re.search(r"(\d+)\s*year", s)
        m_match = re.search(r"(\d+)\s*month", s)
        if y_match:
            years = int(y_match.group(1))
        if m_match:
            months = int(m_match.group(1))
        total = years * 12 + months
        return total if total > 0 else None

    @staticmethod
    def _parse_mm_yyyy(text: str) -> Optional[Tuple[int, int]]:
        """
        Extract (month, year) from strings like "STUDENT LOAN (09/2010)" or "06/2023".
        """
        if not text:
            return None
        m = re.search(r"\b(0?[1-9]|1[0-2])\s*/\s*(\d{4})\b", text)
        if not m:
            return None
        month = int(m.group(1))
        year = int(m.group(2))
        return month, year

    @staticmethod
    def _months_between(d1: datetime, d2: datetime) -> int:
        """Absolute month difference between two dates."""
        ydiff = d2.year - d1.year
        mdiff = d2.month - d1.month
        total = ydiff * 12 + mdiff
        # If day of d2 is earlier than day of d1, treat as not a full month yet
        if d2.day < d1.day:
            total -= 1
        return abs(total)

    @staticmethod
    def _parse_date_any(text: Optional[str]) -> Optional[datetime]:
        """
        Parse dates like "5/11/2024", "7/1/2021", or "2024-05-11".
        """
        if not text:
            return None
        text = text.strip()
        fmts = ["%m/%d/%Y", "%m/%d/%y", "%Y-%m-%d"]
        for fmt in fmts:
            try:
                return datetime.strptime(text, fmt)
            except ValueError:
                continue
        return None

    # ------------------------
    # Main calculation
    # ------------------------
    def calculate(
        self,
        report: Dict[str, Any],
        reference_date: Optional[str] = None,
    ) -> Dict[str, Any]:
        # Scores
        vantage = self._to_int(report.get("vantage_score_3_0"))
        insight = self._to_int(report.get("insight_score"))
        representative = vantage if vantage is not None else insight
        band = self.bands.band(representative)

        # Credit history / mix
        total_accounts = self._to_int(report.get("total_accounts"))
        open_tradelines = self._to_int(report.get("current_tradelines"))
        revolving = self._to_int(report.get("revolving_accounts")) or 0
        installment = self._to_int(report.get("installment_accounts")) or 0
        mortgage = self._to_int(report.get("mortgage_accounts")) or 0

        credit_mix_strength = "unknown"
        if (revolving + installment + mortgage) >= 3 and revolving >= 1 and installment >= 1:
            credit_mix_strength = "adequate_mix"
        elif (revolving + installment + mortgage) >= 1:
            credit_mix_strength = "limited_mix"

        # Credit age
        avg_age_months = self._parse_age_to_months(report.get("average_account_age"))
        file_age_months = self._parse_age_to_months(report.get("account_length"))
        file_age_years = round((file_age_months or 0) / 12.0, 2) if file_age_months else None

        oldest_open = report.get("oldest_open_account")  # e.g., "STUDENT LOAN (09/2010)"
        old_mm_yyyy = self._parse_mm_yyyy(oldest_open) if oldest_open else None
        oldest_open_account_open_date = None
        if old_mm_yyyy:
            oldest_open_account_open_date = f"{old_mm_yyyy[1]:04d}-{old_mm_yyyy[0]:02d}"

        most_recent = report.get("most_recent_account")  # e.g., "Auto Loan (06/2023)"
        mr_mm_yyyy = self._parse_mm_yyyy(most_recent) if most_recent else None

        # Choose reference date for "months ago"
        ref_dt = None
        if reference_date:
            ref_dt = self._parse_date_any(reference_date)
        if ref_dt is None:
            ref_dt = datetime.today()

        recent_months_ago = None
        if mr_mm_yyyy:
            acc_dt = datetime(year=mr_mm_yyyy[1], month=mr_mm_yyyy[0], day=1)
            recent_months_ago = self._months_between(acc_dt, ref_dt)

        # Delinquency profile
        d30 = self._to_int(report.get("thirty_day_delinquencies")) or 0
        d60 = self._to_int(report.get("sixty_day_delinquencies")) or 0
        d90 = self._to_int(report.get("ninety_day_delinquencies")) or 0
        has_recent_delinquency = (d30 + d60 + d90) > 0
        overall_delinquency_risk = (
            "minor_recent_issue" if d30 == 1 and d60 == 0 and d90 == 0
            else "elevated" if (d60 + d90) > 0 or d30 >= 2
            else "clean"
        )

        # Negative events
        bankruptcies = self._to_int(report.get("bankruptcies")) or 0
        collections = self._to_int(report.get("collections")) or 0
        is_clean_from_major_derogatory = (bankruptcies == 0 and collections == 0)

        # Inquiry profile (may be missing)
        recent_inquiries_180d = self._to_int(report.get("application_inquiries_180_days"))
        inquiry_risk = "unknown"
        if recent_inquiries_180d is not None:
            inquiry_risk = "high" if recent_inquiries_180d >= 4 else "moderate" if recent_inquiries_180d >= 2 else "low"

        # Exposure
        max_total_principal = self._to_float(report.get("maximum_total_principal"))
        current_principal = self._to_float(report.get("current_principal"))

        kpis: Dict[str, Any] = {
            "representative_credit_score": representative,
            "secondary_score": insight if representative == vantage else vantage,
            "credit_score_band": band,

            "credit_history": {
                "total_accounts": total_accounts,
                "open_tradelines": open_tradelines,
                "revolving_accounts": revolving,
                "installment_accounts": installment,
                "mortgage_accounts": mortgage,
                "credit_mix_strength": credit_mix_strength
            },

            "credit_age": {
                "average_account_age_months": avg_age_months,
                "file_age_years": file_age_years,
                "oldest_account_open_date": oldest_open_account_open_date,
                "recent_account_open_months_ago": recent_months_ago
            },

            "delinquency_profile": {
                "30_day_delinquencies": d30,
                "60_day_delinquencies": d60,
                "90_day_delinquencies": d90,
                "has_recent_delinquency": has_recent_delinquency,
                "overall_delinquency_risk": overall_delinquency_risk
            },

            "negative_events": {
                "bankruptcies": bankruptcies,
                "collections": collections,
                "is_clean_from_major_derogatory": is_clean_from_major_derogatory
            },

            "inquiry_profile": {
                "recent_hard_inquiries_180d": recent_inquiries_180d,
                "inquiry_risk": inquiry_risk
            },

            "exposure_profile": {
                "maximum_total_principal": max_total_principal,
                "current_principal_balance": current_principal
            }
        }
        return kpis