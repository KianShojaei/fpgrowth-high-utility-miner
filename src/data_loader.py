"""Loader for Quantitative Transactional Databases and External Utility (Profit) Tables."""

import csv
import io
from dataclasses import dataclass
from typing import Dict, List, Tuple


@dataclass
class QuantitativeTransaction:
    """Represents a transaction with item quantities and computed utilities."""

    tid: str
    item_quantities: Dict[str, int]
    item_utilities: Dict[str, float]
    transaction_utility: float


class UtilityDataLoader:
    """Parses quantitative transactions (Item:Quantity) and external profit tables."""

    @staticmethod
    def parse_profit_table(profit_csv: str) -> Dict[str, float]:
        """Parse external utility (unit profit) table from CSV text."""
        lines = [line.strip() for line in profit_csv.strip().splitlines() if line.strip()]
        if not lines:
            return {}

        reader = list(csv.reader(io.StringIO("\n".join(lines))))
        profits: Dict[str, float] = {}

        for row in reader:
            cols = [c.strip() for c in row if c.strip()]
            if len(cols) < 2:
                continue
            if cols[0].lower() in ("item", "items", "name", "آیتم"):
                continue
            try:
                profits[cols[0]] = float(cols[1])
            except ValueError:
                continue

        return profits

    @staticmethod
    def parse_transactions(
        trans_csv: str,
        profits: Dict[str, float],
    ) -> Tuple[List[QuantitativeTransaction], Dict[str, float]]:
        """Parse quantitative transactions from CSV text.

        Supports format:
            TID, "a:1, c:6, e:2"  or  TID, "a, c, e" (defaults quantity to 1)
        If an item is missing from `profits`, assigns a default unit profit of 1.0.
        """
        lines = [line.strip() for line in trans_csv.strip().splitlines() if line.strip()]
        if not lines:
            return [], profits

        reader = list(csv.reader(io.StringIO("\n".join(lines))))
        if not reader:
            return [], profits

        updated_profits = dict(profits)
        first_lower = [c.strip().lower() for c in reader[0]]
        start_idx = 1 if ("tid" in first_lower or "items" in first_lower) else 0

        transactions: List[QuantitativeTransaction] = []

        for idx, row in enumerate(reader[start_idx:], start=1):
            cols = [c.strip() for c in row if c.strip()]
            if not cols:
                continue

            if len(cols) >= 2:
                tid = cols[0]
                raw_items_str = ",".join(cols[1:])
            else:
                tid = f"T{idx}"
                raw_items_str = cols[0]

            raw_tokens = [tok.strip() for tok in raw_items_str.replace(";", ",").split(",") if tok.strip()]
            item_quantities: Dict[str, int] = {}

            for tok in raw_tokens:
                if ":" in tok:
                    parts = tok.split(":", 1)
                    item_name = parts[0].strip()
                    try:
                        qty = int(float(parts[1].strip()))
                    except ValueError:
                        qty = 1
                else:
                    item_name = tok.strip()
                    qty = 1

                if item_name and qty > 0:
                    item_quantities[item_name] = item_quantities.get(item_name, 0) + qty
                    if item_name not in updated_profits:
                        updated_profits[item_name] = 1.0

            if item_quantities:
                item_utils = {
                    it: qty * updated_profits[it] for it, qty in item_quantities.items()
                }
                tu = sum(item_utils.values())
                transactions.append(
                    QuantitativeTransaction(
                        tid=str(tid),
                        item_quantities=item_quantities,
                        item_utilities=item_utils,
                        transaction_utility=tu,
                    )
                )

        return transactions, updated_profits
