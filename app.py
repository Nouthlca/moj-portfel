import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
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

# Tworzenie folderów, jeśli nie istnieją
for folder in [BACKUP_DIR, USER_BACKUP_DIR]:
    if not os.path.exists(folder):
        os.makedirs(folder)

# Pobieranie losowego cytatu z internetu (z zapasową listą awaryjną)
@st.cache_data(ttl=3600)
def pobierz_cytat_z_neta():
    try:
        # Próba pobrania cytatu finansowego/motywacyjnego z darmowego API
        response = requests.get("https://api.quotable.io/random?tags=inspirational|business|wisdom", timeout=3)
        if response.status_code == 200:
            data = response.json()
            return {"cytat": data.get("content"), "autor": data.get("author")}
    except:
        pass
    
    # Awaryjna lista, gdyby serwer nie miał dostępu do internetu
    awaryjne = [
        {"cytat": "Bądź chciwy, gdy inni się boją, i bój się, gdy inni są chciwi.", "autor": "Warren Buffett"},
        {"cytat": "Najlepszą inwestycją, jaką możesz zrobić, jest inwestycja w samego siebie.", "autor": "Warren Buffett"},
        {"cytat": "Inwestowanie powinno być bardziej jak oglądanie schnącej farby lub rosnącej trawy.", "autor": "Paul Samuelson"},
        {"cytat": "Wielkie pieniądze nie znajdują się w kupowaniu i sprzedawaniu, ale w czekaniu.", "autor": "Charlie Munger"}
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
    
    return {
        "wolna_gotowka": 0.0,
        "xtb_pozycje": [],
        "mbank_pozycje": []
    }

def zapisz_pozycje(dane):
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(dane, f, ensure_ascii=False, indent=4)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_file = os.path.join(BACKUP_DIR, f"pozycje_portfela_{timestamp}.json")
    with open(backup_file, "w", encoding="utf-8") as f:
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
        "Data": pd.to_datetime(data_wpisu),
        "Konto": konto,
        "Wartość Konta": wartosc_konta,
        "Dopłata w Miesiącu": doplata,
        "Zysk": zysk,
        "Dokupione Aktywa": aktywa
    }])
    df = pd.concat([df, nowy_wpis], ignore_index=True)
    df = df.sort_values(by="Data")
    df.to_csv(HISTORY_FILE, index=False)
    df.to_csv(os.path.join(BACKUP_DIR, "historia_portfela_backup.csv"), index=False)

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
    nowy_wpis = pd.DataFrame([{
        "Data": pd.to_datetime(data_wpisu),
        "Kwota": kwota,
        "Bank": bank,
        "Lokata / Info": lokata_info
    }])
    df = pd.concat([df, nowy_wpis], ignore_index=True)
    df = df.sort_values(by="Data")
    df.to_csv(CASH_HISTORY_FILE, index=False)
    df.to_csv(os.path.join(BACKUP_DIR, "historia_gotowki_backup.csv"), index=False)

# Pobieranie kursów (bieżących lub historycznych na dany dzień)
@st.cache_data(ttl=1800)
def pobierz_kurs(ticker, data_zakupu=None):
    if not ticker:
        return 0.0
    ticker_clean = ticker.strip().upper()
    try:
        t = yf.Ticker(ticker_clean)
        if data_zakupu:
            # Pobieranie historycznego kursu z konkretnego dnia zakupu
            start_d = pd.to_datetime(data_zakupu)
            end_d = start_d + timedelta(days=5) # Szukamy w oknie kilku dni w razie weekendu
            hist = t.history(start=start_d.strftime('%Y-%m-%d'), end=end_d.strftime('%Y-%m-%d'))
            if not hist.empty:
                return float(hist['Close'].iloc[0])
        
        # Jeśli brak daty lub historii, zwracamy aktualną cenę
        return float(t.fast_info['lastPrice'])
    except:
        return 0.0

KURS_EUR_PLN = pobierz_kurs("EURPLN=X") or 4.30
KURS_USD_PLN = pobierz_kurs("USDPLN=X") or 3.90

zapisane_dane = wczytaj_pozycje()

