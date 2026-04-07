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
try:
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
except Exception as e:
    st.error(f"DB Hata: {e}")

# ---------------- BACKUP ----------------
def create_backup():
    try:
        if os.path.exists(DB_FILE):
            shutil.copy(DB_FILE, BACKUP_FILE)
    except:
        pass

def restore_backup(uploaded_file):
    try:
        with open(DB_FILE, "wb") as f:
            f.write(uploaded_file.read())
    except:
        st.error("Yedek yüklenemedi")

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

# ---------------- MENU ----------------
menu = st.sidebar.radio("Menü", ["Veri Girişi", "Dashboard", "Kayıtlar", "Yedekleme", "Excel Yükle"])

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
            cikan_kg = st.number_input("Çıkan Kumaş KG", min_value=0.0)
            hata_kg = st.number_input("Hata KG", min_value=0.0)

        durum = st.selectbox("Durum", durum_list)
        aksiyon = st.text_area("Aksiyon")

        if st.form_submit_button("Kaydet"):
            try:
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
                create_backup()
                st.success("✅ Kayıt eklendi")
            except Exception as e:
                st.error(f"Kayıt hatası: {e}")

# ---------------- DASHBOARD ----------------
if menu == "Dashboard":
    st.title("📊 Dashboard")

    if df.empty:
        st.warning("Veri yok")
    else:
        try:
            df["tarih"] = pd.to_datetime(df["tarih"], errors="coerce")

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

            col1, col2 = st.columns(2)

            with col1:
                st.plotly_chart(plot(df, "musteri"))
                st.plotly_chart(plot(df, "hata_kaynagi"))

            with col2:
                st.plotly_chart(plot(df, "ana_neden"))
                st.plotly_chart(plot(df, "birim"))

        except Exception as e:
            st.error(f"Dashboard hata: {e}")

# ---------------- KAYITLAR ----------------
if menu == "Kayıtlar":
    st.title("📋 Kayıt Yönetimi")

    if df.empty:
        st.warning("Veri yok")
    else:
        try:
            secilen_id = st.selectbox("Kayıt Seç", df["id"])
            kayit = df[df["id"] == secilen_id].iloc[0]

            with st.form("edit"):

                musteri_index = musteri_list.index(kayit["musteri"]) if kayit["musteri"] in musteri_list else 0
                musteri = st.selectbox("Müşteri", musteri_list, index=musteri_index)

                hata_adi = st.text_input("Hata Adı", kayit["hata_adi"])
                hata_kg = st.number_input("Hata KG", value=float(kayit["hata_kg"]))

                durum_index = durum_list.index(kayit["durum"]) if kayit["durum"] in durum_list else 0
                durum = st.selectbox("Durum", durum_list, index=durum_index)

                aksiyon = st.text_area("Aksiyon", kayit["aksiyon"])

                if st.form_submit_button("Güncelle"):
                    c.execute("""
                    UPDATE kayitlar
                    SET musteri=?, hata_adi=?, hata_kg=?, durum=?, aksiyon=?
                    WHERE id=?
                    """, (musteri, hata_adi, hata_kg, durum, aksiyon, secilen_id))

                    conn.commit()
                    create_backup()
                    st.success("✅ Güncellendi")

            if st.button("🗑️ Sil"):
                c.execute("DELETE FROM kayitlar WHERE id=?", (secilen_id,))
                conn.commit()
                create_backup()
                st.warning("Silindi")

        except Exception as e:
            st.error(f"Kayıt ekranı hata: {e}")

# ---------------- EXCEL YÜKLE ----------------
if menu == "Excel Yükle":
    st.title("📤 Excel Yükle")

    uploaded_file = st.file_uploader("Excel yükle", type=["xlsx"])

    if uploaded_file:
        try:
            df_excel = pd.read_excel(uploaded_file)
            st.dataframe(df_excel)

            if st.button("Aktar"):
                for _, row in df_excel.iterrows():
                    c.execute("""
                    INSERT INTO kayitlar VALUES (NULL,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
                    """, (
                        str(row.get("hafta","")),
                        str(row.get("tarih","")),
                        str(row.get("tesis","İzmir")),
                        str(row.get("bant","Kesimhane")),
                        str(row.get("musteri","")),
                        str(row.get("pastal_no","")),
                        str(row.get("model_no","")),
                        str(row.get("kumas_kalite","")),
                        str(row.get("hata_kaynagi","")),
                        str(row.get("hata_adi","")),
                        str(row.get("ana_neden","")),
                        str(row.get("birim","KG")),
                        float(row.get("pastal_ihtiyac",0)),
                        int(row.get("cikan_top",0)),
                        int(row.get("hatali_top",0)),
                        float(row.get("cikan_kg",0)),
                        float(row.get("hata_kg",0)),
                        str(row.get("durum","Açık")),
                        str(row.get("aksiyon",""))
                    ))
                conn.commit()
                create_backup()
                st.success("✅ Yüklendi")

        except Exception as e:
            st.error(f"Excel hata: {e}")

# ---------------- YEDEK ----------------
if menu == "Yedekleme":
    st.title("💾 Yedekleme")

    try:
        with open(DB_FILE, "rb") as f:
            st.download_button("DB indir", f, file_name="kumas.db")
    except:
        st.warning("DB yok")

    uploaded = st.file_uploader("Yedek yükle", type=["db"])

    if uploaded:
        restore_backup(uploaded)
        st.success("Yüklendi")
