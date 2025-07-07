import streamlit as st
import requests
import json
import os

API_URL = os.getenv("API_URL", "http://localhost:8000")

st.set_page_config(page_title="Hybrid Recommender UI", page_icon="🧠", layout="centered")

st.title("🧠 Hybrid Recommender System")
st.caption("Powered by **FP-Growth** + **Neural Collaborative Filtering (NCF)**")

tab1, tab2, tab3 = st.tabs([
    "🛒 Recommend by Item (FP-Growth)",
    "👤 Recommend by User (NCF)",
    "⚡ Quick Test"
])

# Tab 1: Recommend by Item (FP-Growth)
with tab1:
    st.subheader("📦 Rule-based Suggestions (Association Rules)")
    with st.form(key="item_form"):
        item = st.text_input("Enter product name:", placeholder="e.g., alarm clock bakelike green")
        top_k = st.slider("Number of suggestions (Top K):", 1, 10, 5)
        submit_item = st.form_submit_button("🔍 Get Suggestions")

    if submit_item:
        if item.strip() == "":
            st.warning("⚠️ Please enter a product name.")
        else:
            with st.spinner("Fetching suggestions..."):
                try:
                    res = requests.get(f"{API_URL}/recommend/by-item", params={"item": item, "top_k": top_k})
                    res.raise_for_status()
                    suggestions = res.json().get("suggestions", [])
                    if suggestions:
                        with st.expander("📋 Suggested items:"):
                            for i, s in enumerate(suggestions, 1):
                                st.markdown(f"{i}. **{s}**")
                    else:
                        st.info("No suggestions found for this item.")
                except Exception as e:
                    st.error(f"❌ {e}")

# Tab 2: Recommend by User (NCF)
with tab2:
    st.subheader("🎯 Personalized Suggestions (Deep Learning)")

    with st.form(key="user_form"):
        user_id = st.number_input("Enter User ID:", min_value=1, step=1)
        top_k_user = st.slider("Number of suggestions (Top K):", 1, 10, 5, key="user_topk")
        submit_user = st.form_submit_button("👁️ Get Personalized Recommendations")

    if submit_user:
        with st.spinner("Fetching personalized recommendations..."):
            try:
                res = requests.get(f"{API_URL}/recommend/by-user", params={"user_id": user_id, "top_k": top_k_user})
                res.raise_for_status()
                suggestions = res.json().get("suggestions", [])
                if suggestions:
                    with st.expander("📋 Recommended items:"):
                        for i, s in enumerate(suggestions, 1):
                            st.markdown(f"{i}. **{s}**")
                else:
                    st.info("No recommendations found for this user.")
            except Exception as e:
                st.error(f"❌ {e}")

# Tab 3: Quick Test Case
with tab3:
    st.subheader("⚡ Predefined Test Case")
    st.markdown("""
    **Test**: Call `/recommend/by-item` with  
    - `item = "alarm clock bakelike green"`  
    - `top_k = 3`
    """)

    if st.button("▶️ Run Test Case"):
        with st.spinner("Calling API..."):
            try:
                resp = requests.get(
                    f"{API_URL}/recommend/by-item",
                    params={"item": "alarm clock bakelike green", "top_k": 3},
                    timeout=5
                )
                if resp.status_code == 200:
                    st.success("✅ 200 OK - Successful Response")
                    st.code(json.dumps(resp.json(), indent=2), language="json")
                else:
                    st.error(f"❌ Status {resp.status_code}: {resp.text}")
            except Exception as e:
                st.error(f"❌ Error: {e}")