GLOBALNE_WYDARZENIA = {
    "default": "🌐 Otoczenie rynkowe: Banki centralne utrzymują ostrożną politykę stóp procentowych, co sprzyja dywersyfikacji w bezpieczne aktywa."
}

def pobierz_komentarz_rynkowy(data_str):
    klucz = data_str[:7]
    return GLOBALNE_WYDARZENIA.get(klucz, GLOBALNE_WYDARZENIA["default"])

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
    .quote-box {
        margin-top: 4px; padding-top: 4px;
        border-top: 1px dashed #cbd5e1; font-style: italic; color: #475569; font-size: 0.8rem;
    }
    div[data-testid="stMetric"] {
        background: #ffffff; border: 1px solid #e2ded5; border-radius: 10px; padding: 10px;
    }
    .stButton>button {
        background: #10b981; color: #ffffff !important; font-weight: 700 !important;
        border-radius: 8px; padding: 8px 18px; border: none;
    }
    .macro-news-box {
        background: #fffbeb; border-left: 4px solid #f59e0b; padding: 8px 12px; border-radius: 8px;
        font-size: 0.85rem; color: #92400e; margin-bottom: 8px;
    }
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

# Obliczenia portfelowe z uwzględnieniem dat historycznych zakupu
def oblicz_stan_portfela(dane_input):
    def przetworz(pozycje):
        dane_tabeli = []
        wartosc_akt, zysk_razem, koszt_razem = 0.0, 0.0, 0.0
        temp_items = []
        for item in pozycje:
            t = item.get("ticker", "").strip().upper()
            szt, sr_cena = float(item.get("sztuki", 0)), float(item.get("cena", 0))
            typ = item.get("typ", "Akcje")
            data_z = item.get("data_zakupu", None)
            
            if t and szt > 0:
                # Pobieramy bieżącą cenę rynkową oraz historyczną na dzień zakupu (jeśli podano)
                cena_rkt = pobierz_kurs(t)
                cena_hist_zakupu = pobierz_kurs(t, data_z) if data_z else sr_cena
                
                cena_pln = cena_rkt * KURS_EUR_PLN if ".DE" in t else (cena_rkt * KURS_USD_PLN if t in ["AAPL", "NVDA", "MSFT", "BTC-USD"] else cena_rkt)
                wartosc = szt * cena_pln
                koszt = szt * sr_cena
                zysk = wartosc - koszt
                
                wartosc_akt += wartosc
                koszt_razem += koszt
                zysk_razem += zysk
                temp_items.append({"t": t, "szt": szt, "sr_cena": sr_cena, "cena_pln": cena_pln, "wartosc": wartosc, "koszt": koszt, "zysk": zysk, "typ": typ, "data_zakupu": data_z})
        
        for x in temp_items:
            zysk_pct = (x["zysk"] / x["koszt"] * 100) if x["koszt"] > 0 else 0.0
            status_str = f"🟢 +{x['zysk']:,.2f} PLN (+{zysk_pct:.1f}%)" if x['zysk'] >= 0 else f"🔴 {x['zysk']:,.2f} PLN ({zysk_pct:.1f}%)"
            dane_tabeli.append({
                "Ticker": x["t"], "Typ": x["typ"], "Data Zakupu": x["data_zakupu"] or "Bieżąca", "Sztuki": f"{x['szt']:.4f}".rstrip('0').rstrip('.'),
                "Śr. Cena": f"{x['sr_cena']:.2f} PLN", "Akt. Kurs": f"{x['cena_pln']:.2f} PLN",
                "Wartość": f"{x['wartosc']:,.2f} PLN".replace(",", " "), "Zysk/Strata": status_str,
                "Wartość_raw": x["wartosc"], "Zysk_raw": x["zysk"]
            })
        pct_konta = (zysk_razem / koszt_razem * 100) if koszt_razem > 0 else 0.0
        return wartosc_akt, zysk_razem, pct_konta, dane_tabeli

    aktywa_xtb, zysk_xtb, pct_xtb, tab_xtb = przetworz(dane_input.get("xtb_pozycje", []))
    aktywa_emerytura, zysk_emerytura, pct_emerytura, tab_emerytura = przetworz(dane_input.get("mbank_pozycje", []))
    wolna_gotowka = float(dane_input.get("wolna_gotowka", 0.0))
    
    calosc_xtb = aktywa_xtb
    calosc_emerytura = aktywa_emerytura
    laczny_majatek = calosc_xtb + calosc_emerytura + wolna_gotowka

    return {
        "laczny_majatek": laczny_majatek,
        "laczny_zysk": zysk_xtb + zysk_emerytura,
        "wolna_gotowka": wolna_gotowka,
        "calosc_xtb": calosc_xtb, "calosc_emerytura": calosc_emerytura,
        "aktywa_xtb": aktywa_xtb, "aktywa_emerytura": aktywa_emerytura,
        "zysk_xtb": zysk_xtb, "pct_xtb": pct_xtb,
        "zysk_emerytura": zysk_emerytura, "pct_emerytura": pct_emerytura,
        "tab_xtb": tab_xtb, "tab_emerytura": tab_emerytura
    }

