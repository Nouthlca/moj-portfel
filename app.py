import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.express as px

# Konfiguracja strony
st.set_page_config(page_title="Mój Portfel Inwestycyjny", layout="wide", page_icon="⚡")

# --- CUSTOM CSS: RADIOAKTYWNY NEON & GRADIENTY ---
st.markdown("""
<style>
    /* Głębokie, kontrastowe tło całej aplikacji */
    .stApp {
        background-color: #07090e;
        color: #ffffff;
    }
    
    /* Panel boczny */
    section[data-testid="stSidebar"] {
        background-color: #0d1117;
        border-right: 1px solid #1f293d;
    }
    
    /* Karty metryczne z gradientem i neonową poświatą */
    div[data-testid="stMetric"] {
        background: linear-gradient(135deg, #0d131a 0%, #101a26 100%);
        border: 1px solid #00ff9d;
        border-radius: 16px;
        padding: 18px 22px;
        box-shadow: 0 0 15px rgba(0, 255, 157, 0.15);
    }
    
    /* Etykiety i wartości metryk */
    div[data-testid="stMetricLabel"] > label {
        color: #8fa3bf !important;
        font-size: 1.0rem !important;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    div[data-testid="stMetricValue"] {
        background: linear-gradient(90deg, #00ff9d, #00e5ff);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-size: 2.2rem !important;
        font-weight: 900 !important;
    }
    
    /* Zakładki (Tabs) */
    button[data-baseweb="tab"] {
        background-color: #0d1117;
        color: #7a8b9e;
        border-radius: 10px 10px 0 0;
        font-weight: 700;
        padding: 12px 24px;
        margin-right: 5px;
        border: 1px solid #1f293d;
    }
    button[aria-selected="true"] {
        color: #00ff9d !important;
        border: 1px solid #00ff9d !important;
        border-bottom: none !important;
        background: linear-gradient(180deg, rgba(0,255,157,0.1) 0%, rgba(13,17,23,1) 100%) !important;
        box-shadow: 0 -4px 10px rgba(0, 255, 157, 0.2);
    }

    /* Stylizacje nagłówków */
    h1 {
        background: linear-gradient(90deg, #00ff9d 0%, #00bfff 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-weight: 900;
        font-size: 2.5rem !important;
    }
    h2, h3 {
        color: #00e5ff !important;
        font-weight: 700;
    }
    
    /* Stylizowanie tabeli */
    div[data-testid="stDataFrame"] {
        border: 1px solid #00bfff;
        border-radius: 12px;
        box-shadow: 0 0 10px rgba(0, 191, 255, 0.1);
    }
</style>
""", unsafe_allow_html=True)

st.title("⚡ PRYWATNY TRACKER INWESTYCYJNY")

# --- FUNKCJA POBIERANIA KURSU ---
@st.cache_data(ttl=1800)
def pobierz_kurs(ticker):
    if not ticker:
        return 0.0
    try:
        dane = yf.Ticker(ticker.strip().upper())
        cena = dane.fast_info['lastPrice']
        return float(cena)
    except:
        return 0.0

KURS_EUR_PLN = pobierz_kurs("EURPLN=X") or 4.30
KURS_USD_PLN = pobierz_kurs("USDPLN=X") or 3.90

# --- PANEL BOCZNY: WPROWADZANIE DANYCH ---
st.sidebar.header("⚙️ Zarządzanie Portfelem")

def formularz_pozycji(prefix_konta, domyslny_ticker, domyslne_sztuki, domyslna_cena):
    col1, col2, col3 = st.sidebar.columns(3)
    ticker = col1.text_input("Ticker", value=domyslny_ticker, key=f"{prefix_konta}_ticker").strip().upper()
    sztuki = col2.number_input("Sztuki", min_value=0.0, value=domyslne_sztuki, step=0.0001, format="%.4f", key=f"{prefix_konta}_sztuki")
    cena_zakupu = col3.number_input("Śr. cena", min_value=0.0, value=domyslna_cena, step=0.01, format="%.2f", key=f"{prefix_konta}_cena")
    return ticker, sztuki, cena_zakupu

# --- KONTO XTB ---
st.sidebar.subheader("🔴 Konto XTB")
xtb_gotowka = st.sidebar.number_input("XTB: Gotówka (PLN)", min_value=0.0, value=500.0, step=100.0, key="xtb_cash")

