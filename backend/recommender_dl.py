from __future__ import annotations

from pathlib import Path
from typing import List, Dict

import torch


class NCF(torch.nn.Module):
    def __init__(self, n_users: int, n_items: int, emb_size: int = 64):
        super().__init__()
        self.u_emb = torch.nn.Embedding(n_users, emb_size)
        self.i_emb = torch.nn.Embedding(n_items, emb_size)
        self.fc = torch.nn.Sequential(
            torch.nn.Linear(emb_size * 2, 128),
            torch.nn.ReLU(),
            torch.nn.Linear(128, 1),
            torch.nn.Sigmoid(),
        )

    def forward(self, u, i):
        x = torch.cat([self.u_emb(u), self.i_emb(i)], dim=1)
        return self.fc(x).squeeze()


class DLRecommender:
    """
    Neural Collaborative Filtering inference wrapper.

    * Handles both str and int keys in user2idx/item2idx.
    * Always returns list[str] of item_id (len <= top_k).
    """

    def __init__(self, ckpt_path: str | Path):
        ckpt = torch.load(ckpt_path, map_location="cpu", weights_only=False)

        # --- harmonize user/item mapping to int keys ---
        raw_u2i: Dict[str, int] = ckpt["user2idx"]
        self.user2idx: Dict[int, int] = {}
        for k, v in raw_u2i.items():
            try:
                self.user2idx[int(k)] = v
            except ValueError:
                # fallback keep as hash of str key (rare)
                self.user2idx[k] = v

        raw_i2i: Dict[str, int] = ckpt["item2idx"]
        self.item2idx: Dict[str, int] = {k: v for k, v in raw_i2i.items()}
        self.idx2item: Dict[int, str] = {v: k for k, v in self.item2idx.items()}

        n_users = max(self.user2idx.values()) + 1
        n_items = max(self.item2idx.values()) + 1

        self.model = NCF(n_users, n_items).eval()
        self.model.load_state_dict(ckpt["model"])

    # ------------------------------------------------------------------ #
    # Public API
    # ------------------------------------------------------------------ #
    @torch.inference_mode()
    def recommend(self, user_id: int | str, top_k: int = 5) -> List[str]:
        """
        Return up to `top_k` item_ids with highest predicted score for `user_id`.
        If user not in mapping → return [].
        """
        # normalize user_id key (int preferred)
        try:
            uid_key = int(user_id)
        except ValueError:
            uid_key = user_id  # keep as original if cannot cast

        if uid_key not in self.user2idx:
            return []

        u_idx_val = self.user2idx[uid_key]
        u_idx = torch.full((len(self.item2idx),), u_idx_val, dtype=torch.long)
        i_idx = torch.arange(len(self.item2idx), dtype=torch.long)

        scores = self.model(u_idx, i_idx)
        top_idx = torch.topk(scores, top_k).indices.tolist()
        return [self.idx2item[i] for i in top_idx]
