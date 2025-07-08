import streamlit as st
import requests, os, pathlib, pandas as pd, ast

# ───────────────────────────────────────────────
# 1. File paths & data folder
# ───────────────────────────────────────────────
ROOT_DIR = pathlib.Path(__file__).resolve().parent.parent  # project root (one up from ui/)
DATA_DIR = ROOT_DIR / "data"
PRODUCTS_CSV   = DATA_DIR / "products.csv"
USER_ITEM_CSV  = DATA_DIR / "user_item_dl.csv"
RULES_CSV      = DATA_DIR / "rules.csv"

# ───────────────────────────────────────────────
# 2. Load CSVs with validation
# ───────────────────────────────────────────────
products_df  = pd.read_csv(PRODUCTS_CSV)   if PRODUCTS_CSV.exists()  else None
user_item_df = pd.read_csv(USER_ITEM_CSV)  if USER_ITEM_CSV.exists() else None
rules_df     = pd.read_csv(RULES_CSV)      if RULES_CSV.exists()      else None

if user_item_df is None or rules_df is None:
    st.error("❌ Missing data files in ../data. Please ensure user_item_dl.csv and rules.csv exist.")
    st.stop()

# Build antecedent set by parsing list‑strings → individual items
ante_set: set[str] = set()
for row in rules_df["antecedent"].astype(str):
    try:
        items = [i.strip().lower() for i in ast.literal_eval(row)]
        ante_set.update(items)
    except Exception:
        ante_set.add(row.strip().lower())

# ───────────────────────────────────────────────
# 3. Streamlit page config & CSS
# ───────────────────────────────────────────────
API_URL = os.getenv("API_URL", "http://localhost:8000")
st.set_page_config(page_title="Hybrid Recommender UI", page_icon="🧠", layout="centered")

css_path = pathlib.Path(__file__).parent / "style.css"
if css_path.exists():
    st.markdown(f"<style>{css_path.read_text()}</style>", unsafe_allow_html=True)

# ───────────────────────────────────────────────
# 4. Helper functions
# ───────────────────────────────────────────────

def lookup_meta(item_name: str):
    if products_df is None:
        return {"name": item_name, "price": None, "category": None}
    row = products_df[products_df.item_id.str.lower() == item_name.lower()]
    if not row.empty:
        rec = row.iloc[0]
        return {"name": item_name, "price": rec.price, "category": rec.category}
    return {"name": item_name, "price": None, "category": None}


def html_card(meta: dict) -> str:
    price_html = f"<br><span class='item-price'>💰 ${meta['price']:.2f}</span>" if meta["price"] else ""
    cat_html   = f"<br><span class='item-cat'>🏷️ {meta['category']}</span>"     if meta["category"] else ""
    return f"<div class='recommend-item'>📦 <strong>{meta['name']}</strong>{price_html}{cat_html}</div>"


def render_block(title: str, items: list[str]):
    st.markdown(f"<div class='recommend-box'><h3>{title}</h3><div>", unsafe_allow_html=True)
    if not items:
        st.markdown("<em>Empty.</em>", unsafe_allow_html=True)
    for it in items:
        st.markdown(html_card(lookup_meta(it)), unsafe_allow_html=True)
    st.markdown("</div></div>", unsafe_allow_html=True)

# ───────────────────────────────────────────────
# 5. Build user rank & filter valid users (max 10)
# ───────────────────────────────────────────────
user_rank = (
    user_item_df["user_id"].value_counts().rename_axis("user_id").reset_index(name="count")
)
all_user_ids = user_rank.user_id.astype(int).tolist()


def is_valid_user(uid: int) -> bool:
    items = (
        user_item_df[user_item_df.user_id == uid]["item_id"].str.lower().str.strip().tolist()
    )
    return any(i in ante_set for i in items)

valid_user_ids = [uid for uid in all_user_ids if is_valid_user(uid)][:10]
if not valid_user_ids:
    st.error("❌ No users found matching FP‑Growth antecedents. Check data consistency.")
    st.stop()

# ───────────────────────────────────────────────
# 6. UI layout
# ───────────────────────────────────────────────
st.markdown("<h2>🛍️ Hybrid Recommender Demo</h2>", unsafe_allow_html=True)
st.caption("Select a test user — valid for both AI & FP‑Growth.")
st.markdown("---")

col_user, col_items = st.columns(2)

with col_user:
    st.subheader("👤 Select User (valid)")
    selected_user = st.selectbox("User ID:", options=valid_user_ids, index=0)
    purchase_count = user_rank[user_rank.user_id == selected_user]["count"].iat[0]
    st.write(f"This user purchased **{purchase_count}** items in total.")

user_items = user_item_df[user_item_df.user_id == selected_user]["item_id"].unique().tolist()

with col_items:
    st.subheader("🛒 Products this user bought")
    chosen_items = st.multiselect("Select items:", options=user_items) if user_items else []

# ───────────────────────────────────────────────
# 7. Fetch recommendations
# ───────────────────────────────────────────────

top_k = st.slider("Top‑K suggestions", 1, 10, 3)
if st.button("🚀 Show Suggestions"):
    if not chosen_items:
        st.warning("Please select at least one product.")
    else:
        st.markdown("---")
        with st.spinner("Fetching recommendations…"):
            ai_suggestions: list[str] = []
            try:
                resp = requests.get(
                    f"{API_URL}/recommend/by-user",
                    params={"user_id": selected_user, "top_k": top_k},
                    timeout=10,
                )
                resp.raise_for_status()
                raw = resp.json().get("suggestions", [])
                ai_suggestions = raw if isinstance(raw, list) else []
            except Exception as e:
                st.error(f"NCF error: {e}")

            # FP‑Growth
            fp_pool: list[str] = []
            for prod in chosen_items:
                try:
                    resp = requests.get(
                        f"{API_URL}/recommend/by-item",
                        params={"item": prod, "top_k": top_k},
                        timeout=10,
                    )
                    resp.raise_for_status()
                    raw = resp.json().get("suggestions", [])
                    if isinstance(raw, list):
                        fp_pool.extend(raw)
                except Exception as e:
                    st.error(f"FP‑Growth error for '{prod}': {e}")

            # Deduplicate
            fp_suggestions: list[str] = []
            for s in fp_pool:
                if s not in chosen_items and s not in fp_suggestions:
                    fp_suggestions.append(s)
                if len(fp_suggestions) >= top_k:
                    break

        render_block("🧠 AI (NCF) Recommendations:", ai_suggestions)
        render_block("🔗 Products frequently bought together:", fp_suggestions)
        st.markdown("---")

st.caption("Powered by FP‑Growth + NCF")
