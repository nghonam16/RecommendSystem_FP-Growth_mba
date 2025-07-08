import streamlit as st
import requests
import os
import pathlib
import pandas as pd

# =========================
# Config & Constants
# =========================
API_URL   = os.getenv("API_URL", "http://localhost:8000")
PAGE_ICON = "🧠"
PAGE_TITLE = "Hybrid Recommender UI"

st.set_page_config(page_title=PAGE_TITLE,
                   page_icon=PAGE_ICON,
                   layout="centered")

# =========================
# Load external CSS
# =========================
css_path = pathlib.Path(__file__).parent / "style.css"
if css_path.exists():
    st.markdown(f"<style>{css_path.read_text()}</style>", unsafe_allow_html=True)

# =========================
# Load products metadata
# =========================
products_path = pathlib.Path(__file__).parent / "products.csv"
products_df = None
if products_path.exists():
    try:
        products_df = pd.read_csv(products_path)
    except Exception as e:
        st.warning(f"⚠️ Could not read products.csv: {e}")
else:
    st.warning("⚠️ products.csv not found – price & category will be hidden.")

# Helper to lookup price/category

def lookup_meta(item_name: str):
    if products_df is None:
        return {"name": item_name, "price": None, "category": None}
    row = products_df[products_df['item_id'].str.lower() == item_name.lower()]
    if not row.empty:
        r = row.iloc[0]
        return {
            "name": item_name,
            "price": r.get('price', None),
            "category": r.get('category', None)
        }
    return {"name": item_name, "price": None, "category": None}

# =========================
# Header
# =========================
st.markdown("<h2>🛍️ Xin chào!</h2>", unsafe_allow_html=True)
st.markdown("---")

# =========================
# Popular test user IDs (static list for graders)
# =========================
with st.expander("🎯 Popular test user IDs (click to view)"):
    st.markdown(
        "- **14911** – 1 816 purchases\n"
        "- **12748** – 1 778 purchases\n"
        "- **17841** – 1 345 purchases\n"
        "- **14096** – 1 129 purchases\n"
        "- **14298** – 891 purchases\n"
        "- **14606** – 826 purchases\n"
        "- **14156** – 730 purchases\n"
        "- **14769** – 724 purchases\n"
        "- **14646** – 718 purchases\n"
        "- **13089** – 662 purchases"
    )

# =========================
# Input Form
# =========================
with st.form("hybrid_form"):
    st.subheader("Enter information to get suggestions")

    col1, col2 = st.columns(2)
    with col1:
        user_id = st.number_input("User ID (NCF):", min_value=1, step=1, value=14911)
    with col2:
        bought_items = st.text_input("Purchased products (comma‑separated):",
                                     placeholder="alarm clock bakelike green, red mug")

    top_k = st.slider("Number of suggestions per source (Top K):", 1, 10, 3)
    submitted = st.form_submit_button("🚀 SHOW SUGGESTIONS")

# =========================
# Fetch & Display
# =========================
if submitted:
    st.markdown("---")
    with st.spinner("Fetching recommendations…"):
        # Deep‑Learning
        dl_raw = []
        try:
            resp_dl = requests.get(f"{API_URL}/recommend/by-user",
                                   params={"user_id": user_id, "top_k": top_k}, timeout=10)
            resp_dl.raise_for_status()
            dl_raw = resp_dl.json().get("suggestions", [])
        except Exception as e:
            st.error(f"❌ NCF error: {e}")

        # FP‑Growth
        fp_raw = []
        bought_list = [b.strip() for b in bought_items.split(',') if b.strip()]
        for itm in bought_list:
            try:
                resp_fp = requests.get(f"{API_URL}/recommend/by-item",
                                       params={"item": itm, "top_k": top_k}, timeout=10)
                resp_fp.raise_for_status()
                fp_raw.extend(resp_fp.json().get("suggestions", []))
            except Exception as e:
                st.error(f"❌ FP‑Growth error for '{itm}': {e}")

        # Deduplicate
        fp_names = []
        for x in fp_raw:
            if x not in bought_list and x not in fp_names:
                fp_names.append(x)
            if len(fp_names) >= top_k:
                break

    # Helpers to render cards
    def build_card(meta):
        price_html = f"<br><span class='item-price'>💰 ${meta['price']:.2f}</span>" if meta['price'] is not None else ""
        cat_html   = f"<br><span class='item-cat'>🏷️ {meta['category']}</span>"   if meta['category'] else ""
        return f"<div class='recommend-item'>📦 <strong>{meta['name']}</strong>{price_html}{cat_html}</div>"

    def render_block(title, metas):
        st.markdown(f"<div class='recommend-box'><h3>{title}</h3><div>", unsafe_allow_html=True)
        for m in metas:
            st.markdown(build_card(m), unsafe_allow_html=True)
        st.markdown("</div></div>", unsafe_allow_html=True)

    dl_meta = [lookup_meta(n) for n in dl_raw]
    fp_meta = [lookup_meta(n) for n in fp_names]

    if dl_meta:
        render_block("🧠 Smart suggestions for you (AI):", dl_meta)
    else:
        st.info("No AI suggestions.")

    if fp_meta:
        render_block("🧾 Suggestions based on common behaviour:", fp_meta)
    else:
        st.info("No FP‑Growth suggestions.")

    st.markdown("---")

st.caption("Powered by **FP‑Growth** + **Neural Collaborative Filtering (NCF)**")