st.sidebar.caption("Pozycje XTB:")
p1_t, p1_s, p1_c = formularz_pozycji("xtb_1", "SXR8.DE", 10.0000, 1800.0)
p2_t, p2_s, p2_c = formularz_pozycji("xtb_2", "AAPL", 5.2515, 170.0)
p3_t, p3_s, p3_c = formularz_pozycji("xtb_3", "NVDA", 1.1234, 110.0)
p4_t, p4_s, p4_c = formularz_pozycji("xtb_4", "", 0.0000, 0.0)
p5_t, p5_s, p5_c = formularz_pozycji("xtb_5", "", 0.0000, 0.0)

pozycje_xtb = [
    {"ticker": p1_t, "sztuki": p1_s, "cena_zakupu": p1_c},
    {"ticker": p2_t, "sztuki": p2_s, "cena_zakupu": p2_c},
    {"ticker": p3_t, "sztuki": p3_s, "cena_zakupu": p3_c},
    {"ticker": p4_t, "sztuki": p4_s, "cena_zakupu": p4_c},
    {"ticker": p5_t, "sztuki": p5_s, "cena_zakupu": p5_c},
]

# --- KONTO IKZE MBANK ---
st.sidebar.subheader("🟢 Konto IKZE (mBank)")
mbank_gotowka = st.sidebar.number_input("IKZE: Gotówka (PLN)", min_value=0.0, value=1000.0, step=100.0, key="mbank_cash")

st.sidebar.caption("Pozycje IKZE:")
m1_t, m1_s, m1_c = formularz_pozycji("mbank_1", "SXR8.DE", 3.1250, 1900.0)
m2_t, m2_s, m2_c = formularz_pozycji("mbank_2", "VWCE.DE", 12.5000, 480.0)
m3_t, m3_s, m3_c = formularz_pozycji("mbank_3", "", 0.0000, 0.0)
m4_t, m4_s, m4_c = formularz_pozycji("mbank_4", "", 0.0000, 0.0)
m5_t, m5_s, m5_c = formularz_pozycji("mbank_5", "", 0.0000, 0.0)

pozycje_mbank = [
    {"ticker": m1_t, "sztuki": m1_s, "cena_zakupu": m1_c},
    {"ticker": m2_t, "sztuki": m2_s, "cena_zakupu": m2_c},
    {"ticker": m3_t, "sztuki": m3_s, "cena_zakupu": m3_c},
    {"ticker": m4_t, "sztuki": m4_s, "cena_zakupu": m4_c},
    {"ticker": m5_t, "sztuki": m5_s, "cena_zakupu": m5_c},
]

# --- PRZELICZANIE DANYCH ---
def przetworz_portfel(pozycje, gotowka, nazwa_konta):
    dane_tabeli = []
    dane_wykres = []
    wartosc_aktywow = 0.0
    zysk_razem = 0.0
    
    for item in pozycje:
        t = item["ticker"]
        szt = item["sztuki"]
        sr_cena = item["cena_zakupu"]
        
        if t and szt > 0:
            cena_rkt = pobierz_kurs(t)
            
            if ".DE" in t:
                cena_rkt_pln = cena_rkt * KURS_EUR_PLN
            elif t in ["AAPL", "NVDA", "MSFT", "AMZN", "GOOGL", "TSLA", "META"]:
                cena_rkt_pln = cena_rkt * KURS_USD_PLN
            else:
                cena_rkt_pln = cena_rkt
                
            wartosc = szt * cena_rkt_pln
            koszt = szt * sr_cena
            zysk = wartosc - koszt
            
            wartosc_aktywow += wartosc
            zysk_razem += zysk
            
            dane_tabeli.append({
                "Ticker": t,
                "Sztuki": f"{szt:.4f}",
                "Śr. Cena Zakupu": f"{sr_cena:.2f} PLN",
                "Aktualny Kurs": f"{cena_rkt_pln:.2f} PLN",
                "Wartość": f"{wartosc:,.2f} PLN".replace(",", " "),
                "Zysk / Strata": f"{zysk:,.2f} PLN".replace(",", " ")
            })
            
            dane_wykres.append({
                "Nazwa": f"{t} ({nazwa_konta})",
                "Wartość PLN": wartosc,
                "Konto": nazwa_konta
            })
            
    if gotowka > 0:
        dane_wykres.append({
            "Nazwa": f"Gotówka ({nazwa_konta})",
            "Wartość PLN": gotowka,
            "Konto": nazwa_konta
        })

    calosc = wartosc_aktywow + gotowka
    return calosc, wartosc_aktywow, zysk_razem, dane_tabeli, dane_wykres

