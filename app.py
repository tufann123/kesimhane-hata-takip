import streamlit as st
import pandas as pd
import sqlite3
import io
import os
import shutil
import plotly.express as px

st.set_page_config(page_title="Kesimhane Hata Takip", layout="wide")

DB_FILE = "kumas.db"
BACKUP_FILE = "kumas_backup.db"

# ---------------- DATABASE ----------------
conn = sqlite3.connect(DB_FILE, check_same_thread=False)
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

# ---------------- BACKUP ----------------
def create_backup():
    if os.path.exists(DB_FILE):
        shutil.copy(DB_FILE, BACKUP_FILE)

def restore_backup(uploaded_file):
    with open(DB_FILE, "wb") as f:
        f.write(uploaded_file.read())

# ---------------- DATA ----------------
def load_data():
    return pd.read_sql("SELECT * FROM kayitlar", conn)

df = load_data()

# ---------------- DROPDOWN ----------------
musteri_list = ["Erlich","Hugo Boss","Tommy","Ten Cate","Blackspade","Lisca","Groenendijk","Armedangels","Vanilla Blush","Falke","Mey"]
hata_kaynagi_list = ["GKK","Tedarikçi","Kumaş","Kalıp"]
ana_neden_list = ["Gramaj","Leke","En Problemi","Kola Kenarı","Kırık","Abraj","Renk Farkı"]
birim_list = ["KG","MT"]
durum_list = ["Açık","Devam Ediyor","Tamamlandı"]

menu = st.sidebar.radio("Menü", ["Veri Girişi", "Dashboard", "Kayıtlar", "Yedekleme"])

# ---------------- VERİ GİRİŞ ----------------
if menu == "Veri Girişi":
    st.title("📝 Veri Girişi")

    with st.form("form"):
        tarih = st.date_input("Tarih")
        hafta = f"{tarih.isocalendar().week}. Hafta"

        musteri = st.selectbox("Müşteri", musteri_list)
        hata_kaynagi = st.selectbox("Hata Kaynağı", hata_kaynagi_list)
        ana_neden = st.selectbox("Ana Neden", ana_neden_list)
        birim = st.selectbox("Birim", birim_list)

        cikan_kg = st.number_input("Çıkan KG", min_value=0.0)
        hata_kg = st.number_input("Hata KG", min_value=0.0)

        durum = st.selectbox("Durum", durum_list)
        aksiyon = st.text_area("Aksiyon")

        submit = st.form_submit_button("Kaydet")

        if submit:
            c.execute("""
            INSERT INTO kayitlar VALUES (NULL,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
            """, (
                hafta, str(tarih), "İzmir", "Kesimhane", musteri,
                "", "", "",
                hata_kaynagi, "", ana_neden,
                birim,
                0, 0, 0,
                cikan_kg, hata_kg,
                durum, aksiyon
            ))
            conn.commit()

            # 🔥 OTOMATİK BACKUP
            create_backup()

            st.success("✅ Kayıt eklendi ve yedeklendi")

# ---------------- DASHBOARD ----------------
if menu == "Dashboard":
    st.title("📊 Dashboard")

    if df.empty:
        st.warning("Veri yok")
    else:
        df["tarih"] = pd.to_datetime(df["tarih"])

        toplam_hata = df["hata_kg"].sum()
        toplam_uretim = df["cikan_kg"].sum()
        oran = toplam_hata / toplam_uretim if toplam_uretim > 0 else 0

        st.metric("Hata Oranı", f"%{round(oran*100,2)}")

        def plot(data, x):
            data = data.groupby(x)["hata_kg"].sum().reset_index()
            data["%"] = data["hata_kg"] / data["hata_kg"].sum() * 100

            fig = px.bar(data, x=x, y="hata_kg",
                         text=data["%"].apply(lambda v: f"%{v:.1f}"))
            fig.update_traces(textposition='outside')
            return fig

        st.plotly_chart(plot(df, "musteri"))
        st.plotly_chart(plot(df, "ana_neden"))

# ---------------- KAYITLAR ----------------
if menu == "Kayıtlar":
    st.title("📋 Kayıtlar")
    st.dataframe(df, use_container_width=True)

# ---------------- YEDEKLEME ----------------
if menu == "Yedekleme":
    st.title("💾 Yedekleme")

    # 📥 DB İNDİR
    with open(DB_FILE, "rb") as f:
        st.download_button(
            "📦 Veritabanını indir",
            data=f,
            file_name="kumas.db"
        )

    # 📤 DB YÜKLE
    uploaded = st.file_uploader("📤 Yedek yükle", type=["db"])

    if uploaded:
        restore_backup(uploaded)
        st.success("✅ Yedek yüklendi, sayfayı yenile")

    # 🔁 BACKUP İNDİR
    if os.path.exists(BACKUP_FILE):
        with open(BACKUP_FILE, "rb") as f:
            st.download_button(
                "🔁 Otomatik yedeği indir",
                data=f,
                file_name="kumas_backup.db"
            )
