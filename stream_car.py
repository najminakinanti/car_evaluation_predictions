# stream_car.py
import streamlit as st
import joblib
import pandas as pd
import difflib
import io

st.set_page_config(page_title="Car Evaluation Predictor", layout="centered")

# -----------------------
# Load bundle (joblib)
# -----------------------
@st.cache_resource
def load_bundle(path="car_bundle.pkl"):
    bundle = joblib.load(path)
    return bundle

try:
    bundle = load_bundle("car_bundle.pkl")
except FileNotFoundError:
    st.error("File 'car_bundle.pkl' tidak ditemukan. Pastikan file ada di folder yang sama.")
    st.stop()
except Exception as e:
    st.error(f"Gagal load bundle: {e}")
    st.stop()

# extract objects from bundle (try common names)
model = bundle.get("model") or bundle.get("model_lgb") or bundle.get("model_lgbm")
ordinal_mapping = bundle.get("ordinal_mapping") or bundle.get("mapping") or {}
label_encoder = bundle.get("label_encoder") or bundle.get("le") or bundle.get("label_enc")

# sanity checks
if model is None:
    st.error("Bundle tidak berisi model. Pastikan bundle['model'] ada.")
    st.stop()
if label_encoder is None:
    st.warning("Label encoder tidak ditemukan di bundle. Output akan berupa encoded label.")

# Ensure doors/persons mappings exist (add sensible defaults if missing)
defaults = {
    "doors": {"2": 2, "3": 3, "4": 4, "5more": 5},
    "persons": {"2": 2, "4": 4, "more": 5}
}
for k, v in defaults.items():
    if k not in ordinal_mapping:
        ordinal_mapping[k] = v

# Ensure buying/maint/lug_boot/safety exist; if not, attempt sensible defaults
if "buying" not in ordinal_mapping or "maint" not in ordinal_mapping:
    ordinal_mapping.setdefault("buying", {"low":1, "med":2, "high":3, "vhigh":4})
    ordinal_mapping.setdefault("maint", {"low":1, "med":2, "high":3, "vhigh":4})
ordinal_mapping.setdefault("lug_boot", {"small":1, "med":2, "big":3})
ordinal_mapping.setdefault("safety", {"low":1, "med":2, "high":3})

# -----------------------
# Helpers
# -----------------------
def fuzzy_key_lookup(keys, s, cutoff=0.6):
    """Return best matching key from keys for string s, or None."""
    s = str(s).strip().lower()
    if s in keys:
        return s
    matches = difflib.get_close_matches(s, keys, n=1, cutoff=cutoff)
    return matches[0] if matches else None

def map_val(feature, v):
    s = str(v).strip().lower()
    if feature in ["buying","maint","lug_boot","safety"]:
        keys = list(ordinal_mapping[feature].keys())
        match = fuzzy_key_lookup(keys, s)
        if match:
            return ordinal_mapping[feature][match]
        raise ValueError(f"Invalid value '{v}' for {feature}. Kandidat: {keys}")
    if feature == "doors":
        s2 = s
        if s2 == "5more": return 5
        # extract number
        import re
        m = re.search(r'\d+', s2)
        if m: return int(m.group())
        raise ValueError(f"Invalid value for doors: '{v}'")
    if feature == "persons":
        s2 = s
        if s2 == "more": return 5
        import re
        m = re.search(r'\d+', s2)
        if m: return int(m.group())
        raise ValueError(f"Invalid value for persons: '{v}'")
    raise KeyError(feature)

# -----------------------
# UI
# -----------------------
st.title("Car Evaluation — Prediksi Kelayakan Mobil")

st.markdown("Pilih mode input: *Manual* atau *Upload CSV* (boleh tanpa header).")

mode = st.radio("Mode input:", ["Manual", "Upload CSV"])

