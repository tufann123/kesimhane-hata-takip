import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime
import io

st.set_page_config(page_title="Kumaş Analiz Sistemi", layout="wide")

# ----------------------------
# DATABASE
# ----------------------------
conn = sqlite3.connect("kumas.db", check_same_thread=False)
c = conn.cursor()

c.execute("""
CREATE TABLE IF NOT EXISTS kayitlar (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    tarih TEXT,
    operator TEXT,
    makine TEXT,
    kumas_turu TEXT,
    hata_turu TEXT,
    hata_adedi INTEGER,
    metre REAL,
    aciklama TEXT
)
""")
conn.commit()

# ----------------------------
# SIDEBAR
# ----------------------------
st.sidebar.title("📊 Menü")
menu = st.sidebar.radio("Seçim Yap", [
    "Veri Girişi",
    "Dashboard",
    "Kayıtlar",
])

# ----------------------------
# VERİ GİRİŞİ
# ----------------------------
if menu == "Veri Girişi":
    st.title("📝 Veri Girişi")

    with st.form("veri_formu"):
        col1, col2, col3 = st.columns(3)

        with col1:
            tarih = st.date_input("Tarih", datetime.today())
            operator = st.text_input("Operatör")

        with col2:
            makine = st.text_input("Makine")
            kumas_turu = st.text_input("Kumaş Türü")

        with col3:
            hata_turu = st.selectbox("Hata Türü", [
                "Delik",
                "Yağ Lekesi",
                "İplik Hatası",
                "Boyama Hatası",
                "Diğer"
            ])
            hata_adedi = st.number_input("Hata Adedi", min_value=0)

        metre = st.number_input("Metre", min_value=0.0)
        aciklama = st.text_area("Açıklama")

        kaydet = st.form_submit_button("Kaydet")

        if kaydet:
            c.execute("""
            INSERT INTO kayitlar 
            (tarih, operator, makine, kumas_turu, hata_turu, hata_adedi, metre, aciklama)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                str(tarih),
                operator,
                makine,
                kumas_turu,
                hata_turu,
                hata_adedi,
                metre,
                aciklama
            ))
            conn.commit()
            st.success("✅ Kayıt eklendi!")

# ----------------------------
# DATAFRAME ÇEK
# ----------------------------
def veri_getir():
    df = pd.read_sql("SELECT * FROM kayitlar", conn)
    if not df.empty:
        df["tarih"] = pd.to_datetime(df["tarih"])
    return df

df = veri_getir()

# ----------------------------
# DASHBOARD
# ----------------------------
if menu == "Dashboard":
    st.title("📈 Dashboard")

    if df.empty:
        st.warning("Veri yok")
    else:
        col1, col2, col3 = st.columns(3)

        col1.metric("Toplam Kayıt", len(df))
        col2.metric("Toplam Hata", int(df["hata_adedi"].sum()))
        col3.metric("Toplam Metre", int(df["metre"].sum()))

        st.divider()

        # Operatör bazlı
        st.subheader("👥 Operatör Performansı")
        op = df.groupby("operator")["hata_adedi"].sum().sort_values()
        st.bar_chart(op)

        # En iyi / kötü
        if not op.empty:
            st.success(f"🏆 En iyi: {op.idxmin()}")
            st.error(f"⚠️ En kötü: {op.idxmax()}")

        # Hata türü
        st.subheader("📊 Hata Türü Dağılımı")
        hata = df.groupby("hata_turu")["hata_adedi"].sum()
        st.bar_chart(hata)

        # Haftalık trend
        st.subheader("📅 Haftalık Trend")
        df["hafta"] = df["tarih"].dt.to_period("W").astype(str)
        haftalik = df.groupby("hafta")["hata_adedi"].sum()
        st.line_chart(haftalik)

        # Düşüş alarmı
        if len(haftalik) > 2:
            if haftalik.iloc[-1] > haftalik.iloc[-2]:
                st.error("🚨 Hata artışı var!")
            else:
                st.success("📉 İyileşme var!")

# ----------------------------
# KAYITLAR + EXPORT
# ----------------------------
if menu == "Kayıtlar":
    st.title("📋 Kayıtlar")

    if df.empty:
        st.warning("Veri yok")
    else:
        st.dataframe(df, use_container_width=True)

        # Excel export
        def to_excel(df):
            output = io.BytesIO()
            with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                df.to_excel(writer, index=False)
            return output.getvalue()

        excel_data = to_excel(df)

        st.download_button(
            label="📥 Excel indir",
            data=excel_data,
            file_name="kumas_analiz.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
