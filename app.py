import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import json
import os
import random
import requests
from datetime import datetime, timedelta

# Konfiguracja strony
st.set_page_config(page_title="Finanse Karola", layout="wide", page_icon="⚡")

CONFIG_FILE = "pozycje_portfela.json"
HISTORY_FILE = "historia_portfela.csv"
CASH_HISTORY_FILE = "historia_gotowki.csv"
BACKUP_DIR = "backupy"
USER_BACKUP_DIR = "moje_kopie_zapasowe"

# Tworzenie folderów
for folder in [BACKUP_DIR, USER_BACKUP_DIR]:
    if not os.path.exists(folder):
        os.makedirs(folder)

# Pobieranie losowego cytatu z internetu
@st.cache_data(ttl=3600)
def pobierz_cytat_z_neta():
    try:
        response = requests.get("https://api.quotable.io/random?tags=inspirational|business|wisdom", timeout=3)
        if response.status_code == 200:
            data = response.json()
            return {"cytat": data.get("content"), "autor": data.get("author")}
    except:
        pass
    
    awaryjne = [
        {"cytat": "Bądź chciwy, gdy inni się boją, i bój się, gdy inni są chciwi.", "autor": "Warren Buffett"},
        {"cytat": "Najlepszą inwestycją, jaką możesz zrobić, jest inwestycja w samego siebie.", "autor": "Warren Buffett"},
        {"cytat": "Inwestowanie powinno być bardziej jak oglądanie schnącej farby lub rosnącej trawy.", "autor": "Paul Samuelson"}
    ]
    return random.choice(awaryjne)

# --- ZARZĄDZANIE DANYMI I PLIKAMI ---
def wczytaj_pozycje():
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                dane = json.load(f)
                if "wolna_gotowka" not in dane:
                    dane["wolna_gotowka"] = 0.0
                return dane
        except:
            pass
    return {"wolna_gotowka": 0.0, "xtb_pozycje": [], "mbank_pozycje": []}

def zapisz_pozycje(dane):
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(dane, f, ensure_ascii=False, indent=4)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    with open(os.path.join(BACKUP_DIR, f"pozycje_{timestamp}.json"), "w", encoding="utf-8") as f:
        json.dump(dane, f, ensure_ascii=False, indent=4)

def wczytaj_historie():
    if os.path.exists(HISTORY_FILE):
        try:
            df = pd.read_csv(HISTORY_FILE)
            if not df.empty:
                df['Data'] = pd.to_datetime(df['Data'])
                return df
        except:
            pass
    return pd.DataFrame(columns=["Data", "Konto", "Wartość Konta", "Dopłata w Miesiącu", "Zysk", "Dokupione Aktywa"])

def zapisz_wpis_historii(data_wpisu, konto, wartosc_konta, doplata, zysk, aktywa):
    df = wczytaj_historie()
    nowy_wpis = pd.DataFrame([{
        "Data": pd.to_datetime(data_wpisu), "Konto": konto, "Wartość Konta": wartosc_konta,
        "Dopłata w Miesiącu": doplata, "Zysk": zysk, "Dokupione Aktywa": aktywa
    }])
    df = pd.concat([df, nowy_wpis], ignore_index=True).sort_values(by="Data")
    df.to_csv(HISTORY_FILE, index=False)
    df.to_csv(os.path.join(BACKUP_DIR, "hist_portfela_backup.csv"), index=False)

def wczytaj_historie_gotowki():
    if os.path.exists(CASH_HISTORY_FILE):
        try:
            df = pd.read_csv(CASH_HISTORY_FILE)
            if not df.empty:
                df['Data'] = pd.to_datetime(df['Data'])
                return df
        except:
            pass
    return pd.DataFrame(columns=["Data", "Kwota", "Bank", "Lokata / Info"])

