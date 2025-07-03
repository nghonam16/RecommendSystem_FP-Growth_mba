import streamlit as st
import requests
import json

API_URL = "http://localhost:8000"

st.set_page_config(page_title="Hybrid Recommender UI", page_icon="🧠")

st.title("🧠 Hybrid Recommender System")
st.caption("Powered by FP-Growth + Deep Learning (NCF)")

tab1, tab2, tab3 = st.tabs(
    ["Recommend by Item (FP-Growth)",
     "Recommend by User (NCF)",
     "Quick Test"]
)

with tab1:
    st.header("🛒 Rule-based Suggestions")
    item = st.text_input("Enter product name:")
    top_k = st.slider("Top K", 1, 10, 5)

    if st.button("Get Suggestions", key="by_item"):
        if item:
            with st.spinner("Fetching suggestions..."):
                try:
                    res = requests.get(f"{API_URL}/recommend/by-item", params={"item": item, "top_k": top_k})
                    res.raise_for_status()
                    st.success("Suggested items:")
                    for i, v in enumerate(res.json()["suggestions"], 1):
                        st.write(f"{i}. {v}")
                except Exception as e:
                    st.error(f"❌ {e}")

with tab2:
    st.header("👤 Personalized Recommendations")
    user_id = st.number_input("Enter user ID:", min_value=1, step=1)
    top_k = st.slider("Top K", 1, 10, 5, key="by_user_topk")

    if st.button("Get Suggestions", key="by_user"):
        with st.spinner("Fetching personalized suggestions..."):
            try:
                res = requests.get(f"{API_URL}/recommend/by-user", params={"user_id": user_id, "top_k": top_k})
                res.raise_for_status()
                st.success("Suggested items:")
                for i, v in enumerate(res.json()["suggestions"], 1):
                    st.write(f"{i}. {v}")
            except Exception as e:
                st.error(f"❌ {e}")

with tab3:
    st.header("✅ Predefined Test Case")

    st.markdown("""
**Test:** Call `/recommend/by-item` with  
`item = "alarm clock bakelike green"` and `top_k = 3`
""")

    if st.button("Run Test Case"):
        with st.spinner("Calling FastAPI..."):
            try:
                resp = requests.get(
                    f"{API_URL}/recommend/by-item",
                    params={"item": "alarm clock bakelike green", "top_k": 3},
                    timeout=5
                )
                if resp.status_code == 200:
                    st.success("✅ 200 OK")
                    st.code(json.dumps(resp.json(), indent=2), language="json")
                else:
                    st.error(f"❌ Status {resp.status_code}: {resp.text}")
            except Exception as e:
                st.error(f"❌ Error: {e}")