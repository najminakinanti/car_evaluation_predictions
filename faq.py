# home_component.py
import streamlit as st

def faq(compact: bool = True, show_metrics: bool = True):
    st.markdown("""
        <style>
        .faq-container {
            padding: 2rem 0;
        }
        .stExpander {
            border-radius: 8px;
            margin-bottom: 10px;
            border: 1px solid #e0e0e0;
        }
        .faq-title {
            text-align: center;
            font-size: 4rem;
            font-weight: bold;
            margin-bottom: 0;
        }
        .faq-subtitle {
            text-align: center;
            font-size: 1.2rem;
            margin-bottom: 2rem;
        }
        </style>
    """, unsafe_allow_html=True)

    # Header
    st.markdown("<h1 class='faq-title'>FAQ</h1>", unsafe_allow_html=True)
    st.markdown("<p class='faq-subtitle'>Frequently asked questions</p>", unsafe_allow_html=True)

    # FAQ items
    with st.expander("Apa itu BUY OR BYE?", expanded=False):
        st.write("""
        **BUY OR BYE?** adalah aplikasi simulasi berbasis model klasifikasi yang membantu pengguna
        menilai apakah sebuah mobil layak dibeli atau tidak berdasarkan beberapa fitur utama kendaraan.
        """)

    with st.expander("Bagaimana cara kerja penilaian mobil di aplikasi ini?", expanded=False):
        st.write("""
        Pengguna memasukkan data mobil seperti:
        - Harga beli (*buying price*)
        - Biaya perawatan (*maintenance*)
        - Jumlah pintu
        - Kapasitas penumpang
        - Ukuran bagasi
        - Tingkat keamanan

        Sistem kemudian memproses data tersebut menggunakan model klasifikasi dan
        menghasilkan kategori kelayakan mobil.
        """)

    with st.expander("Apa arti hasil unacc, acc, good, dan vgood?", expanded=False):
        st.write("""
        - **unacc** → Mobil tidak layak dibeli  
        - **acc** → Mobil cukup layak  
        - **good** → Mobil layak dibeli  
        - **vgood** → Mobil sangat layak dibeli  

        Kategori ini memberikan gambaran cepat untuk membantu pengambilan keputusan.
        """)

    with st.expander("Apakah saya harus mengisi data secara manual?", expanded=False):
        st.write("""
        Tidak harus. Aplikasi menyediakan dua mode input:
        - **Manual** → Mengisi fitur satu per satu melalui form
        - **Upload CSV** → Mengunggah file CSV (boleh tanpa header) untuk prediksi banyak data sekaligus
        """)

    with st.expander("Apakah data yang saya masukkan akan disimpan?", expanded=False):
        st.write("""
        Tidak.  
        Aplikasi ini bersifat simulasi, dan data pengguna tidak disimpan tanpa izin.
        """)

    with st.expander("Apakah hasil prediksi ini 100% akurat?", expanded=False):
        st.write("""
        Tidak.  
        Hasil prediksi merupakan estimasi berbasis model dan dataset latih, sehingga
        tidak menggantikan penilaian profesional atau inspeksi langsung kendaraan.
        """)

    with st.expander("Untuk siapa aplikasi ini dibuat?", expanded=False):
        st.write("""
        Aplikasi ini ditujukan untuk:
        - Pengguna umum yang ingin gambaran awal sebelum membeli mobil
        - Mahasiswa atau peneliti yang mempelajari sistem klasifikasi
        - Demo atau simulasi sistem pendukung keputusan
        """)

    with st.expander("Apakah aplikasi ini bisa digunakan untuk mobil bekas?", expanded=False):
        st.write("""
        Bisa, selama fitur yang dimasukkan sesuai kondisi mobil tersebut.
        Namun, hasil yang diberikan tetap bersifat simulasi.
        """)

    with st.expander("Mengapa hasil prediksi bisa berbeda untuk mobil yang mirip?", expanded=False):
        st.write("""
        Perbedaan kecil pada fitur seperti tingkat keamanan atau kapasitas penumpang
        dapat memengaruhi hasil klasifikasi, karena setiap fitur memiliki bobot tersendiri
        dalam model.
        """)

    return {"action": None}