def zapisz_wpis_gotowki(data_wpisu, kwota, bank, lokata_info):
    df = wczytaj_historie_gotowki()
    nowy_wpis = pd.DataFrame([{"Data": pd.to_datetime(data_wpisu), "Kwota": kwota, "Bank": bank, "Lokata / Info": lokata_info}])
    df = pd.concat([df, nowy_wpis], ignore_index=True).sort_values(by="Data")
    df.to_csv(CASH_HISTORY_FILE, index=False)
    df.to_csv(os.path.join(BACKUP_DIR, "hist_gotowki_backup.csv"), index=False)

# --- POBIERANIE KURSÓW BIEŻĄCYCH I HISTORYCZNYCH ---
@st.cache_data(ttl=1800)
def pobierz_kurs_biezacy(ticker):
    if not ticker: return 0.0
    try:
        return float(yf.Ticker(ticker.strip().upper()).fast_info['lastPrice'])
    except:
        return 0.0

KURS_EUR_PLN = pobierz_kurs_biezacy("EURPLN=X") or 4.30
KURS_USD_PLN = pobierz_kurs_biezacy("USDPLN=X") or 3.90

@st.cache_data(ttl=3600)
def pobierz_historie_cen_zbiorczo(tickers_tuple, start_date):
    hist_dict = {}
    if not tickers_tuple: return hist_dict
    
    tickers_to_fetch = set(tickers_tuple)
    for t in tickers_tuple:
        if ".DE" in t: tickers_to_fetch.add("EURPLN=X")
        if t in ["AAPL", "NVDA", "MSFT", "BTC-USD"]: tickers_to_fetch.add("USDPLN=X")
        
    for t in tickers_to_fetch:
        try:
            tk = yf.Ticker(t)
            df = tk.history(start=start_date)
            if not df.empty:
                df.index = df.index.tz_localize(None).normalize()
                hist_dict[t] = df['Close']
        except:
            pass
    return hist_dict

def cena_w_dniu(hist_dict, ticker, d_date):
    if ticker in hist_dict:
        series = hist_dict[ticker]
        past_dates = series.index[series.index <= pd.Timestamp(d_date)]
        if not past_dates.empty:
            return float(series.loc[past_dates[-1]])
    return None

zapisane_dane = wczytaj_pozycje()

# Styling
st.markdown("""
<style>
    .stApp { background-color: #f7f4ed; color: #2c3e50; font-family: 'Segoe UI', sans-serif; }
    div[data-testid="stRadio"] > div { flex-direction: row; gap: 8px; flex-wrap: wrap; }
    div[data-testid="stRadio"] label {
        background: #ffffff; border: 2px solid #dcd6cd; padding: 6px 14px;
        border-radius: 10px; font-weight: 700 !important; color: #2c3e50 !important; font-size: 0.9rem;
    }
    div[data-testid="stRadio"] label:hover { border-color: #10b981; background-color: #f0fdf4; }
    .welcome-header {
        background: linear-gradient(135deg, #ffffff 0%, #efebe4 100%);
        border-left: 5px solid #10b981; padding: 10px 14px; border-radius: 10px;
        margin-bottom: 8px; border: 1px solid #e5dfd5;
    }
    .quote-box { margin-top: 4px; padding-top: 4px; border-top: 1px dashed #cbd5e1; font-style: italic; color: #475569; font-size: 0.8rem; }
    div[data-testid="stMetric"] { background: #ffffff; border: 1px solid #e2ded5; border-radius: 10px; padding: 10px; }
    .stButton>button { background: #10b981; color: #ffffff !important; font-weight: 700 !important; border-radius: 8px; padding: 8px 18px; border: none; }
</style>
""", unsafe_allow_html=True)

if "page" not in st.session_state:
    st.session_state.page = "🏠 Główna"

st.session_state.page = st.radio(
    "Nawigacja",
    ["🏠 Główna", "📈 Portfel XTB", "🛡️ Emerytura (IKZE)", "💵 Wolna Gotówka", "📝 Dane"],
    index=["🏠 Główna", "📈 Portfel XTB", "🛡️ Emerytura (IKZE)", "💵 Wolna Gotówka", "📝 Dane"].index(st.session_state.page),
    label_visibility="collapsed"
)

