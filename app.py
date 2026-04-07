import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime
import io

st.set_page_config(page_title="Kesimhane Hata Takip", layout="wide")

# ---------------- DATABASE ----------------
conn = sqlite3.connect("kumas.db", check_same_thread=False)
c = conn.cursor()

c.execute("""
CREATE TABLE IF NOT EXISTS kayitlar (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    hafta TEXT,
    tarih TEXT,
    tesis TEXT,
    bant TEXT,
    musteri TEXT,
    pastal_no TEXT,
    model_no TEXT,
    kumas_kalite TEXT,
    hata_kaynagi TEXT,
    hata_adi TEXT,
    ana_neden TEXT,
    pastal_ihtiyac REAL,
    cikan_top INTEGER,
    hatali_top INTEGER,
    cikan_kg REAL,
    hata_kg REAL
)
""")
conn.commit()

# ---------------- MENU ----------------
menu = st.sidebar.radio("Menü", ["Veri Girişi", "Dashboard", "Kayıtlar"])

# ---------------- VERİ GİRİŞ ----------------
if menu == "Veri Girişi":
    st.title("📝 Veri Girişi")

    with st.form("form"):
        col1, col2, col3 = st.columns(3)

        with col1:
            hafta = st.text_input("Hafta")
            tarih = st.date_input("Tarih", datetime.today())
            tesis = st.text_input("Tesis Adı")

        with col2:
            bant = st.text_input("Bant No")
            musteri = st.text_input("Müşteri")
            pastal_no = st.text_input("Pastal No")

        with col3:
            model_no = st.text_input("Model No")
            kumas_kalite = st.text_input("Kumaş Kalite / Varyant")
            hata_kaynagi = st.selectbox("Hata Kaynağı", ["Kesim", "Kumaş", "Operatör", "Makine"])

        hata_adi = st.text_input("Hata Adı")
        ana_neden = st.text_input("Ana Neden")

        col4, col5, col6 = st.columns(3)

        with col4:
            pastal_ihtiyac = st.number_input("Pastal İhtiyacı", min_value=0.0)

        with col5:
            cikan_top = st.number_input("Çıkan Top Sayısı", min_value=0)
            hatali_top = st.number_input("Hatalı Top Sayısı", min_value=0)

        with col6:
            cikan_kg = st.number_input("Çıkan Kumaş KG", min_value=0.0)
            hata_kg = st.number_input("Hata KG", min_value=0.0)

        submit = st.form_submit_button("Kaydet")

        if submit:
            c.execute("""
            INSERT INTO kayitlar VALUES (NULL,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
            """, (
                hafta, str(tarih), tesis, bant, musteri,
                pastal_no, model_no, kumas_kalite,
                hata_kaynagi, hata_adi, ana_neden,
                pastal_ihtiyac, cikan_top, hatali_top,
                cikan_kg, hata_kg
            ))
            conn.commit()
            st.success("✅ Kayıt eklendi")

# ---------------- DATA ----------------
df = pd.read_sql("SELECT * FROM kayitlar", conn)

# ---------------- DASHBOARD ----------------
if menu == "Dashboard":
    st.title("📊 Dashboard")

    if df.empty:
        st.warning("Veri yok")
    else:
        df["tarih"] = pd.to_datetime(df["tarih"])

        col1, col2, col3 = st.columns(3)

        col1.metric("Toplam Kayıt", len(df))
        col2.metric("Toplam Hata KG", int(df["hata_kg"].sum()))
        col3.metric("Toplam Üretim KG", int(df["cikan_kg"].sum()))

        st.divider()

        # Hata oranı
        df["hata_oran"] = df["hata_kg"] / df["cikan_kg"]

        st.subheader("📉 Hata Oranı Trend")
        trend = df.groupby("tarih")["hata_oran"].mean()
        st.line_chart(trend)

        # Hata kaynağı
        st.subheader("📊 Hata Kaynağı")
        kaynak = df.groupby("hata_kaynagi")["hata_kg"].sum()
        st.bar_chart(kaynak)

        # Müşteri bazlı
        st.subheader("👥 Müşteri Bazlı Hata")
        musteri = df.groupby("musteri")["hata_kg"].sum()
        st.bar_chart(musteri)

        # En kötü model
        st.subheader("⚠️ Model Analizi")
        model = df.groupby("model_no")["hata_kg"].sum().sort_values(ascending=False)
        st.bar_chart(model.head(10))

# ---------------- KAYITLAR ----------------
if menu == "Kayıtlar":
    st.title("📋 Kayıtlar")

    st.dataframe(df, use_container_width=True)

    def to_excel(df):
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            df.to_excel(writer, index=False)
        return output.getvalue()

    st.download_button(
        "📥 Excel indir",
        data=to_excel(df),
        file_name="hata_takip.xlsx"
    )
