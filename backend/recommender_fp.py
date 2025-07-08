from __future__ import annotations

import ast
from pathlib import Path
from typing import List, Dict, Tuple

import pandas as pd


class FPGrowthRecommender:
    """FP‑Growth rule‑based recommender (single‑item lookup)."""

    # ────────────────────────────────────────────────────────────────
    def __init__(self, rule_path: str | Path):
        rule_path = Path(rule_path)
        if not rule_path.exists():
            raise FileNotFoundError(f"Rules file not found: {rule_path}")

        rules = pd.read_csv(rule_path)
        if not {"antecedent", "consequent", "confidence"}.issubset(rules.columns):
            raise ValueError("rules.csv must have antecedent, consequent, confidence columns")

        # ── Parse antecedent safely ────────────────────────────────
        def parse(val) -> List[str]:
            """
            Try to parse list-string; fall back to single string.
            Always return lower‑cased list of items.
            """
            try:
                res = ast.literal_eval(str(val))
                if isinstance(res, list):
                    return [str(i).strip().lower() for i in res]
            except Exception:
                pass
            # fallback: treat as single item
            return [str(val).strip().lower()]

        rules["antecedent"] = rules["antecedent"].apply(parse)
        rules["consequent"] = rules["consequent"].astype(str).str.lower().str.strip()

        # Sort by confidence (desc)
        rules = rules.sort_values("confidence", ascending=False, ignore_index=True)

        # ── Build lookup: item → list[(consequent, confidence)] ──
        self._lookup: Dict[str, List[Tuple[str, float]]] = {}
        for _, row in rules.iterrows():
            for a in row["antecedent"]:
                self._lookup.setdefault(a, []).append((row["consequent"], row["confidence"]))

    # ────────────────────────────────────────────────────────────────
    def recommend(self, item: str, top_k: int = 5) -> List[str]:
        """
        Return up to `top_k` consequents for `item`.
        Fuzzy: if exact key missing, takes first antecedent containing `item`.
        """
        key = item.strip().lower()
        pool = self._lookup.get(key)

        if pool is None:  # fuzzy substring match
            pool = next((v for k, v in self._lookup.items() if key in k), [])

        if not pool:
            return []

        # deduplicate, keep order
        seen, results = set(), []
        for cons, _ in pool:
            if cons not in seen:
                seen.add(cons)
                results.append(cons)
            if len(results) >= top_k:
                break
        return results

    # ────────────────────────────────────────────────────────────────
    def available_items(self) -> List[str]:
        """Return sorted list of all individual items with outgoing rules."""
        return sorted(self._lookup.keys())
