import streamlit as st
import yfinance as yf

st.set_page_config(page_title="Mój Portfel Inwestycyjny", layout="wide", page_icon="📈")

st.title("📊 Prywatny Tracker Inwestycyjny")

# --- POBIERANIE KURSU NA ŻYWO ---
@st.cache_data(ttl=3600)
def pobierz_kurs(ticker):
    try:
        dane = yf.Ticker(ticker)
        cena = dane.fast_info['lastPrice']
        return cena
    except:
        return 0.0

# Ticker dla ETF na S&P 500 (np. iShares Core S&P 500 UCITS ETF w EUR)
CENA_SP500_EUR = pobierz_kurs("SXR8.DE")
KURS_EUR_PLN = pobierz_kurs("EURPLN=X")

# Przeliczenie ceny na PLN
cena_sp500_pln = CENA_SP500_EUR * KURS_EUR_PLN if (CENA_SP500_EUR and KURS_EUR_PLN) else 2100.0

# --- PANEL BOCZNY: WPROWADZANIE DANYCH ---
st.sidebar.header("⚙️ Twoje Aktywa")

st.sidebar.subheader("🔴 Konto XTB")
xtb_sztuki = st.sidebar.number_input("XTB: Liczba ETF S&P 500", min_value=0.0, value=10.0, step=1.0)
xtb_srednia = st.sidebar.number_input("XTB: Średnia cena zakupu (PLN)", min_value=0.0, value=1800.0, step=10.0)
xtb_gotowka = st.sidebar.number_input("XTB: Wolna gotówka (PLN)", min_value=0.0, value=500.0, step=100.0)

st.sidebar.subheader("🟢 Konto IKZE (mBank)")
mbank_sztuki = st.sidebar.number_input("IKZE: Liczba ETF S&P 500", min_value=0.0, value=5.0, step=1.0)
mbank_srednia = st.sidebar.number_input("IKZE: Średnia cena zakupu (PLN)", min_value=0.0, value=1900.0, step=10.0)
mbank_gotowka = st.sidebar.number_input("IKZE: Wolna gotówka (PLN)", min_value=0.0, value=1000.0, step=100.0)

# --- OBLICZENIA ---
wartosc_aktyw_xtb = xtb_sztuki * cena_sp500_pln
koszt_xtb = xtb_sztuki * xtb_srednia
zysk_aktyw_xtb = wartosc_aktyw_xtb - koszt_xtb
calosc_xtb = wartosc_aktyw_xtb + xtb_gotowka

wartosc_aktyw_mbank = mbank_sztuki * cena_sp500_pln
koszt_mbank = mbank_sztuki * mbank_srednia
zysk_aktyw_mbank = wartosc_aktyw_mbank - koszt_mbank
calosc_mbank = wartosc_aktyw_mbank + mbank_gotowka

laczny_majatek = calosc_xtb + calosc_mbank
laczny_zysk = zysk_aktyw_xtb + zysk_aktyw_mbank
laczna_gotowka = xtb_gotowka + mbank_gotowka

# --- WIDOK GŁÓWNY ---
st.header("📈 Podsumowanie Łączne")
c1, c2, c3 = st.columns(3)
c1.metric("Wartość całego portfela", f"{laczny_majatek:,.2f} PLN".replace(",", " "))
c2.metric("Łączny Zysk / Strata", f"{laczny_zysk:,.2f} PLN".replace(",", " "), delta=f"{laczny_zysk:,.2f} PLN".replace(",", " "))
c3.metric("Wolna gotówka razem", f"{laczna_gotowka:,.2f} PLN".replace(",", " "))

st.caption(f"ℹ️ Aktualny kurs rynkowy ETF S&P 500 (SXR8.DE): **{cena_sp500_pln:.2f} PLN** (pobrany automatycznie)")

st.divider()

# ZAKŁADKI NA KONTA
tab_xtb, tab_mbank = st.tabs(["🔴 XTB", "🟢 IKZE mBank"])

with tab_xtb:
    st.subheader("Konto XTB")
    col1, col2, col3 = st.columns(3)
    col1.metric("Łączna wartość konta", f"{calosc_xtb:,.2f} PLN".replace(",", " "))
    col2.metric("Zysk na akcjach/ETF", f"{zysk_aktyw_xtb:,.2f} PLN".replace(",", " "))
    col3.metric("Dostępna gotówka", f"{xtb_gotowka:,.2f} PLN".replace(",", " "))

with tab_mbank:
    st.subheader("Konto IKZE w mBanku")
    col1, col2, col3 = st.columns(3)
    col1.metric("Łączna wartość konta", f"{calosc_mbank:,.2f} PLN".replace(",", " "))
    col2.metric("Zysk na akcjach/ETF", f"{zysk_aktyw_mbank:,.2f} PLN".replace(",", " "))
    col3.metric("Dostępna gotówka", f"{mbank_gotowka:,.2f} PLN".replace(",", " "))