# --- OBLICZANIE BIEŻĄCEGO STANU PORTFELA ---
def oblicz_stan_portfela(dane_input):
    def przetworz(pozycje):
        dane_tabeli = []
        wartosc_akt, zysk_razem, koszt_razem = 0.0, 0.0, 0.0
        for item in pozycje:
            t = item.get("ticker", "").strip().upper()
            szt = float(item.get("sztuki", 0))
            
            if "cena" in item:
                sr_cena = float(item["cena"])
            else:
                zainwestowano = float(item.get("zainwestowano", 0))
                sr_cena = zainwestowano / szt if szt > 0 else 0.0

            if t and szt > 0:
                cena_rkt = pobierz_kurs_biezacy(t) or sr_cena
                cena_pln = cena_rkt * KURS_EUR_PLN if ".DE" in t else (cena_rkt * KURS_USD_PLN if t in ["AAPL", "NVDA", "MSFT", "BTC-USD"] else cena_rkt)
                wartosc = szt * cena_pln
                koszt = szt * sr_cena
                zysk = wartosc - koszt
                
                wartosc_akt += wartosc
                koszt_razem += koszt
                zysk_razem += zysk
                
                zysk_pct = (zysk / koszt * 100) if koszt > 0 else 0.0
                status_str = f"🟢 +{zysk:,.2f} PLN (+{zysk_pct:.1f}%)" if zysk >= 0 else f"🔴 {zysk:,.2f} PLN ({zysk_pct:.1f}%)"
                dane_tabeli.append({
                    "Ticker": t, "Typ": item.get("typ", "Akcje"), "Data Zakupu": item.get("data_zakupu", "Bieżąca"),
                    "Sztuki": f"{szt:.4f}".rstrip('0').rstrip('.'), "Śr. Cena": f"{sr_cena:.2f} PLN", 
                    "Akt. Kurs": f"{cena_pln:.2f} PLN", "Wartość": f"{wartosc:,.2f} PLN".replace(",", " "), 
                    "Zysk/Strata": status_str, "Wartość_raw": wartosc, "Zysk_raw": zysk
                })
        return wartosc_akt, zysk_razem, (zysk_razem/koszt_razem*100) if koszt_razem > 0 else 0.0, dane_tabeli

    aktywa_xtb, zysk_xtb, pct_xtb, tab_xtb = przetworz(dane_input.get("xtb_pozycje", []))
    aktywa_emerytura, zysk_emerytura, pct_emerytura, tab_emerytura = przetworz(dane_input.get("mbank_pozycje", []))
    wolna_gotowka = float(dane_input.get("wolna_gotowka", 0.0))
    laczny_majatek = aktywa_xtb + aktywa_emerytura + wolna_gotowka

    return {
        "laczny_majatek": laczny_majatek, "wolna_gotowka": wolna_gotowka,
        "calosc_xtb": aktywa_xtb, "calosc_emerytura": aktywa_emerytura,
        "zysk_xtb": zysk_xtb, "pct_xtb": pct_xtb, "zysk_emerytura": zysk_emerytura, "pct_emerytura": pct_emerytura,
        "tab_xtb": tab_xtb, "tab_emerytura": tab_emerytura
    }

stan = oblicz_stan_portfela(zapisane_dane)

