from __future__ import annotations
from typing import Dict, Any, List, Optional
from datetime import date, timedelta, datetime


class BankStatementKPIs:
    """
    Compute underwriting KPIs from a bank statement JSON with fields:
      {
        "transactions_table": [
          {"date": "Apr-01-14", "description": "...", "amount": "694.81", "type": "Credit"|"Debit"|""},
          ...
        ]
      }

    Returned KPIs:
      - average_monthly_transaction_count
      - monthly_average_debit
      - monthly_average_credit
      - average_monthly_debit_credit_ratio
      - average_monthly_balance
    """

    # ---------- parsing helpers ----------
    @staticmethod
    def _amt(x: Any) -> float:
        if x is None:
            return 0.0
        try:
            return float(str(x).replace("$", "").replace(",", "").strip())
        except Exception:
            return 0.0

    @staticmethod
    def _parse_date(token: str) -> Optional[date]:
        """
        Parse date strings in multiple formats, such as:
          - 'Apr-01-14' or 'Sep-03-00' (month abbrev + day + 2-digit year)
          - '03-10-2025' or '2025-03-10' (numeric month-day-year)
          - '03/10/2025' or '2025/03/10' (with slashes)
        """
        if not token:
            return None

        token = token.strip()

        # Try custom 'Apr-01-14' format (3-letter month + day + 2-digit year)
        try:
            mon_abbr, dd, yy = token.split("-")
            if len(mon_abbr) == 3 and mon_abbr.isalpha():
                month = datetime.strptime(mon_abbr, "%b").month
                day = int(dd)
                year2 = int(yy)
                year = 2000 + year2 if year2 <= 25 else 1900 + year2
                return date(year, month, day)
        except Exception:
            pass

        # Try common date formats in order
        for fmt in (
            "%d-%m-%Y",  # 03-10-2025
            "%m-%d-%Y",  # 10-03-2025 (if month/day swapped)
            "%Y-%m-%d",  # 2025-03-10
            "%d/%m/%Y",  # 03/10/2025
            "%m/%d/%Y",  # 10/03/2025
            "%b-%d-%Y",  # Apr-01-2014
            "%b %d, %Y", # Apr 01, 2014
        ):
            try:
                return datetime.strptime(token, fmt).date()
            except Exception:
                continue

        return None

    @staticmethod
    def _month_key(d: date) -> date:
        """First of month as a key."""
        return d.replace(day=1)

    # ---------- main API ----------
    def calculate(self, statement: Dict[str, Any]) -> Dict[str, float | None]:
        rows: List[Dict[str, Any]] = statement.get("transactions_table", []) or []

        # Parse transactions
        parsed = []
        for r in rows:
            d = self._parse_date(str(r.get("date", "")).strip())
            desc = (r.get("description") or "").strip()
            amt = self._amt(r.get("amount"))
            t = (r.get("type") or "").strip().lower()
            parsed.append({"date": d, "description": desc, "amount": amt, "type": t})

        # Drop rows without a valid date
        parsed = [r for r in parsed if r["date"] is not None]
        if not parsed:
            return {
                "average_monthly_transaction_count": 0.0,
                "monthly_average_debit": 0.0,
                "monthly_average_credit": 0.0,
                "average_monthly_debit_credit_ratio": None,
                "average_monthly_balance": 0.0,
            }

        # Sort by date
        parsed.sort(key=lambda r: r["date"])

        # Detect opening balance (row with "previous balance" and empty type)
        opening_balance = 0.0
        if "previous balance" in parsed[0]["description"].lower() and parsed[0]["type"] == "":
            opening_balance = parsed[0]["amount"]
            # exclude this row from transaction counts/totals (it’s just the starting balance)
            parsed = parsed[1:]

        # Build signed amounts for monthly debit/credit stats
        tx_by_month: Dict[date, Dict[str, float]] = {}
        count_by_month: Dict[date, int] = {}

        for r in parsed:
            mkey = self._month_key(r["date"])
            tx_by_month.setdefault(mkey, {"debit": 0.0, "credit": 0.0})
            count_by_month[mkey] = count_by_month.get(mkey, 0) + 1

            if r["type"] == "credit":
                tx_by_month[mkey]["credit"] += r["amount"]
            elif r["type"] == "debit":
                tx_by_month[mkey]["debit"] += r["amount"]
            else:
                # Unknown type -> ignore for debit/credit totals
                pass
        print(tx_by_month)
        # Averages across observed months
        months = sorted(tx_by_month.keys())
        n_months = max(1, len(months))

        avg_tx_count = sum(count_by_month.get(m, 0) for m in months) / n_months
        avg_debit = sum(tx_by_month[m]["debit"] for m in months) / n_months
        avg_credit = sum(tx_by_month[m]["credit"] for m in months) / n_months
        ratio = (avg_debit / avg_credit) if avg_credit and avg_credit > 0 else None

        # ----- Average monthly balance via daily running balance -----
        # Create daily series from min to max date (inclusive)
        start_date = parsed[0]["date"]
        end_date = parsed[-1]["date"]

        # Build list of transactions per day with signed impact
        by_day: Dict[date, float] = {}
        for r in parsed:
            impact = 0.0
            if r["type"] == "credit":
                impact = r["amount"]
            elif r["type"] == "debit":
                impact = -r["amount"]
            # else unknown -> 0
            by_day[r["date"]] = by_day.get(r["date"], 0.0) + impact

        # Run daily balance
        daily_balances: List[Dict[str, Any]] = []
        bal = opening_balance
        cur = start_date
        # carry balance until the first transaction day (if opening balance exists)
        # then apply daily impacts
        while cur <= end_date:
            # apply today’s net impact (if any)
            bal += by_day.get(cur, 0.0)
            daily_balances.append({"date": cur, "balance": bal})
            cur += timedelta(days=1)

        # Average balance per month, then average across months
        bal_by_month: Dict[date, List[float]] = {}
        for row in daily_balances:
            mkey = self._month_key(row["date"])
            bal_by_month.setdefault(mkey, []).append(row["balance"])

        monthly_avg_balances = [sum(vals) / len(vals) for vals in bal_by_month.values()]
        avg_monthly_balance = sum(monthly_avg_balances) / len(monthly_avg_balances) if monthly_avg_balances else 0.0

        return {
            "average_monthly_transaction_count": round(avg_tx_count, 2),
            "monthly_average_debit": round(avg_debit, 2),
            "monthly_average_credit": round(avg_credit, 2),
            "average_monthly_debit_credit_ratio": round(ratio, 4) if ratio is not None else None,
            "average_monthly_balance": round(avg_monthly_balance, 2),
        }