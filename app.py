import streamlit as st
import pandas as pd
import sqlite3
import io
import os
import shutil
import plotly.express as px

st.set_page_config(page_title="Kesimhane Hata Takip", layout="wide")

st.write("✅ APP BAŞLADI")

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
    try:
        if os.path.exists(DB_FILE):
            shutil.copy(DB_FILE, BACKUP_FILE)
    except:
        pass

# ---------------- DATA ----------------
def load_data():
    try:
        return pd.read_sql("SELECT * FROM kayitlar", conn)
    except:
        return pd.DataFrame()

df = load_data()

# ---------------- LISTELER ----------------
musteri_list = ["Erlich","Hugo Boss","Tommy","Ten Cate","Blackspade","Lisca","Groenendijk","Armedangels","Vanilla Blush","Falke","Mey"]
hata_kaynagi_list = ["GKK","Tedarikçi","Kumaş","Kalıp"]
ana_neden_list = ["Gramaj","Leke","En Problemi","Kola Kenarı","Kırık","Abraj","Renk Farkı"]
birim_list = ["KG","MT"]
durum_list = ["Açık","Devam Ediyor","Tamamlandı"]

menu = st.sidebar.radio("Menü", ["Veri Girişi", "Dashboard", "Excel Yükle"])

# ---------------- VERİ GİRİŞ ----------------
if menu == "Veri Girişi":
    st.title("📝 Veri Girişi")

    with st.form("form"):
        tarih = st.date_input("Tarih")
        hafta = f"{tarih.isocalendar().week}. Hafta"

        musteri = st.selectbox("Müşteri", musteri_list)
        hata_adi = st.text_input("Hata Adı")
        hata_kg = st.number_input("Hata KG", min_value=0.0)

        if st.form_submit_button("Kaydet"):
            c.execute("""
            INSERT INTO kayitlar VALUES (NULL,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
            """, (
                hafta, str(tarih), "İzmir", "Kesimhane", musteri,
                "", "", "",
                "", hata_adi, "",
                "KG",
                0, 0, 0,
                0, hata_kg,
                "Açık", ""
            ))
            conn.commit()
            create_backup()
            st.success("✅ Kayıt eklendi")

# ---------------- DASHBOARD ----------------
if menu == "Dashboard":
    st.title("📊 Dashboard")

    if df.empty:
        st.warning("⚠️ Veri yok (Excel doğru yüklenmemiş olabilir)")
    else:
        df["hata_kg"] = pd.to_numeric(df["hata_kg"], errors="coerce").fillna(0)

        st.write("Toplam Kayıt:", len(df))

        toplam = df["hata_kg"].sum()

        if toplam == 0:
            st.warning("⚠️ Veri var ama hata_kg boş!")
        else:
            data = df.groupby("musteri")["hata_kg"].sum().reset_index()
            data["%"] = data["hata_kg"] / toplam * 100

            fig = px.bar(data, x="musteri", y="hata_kg",
                         text=data["%"].apply(lambda x: f"%{x:.1f}"))
            st.plotly_chart(fig)

# ---------------- EXCEL YÜKLE ----------------
if menu == "Excel Yükle":
    st.title("📤 Excel'den Veri Yükle")

    uploaded_file = st.file_uploader("Excel yükle", type=["xlsx"])

    if uploaded_file:
        df_excel = pd.read_excel(uploaded_file)

        # normalize
        df_excel.columns = df_excel.columns.str.strip().str.lower()

        st.write("📌 Kolonlar:", df_excel.columns.tolist())
        st.dataframe(df_excel)

        # kolon map
        kolon_map = {
            "müşteri": "musteri",
            "musteri": "musteri",
            "hata kg": "hata_kg",
            "hata_kg": "hata_kg",
            "hata adı": "hata_adi",
            "hata_adi": "hata_adi",
            "tarih": "tarih",
            "hafta": "hafta"
        }

        df_excel = df_excel.rename(columns=kolon_map)

        if st.button("🚀 Aktar"):
            sayac = 0

            for _, row in df_excel.iterrows():
                try:
                    # boş kayıt alma
                    if pd.isna(row.get("musteri")):
                        continue

                    c.execute("""
                    INSERT INTO kayitlar VALUES (NULL,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
                    """, (
                        str(row.get("hafta","")),
                        str(row.get("tarih","")),
                        "İzmir",
                        "Kesimhane",
                        str(row.get("musteri","")),
                        "",
                        "",
                        "",
                        "",
                        str(row.get("hata_adi","")),
                        "",
                        "KG",
                        0,
                        0,
                        0,
                        0,
                        float(row.get("hata_kg",0) or 0),
                        "Açık",
                        ""
                    ))

                    sayac += 1

                except Exception as e:
                    st.warning(f"Satır atlandı: {e}")

            conn.commit()
            create_backup()

            st.success(f"✅ {sayac} kayıt eklendi!")

            # DEBUG
            yeni_df = load_data()
            st.write("DB kayıt sayısı:", len(yeni_df))
            st.dataframe(yeni_df)
