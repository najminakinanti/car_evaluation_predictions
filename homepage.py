# home_component.py
import streamlit as st

def home(compact: bool = True, show_metrics: bool = True):
    st.markdown(
        """
        <div style="line-height:1; margin-bottom:6px">
          <h1 style="margin:0; padding:0; font-weight:800; letter-spacing:0.2px;">
            BUY OR BYE?
          </h1>
          <h3 style="margin:2px 0 40px 0; padding:0; font-weight:800;">
            Penilaian Cerdas untuk Kelayakan Mobil
          </h3>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.markdown(
        "Menentukan apakah sebuah mobil layak dibeli kini jauh lebih mudah. Buy or Bye menggunakan model klasifikasi untuk menilai kelayakan mobil "
        "berdasarkan berbagai fitur penting seperti buying price, maintenance cost, jumlah pintu, kapasitas penumpang, ukuran bagasi, hingga "
        "tingkat keamanan."
    )
    
    st.write("") 

    st.markdown(
        "Masukkan informasi utama tentang mobil Anda, lalu sistem akan mengelompokkan hasil penilaiannya ke dalam empat kategori yaitu **unacc, acc, good, dan vgood**. "
        "Hasil ini membantu Anda mendapatkan gambaran cepat, jelas, dan meyakinkan untuk menentukan pilihan terbaik.\n\n"
        "**💡Isi data mobil Anda → Dapatkan analisis otomatis → Putuskan buy atau bye dalam hitungan detik**"
    )
    
    return {"action": None}
