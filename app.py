import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.express as px

# Konfiguracja strony
st.set_page_config(page_title="Mój Portfel Inwestycyjny", layout="wide", page_icon="📈")

# --- CUSTOM CSS (STYLES & DARK THEME) ---
st.markdown("""
<style>
    /* Tło całej aplikacji */
    .stApp {
        background-color: #0e1117;
        color: #e0e0e0;
    }
    
    /* Stylizacja panelu bocznego */
    section[data-testid="stSidebar"] {
        background-color: #161b22;
        border-right: 1px solid #30363d;
    }
    
    /* Stylizacja kafelków z metrykami */
    div[data-testid="stMetric"] {
        background-color: #161b22;
        border: 1px solid #30363d;
        border-radius: 12px;
        padding: 15px 20px;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
    }
    
    /* Stylizacja etykiet i wartości w metrykach */
    div[data-testid="stMetricLabel"] > label {
        color: #8b949e !important;
        font-size: 0.9rem !important;
        font-weight: 600;
    }
    div[data-testid="stMetricValue"] {
        color: #58a6ff !important;
        font-weight: 700;
    }
    
    /* Zakładki (Tabs) */
    button[data-baseweb="tab"] {
        background-color: transparent;
        color: #8b949e;
        border-radius: 8px 8px 0px 0px;
        font-weight: 600;
        padding: 10px 20px;
    }
    button[aria-selected="true"] {
        color: #58a6ff !important;
        border-bottom: 3px solid #58a6ff !important;
        background-color: #161b22 !important;
    }

    /* Nagłówki z subtelnym akcentem */
    h1, h2, h3 {
        color: #f0f6fc;
        font-family: 'SF Pro Display', -apple-system, BlinkMacSystemFont, Roboto, sans-serif;
    }
</style>
""", unsafe_allow_html=Trick if 'Trick' in locals() else True)

st.title("⚡ Prywatny Tracker Inwestycyjny")

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
st.header("📈 Podsumowanie Łączne")
c1, c2, c3 = st.columns(3)
c1.metric("Wartość całego portfela", f"{laczny_majatek:,.2f} PLN".replace(",", " "))
c2.metric("Łączny Zysk / Strata", f"{laczny_zysk:,.2f} PLN".replace(",", " "), delta=f"{laczny_zysk:,.2f} PLN".replace(",", " "))
c3.metric("Wolna gotówka razem", f"{laczna_gotowka:,.2f} PLN".replace(",", " "))

st.divider()

# ZAKŁADKI W APLIKACJI
tab_xtb, tab_mbank, tab_wykresy = st.tabs(["🔴 XTB", "🟢 IKZE mBank", "📊 Wykresy i Analityka"])

with tab_xtb:
    st.subheader("Konto XTB")
    col1, col2, col3 = st.columns(3)
    col1.metric("Łączna wartość", f"{calosc_xtb:,.2f} PLN".replace(",", " "))
    col2.metric("Zysk na aktywach", f"{zysk_xtb:,.2f} PLN".replace(",", " "))
    col3.metric("Gotówka", f"{xtb_gotowka:,.2f} PLN".replace(",", " "))
    
    st.markdown("<br>", unsafe_allow_html=True)
    if tabela_xtb:
        st.dataframe(pd.DataFrame(tabela_xtb), use_container_width=True)
    else:
        st.info("Brak wprowadzonych aktywów dla XTB.")

with tab_mbank:
    st.subheader("Konto IKZE w mBanku")
    col1, col2, col3 = st.columns(3)
    col1.metric("Łączna wartość", f"{calosc_mbank:,.2f} PLN".replace(",", " "))
    col2.metric("Zysk na aktywach", f"{zysk_mbank:,.2f} PLN".replace(",", " "))
    col3.metric("Gotówka", f"{mbank_gotowka:,.2f} PLN".replace(",", " "))
    
    st.markdown("<br>", unsafe_allow_html=True)
    if tabela_mbank:
        st.dataframe(pd.DataFrame(tabela_mbank), use_container_width=True)
    else:
        st.info("Brak wprowadzonych aktywów dla IKZE.")

with tab_wykresy:
    st.subheader("📊 Struktura Twojego Majątku")
    
    wszystkie_dane_wykres = wykres_xtb + wykres_mbank
    
    if wszystkie_dane_wykres:
        df_wykres = pd.DataFrame(wszystkie_dane_wykres)
        
        col_w1, col_w2 = st.columns(2)
        
        with col_w1:
            st.markdown("**Alokacja Całego Portfela**")
            fig_pie = px.pie(
                df_wykres, 
                values="Wartość PLN", 
                names="Nazwa", 
                hole=0.45,
                color_discrete_sequence=px.colors.qualitative.Dark24
            )
            fig_pie.update_layout(
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                font=dict(color="#e0e0e0")
            )
            st.plotly_chart(fig_pie, use_container_width=True)
            
        with col_w2:
            st.markdown("**Porównanie Kont (XTB vs IKZE)**")
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
                color_discrete_map={"XTB": "#e63946", "IKZE mBank": "#2a9d8f"}
            )
            fig_bar.update_layout(
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                font=dict(color="#e0e0e0")
            )
            st.plotly_chart(fig_bar, use_container_width=True)
    else:
        st.info("Brak danych do wyświetlenia wykresów.")