# --- ZAAWANSOWANY WYKRES HISTORYCZNY ---
def pokaz_wykres_i_historie_konta(nazwa_konta, kolor_glowny, pozycje_portfela):
    df_h = wczytaj_historie()
    df_doplaty = df_h[df_h["Konto"] == nazwa_konta].copy() if not df_h.empty else pd.DataFrame()
    
    st.markdown("<br>", unsafe_allow_html=True)
    c_head1, c_head2 = st.columns([2, 1])
    with c_head1: st.subheader(f"📈 Historia Rzeczywista ({nazwa_konta})")
    with c_head2: horyzont = st.selectbox("⏳ Horyzont:", ["Dni", "Tygodnie", "Miesiące"], index=0, key=f"h_{nazwa_konta}")

    daty_aktywnosci = []
    for p in pozycje_portfela:
        if p.get("data_zakupu"): daty_aktywnosci.append(pd.to_datetime(p["data_zakupu"]).date())
    if not df_doplaty.empty:
        daty_aktywnosci.extend(df_doplaty['Data'].dt.date.tolist())
        
    if not daty_aktywnosci:
        st.info("Brak wpisów. Dodaj aktywa z datą zakupu w zakładce '📝 Dane'.")
        return

    min_date = min(daty_aktywnosci)
    today = datetime.now().date()
    
    tickers_tuple = tuple(p.get("ticker", "").strip().upper() for p in pozycje_portfela if p.get("ticker"))
    hist_cen = pobierz_historie_cen_zbiorczo(tickers_tuple, min_date.strftime('%Y-%m-%d'))

    dates_range = pd.date_range(start=min_date, end=today)
    dane_wykresu = []

    for d in dates_range:
        d_date = d.date()
        wartosc_rynkowa_dnia = 0.0
        koszt_historyczny_dnia = 0.0
        
        for p in pozycje_portfela:
            p_date = pd.to_datetime(p.get("data_zakupu", today)).date()
            if p_date <= d_date:
                t = p.get("ticker", "").strip().upper()
                szt = float(p.get("sztuki", 0))
                
                if "cena" in p:
                    sr_cena = float(p["cena"])
                else:
                    sr_cena = float(p.get("zainwestowano", 0)) / szt if szt > 0 else 0.0

                koszt_historyczny_dnia += szt * sr_cena
                
                cena_w_d = cena_w_dniu(hist_cen, t, d_date)
                if cena_w_d is None: 
                    cena_w_d = sr_cena if sr_cena > 0 else pobierz_kurs_biezacy(t)
                
                mnoznik = 1.0
                if ".DE" in t: mnoznik = cena_w_dniu(hist_cen, "EURPLN=X", d_date) or KURS_EUR_PLN
                elif t in ["AAPL", "NVDA", "MSFT", "BTC-USD"]: mnoznik = cena_w_dniu(hist_cen, "USDPLN=X", d_date) or KURS_USD_PLN
                
                wartosc_rynkowa_dnia += szt * cena_w_d * mnoznik

        suma_doplat = 0.0
        if not df_doplaty.empty:
            suma_doplat = df_doplaty[df_doplaty['Data'].dt.date <= d_date]['Dopłata w Miesiącu'].sum()
            
        wplacony_kapital = max(suma_doplat, koszt_historyczny_dnia)
        zysk_pln = wartosc_rynkowa_dnia - wplacony_kapital
        zysk_pct = (zysk_pln / wplacony_kapital * 100) if wplacony_kapital > 0 else 0.0
            
        dane_wykresu.append({
            "Data": d,
            "Wartość Rynkowa (Aktywa)": wartosc_rynkowa_dnia,
            "Wpłacony Kapitał": wplacony_kapital,
            "Zysk PLN": zysk_pln,
            "Zysk %": zysk_pct
        })

    df_wyk = pd.DataFrame(dane_wykresu)
    
    if horyzont == "Miesiące": df_wyk['Okres'] = df_wyk['Data'].dt.strftime('%Y-%m')
    elif horyzont == "Tygodnie": df_wyk['Okres'] = df_wyk['Data'].dt.strftime('%Y-W%U')
    else: df_wyk['Okres'] = df_wyk['Data'].dt.strftime('%Y-%m-%d')

    df_grouped = df_wyk.groupby('Okres').agg({
        'Wartość Rynkowa (Aktywa)': 'last', 
        'Wpłacony Kapitał': 'last',
        'Zysk PLN': 'last',
        'Zysk %': 'last',
        'Data': 'last'
    }).reset_index()

    fig = make_subplots(specs=[[{"secondary_y": True}]])

    fig.add_trace(go.Bar(
        x=df_grouped['Okres'], y=df_grouped['Wpłacony Kapitał'],
        name='Zainwestowany Kapitał', marker_color='#f59e0b', opacity=0.4,
        hovertemplate="Okres: %{x}<br>Koszt zakupu: %{y:,.2f} PLN<extra></extra>"
    ), secondary_y=False)

    fig.add_trace(go.Scatter(
        x=df_grouped['Okres'], y=df_grouped['Wartość Rynkowa (Aktywa)'],
        name='Wartość Rynkowa Aktywów', mode='lines',
        line=dict(color=kolor_glowny, width=3, shape='spline'),
        customdata=df_grouped[['Zysk PLN', 'Zysk %']],
        hovertemplate="<b>Okres: %{x}</b><br>Wartość rynkowa: %{y:,.2f} PLN<br><b>Zysk/Strata: %{customdata[0]:,.2f} PLN (%{customdata[1]:.2f}%)</b><extra></extra>"
    ), secondary_y=True)

    fig.update_layout(
        height=350, paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        legend=dict(orientation="h", y=1.15), margin=dict(l=10, r=10, t=10, b=10)
    )
    fig.update_yaxes(title_text="", secondary_y=False, showgrid=False)
    fig.update_yaxes(title_text="PLN (Wartość Aktywów)", secondary_y=True, showgrid=True)

    st.plotly_chart(fig, use_container_width=True)