# Manual mode
if mode == "Manual":
    st.sidebar.header("Masukkan fitur (Manual)")
    buying = st.sidebar.selectbox("buying", options=list(ordinal_mapping["buying"].keys()), index=1)
    maint  = st.sidebar.selectbox("maint", options=list(ordinal_mapping["maint"].keys()), index=1)
    doors  = st.sidebar.selectbox("doors", options=list(ordinal_mapping["doors"].keys()), index=0)
    persons= st.sidebar.selectbox("persons", options=list(ordinal_mapping["persons"].keys()), index=0)
    lug_boot = st.sidebar.selectbox("lug_boot", options=list(ordinal_mapping["lug_boot"].keys()), index=0)
    safety = st.sidebar.selectbox("safety", options=list(ordinal_mapping["safety"].keys()), index=2)

    if st.button("Predict"):
        try:
            row = {
                "buying": map_val("buying", buying),
                "maint":  map_val("maint", maint),
                "doors":  map_val("doors", doors),
                "persons":map_val("persons", persons),
                "lug_boot":map_val("lug_boot", lug_boot),
                "safety": map_val("safety", safety)
            }
            X_new = pd.DataFrame([row], columns=['buying','maint','doors','persons','lug_boot','safety'])

            # some models were trained without scaling; just ensure DataFrame columns preserved
            X_for_model = X_new.copy()
            # If bundle has scaler and you used it in training, apply it:
            if "scaler" in bundle and bundle["scaler"] is not None:
                scaler = bundle["scaler"]
                X_scaled = scaler.transform(X_new)
                X_for_model = pd.DataFrame(X_scaled, columns=X_new.columns)

            # predict: ensure DataFrame passed (preserve columns)
            pred_enc = model.predict(X_for_model)
            pred_label = None
            if label_encoder is not None:
                pred_label = label_encoder.inverse_transform(pred_enc.astype(int))[0]
                st.success(f"Hasil Prediksi: **{pred_label}**")
            else:
                st.success(f"Hasil Prediksi (encoded): {pred_enc[0]}")

            st.write("Input (numeric):", X_new.to_dict(orient='records')[0])
            st.write("Model booster present:", bool(getattr(model, "_Booster", None)))
        except Exception as e:
            st.error(f"Error saat prediksi: {e}")

# Upload CSV mode
else:
    uploaded = st.file_uploader("Upload CSV (boleh tanpa header). Kolom urut: buying,maint,doors,persons,lug_boot,safety[,class]", type=["csv"])
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
                    st.stop()
            else:
                df = pd.read_csv(uploaded)
                expected = set(['buying','maint','doors','persons','lug_boot','safety'])
                if not expected.issubset(set(df.columns)):
                    st.warning("Header CSV tidak cocok. Pastikan kolom: buying,maint,doors,persons,lug_boot,safety (atau upload tanpa header).")

            st.write(f"Preview data: menampilkan seluruh {len(df)} baris")
            st.dataframe(df)   # <-- tampil semua baris yang di-upload

            processed = []
            bad_rows = []
            for i, r in df.iterrows():
                try:
                    mapped = {
                        "buying": map_val("buying", r['buying']),
                        "maint":  map_val("maint",  r['maint']),
                        "doors":  map_val("doors",  r['doors']),
                        "persons":map_val("persons",r['persons']),
                        "lug_boot":map_val("lug_boot", r['lug_boot']),
                        "safety": map_val("safety", r['safety'])
                    }
                    processed.append(mapped)
                except Exception as ex:
                    bad_rows.append((i, str(ex)))

            if bad_rows:
                st.warning(f"Ada {len(bad_rows)} baris bermasalah (ditampilkan sebagian):")
                st.write(bad_rows[:10])

            if len(processed) == 0:
                st.error("Tidak ada baris valid untuk diproses.")
                st.stop()

            proc_df = pd.DataFrame(processed, columns=['buying','maint','doors','persons','lug_boot','safety'])
            X_for_model = proc_df.copy()
            if "scaler" in bundle and bundle["scaler"] is not None:
                scaler = bundle["scaler"]
                X_scaled = scaler.transform(proc_df)
                X_for_model = pd.DataFrame(X_scaled, columns=proc_df.columns)

            preds_enc = model.predict(X_for_model)
            if label_encoder is not None:
                preds_label = label_encoder.inverse_transform(preds_enc.astype(int))
                proc_df['predicted'] = preds_label
            else:
                proc_df['predicted_enc'] = preds_enc

            st.write(f"Hasil prediksi: menampilkan seluruh {len(proc_df)} baris")
            st.dataframe(proc_df)   # <-- tampil semua hasil prediksi

            # download
            csv_buf = io.StringIO()
            proc_df.to_csv(csv_buf, index=False)
            st.download_button("Download hasil prediksi (CSV)", data=csv_buf.getvalue().encode('utf-8'),
                               file_name="predictions.csv", mime="text/csv")
        except Exception as e:
            st.error(f"Error saat memproses file: {e}")

# footer: tampilkan mapping keys untuk debug
st.sidebar.header("Debug info")
st.sidebar.write("Ordinal mapping keys:", list(ordinal_mapping.keys()))
if st.sidebar.button("Tampilkan mapping detail"):
    st.sidebar.write(ordinal_mapping)