stan = oblicz_stan_portfela(zapisane_dane)

def pokaz_wykres_i_historie_konta(nazwa_konta, kolor_glowny):
    df_h = wczytaj_historie()
    if not df_h.empty and "Konto" in df_h.columns:
        df_konta = df_h[df_h["Konto"] == nazwa_konta].copy()
    else:
        df_konta = pd.DataFrame()
    
    st.markdown("<br>", unsafe_allow_html=True)
    c_head1, c_head2 = st.columns([2, 1])
    with c_head1:
        st.subheader(f"📈 Historia i Wzrost ({nazwa_konta})")
    with c_head2:
        horyzont = st.selectbox("⏳ Horyzont:", ["Dni", "Tygodnie", "Miesiące", "Lata"], index=2, key=f"horiz_{nazwa_konta}")

    if not df_konta.empty:
        if horyzont == "Lata":
            df_konta['Okres'] = df_konta['Data'].dt.strftime('%Y')
        elif horyzont == "Miesiące":
            df_konta['Okres'] = df_konta['Data'].dt.strftime('%Y-%m')
        elif horyzont == "Tygodnie":
            df_konta['Okres'] = df_konta['Data'].dt.strftime('%Y-W%U')
        else:
            df_konta['Okres'] = df_konta['Data'].dt.strftime('%Y-%m-%d')

        df_grouped = df_konta.groupby('Okres').agg({
            'Wartość Konta': 'last', 'Dopłata w Miesiącu': 'sum', 'Zysk': 'last',
            'Dokupione Aktywa': lambda x: ", ".join(set([str(item) for item in x if pd.notnull(item)]))
        }).reset_index()

        df_grouped['Skumulowane Dopłaty'] = df_grouped['Dopłata w Miesiącu'].cumsum()
        df_grouped['Suma'] = df_grouped['Skumulowane Dopłaty'] + df_grouped['Zysk']
        bar_colors = ['#f59e0b' if val >= 0 else '#ef4444' for val in df_grouped['Suma']]

        ostatni_okres = df_grouped['Okres'].iloc[-1] if not df_grouped.empty else datetime.now().strftime('%Y-%m')
        komentarz_swiatowy = pobierz_komentarz_rynkowy(str(ostatni_okres))
        st.markdown(f'<div class="macro-news-box"><b>🌍 Kontekst rynkowy / Informacje ze świata:</b> {komentarz_swiatowy}</div>', unsafe_allow_html=True)

        fig = go.Figure()
        fig.add_trace(go.Bar(
            x=df_grouped['Okres'], y=df_grouped['Suma'], name='Skumulowane (Dopłaty + Zysk)',
            marker_color=bar_colors, opacity=0.75, text=df_grouped['Dokupione Aktywa'],
            hovertemplate="<b>Okres: %{x}</b><br>Suma: %{y:,.2f} PLN<br>Aktywa: %{text}<extra></extra>"
        ))
        fig.add_trace(go.Scatter(
            x=df_grouped['Okres'], y=df_grouped['Wartość Konta'], name='Wartość Konta',
            mode='lines+markers', line=dict(color=kolor_glowny, width=3), marker=dict(size=7)
        ))

        fig.update_layout(
            height=280, paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
            xaxis=dict(title=""), yaxis=dict(title="PLN", showgrid=True),
            legend=dict(orientation="h", y=1.2), margin=dict(l=10, r=10, t=10, b=10)
        )
        st.plotly_chart(fig, use_container_width=True)
        
        with st.expander(f"📜 Rejestr transakcji: {nazwa_konta}"):
            st.dataframe(df_konta.sort_values(by="Data", ascending=False)[["Data", "Wartość Konta", "Dopłata w Miesiącu", "Zysk", "Dokupione Aktywa"]], use_container_width=True, hide_index=True)
    else:
        st.info("Brak historii wpisów. Dodaj pierwszy wpis w zakładce '📝 Dane' -> 'Dopłaty do Historii'.")

