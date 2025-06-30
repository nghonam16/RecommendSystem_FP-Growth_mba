import torch
from pathlib import Path
from typing import List

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
    def __init__(self, ckpt_path: str | Path):
        ckpt = torch.load(ckpt_path, map_location="cpu", weights_only=False)


        self.user2idx = ckpt["user2idx"]
        self.item2idx = ckpt["item2idx"]
        self.idx2item = {v: k for k, v in self.item2idx.items()}

        n_users = len(self.user2idx)
        n_items = len(self.item2idx)

        self.model = NCF(n_users, n_items).eval()
        self.model.load_state_dict(ckpt["model"])

    @torch.inference_mode()
    def recommend(self, user_id: int, top_k: int = 5) -> List[str]:
        if user_id not in self.user2idx:
            return []

        u_idx = torch.tensor([self.user2idx[user_id]] * len(self.item2idx))
        i_idx = torch.arange(len(self.item2idx))

        scores = self.model(u_idx, i_idx).numpy()
        top_idx = scores.argsort()[::-1][:top_k]
        return [self.idx2item[i] for i in top_idx]
