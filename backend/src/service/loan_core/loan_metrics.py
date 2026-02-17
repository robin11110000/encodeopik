from __future__ import annotations
from dataclasses import dataclass
from typing import Any, Dict, Optional
import json
import argparse
import json


@dataclass
class Weights:
    """
    Defines the weighting factors for various loan underwriting metrics.
    These weights determine the relative importance of each feature
    when calculating the final loan approval score.
    """
    income: float = 0.20
    credit: float = 0.23
    delinquency_risk: float = 0.18
    dti: float = 0.23
    liquidity: float = 0.09
    income_consistency: float = 0.03
    employment_stability: float = 0.02
    residency_stability: float = 0.02  # optional / can be ignored

    def normalize(self):
        """Normalizes all weight values so they sum up to 1."""
        total = sum(getattr(self, f) for f in self.__dataclass_fields__)
        for f in self.__dataclass_fields__:
            setattr(self, f, getattr(self, f) / total)


def _to_float(x):
    """
    Converts string-like numerical values (e.g., "$2,500", "1,000")
    into a clean float. Returns None if conversion fails.
    """
    if x is None:
        return None
    try:
        return float(str(x).replace("$", "").replace(",", "").strip())
    except:
        return None


class LoanUnderwritingScorerSimple:
    """
    A simplified loan underwriting scorer.
    It evaluates multiple dimensions (income, credit, delinquency, liquidity, etc.)
    and produces a weighted score representing applicant risk.
    """

    def __init__(self, weights: Weights | None = None):
        # Initialize with default or provided weights
        self.w = weights or Weights()
        self.w.normalize()

    # ------------------------- Scoring Sub-Functions -------------------------

    def _score_income(self, days_old):
        """
        Scores income recency (how recent the paystub is).
        More recent = higher score.
        """
        if days_old is None or days_old < 0:
            return None
        if days_old <= 45:
            return 100
        if days_old <= 90:
            return 100 - (days_old - 45) * (40 / 45)   # 100 → 60
        if days_old <= 180:
            return 60 - (days_old - 90) * (30 / 90)    # 60 → 30
        if days_old <= 365:
            return 30 - (days_old - 180) * (20 / 185)  # 30 → 10
        return 0

    def _score_credit(self, cs):
        """
        Scores based on the applicant's credit score.
        Higher credit score = higher points.
        """
        print(f"Credit score - {cs}")
        if cs is None:
            return None
        if cs >= 750:
            return 100
        if cs >= 700:
            return 80 + (cs - 700) * 0.4
        if cs >= 650:
            return 60 + (cs - 650) * 0.4
        if cs >= 600:
            return 40 + (cs - 600) * 0.4
        return 20

    def _score_dti(self, dti):
        """Scores the debt-to-income ratio (lower DTI = higher score)."""
        if dti is None:
            return None
        if dti <= 0.25:
            return 100
        if dti <= 0.36:
            return 80
        if dti <= 0.43:
            return 60
        return 20

    def _score_liquidity(self, balance):
        """Scores average account balance to gauge liquidity strength."""
        if balance is None:
            return None
        if balance >= 5000:
            return 100
        if balance >= 2500:
            return 80
        if balance >= 1000:
            return 60
        if balance >= 0:
            return 40
        return 20

    def _score_delinquency(self, d30, d60, d90, banks, col):
        """
        Penalizes applicant based on delinquency, bankruptcies, and collections.
        Each delinquency reduces the score proportionally.
        """
        score = 100
        score -= min(d30, 5) * 8
        score -= min(d60, 5) * 18
        score -= min(d90, 5) * 28
        score -= min(col, 5) * 15
        score -= min(banks, 2) * 50
        return max(0, min(100, score))

    def _score_income_stability(self, flag):
        """
        Scores income stability labels (e.g., 'stable', 'variable').
        """
        if not flag:
            return None
        flag = flag.lower()
        if flag in ("stable", "consistent"):
            return 100
        if flag in ("variable", "volatile"):
            return 60
        return 80

    def _score_employment_stability(self, months):
        """
        Scores based on employment tenure in months.
        Longer tenure = higher stability = higher score.
        """
        if months is None:
            return None
        if months >= 24:
            return 100
        if months >= 12:
            return 70
        return 40

    def _score_residency(self, recency_label):
        """
        Scores residency recency 
        """
        if not recency_label:
            return 0
        if "yes" in recency_label.lower():
            return 100
        if "no" in recency_label.lower():
            return 0
        return 60

    # ---------------------- Utility Function ----------------------

    def json_to_python_dict(self, json_like):
        """
        Converts a JSON-like string (possibly with true/false/null)
        into a valid Python dictionary. Ensures safe replacement of
        null → "None", true/false → True/False.
        """
        if isinstance(json_like, str):
            data = json.loads(json_like)
        elif isinstance(json_like, dict):
            data = json_like
        else:
            return {}

        def replace_none(obj):
            if isinstance(obj, dict):
                return {k: replace_none(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [replace_none(v) for v in obj]
            elif obj is None:
                return "None"
            return obj

        return replace_none(data)

    # ---------------------- Main Scoring Function ----------------------

    def score(self, f: Dict[str, Any]) -> Dict[str, Any]:
        """
        Main scoring pipeline:
        Extracts financial and behavioral metrics,
        computes individual scores, then aggregates them
        using weighted averages (ignoring missing values).
        """

        # Extract and normalize raw inputs
        days_old = _to_float(f.get("paystub_recency_days"))
        cs = _to_float(f.get("credit_score") or f.get("representative_credit_score"))
        dti = _to_float(f.get("debt_to_income_ratio") or f.get("dti"))
        bal = _to_float(f.get("average_monthly_balance"))
        d30 = int(_to_float(f.get("30_day_delinquencies") or 0))
        d60 = int(_to_float(f.get("60_day_delinquencies") or 0))
        d90 = int(_to_float(f.get("90_day_delinquencies") or 0))
        banks = int(_to_float(f.get("bankruptcies") or 0))
        col = int(_to_float(f.get("collections") or 0))
        stab = f.get("stability_flag")
        emp = _to_float(f.get("employment_tenure_months"))
        res = f.get("Consistency")

        # Compute sub-scores for all dimensions
        scores = {
            "income_score": self._score_income(days_old),
            "credit_score_score": self._score_credit(cs),
            "delinquency_risk_score": self._score_delinquency(d30, d60, d90, banks, col),
            "dti_score": self._score_dti(dti),
            "liquidity_score": self._score_liquidity(bal),
            "income_consistency_score": self._score_income_stability(stab),
            "employment_stability_score": self._score_employment_stability(emp),
            "residency_stability_score": self._score_residency(res)
        }

        # Compute weighted average, ignoring None values
        total_w = 0
        total_s = 0
        for name, score in scores.items():
            if score is not None:
                w = getattr(self.w, name.replace("_score", ""))
                total_w += w
                total_s += w * score

        # Return detailed breakdown and final score
        return {
            "sub_scores": scores,
            "final_weighted_score": round(total_s / total_w, 2) if total_w > 0 else None
        }
