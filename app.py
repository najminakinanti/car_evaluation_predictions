import streamlit as st
from homepage import home
from stream_car import render_prediction
from faq import faq

st.set_page_config(page_title="BUY OR BYE? — Car Evaluator", layout="centered")

home()
st.markdown("---")
render_prediction()
st.markdown("---")
faq()

st.markdown("---")
st.markdown(
    """
    <div style="text-align: center;">
        <p style="margin: 0; font-size: 16px; font-weight: bold;">BUY OR BYE?</p>
        <p style="margin: 0; font-size: 14px;">© 2025</p>
    </div>
    """,
    unsafe_allow_html=True
)
