import streamlit as st
import requests
import os
import pathlib

# Set up API URL and page configuration
API_URL   = os.getenv("API_URL", "http://localhost:8000")
PAGE_ICON = "🧠"
PAGE_TITLE = "Hybrid Recommender UI"

# Configure Streamlit page
st.set_page_config(page_title=PAGE_TITLE,
                   page_icon=PAGE_ICON,
                   layout="centered")

# Load custom CSS for styling
css_path = pathlib.Path(__file__).parent / "style.css"
if css_path.exists():
    st.markdown(f"<style>{css_path.read_text()}</style>",
                unsafe_allow_html=True)

# Hide default Streamlit header and footer
st.markdown("<h2>🛍️Hi, bro!</h2>", unsafe_allow_html=True)
st.markdown("---")

# Main content of the app
with st.form("hybrid_form"):
    st.subheader("Enter information to get suggestions")

    # Input fields for user ID and purchased items
    col1, col2 = st.columns(2)
    with col1:
        user_id = st.number_input("User ID (NCF):",
                                  min_value=1, step=1, value=1)
    # Input for purchased items
    with col2:
        bought_items = st.text_input(
            "Purchased products (separated by commas):",
            placeholder="alarm clock bakelike green, red mug",
            label_visibility="visible"
        )

    # Slider for number of suggestions per source
    top_k = st.slider("Number of suggestions per source (Top K):",
                      min_value=1, max_value=10, value=3)
    submitted = st.form_submit_button("🚀 SUGGESTION DISPLAY")

# Display the form submission result
if submitted:
    st.markdown("---")
    with st.spinner("Getting suggestions from the system ... please wait..."):
        # Initialize empty suggestion lists
        dl_suggestions = []
        try:
            resp_dl = requests.get(
                f"{API_URL}/recommend/by-user",
                params={"user_id": user_id, "top_k": top_k},
                timeout=10,
            )
            resp_dl.raise_for_status()
            dl_suggestions = resp_dl.json().get("suggestions", [])
        except Exception as e:
            st.error(f"❌ Error retrieving NCF suggestion: {e}")

        # Display NCF suggestions
        fp_suggestions = []
        bought_list = [item.strip() for item in bought_items.split(',')
                       if item.strip()]
        for item in bought_list:
            try:
                resp_fp = requests.get(
                    f"{API_URL}/recommend/by-item",
                    params={"item": item, "top_k": top_k},
                    timeout=10,
                )
                resp_fp.raise_for_status()
                fp_suggestions.extend(
                    resp_fp.json().get("suggestions", []))
            except Exception as e:
                st.error(f"❌ FP-Growth error for '{item}': {e}")

        fp_suggestions = [s for s in dict.fromkeys(fp_suggestions)
                          if s not in bought_list][:top_k]

    # Display the suggestions
    if dl_suggestions:
        st.markdown(
            f"""
<div class='recommend-box'>
  <h3>🧠 Smart suggestions for you (AI):</h3>
  <div>
    {' '.join(f"<span class='recommend-item'>📦 {s}</span>"
              for s in dl_suggestions)}
  </div>
</div>
""",
            unsafe_allow_html=True,
        )
    else:
        st.info("No AI suggestion found.")

    if fp_suggestions:
        bought_str = ", ".join(f"<strong>{b}</strong>" for b in bought_list)
        st.markdown(
            f"""
<div class='recommend-box'>
  <h3>🧾 Suggestions based on common behavior (Community data):</h3>
  <p>👉 Because you bought {bought_str}, others often buy too.:</p>
  <div>
    {' '.join(f"<span class='recommend-item'>📦 {s}</span>"
              for s in fp_suggestions)}
  </div>
</div>
""",
            unsafe_allow_html=True,
        )
    else:
        st.info("No FP-Growth suggestions found..")

    st.markdown("---")

st.caption("Powered by **FP‑Growth** + **Neural Collaborative Filtering (NCF)**")
