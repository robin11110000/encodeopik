import json

# 🔹 Opik tracing
from src.service.opik_tracing import trace_with_metadata
import opik
from opik import track, opik_context


class DecisionEngine:
    def __init__(self):
        """Initialize the DecisionEngine."""
        pass

    # ------------------------------------------------------------------
    # MAIN DECISION PIPELINE
    # ------------------------------------------------------------------
    @trace_with_metadata(
        name="loan_decision",
        capture_input=True,
        capture_output=True
    )
    def make_decision(
        self,
        loan_metrics={},
        final_score={},
        fraud_result={},
        text_fraud_result={}
    ):
        """
        Make loan approval decision with full tracing.
        """

        # ----------------------------
        # Step 1: Identity Fraud Check
        # ----------------------------
        with opik.start_as_current_span(name="identity_fraud_check") as span:
            is_authentic = fraud_result.get("is_authentic", False)
            is_text_fraud = text_fraud_result.get("type", "Unknown")

            span.metadata = {
                "is_authentic": is_authentic,
                "text_fraud_type": is_text_fraud
            }

        # ----------------------------
        # Step 2: Proceed if authentic
        # ----------------------------
        if is_authentic:

            with opik.start_as_current_span(name="text_fraud_evaluation") as span:
                span.metadata = {
                    "text_fraud_type": is_text_fraud
                }

                if is_text_fraud == "Authentic":

                    # ----------------------------
                    # Step 3: Credit Score Evaluation
                    # ----------------------------
                    with opik.start_as_current_span(name="credit_scoring") as span:
                        score = final_score.get("final_weighted_score", 0)

                        span.metadata = {
                            "credit_score": score
                        }

                    decision = self.evaluate_credit_score(score)

                else:
                    decision = {
                        "status": "manual_review",
                        "reason": "Documents failed text consistency validation",
                        "score": 0,
                    }

        # ----------------------------
        # Step 4: Reject if fraudulent
        # ----------------------------
        else:
            decision = {
                "status": "rejected",
                "reason": "Documents are not authentic",
                "score": 0,
            }

        return decision

    # ------------------------------------------------------------------
    # CREDIT SCORE LOGIC
    # ------------------------------------------------------------------
    @track(name="credit_score_evaluation", capture_input=True, capture_output=True)
    def evaluate_credit_score(self, score):
        """Evaluate credit score and determine final decision."""

        if score >= 60:
            return {
                "status": "approved",
                "reason": "Strong financial and credit indicators",
                "score": score,
            }

        elif 40 <= score < 60:
            return {
                "status": "manual_review",
                "reason": "Borderline score; manual verification needed",
                "score": score,
            }

        else:
            return {
                "status": "rejected",
                "reason": "Low creditworthiness",
                "score": score,
            }