# ----------------------------------------------------
# STRONY APLIKACJI
# ----------------------------------------------------
if st.session_state.page == "🏠 Główna":
    cytat_z_internetu = pobierz_cytat_z_neta()
    st.markdown(f"""
    <div class="welcome-header">
        <h3 style="margin:0; color: #1e293b;">Cześć Karol! 👋</h3>
        <div class="quote-box">💡 <i>„{cytat_z_internetu['cytat']}”</i> — <b>{cytat_z_internetu['autor']}</b></div>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("<h5 style='margin-bottom:0; margin-top:0;'>📊 Alokacja Majątku</h5>", unsafe_allow_html=True)
    
    df_main_pie = pd.DataFrame([
        {"Składnik": "XTB", "Wartość": stan["calosc_xtb"]},
        {"Składnik": "Emerytura (IKZE)", "Wartość": stan["calosc_emerytura"]},
        {"Składnik": "Wolna Gotówka", "Wartość": stan["wolna_gotowka"]}
    ])
    
    fig_main_pie = px.pie(df_main_pie, values="Wartość", names="Składnik", hole=0.45,
                          color="Składnik", color_discrete_map={"XTB": "#10b981", "Emerytura (IKZE)": "#3b82f6", "Wolna Gotówka": "#f59e0b"})
    fig_main_pie.update_layout(height=230, paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", margin=dict(l=10, r=10, t=5, b=5))
    st.plotly_chart(fig_main_pie, use_container_width=True)

    c_main, c_xtb, c_emerytura, c_cash = st.columns(4)
    with c_main: st.metric("ŁĄCZNY MAJĄTEK", f"{stan['laczny_majatek']:,.2f} PLN".replace(",", " "))
    with c_xtb: st.metric("📈 XTB", f"{stan['calosc_xtb']:,.2f} PLN".replace(",", " "), delta=f"{stan['pct_xtb']:.1f}%")
    with c_emerytura: st.metric("🛡️ IKZE", f"{stan['calosc_emerytura']:,.2f} PLN".replace(",", " "), delta=f"{stan['pct_emerytura']:.1f}%")
    with c_cash: st.metric("💵 GOTÓWKA", f"{stan['wolna_gotowka']:,.2f} PLN".replace(",", " "))

elif st.session_state.page == "📈 Portfel XTB":
    st.title("📈 PORTFEL XTB")
    c1, c2 = st.columns(2)
    c1.metric("WARTOŚĆ XTB", f"{stan['calosc_xtb']:,.2f} PLN".replace(",", " "))
    c2.metric("ZYSK / STRATA", f"{stan['zysk_xtb']:,.2f} PLN".replace(",", " "), delta=f"{stan['pct_xtb']:.1f}%")
    
    col_info, col_chart_mini = st.columns([2, 1])
    with col_info:
        st.subheader("📋 Aktywa")
        if stan["tab_xtb"]:
            st.dataframe(pd.DataFrame(stan["tab_xtb"]).drop(columns=["Wartość_raw", "Zysk_raw"]), use_container_width=True, hide_index=True)
        else: st.info("Brak wpisanych pozycji.")
    with col_chart_mini:
        st.subheader("Struktura")
        if stan["tab_xtb"]:
            fig_xtb = px.pie(pd.DataFrame(stan["tab_xtb"]), values="Wartość_raw", names="Ticker", hole=0.4)
            fig_xtb.update_layout(height=220, paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", margin=dict(l=5, r=5, t=5, b=5))
            st.plotly_chart(fig_xtb, use_container_width=True)

    pokaz_wykres_i_historie_konta("XTB", "#10b981", zapisane_dane.get("xtb_pozycje", []))

elif st.session_state.page == "🛡️ Emerytura (IKZE)":
    st.title("🛡️ PORTFEL EMERYTURA (IKZE)")
    c1, c2 = st.columns(2)
    c1.metric("WARTOŚĆ IKZE", f"{stan['calosc_emerytura']:,.2f} PLN".replace(",", " "))
    c2.metric("ZYSK / STRATA", f"{stan['zysk_emerytura']:,.2f} PLN".replace(",", " "), delta=f"{stan['pct_emerytura']:.1f}%")
    
    col_info_em, col_chart_mini_em = st.columns([2, 1])
    with col_info_em:
        st.subheader("📋 Aktywa")
        if stan["tab_emerytura"]:
            st.dataframe(pd.DataFrame(stan["tab_emerytura"]).drop(columns=["Wartość_raw", "Zysk_raw"]), use_container_width=True, hide_index=True)
        else: st.info("Brak wpisanych pozycji.")
    with col_chart_mini_em:
        st.subheader("Struktura")
        if stan["tab_emerytura"]:
            fig_em = px.pie(pd.DataFrame(stan["tab_emerytura"]), values="Wartość_raw", names="Ticker", hole=0.4)
            fig_em.update_layout(height=220, paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", margin=dict(l=5, r=5, t=5, b=5))
            st.plotly_chart(fig_em, use_container_width=True)

    pokaz_wykres_i_historie_konta("Emerytura", "#3b82f6", zapisane_dane.get("mbank_pozycje", []))

elif st.session_state.page == "💵 Wolna Gotówka":
    st.title("💵 ANALIZA WOLNEJ GOTÓWKI")
    c1, c2 = st.columns(2)
    c1.metric("AKTUALNA WOLNA GOTÓWKA", f"{stan['wolna_gotowka']:,.2f} PLN".replace(",", " "))
    df_gotowka_h = wczytaj_historie_gotowki()
    c2.metric("ZAPISANE LOKATY", f"{len(df_gotowka_h)}")

    st.markdown("<br>", unsafe_allow_html=True)
    st.subheader("📈 Ulokowania w Bankach")
    if not df_gotowka_h.empty:
        fig_cash = px.bar(df_gotowka_h, x="Data", y="Kwota", color="Bank", text="Lokata / Info", color_discrete_sequence=px.colors.qualitative.Safe)
        fig_cash.update_layout(height=320, paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", xaxis=dict(title=""), margin=dict(l=10, r=10, t=10, b=10))
        st.plotly_chart(fig_cash, use_container_width=True)
        st.dataframe(df_gotowka_h.sort_values(by="Data", ascending=False), use_container_width=True, hide_index=True)
    else: st.info("Brak wpisów.")

elif st.session_state.page == "📝 Dane":
    st.title("📝 ZARZĄDZANIE DANYMI")
    
    tab1, tab2, tab3, tab4 = st.tabs(["💼 Portfele Aktywów", "💵 Wolna Gotówka & Lokaty", "➕ Dopłaty", "💾 Kopia Zapasowa"])
    
    with tab1:
        col_x, col_m = st.columns(2)
        nowe_dane = {"wolna_gotowka": zapisane_dane.get("wolna_gotowka", 0.0), "xtb_pozycje": [], "mbank_pozycje": []}
        
        xtb_zap = zapisane_dane.get("xtb_pozycje", [])
        mbank_zap = zapisane_dane.get("mbank_pozycje", [])
        
        # Dynamiczne liczenie wierszy
        if "x_rows" not in st.session_state: st.session_state.x_rows = max(3, len(xtb_zap) + 1)
        if "m_rows" not in st.session_state: st.session_state.m_rows = max(3, len(mbank_zap) + 1)
        
        with col_x:
            st.subheader("📈 XTB")
            st.info("Wskazówka: Zostaw puste lub wpisz '0' w Sztukach, by usunąć akcję.")
            for i in range(st.session_state.x_rows):
                prev = xtb_zap[i] if i < len(xtb_zap) else {"ticker": "", "sztuki": 0.0, "cena": 0.0, "typ": "Akcje", "data_zakupu": str(datetime.now().date())}
                c1, c2, c3, c4, c5 = st.columns([1.5, 1, 1, 1.2, 1.5])
                
                t = c1.text_input("Ticker", value=prev["ticker"], key=f"x_t_{i}", label_visibility="collapsed" if i>0 else "visible").strip().upper()
                s = c2.number_input("Sztuki", min_value=0.0, value=float(prev.get("sztuki", 0)), key=f"x_s_{i}", label_visibility="collapsed" if i>0 else "visible")
                
                old_c = float(prev["cena"]) if "cena" in prev else (float(prev.get("zainwestowano", 0)) / float(prev["sztuki"]) if float(prev.get("sztuki", 0)) > 0 else 0.0)
                p = c3.number_input("Śr. Cena", min_value=0.0, value=old_c, key=f"x_p_{i}", label_visibility="collapsed" if i>0 else "visible")
                
                typ = c4.selectbox("Typ", ["Akcje", "ETF", "Krypto"], index=["Akcje", "ETF", "Krypto"].index(prev.get("typ", "Akcje")) if prev.get("typ", "Akcje") in ["Akcje", "ETF", "Krypto"] else 0, key=f"x_c_{i}", label_visibility="collapsed" if i>0 else "visible")
                
                try: dz_val = pd.to_datetime(prev.get("data_zakupu", datetime.now())).date()
                except: dz_val = datetime.now().date()
                dz = c5.date_input("Data zak.", value=dz_val, key=f"x_d_{i}", label_visibility="collapsed" if i>0 else "visible")
                
                # Usuwanie pustych pozycji przy zapisie
                if t and s > 0:
                    nowe_dane["xtb_pozycje"].append({"ticker": t, "sztuki": s, "cena": p, "typ": typ, "data_zakupu": str(dz)})
                    
            if st.button("➕ Dodaj kolejny wiersz XTB"):
                st.session_state.x_rows += 1
                st.rerun()

        with col_m:
            st.subheader("🛡️ IKZE")
            st.info("Wskazówka: Zostaw puste lub wpisz '0' w Sztukach, by usunąć akcję.")
            for i in range(st.session_state.m_rows):
                prev = mbank_zap[i] if i < len(mbank_zap) else {"ticker": "", "sztuki": 0.0, "cena": 0.0, "typ": "ETF", "data_zakupu": str(datetime.now().date())}
                c1, c2, c3, c4, c5 = st.columns([1.5, 1, 1, 1.2, 1.5])
                
                t = c1.text_input("Ticker", value=prev["ticker"], key=f"m_t_{i}", label_visibility="collapsed" if i>0 else "visible").strip().upper()
                s = c2.number_input("Sztuki", min_value=0.0, value=float(prev.get("sztuki", 0)), key=f"m_s_{i}", label_visibility="collapsed" if i>0 else "visible")
                
                old_c = float(prev["cena"]) if "cena" in prev else (float(prev.get("zainwestowano", 0)) / float(prev["sztuki"]) if float(prev.get("sztuki", 0)) > 0 else 0.0)
                p = c3.number_input("Śr. Cena", min_value=0.0, value=old_c, key=f"m_p_{i}", label_visibility="collapsed" if i>0 else "visible")
                
                typ = c4.selectbox("Typ", ["Akcje", "ETF"], index=["Akcje", "ETF"].index(prev.get("typ", "ETF")) if prev.get("typ", "ETF") in ["Akcje", "ETF"] else 0, key=f"m_c_{i}", label_visibility="collapsed" if i>0 else "visible")
                
                try: dz_val = pd.to_datetime(prev.get("data_zakupu", datetime.now())).date()
                except: dz_val = datetime.now().date()
                dz = c5.date_input("Data zak.", value=dz_val, key=f"m_d_{i}", label_visibility="collapsed" if i>0 else "visible")
                
                if t and s > 0:
                    nowe_dane["mbank_pozycje"].append({"ticker": t, "sztuki": s, "cena": p, "typ": typ, "data_zakupu": str(dz)})
                    
            if st.button("➕ Dodaj kolejny wiersz IKZE"):
                st.session_state.m_rows += 1
                st.rerun()
                
        if st.button("💾 ZAPISZ PORTFELE", use_container_width=True):
            zapisz_pozycje(nowe_dane)
            st.success("Zapisano pozycje portfeli!")
            st.rerun()

    with tab2:
        c_g1, c_g2, c_g3, c_g4 = st.columns(4)
        data_g = c_g1.date_input("Data:", value=datetime.now())
        kwota_g = c_g2.number_input("Kwota (PLN):", value=float(zapisane_dane.get("wolna_gotowka", 0.0)))
        bank_g = c_g3.text_input("Bank:")
        lokata_g = c_g4.text_input("Lokata:")
        if st.button("💾 ZAPISZ GOTÓWKĘ"):
            zapisane_dane["wolna_gotowka"] = kwota_g
            zapisz_pozycje(zapisane_dane)
            zapisz_wpis_gotowki(data_g, kwota_g, bank_g, lokata_g)
            st.success("Zapisano gotówkę!")
            st.rerun()

    with tab3:
        st.info("Dodaj dopłatę (zasilenie konta gotówką z zewnątrz).")
        c_d1, c_d2, c_d3, c_d4 = st.columns(4)
        data_wpisu = c_d1.date_input("Data dopłaty:", value=datetime.now())
        konto = c_d2.selectbox("Konto:", ["XTB", "Emerytura"])
        doplata = c_d3.number_input("Kwota Dopłaty:", min_value=0.0)
        aktywa = c_d4.text_input("Uwagi:")
        if st.button("📈 ZAPISZ DOPŁATĘ"):
            zapisz_wpis_historii(data_wpisu, konto, 0, doplata, 0, aktywa)
            st.success("Zapisano dopłatę!")
            st.rerun()

    with tab4:
        if st.button("📁 Utwórz pełną kopię na dysku"):
            ts = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
            with open(CONFIG_FILE, "r") as f: json.dump(json.load(f), open(os.path.join(USER_BACKUP_DIR, f"backup_{ts}.json"), "w"))
            st.success(f"Utworzono kopię w {USER_BACKUP_DIR}!")
        
        c1, c2 = st.columns(2)
        if os.path.exists(CONFIG_FILE): c1.download_button("Pobierz .JSON", open(CONFIG_FILE, "r").read(), "pozycje.json")
        if os.path.exists(HISTORY_FILE): c2.download_button("Pobierz Historie .CSV", open(HISTORY_FILE, "r").read(), "historia.csv")
