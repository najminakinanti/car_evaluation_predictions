# app.py
import streamlit as st
from homepage import home
import stream_car   # modul yang berisi render_prediction()

st.set_page_config(page_title="BUY OR BYE? — Car Evaluator", layout="centered")

# Render homepage (compact)
res = home(compact=True)

# Jika user menekan Coba Demo, set session flag lalu rerun agar prediksi tampil
if res.get("action") == "demo":
    st.session_state["show_demo"] = True
    st.experimental_rerun()

# Selalu tampilkan prediksi di bawah beranda
st.markdown("---")
# Jika ingin hanya tampilkan ketika demo di-request, ganti kondisi di bawah:
if st.session_state.get("show_demo", False):
    stream_car.render_prediction()
else:
    # jika mau selalu tampilkan prediksi, langsung panggil:
    stream_car.render_prediction()
