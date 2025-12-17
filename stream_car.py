import streamlit as st
import joblib
import pandas as pd
import difflib
import io
import re

# load joblib pakai st.cache_resource biar model dimuat sekali doang
# tidak dimuat ulang tiap user klik tombol
@st.cache_resource
def load_bundle(path="car_bundle.pkl"):
    bundle = joblib.load(path)
    return bundle

# fungsi untuk cari kata yg mirip jika user typo
# misal diketik 'hgh', maka akan langsung ditebak itu 'high'
def fuzzy_key_lookup(keys, s, cutoff=0.6):
    s = str(s).strip().lower()
    keys_low = [k.lower() for k in keys]

    # kalau kata persis ditemukan
    if s in keys_low:
        return keys[keys_low.index(s)]
    
    # kalo gk persis cari yg paling mirip pake difflib
    matches = difflib.get_close_matches(s, keys_low, n=1, cutoff=cutoff)
    return keys[keys_low.index(matches[0])] if matches else None

# fungsi buat ubah input teks jd angka agar dibaca model
def map_val(feature, v, ordinal_mapping):
    s = str(v).strip().lower()

    # untuk atribut buying maint lugboot safety
    if feature in ["buying","maint","lug_boot","safety"]:
        keys = list(ordinal_mapping[feature].keys())
        match = fuzzy_key_lookup(keys, s)
        if match:
            return ordinal_mapping[feature][match]
        raise ValueError(f"Invalid value '{v}' for {feature}. Kandidat: {keys}")
    
    # untuk atribut doors
    if feature == "doors":
        s2 = s
        if s2 == "5more": return 5      # Khusus teks '5more' jadi 5
        m = re.search(r'\d+', s2)
        if m: return int(m.group())
        raise ValueError(f"Invalid value for doors: '{v}'")
    
    # untuk atribut persons
    if feature == "persons":
        s2 = s
        if s2 == "more": return 5      # Khusus teks 'more' jadi 5
        m = re.search(r'\d+', s2)
        if m: return int(m.group())
        raise ValueError(f"Invalid value for persons: '{v}'")
    raise KeyError(feature)

# mapping pesan berdasarkan hasil prediksi
PRED_MSG = {
    "unacc": "❌ Mobil Anda terklasifikasi sebagai **UNACCEPTABLE**. Hasil ini terutama dipengaruhi oleh tingkat keamanan yang rendah, ditambah dengan kombinasi harga pembelian tinggi, biaya perawatan mahal, serta kapasitas bagasi dan penumpang yang terbatas. Kami menyarankan untuk mempertimbangkan mobil dengan spesifikasi lebih baik, terutama dari segi keamanan.",
    "acc": "👍 Mobil Anda terklasifikasi sebagai **ACCEPTABLE**. Mobil ini memenuhi standar keamanan yang memadai dan menawarkan keseimbangan wajar antara harga pembelian dan biaya perawatan. Kapasitas bagasi dan penumpang cukup untuk kebutuhan keluarga kecil atau penggunaan personal. Secara keseluruhan, ini adalah pilihan yang rasional untuk penggunaan harian.",
    "good": "🚗 Mobil Anda terklasifikasi sebagai **GOOD**. Mobil ini unggul pada sistem keamanan yang memberikan perlindungan optimal, dengan harga pembelian kompetitif dan biaya perawatan terjangkau. Kapasitas bagasi yang luas dan penumpang yang memadai cocok untuk keluarga atau perjalanan bersama. Mobil ini menawarkan keseimbangan optimal antara kualitas, fungsionalitas, dan efisiensi biaya.",
    "vgood": "🔥 Mobil Anda terklasifikasi sebagai **VERY GOOD**. Selamat! Mobil ini unggul di semua aspek dengan sistem keamanan tingkat tinggi, kapasitas bagasi sangat luas, dan penumpang maksimal. Meskipun harga pembelian dan biaya perawatan lebih tinggi, kualitas superior yang didapat sangat sepadan. Mobil ini adalah investasi terbaik untuk pengalaman berkendara optimal jangka panjang."
}

