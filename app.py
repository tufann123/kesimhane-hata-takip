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
    birim TEXT,
    pastal_ihtiyac REAL,
    cikan_top INTEGER,
    hatali_top INTEGER,
    cikan_kg REAL,
    hata_kg REAL,
    durum TEXT,
    aksiyon TEXT
)
""")
conn.commit()

# ---------------- DROPDOWN ----------------
musteri_list = [
    "Erlich", "Hugo Boss", "Tommy", "Ten Cate",
    "Blackspade", "Lisca", "Groenendijk",
    "Armedangels", "Vanilla Blush", "Falke", "Mey"
]

hata_kaynagi_list = ["GKK", "Tedarikçi", "Kumaş", "Kalıp"]

ana_neden_list = [
    "Gramaj", "Leke", "En Problemi", "Kola Kenarı",
    "Kırık", "Abraj", "Renk Farkı"
]

birim_list = ["KG", "MT"]

durum_list = ["Açık", "Devam Ediyor", "Tamamlandı"]

# ---------------- MENU ----------------
menu = st.sidebar.radio("Menü", ["Veri Girişi", "Dashboard", "Kayıtlar"])

# ---------------- VERİ GİRİŞ ----------------
if menu == "Veri Girişi":
    st.title("📝 Veri Girişi")

    with st.form("form"):
        col1, col2, col3 = st.columns(3)

        with col1:
            tarih = st.date_input("Tarih")
            hafta = f"{tarih.isocalendar().week}. Hafta"
            st.text_input("Hafta", value=hafta, disabled=True)

            st.text_input("Tesis Adı", value="İzmir", disabled=True)
            tesis = "İzmir"

        with col2:
            st.text_input("Bant No", value="Kesimhane", disabled=True)
            bant = "Kesimhane"

            musteri = st.selectbox("Müşteri", musteri_list)
            pastal_no = st.text_input("Pastal No")

        with col3:
            model_no = st.text_input("Model No")
            kumas_kalite = st.text_input("Kumaş Kalite / Varyant")
            hata_kaynagi = st.selectbox("Hata Kaynağı", hata_kaynagi_list)

        hata_adi = st.text_input("Hata Adı")
        ana_neden = st.selectbox("Ana Neden", ana_neden_list)

        birim = st.selectbox("Birim", birim_list)

        col4, col5, col6 = st.columns(3)

        with col4:
            pastal_ihtiyac = st.number_input("Pastal İhtiyacı", min_value=0.0)

        with col5:
            cikan_top = st.number_input("Çıkan Top Sayısı", min_value=0)
            hatali_top = st.number_input("Hatalı Top Sayısı", min_value=0)

        with col6:
            cikan_kg = st.number_input("Çıkan Kumaş", min_value=0.0)
            hata_kg = st.number_input("Hata", min_value=0.0)

        # 🔥 YENİ
        durum = st.selectbox("Durum", durum_list)
        aksiyon = st.text_area("Aksiyon / Alınan Önlem")

        submit = st.form_submit_button("Kaydet")

        if submit:
            c.execute("""
            INSERT INTO kayitlar VALUES (NULL,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
            """, (
                hafta, str(tarih), tesis, bant, musteri,
                pastal_no, model_no, kumas_kalite,
                hata_kaynagi, hata_adi, ana_neden,
                birim,
                pastal_ihtiyac, cikan_top, hatali_top,
                cikan_kg, hata_kg,
                durum, aksiyon
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

        # 🔍 TARİH FİLTRE
        min_date = df["tarih"].min()
        max_date = df["tarih"].max()

        colf1, colf2 = st.columns(2)
        start_date = colf1.date_input("Başlangıç Tarihi", min_date)
        end_date = colf2.date_input("Bitiş Tarihi", max_date)

        df = df[(df["tarih"] >= pd.to_datetime(start_date)) &
                (df["tarih"] <= pd.to_datetime(end_date))]

        col1, col2, col3 = st.columns(3)

        toplam_hata = df["hata_kg"].sum()
        toplam_uretim = df["cikan_kg"].sum()
        hata_oran = toplam_hata / toplam_uretim if toplam_uretim > 0 else 0

        col1.metric("Toplam Kayıt", len(df))
        col2.metric("Toplam Hata", int(toplam_hata))
        col3.metric("Hata Oranı", f"%{round(hata_oran*100,2)}")

        # 🚨 KRİTİK ALARM
        if hata_oran > 0.05:
            st.error("🚨 Kritik! Hata oranı %5 üstünde")
        else:
            st.success("✅ Hata oranı normal")

        st.divider()

        # 📊 EN KÖTÜ MÜŞTERİ
        st.subheader("⚠️ En Kötü Müşteri")
        musteri = df.groupby("musteri")["hata_kg"].sum().sort_values(ascending=False)
        st.bar_chart(musteri)

        if not musteri.empty:
            st.error(f"En problemli müşteri: {musteri.idxmax()}")

        # 📊 BİRİM ANALİZ
        st.subheader("🧠 Birim Bazlı Analiz")
        birim = df.groupby("birim")["hata_kg"].sum()
        st.bar_chart(birim)

        # 📈 HAFTALIK PERFORMANS
        st.subheader("📈 Haftalık Performans")
        haftalik = df.groupby("hafta")["hata_kg"].sum()
        st.line_chart(haftalik)

        # 📌 AKSİYON DURUMU
        st.subheader("📌 Aksiyon Takibi")
        durum = df["durum"].value_counts()
        st.bar_chart(durum)

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