# ----------------------------------------------------
# 1. STRONA GŁÓWNA
# ----------------------------------------------------
if st.session_state.page == "🏠 Główna":
    cytat_z_internetu = pobierz_cytat_z_neta()
    
    st.markdown(f"""
    <div class="welcome-header">
        <h3 style="margin:0; color: #1e293b;">Cześć Karol! 👋</h3>
        <div class="quote-box">💡 <i>„{cytat_z_internetu['cytat']}”</i> — <b>{cytat_z_internetu['autor']}</b></div>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("<h4 style='margin-bottom:0; margin-top:0;'>📊 Alokacja Majątku</h4>", unsafe_allow_html=True)
    
    df_main_pie = pd.DataFrame([
        {"Składnik": "XTB", "Wartość": stan["aktywa_xtb"]},
        {"Składnik": "Emerytura (IKZE)", "Wartość": stan["aktywa_emerytura"]},
        {"Składnik": "Wolna Gotówka", "Wartość": stan["wolna_gotowka"]}
    ])
    
    fig_main_pie = px.pie(df_main_pie, values="Wartość", names="Składnik", hole=0.45,
                          color="Składnik",
                          color_discrete_map={"XTB": "#10b981", "Emerytura (IKZE)": "#3b82f6", "Wolna Gotówka": "#f59e0b"})
    fig_main_pie.update_layout(height=210, paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", margin=dict(l=10, r=10, t=5, b=5))
    st.plotly_chart(fig_main_pie, use_container_width=True)

    c_main, c_xtb, c_emerytura, c_cash = st.columns(4)
    with c_main:
        st.metric("ŁĄCZNY MAJÁTEK", f"{stan['laczny_majatek']:,.2f} PLN".replace(",", " "))
    with c_xtb:
        st.metric("📈 XTB", f"{stan['calosc_xtb']:,.2f} PLN".replace(",", " "), delta=f"{stan['pct_xtb']:.1f}%")
    with c_emerytura:
        st.metric("🛡️ IKZE", f"{stan['calosc_emerytura']:,.2f} PLN".replace(",", " "), delta=f"{stan['pct_emerytura']:.1f}%")
    with c_cash:
        st.metric("💵 GOTÓWKA", f"{stan['wolna_gotowka']:,.2f} PLN".replace(",", " "))

# ----------------------------------------------------
# 2. PORTFEL XTB
# ----------------------------------------------------
elif st.session_state.page == "📈 Portfel XTB":
    st.title("📈 PORTFEL XTB")
    c1, c2 = st.columns(2)
    c1.metric("WARTOŚĆ XTB", f"{stan['calosc_xtb']:,.2f} PLN".replace(",", " "))
    c2.metric("ZYSK / STRATA", f"{stan['zysk_xtb']:,.2f} PLN".replace(",", " "), delta=f"{stan['pct_xtb']:.1f}%")
    
    col_info, col_chart_mini = st.columns([2, 1])
    with col_info:
        st.subheader("📋 Aktywa")
        if stan["tab_xtb"]:
            df_tab_xtb = pd.DataFrame(stan["tab_xtb"])
            st.dataframe(df_tab_xtb.drop(columns=["Wartość_raw", "Zysk_raw"]), use_container_width=True, hide_index=True)
        else:
            st.info("Brak wpisanych pozycji w XTB. Przejdź do zakładki '📝 Dane', aby je dodać.")
    with col_chart_mini:
        st.subheader("Struktura")
        if stan["tab_xtb"]:
            fig_xtb = px.pie(pd.DataFrame(stan["tab_xtb"]), values="Wartość_raw", names="Ticker", hole=0.4)
            fig_xtb.update_layout(height=220, paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", margin=dict(l=5, r=5, t=5, b=5))
            st.plotly_chart(fig_xtb, use_container_width=True)

    pokaz_wykres_i_historie_konta("XTB", "#10b981")

# ----------------------------------------------------
# 3. PORTFEL EMERYTURA (IKZE)
# ----------------------------------------------------
elif st.session_state.page == "🛡️ Emerytura (IKZE)":
    st.title("🛡️ PORTFEL EMERYTURA (IKZE)")
    c1, c2 = st.columns(2)
    c1.metric("WARTOŚĆ IKZE", f"{stan['calosc_emerytura']:,.2f} PLN".replace(",", " "))
    c2.metric("ZYSK / STRATA", f"{stan['zysk_emerytura']:,.2f} PLN".replace(",", " "), delta=f"{stan['pct_emerytura']:.1f}%")
    
    col_info_em, col_chart_mini_em = st.columns([2, 1])
    with col_info_em:
        st.subheader("📋 Aktywa")
        if stan["tab_emerytura"]:
            df_tab_em = pd.DataFrame(stan["tab_emerytura"])
            st.dataframe(df_tab_em.drop(columns=["Wartość_raw", "Zysk_raw"]), use_container_width=True, hide_index=True)
        else:
            st.info("Brak wpisanych pozycji w IKZE. Przejdź do zakładki '📝 Dane', aby je dodać.")
    with col_chart_mini_em:
        st.subheader("Struktura")
        if stan["tab_emerytura"]:
            fig_em = px.pie(pd.DataFrame(stan["tab_emerytura"]), values="Wartość_raw", names="Ticker", hole=0.4)
            fig_em.update_layout(height=220, paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", margin=dict(l=5, r=5, t=5, b=5))
            st.plotly_chart(fig_em, use_container_width=True)

    pokaz_wykres_i_historie_konta("Emerytura", "#3b82f6")

# ----------------------------------------------------
# 4. WOLNA GOTÓWKA
# ----------------------------------------------------
elif st.session_state.page == "💵 Wolna Gotówka":
    st.title("💵 ANALIZA WOLNEJ GOTÓWKI I LOKAT")
    
    c1, c2 = st.columns(2)
    c1.metric("AKTUALNA WOLNA GOTÓWKA", f"{stan['wolna_gotowka']:,.2f} PLN".replace(",", " "))
    
    df_gotowka_h = wczytaj_historie_gotowki()
    c2.metric("LICZBA ZAPISANYCH LOKAT / MIEJSC", f"{len(df_gotowka_h)}")

    st.markdown("<br>", unsafe_allow_html=True)
    st.subheader("📈 Trend Wolnych Środków i Ulokowania w Bankach")
    
    if not df_gotowka_h.empty:
        fig_cash = px.bar(
            df_gotowka_h, x="Data", y="Kwota", color="Bank",
            text="Lokata / Info", hover_data=["Bank", "Lokata / Info"],
            color_discrete_sequence=px.colors.qualitative.Safe
        )
        fig_cash.update_layout(
            height=320, paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
            xaxis=dict(title=""), yaxis=dict(title="PLN (Kwota)", showgrid=True),
            margin=dict(l=10, r=10, t=10, b=10)
        )
        st.plotly_chart(fig_cash, use_container_width=True)

        st.markdown("### 🏛️ Rejestr Banków i Lokat")
        st.dataframe(df_gotowka_h.sort_values(by="Data", ascending=False), use_container_width=True, hide_index=True)
    else:
        st.info("Brak wpisów w historii gotówki. Dodaj wpis w zakładce '📝 Dane'.")

# ----------------------------------------------------
# 5. DANE (Edycja i wprowadzanie)
# ----------------------------------------------------
elif st.session_state.page == "📝 Dane":
    st.title("📝 ZARZĄDZANIE DANYMI I WPROWADZANIE")
    
    tab1, tab2, tab3, tab4 = st.tabs(["💼 Portfele Aktywów", "💵 Wolna Gotówka & Lokaty", "➕ Dopłaty do Historii", "💾 Kopia Zapasowa"])
    
    kategorie_opcje = ["Akcje", "ETF", "Obligacje", "Krypto", "Inne"]
    
    with tab1:
        col_x, col_m = st.columns(2)
        nowe_dane = {"wolna_gotowka": zapisane_dane.get("wolna_gotowka", 0.0), "xtb_pozycje": [], "mbank_pozycje": []}
        
        with col_x:
            st.subheader("📈 XTB - Pozycje (Możesz podać datę zakupu)")
            for i in range(5):
                st.caption(f"Pozycja XTB #{i+1}")
                prev = zapisane_dane["xtb_pozycje"][i] if i < len(zapisane_dane["xtb_pozycje"]) else {"ticker": "", "sztuki": 0.0, "cena": 0.0, "typ": "Akcje", "data_zakupu": str(datetime.now().date())}
                c1, c2, c3, c4, c5 = st.columns(5)
                t = c1.text_input("Ticker", value=prev["ticker"], key=f"x_t_{i}").strip().upper()
                s = c2.number_input("Sztuki", min_value=0.0, value=float(prev["sztuki"]), key=f"x_s_{i}")
                p = c3.number_input("Śr. cena", min_value=0.0, value=float(prev["cena"]), key=f"x_p_{i}")
                typ = c4.selectbox("Typ", kategorie_opcje, index=kategorie_opcje.index(prev.get("typ", "Akcje")), key=f"x_cat_{i}")
                
                # Dodatkowe pole na datę zakupu historycznego
                d_zak_val = pd.to_datetime(prev.get("data_zakupu", datetime.now())).date()
                d_zak = c5.date_input("Data zakupu", value=d_zak_val, key=f"x_dz_{i}")
                
                nowe_dane["xtb_pozycje"].append({"ticker": t, "sztuki": s, "cena": p, "typ": typ, "data_zakupu": str(d_zak)})

        with col_m:
            st.subheader("🛡️ Emerytura (IKZE) - Pozycje")
            for i in range(5):
                st.caption(f"Pozycja IKZE #{i+1}")
                prev = zapisane_dane["mbank_pozycje"][i] if i < len(zapisane_dane["mbank_pozycje"]) else {"ticker": "", "sztuki": 0.0, "cena": 0.0, "typ": "ETF", "data_zakupu": str(datetime.now().date())}
                c1, c2, c3, c4, c5 = st.columns(5)
                t = c1.text_input("Ticker", value=prev["ticker"], key=f"m_t_{i}").strip().upper()
                s = c2.number_input("Sztuki", min_value=0.0, value=float(prev["sztuki"]), key=f"m_s_{i}")
                p = c3.number_input("Śr. cena", min_value=0.0, value=float(prev["cena"]), key=f"m_p_{i}")
                typ = c4.selectbox("Typ", kategorie_opcje, index=kategorie_opcje.index(prev.get("typ", "ETF")), key=f"m_cat_{i}")
                
                d_zak_val = pd.to_datetime(prev.get("data_zakupu", datetime.now())).date()
                d_zak = c5.date_input("Data zakupu", value=d_zak_val, key=f"m_dz_{i}")
                
                nowe_dane["mbank_pozycje"].append({"ticker": t, "sztuki": s, "cena": p, "typ": typ, "data_zakupu": str(d_zak)})
                
        if st.button("💾 ZAPISZ PORTFELE", use_container_width=True):
            zapisz_pozycje(nowe_dane)
            st.success("Zapisano pozycje portfeli!")
            st.rerun()

    with tab2:
        st.subheader("💵 Zapisz stan Wolnej Gotówki, Bank i Lokatę")
        c_g1, c_g2 = st.columns(2)
        data_g = c_g1.date_input("📅 Data wpisu gotówki:", value=datetime.now(), key="cash_date")
        kwota_g = c_g2.number_input("Łączna kwota wolnej gotówki (PLN):", min_value=0.0, value=float(zapisane_dane.get("wolna_gotowka", 0.0)), step=100.0)
        
        c_g3, c_g4 = st.columns(2)
        bank_g = c_g3.text_input("Nazwa banku (np. mBank, PKO BP):", value="")
        lokata_g = c_g4.text_input("Lokata / Szczegóły (np. Lokata 3M 4.5%):", value="")
        
        if st.button("💾 ZAPISZ STAN GOTÓWKI I LOKATY", use_container_width=True):
            zapisane_dane["wolna_gotowka"] = kwota_g
            zapisz_pozycje(zapisane_dane)
            zapisz_wpis_gotowki(data_g, kwota_g, bank_g, lokata_g)
            st.success("Zapisano stan wolnej gotówki i lokaty!")
            st.rerun()

    with tab3:
        st.subheader("➕ Dopisz wpis historyczny do XTB lub Emerytury")
        c_d1, c_d2 = st.columns(2)
        data_wpisu = c_d1.date_input("Data wpisu:", value=datetime.now(), key="hist_date")
        wybrane_konto = c_d2.selectbox("Konto:", ["XTB", "Emerytura"])
        
        c_d3, c_d4 = st.columns(2)
        kwota_doplata = c_d3.number_input("Dopłata w miesiącu (PLN):", min_value=0.0, step=100.0)
        dokupione_aktywa = c_d4.text_input("Dokupione Aktywa (np. NVDA, AAPL):").strip().upper()
        
        st_aktualny = oblicz_stan_portfela(zapisane_dane)
        val_konta = st_aktualny["calosc_xtb"] if wybrane_konto == "XTB" else st_aktualny["calosc_emerytura"]
        zysk_konta = st_aktualny["zysk_xtb"] if wybrane_konto == "XTB" else st_aktualny["zysk_emerytura"]
        
        if st.button("📈 ZAPISZ WPIS HISTORII", use_container_width=True):
            zapisz_wpis_historii(data_wpisu, wybrane_konto, val_konta, kwota_doplata, zysk_konta, dokupione_aktywa)
            st.success(f"Dodano wpis historyczny dla {wybrane_konto}!")
            st.rerun()

    with tab4:
        st.subheader("💾 Ręczny zapis kopii zapasowej na dysku")
        st.info("Kliknięcie poniższego przycisku spowoduje utworzenie kompletnej kopii zapasowej wszystkich Twoich danych w osobnym folderze **`moje_kopie_zapasowe/`** na dysku serwera.")
        
        if st.button("📁 Utwórz osobną kopię na dysku", use_container_width=True):
            timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
            if os.path.exists(CONFIG_FILE):
                with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                    dane_poz = json.load(f)
                with open(os.path.join(USER_BACKUP_DIR, f"backup_portfela_{timestamp}.json"), "w", encoding="utf-8") as f:
                    json.dump(dane_poz, f, ensure_ascii=False, indent=4)
                    
            if os.path.exists(HISTORY_FILE):
                df_hist = pd.read_csv(HISTORY_FILE)
                df_hist.to_csv(os.path.join(USER_BACKUP_DIR, f"backup_historia_portfela_{timestamp}.csv"), index=False)
                
            if os.path.exists(CASH_HISTORY_FILE):
                df_cash = pd.read_csv(CASH_HISTORY_FILE)
                df_cash.to_csv(os.path.join(USER_BACKUP_DIR, f"backup_historia_gotowki_{timestamp}.csv"), index=False)

            st.success(f"Pomyślnie utworzono kopię zapasową w folderze `{USER_BACKUP_DIR}/`!")

        st.markdown("<hr>", unsafe_allow_html=True)
        st.subheader("📥 Pobieranie / Wgrywanie plików (Backup w przeglądarce)")
        col_b1, col_b2 = st.columns(2)
        if os.path.exists(CONFIG_FILE):
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                col_b1.download_button("⬇️ Pobierz pozycje (.JSON)", f.read(), "pozycje_portfela.json", "application/json")
        if os.path.exists(HISTORY_FILE):
            with open(HISTORY_FILE, "r", encoding="utf-8") as f:
                col_b2.download_button("⬇️ Pobierz historię (.CSV)", f.read(), "historia_portfela.csv", "text/csv")
        
        st.markdown("<br>", unsafe_allow_html=True)
        up_json = st.file_uploader("Wgraj plik `pozycje_portfela.json`", type=["json"])
        if up_json is not None:
            with open(CONFIG_FILE, "wb") as f:
                f.write(up_json.getbuffer())
            st.success("Przywrócono dane z pliku!")
            st.rerun()