calosc_xtb, aktywa_xtb, zysk_xtb, tabela_xtb, wykres_xtb = przetworz_portfel(pozycje_xtb, xtb_gotowka, "XTB")
calosc_mbank, aktywa_mbank, zysk_mbank, tabela_mbank, wykres_mbank = przetworz_portfel(pozycje_mbank, mbank_gotowka, "IKZE")

laczny_majatek = calosc_xtb + calosc_mbank
laczny_zysk = zysk_xtb + zysk_mbank
laczna_gotowka = xtb_gotowka + mbank_gotowka

# --- WIDOK GŁÓWNY ---
st.markdown("### 💎 STAN MAJĄTKU")
c1, c2, c3 = st.columns(3)
c1.metric("ŁĄCZNY PORTFEL", f"{laczny_majatek:,.2f} PLN".replace(",", " "))
c2.metric("ZYSK / STRATA", f"{laczny_zysk:,.2f} PLN".replace(",", " "), delta=f"{laczny_zysk:,.2f} PLN".replace(",", " "))
c3.metric("WOLNA GOTÓWKA", f"{laczna_gotowka:,.2f} PLN".replace(",", " "))

st.markdown("<br>", unsafe_allow_html=True)

# ZAKŁADKI
tab_xtb, tab_mbank, tab_wykresy = st.tabs(["🔴 KONTO XTB", "🟢 IKZE MBANK", "📊 ANALITYKA I WYKRESY"])

with tab_xtb:
    st.subheader("🔴 Szczegóły Portfela XTB")
    col1, col2, col3 = st.columns(3)
    col1.metric("Wartość konta", f"{calosc_xtb:,.2f} PLN".replace(",", " "))
    col2.metric("Zysk na akcjach", f"{zysk_xtb:,.2f} PLN".replace(",", " "))
    col3.metric("Wolna gotówka", f"{xtb_gotowka:,.2f} PLN".replace(",", " "))
    
    st.markdown("<br>", unsafe_allow_html=True)
    if tabela_xtb:
        st.dataframe(pd.DataFrame(tabela_xtb), use_container_width=True)
    else:
        st.info("Brak wprowadzonych aktywów dla XTB.")

with tab_mbank:
    st.subheader("🟢 Szczegóły Portfela IKZE")
    col1, col2, col3 = st.columns(3)
    col1.metric("Wartość konta", f"{calosc_mbank:,.2f} PLN".replace(",", " "))
    col2.metric("Zysk na akcjach", f"{zysk_mbank:,.2f} PLN".replace(",", " "))
    col3.metric("Wolna gotówka", f"{mbank_gotowka:,.2f} PLN".replace(",", " "))
    
    st.markdown("<br>", unsafe_allow_html=True)
    if tabela_mbank:
        st.dataframe(pd.DataFrame(tabela_mbank), use_container_width=True)
    else:
        st.info("Brak wprowadzonych aktywów dla IKZE.")

with tab_wykresy:
    st.subheader("📊 Neonowa Analityka Portfela")
    
    wszystkie_dane_wykres = wykres_xtb + wykres_mbank
    
    if wszystkie_dane_wykres:
        df_wykres = pd.DataFrame(wszystkie_dane_wykres)
        
        col_w1, col_w2 = st.columns(2)
        
        # Paleta barw "radioaktywna zielono-niebieska"
        neon_colors = ["#00ff9d", "#00e5ff", "#00bfff", "#0072ff", "#00ffcc", "#39ff14", "#00f0ff"]
        
        with col_w1:
            st.markdown("**Struktura Wszystkich Aktywów**")
            fig_pie = px.pie(
                df_wykres, 
                values="Wartość PLN", 
                names="Nazwa", 
                hole=0.5,
                color_discrete_sequence=neon_colors
            )
            fig_pie.update_layout(
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                font=dict(color="#ffffff", size=14)
            )
            st.plotly_chart(fig_pie, use_container_width=True)
            
        with col_w2:
            st.markdown("**Porównanie Kont Inwestycyjnych**")
            df_konta = pd.DataFrame([
                {"Konto": "XTB", "Wartość PLN": calosc_xtb},
                {"Konto": "IKZE mBank", "Wartość PLN": calosc_mbank}
            ])
            fig_bar = px.bar(
                df_konta, 
                x="Konto", 
                y="Wartość PLN", 
                color="Konto", 
                text_auto='.2f',
                color_discrete_sequence=["#00ff9d", "#00e5ff"]
            )
            fig_bar.update_layout(
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                font=dict(color="#ffffff", size=14)
            )
            st.plotly_chart(fig_bar, use_container_width=True)
    else:
        st.info("Brak danych do wyświetlenia wykresów.")
