import streamlit as st
import pandas as pd
import sqlite3
import plotly.express as px

st.set_page_config(page_title="Kumaş Hata Takip", layout="wide")

# ---------------- DB ----------------
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

def load_data():
    return pd.read_sql("SELECT * FROM kayitlar", conn)

df = load_data()

# ---------------- LISTELER ----------------
musteri_list = ["Erlich","Hugo Boss","Tommy","Ten Cate","Blackspade","Lisca"]
hata_kaynagi_list = ["GKK","Tedarikçi","Kumaş","Kalıp"]
ana_neden_list = ["Gramaj","Leke","En Problemi","Kola Kenarı"]
birim_list = ["KG","MT"]
durum_list = ["Açık","Devam Ediyor","Tamamlandı"]

menu = st.sidebar.radio("Menü", ["Veri Girişi","Dashboard","Kayıtlar","Excel Yükle"])

# ---------------- VERİ GİRİŞ ----------------
if menu == "Veri Girişi":
    st.title("📝 Veri Girişi")

    with st.form("form"):
        col1,col2,col3 = st.columns(3)

        with col1:
            tarih = st.date_input("Tarih")
            hafta = f"{tarih.isocalendar().week}. Hafta"
            st.text_input("Hafta", value=hafta, disabled=True)
            st.text_input("Tesis", value="İzmir", disabled=True)

        with col2:
            st.text_input("Bant", value="Kesimhane", disabled=True)
            musteri = st.selectbox("Müşteri", musteri_list)
            pastal_no = st.text_input("Pastal No")

        with col3:
            model_no = st.text_input("Model No")
            kumas_kalite = st.text_input("Kumaş Kalite")
            hata_kaynagi = st.selectbox("Hata Kaynağı", hata_kaynagi_list)

        hata_adi = st.text_input("Hata Adı")
        ana_neden = st.selectbox("Ana Neden", ana_neden_list)
        birim = st.selectbox("Birim", birim_list)

        col4,col5,col6 = st.columns(3)

        with col4:
            pastal_ihtiyac = st.number_input("Pastal İhtiyacı", 0.0)

        with col5:
            cikan_top = st.number_input("Çıkan Top", 0)
            hatali_top = st.number_input("Hatalı Top", 0)

        with col6:
            cikan_kg = st.number_input("Çıkan KG", 0.0)
            hata_kg = st.number_input("Hata KG", 0.0)

        durum = st.selectbox("Durum", durum_list)
        aksiyon = st.text_area("Aksiyon")

        if st.form_submit_button("Kaydet"):
            c.execute("""
            INSERT INTO kayitlar VALUES (NULL,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
            """,(hafta,str(tarih),"İzmir","Kesimhane",musteri,
                 pastal_no,model_no,kumas_kalite,
                 hata_kaynagi,hata_adi,ana_neden,
                 birim,
                 pastal_ihtiyac,cikan_top,hatali_top,
                 cikan_kg,hata_kg,
                 durum,aksiyon))
            conn.commit()
            st.success("Kayıt eklendi")

# ---------------- DASHBOARD ----------------
if menu == "Dashboard":
    st.title("📊 Dashboard")

    if df.empty:
        st.warning("Veri yok")
    else:
        df["hata_kg"] = pd.to_numeric(df["hata_kg"], errors="coerce").fillna(0)

        toplam = df["hata_kg"].sum()

        if toplam > 0:
            def grafik(col):
                d = df.groupby(col)["hata_kg"].sum().reset_index()
                d["%"] = d["hata_kg"] / toplam * 100
                fig = px.bar(d, x=col, y="hata_kg",
                             text=d["%"].apply(lambda x: f"%{x:.1f}"))
                return fig

            col1,col2 = st.columns(2)
            with col1:
                st.plotly_chart(grafik("musteri"))
                st.plotly_chart(grafik("hata_kaynagi"))
            with col2:
                st.plotly_chart(grafik("ana_neden"))
                st.plotly_chart(grafik("birim"))
        else:
            st.warning("Hata verisi yok")

# ---------------- KAYITLAR ----------------
if menu == "Kayıtlar":
    st.title("Kayıtlar")

    if not df.empty:
        secilen = st.selectbox("Kayıt seç", df["id"])
        kayit = df[df["id"]==secilen].iloc[0]

        musteri_index = musteri_list.index(kayit["musteri"]) if kayit["musteri"] in musteri_list else 0
        durum_index = durum_list.index(kayit["durum"]) if kayit["durum"] in durum_list else 0

        musteri = st.selectbox("Müşteri", musteri_list, index=musteri_index)
        hata_kg = st.number_input("Hata KG", value=float(kayit["hata_kg"]))
        durum = st.selectbox("Durum", durum_list, index=durum_index)
        aksiyon = st.text_area("Aksiyon", kayit["aksiyon"])

        if st.button("Güncelle"):
            c.execute("UPDATE kayitlar SET musteri=?, hata_kg=?, durum=?, aksiyon=? WHERE id=?",
                      (musteri,hata_kg,durum,aksiyon,secilen))
            conn.commit()
            st.success("Güncellendi")

        if st.button("Sil"):
            c.execute("DELETE FROM kayitlar WHERE id=?", (secilen,))
            conn.commit()
            st.warning("Silindi")

# ---------------- EXCEL ----------------
if menu == "Excel Yükle":
    st.title("Excel Yükle")

    file = st.file_uploader("Excel seç", type=["xlsx"])

    if file:
        df_excel = pd.read_excel(file)
        df_excel.columns = df_excel.columns.str.lower().str.strip()

        st.dataframe(df_excel)

        if st.button("Aktar"):
            sayac = 0

            for _,row in df_excel.iterrows():
                try:
                    musteri = str(row.get("musteri") or row.get("müşteri") or "")
                    if musteri == "":
                        continue

                    c.execute("""
                    INSERT INTO kayitlar VALUES (NULL,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
                    """,(
                        str(row.get("hafta","")),
                        str(row.get("tarih","")),
                        "İzmir",
                        "Kesimhane",
                        musteri,
                        "",
                        "",
                        "",
                        "",
                        str(row.get("hata_adi","")),
                        "",
                        "KG",
                        0,0,0,0,
                        float(row.get("hata_kg",0) or 0),
                        "Açık",
                        ""
                    ))

                    sayac+=1
                except:
                    continue

            conn.commit()
            st.success(f"{sayac} kayıt eklendi")