# untuk UI
def render_prediction():
    # load bundle pkl
    try:
        bundle = load_bundle("car_bundle.pkl")
    except FileNotFoundError:
        st.error("File 'car_bundle.pkl' tidak ditemukan. Pastikan file ada di folder yang sama.")
        return
    except Exception as e:
        st.error(f"Gagal load bundle: {e}")
        return

    # ambil komponen model, scaler, dan encoder dari bundle 
    model = bundle.get("model") or bundle.get("model_lgb") or bundle.get("model_lgbm")
    ordinal_mapping = bundle.get("ordinal_mapping") or bundle.get("mapping") or {}
    label_encoder = bundle.get("label_encoder") or bundle.get("le") or bundle.get("label_enc")

    if model is None:
        st.error("Bundle tidak berisi model. Pastikan bundle['model'] ada.")
        return
    if label_encoder is None:
        st.warning("Label encoder tidak ditemukan di bundle. Output akan berupa encoded label.")

    # Kalau mapping gk ada di pickle, jd manual
    defaults = {
        "doors": {"2": 2, "3": 3, "4": 4, "5more": 5},
        "persons": {"2": 2, "4": 4, "more": 5}
    }
    for k, v in defaults.items():
        if k not in ordinal_mapping:
            ordinal_mapping[k] = v

    # set mapping manual atribut lainnya
    ordinal_mapping.setdefault("buying", {"low":1, "med":2, "high":3, "vhigh":4})
    ordinal_mapping.setdefault("maint", {"low":1, "med":2, "high":3, "vhigh":4})
    ordinal_mapping.setdefault("lug_boot", {"small":1, "med":2, "big":3})
    ordinal_mapping.setdefault("safety", {"low":1, "med":2, "high":3})

    # UI
    st.title("**Prediksi Cepat**")
    st.markdown("Pilih mode input: *Manual* atau *Upload CSV* (boleh tanpa header).")
    mode = st.radio("Mode input:", ["Manual", "Upload CSV"]) 

    # INPUT MANUAL
    if mode == "Manual":
        st.header("Masukkan fitur (Manual)")
        c1, c2 = st.columns(2)

        with c1:
            buying = st.selectbox("buying", options=list(ordinal_mapping["buying"].keys()), index=1)
            doors  = st.selectbox("doors", options=list(ordinal_mapping["doors"].keys()), index=0)
            lug_boot = st.selectbox("lug_boot", options=list(ordinal_mapping["lug_boot"].keys()), index=0)
        with c2:
            maint  = st.selectbox("maint", options=list(ordinal_mapping["maint"].keys()), index=1)
            persons= st.selectbox("persons", options=list(ordinal_mapping["persons"].keys()), index=0)
            safety = st.selectbox("safety", options=list(ordinal_mapping["safety"].keys()), index=2)

        if st.button("Predict"):
            try:
                row = {
                    "buying": map_val("buying", buying, ordinal_mapping),
                    "maint":  map_val("maint", maint, ordinal_mapping),
                    "doors":  map_val("doors", doors, ordinal_mapping),
                    "persons":map_val("persons", persons, ordinal_mapping),
                    "lug_boot":map_val("lug_boot", lug_boot, ordinal_mapping),
                    "safety": map_val("safety", safety, ordinal_mapping)
                }
                X_new = pd.DataFrame([row], columns=['buying','maint','doors','persons','lug_boot','safety'])

                X_for_model = X_new.copy()
                if "scaler" in bundle and bundle["scaler"] is not None:
                    scaler = bundle["scaler"]
                    X_scaled = scaler.transform(X_new)
                    X_for_model = pd.DataFrame(X_scaled, columns=X_new.columns)

                pred_enc = model.predict(X_for_model)
                if label_encoder is not None:
                    pred_label = label_encoder.inverse_transform(pred_enc.astype(int))[0]
                    msg = PRED_MSG.get(pred_label, "Hasil prediksi tidak dikenali.")
                    st.success(f"Hasil Prediksi: **{pred_label}**")
                    st.info(msg)
                else:
                    st.success(f"Hasil Prediksi (encoded): {pred_enc[0]}")

            except Exception as e:
                st.error(f"Error saat prediksi: {e}")

    # UPLOAD CSV
    else:
        uploaded = st.file_uploader("Upload CSV. Kolom urut: buying,maint,doors,persons,lug_boot,safety[,class]", type=["csv"])
        header_opt = st.selectbox("CSV memiliki header?", ["Tidak", "Ya"], index=0)

        if uploaded is not None:
            try:
                if header_opt == "Tidak":
                    df = pd.read_csv(uploaded, header=None)
                    if df.shape[1] == 7:
                        df.columns = ['buying','maint','doors','persons','lug_boot','safety','class']
                    elif df.shape[1] == 6:
                        df.columns = ['buying','maint','doors','persons','lug_boot','safety']
                    else:
                        st.error(f"CSV punya {df.shape[1]} kolom — harapkan 6 atau 7.")
                        return
                else:
                    df = pd.read_csv(uploaded)
                    expected = set(['buying','maint','doors','persons','lug_boot','safety'])
                    if not expected.issubset(set(df.columns)):
                        st.warning("Header CSV tidak cocok. Pastikan kolom: buying,maint,doors,persons,lug_boot,safety (atau upload tanpa header).")

                # Simpan data asli untuk ditampilkan
                df_original = df[['buying','maint','doors','persons','lug_boot','safety']].copy()

                processed = []
                bad_rows = []
                for i, r in df.iterrows():
                    try:
                        mapped = {
                            "buying": map_val("buying", r['buying'], ordinal_mapping),
                            "maint":  map_val("maint",  r['maint'], ordinal_mapping),
                            "doors":  map_val("doors",  r['doors'], ordinal_mapping),
                            "persons":map_val("persons",r['persons'], ordinal_mapping),
                            "lug_boot":map_val("lug_boot", r['lug_boot'], ordinal_mapping),
                            "safety": map_val("safety", r['safety'], ordinal_mapping)
                        }
                        processed.append(mapped)
                    except Exception as ex:
                        bad_rows.append((i, str(ex)))

                if bad_rows:
                    st.warning(f"Ada {len(bad_rows)} baris bermasalah (ditampilkan sebagian):")
                    st.write(bad_rows[:10])

                if len(processed) == 0:
                    st.error("Tidak ada baris valid untuk diproses.")
                    return

                proc_df = pd.DataFrame(processed, columns=['buying','maint','doors','persons','lug_boot','safety'])
                X_for_model = proc_df.copy()
                if "scaler" in bundle and bundle["scaler"] is not None:
                    scaler = bundle["scaler"]
                    X_scaled = scaler.transform(proc_df)
                    X_for_model = pd.DataFrame(X_scaled, columns=proc_df.columns)

                preds_enc = model.predict(X_for_model)
                if label_encoder is not None:
                    preds_label = label_encoder.inverse_transform(preds_enc.astype(int))
                    # Tambahkan kolom prediksi ke data asli
                    df_original['predicted_class'] = preds_label
                else:
                    df_original['predicted_class'] = preds_enc

                st.write(f"Hasil prediksi: menampilkan seluruh {len(df_original)} baris")
                st.dataframe(df_original)

                csv_buf = io.StringIO()
                df_original.to_csv(csv_buf, index=False)
                st.download_button("Download hasil prediksi (CSV)", data=csv_buf.getvalue().encode('utf-8'),
                                   file_name="predictions.csv", mime="text/csv")
            except Exception as e:
                st.error(f"Error saat memproses file: {e}")

# Preprocessing tetap dilakukan di Streamlit karena model hanya menerima data dalam 
# format numerik yang sama seperti saat training. File .pkl hanya menyimpan model 
# dan objek preprocessing, bukan menjalankannya secara otomatis

# preprocessing dilakukan di luar pipeline agar alur inferensi lebih transparan 
# dan mudah dijelaskan pada tahap deployment, meskipun pipeline tetap merupakan best practice.

# intinya pipeline standar terlalu kaku untuk kebutuhan cleaning data saya yg spesifik
# (menangani 5more dan typo)