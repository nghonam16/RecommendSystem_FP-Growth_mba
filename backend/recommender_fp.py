from __future__ import annotations


from pathlib import Path
from typing import List

import pandas as pd


class FPGrowthRecommender:
    
    def __init__(self, rule_path: str | Path):
        self.rule_path = Path(rule_path)
        if not self.rule_path.exists():
            raise FileNotFoundError(f"Rules file not found: {self.rule_path}")

        rules = pd.read_csv(self.rule_path)
        if not {"antecedent", "consequent", "confidence"}.issubset(rules.columns):
            raise ValueError("rules.csv must contain antecedent, consequent, confidence columns")

        rules["antecedent"] = (
            rules["antecedent"].astype(str).str.strip().str.lower()
        )
        rules["consequent"] = rules["consequent"].astype(str).str.strip()

        # Sort by confidence so the first elements are the most relevant.
        rules = rules.sort_values("confidence", ascending=False, ignore_index=True)

        # Build lookup: {antecedent: list[(consequent, confidence)]}
        self._lookup: dict[str, list[tuple[str, float]]] = (
            rules.groupby("antecedent")[["consequent", "confidence"]]
            .apply(lambda df: list(df.itertuples(index=False, name=None)))
            .to_dict()
        )

    # Public API
    def recommend(self, item: str, top_k: int = 5) -> List[str]:

        key = item.strip().lower()
        if key not in self._lookup:
            return []
        return [conseq for conseq, _ in self._lookup[key][: top_k]]

    def available_items(self) -> List[str]:
        """Return a sorted list of all items that have outgoing rules."""
        return sorted(self._lookup.keys())
