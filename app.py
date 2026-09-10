import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import json
import os
import random
from datetime import datetime, timedelta

# Konfiguracja strony
st.set_page_config(page_title="Finanse Karola", layout="wide", page_icon="⚡")

CONFIG_FILE = "pozycje_portfela.json"
HISTORY_FILE = "historia_portfela.csv"
CASH_HISTORY_FILE = "historia_gotowki.csv"

# Baza cytatów inwestycyjnych
CYTATY_INWESTYCYJNE = [
    {"cytat": "Bądź chciwy, gdy inni się boją, i bój się, gdy inni są chciwi.", "autor": "Warren Buffett"},
    {"cytat": "Najlepszą inwestycją, jaką możesz zrobić, jest inwestycja w samego siebie.", "autor": "Warren Buffett"},
    {"cytat": "Inwestowanie powinno być bardziej jak oglądanie schnącej farby lub rosnącej trawy. Jeśli chcesz emocji, weź 800 dolarów i jedź do Las Vegas.", "autor": "Paul Samuelson"},
    {"cytat": "Kluczem do zarabiania pieniędzy na akcjach jest niebać się ich.", "autor": "Peter Lynch"},
    {"cytat": "Inwestor indywidualny powinien działać konsekwentnie jako inwestor, a nie jako spekulant.", "autor": "Benjamin Graham"},
    {"cytat": "Niewiedza jest o wiele bardziej kosztowna niż ryzyko.", "autor": "Ray Dalio"},
    {"cytat": "Więcej pieniędzy stracono przygotowując się na korekty lub próbując je przewidzieć, niż w samych korektach.", "autor": "Peter Lynch"},
    {"cytat": "Rynek akcji to urządzenie do transferu pieniędzy od niecierpliwych do cierpliwych.", "autor": "Warren Buffett"},
    {"cytat": "Wielkie pieniądze nie znajdują się w kupowaniu i sprzedawaniu, ale w czekaniu.", "autor": "Charlie Munger"},
    {"cytat": "Dla inwestora najważniejsza jest cecha charakteru, a nie intelekt.", "autor": "Benjamin Graham"}
]

# --- ZARZĄDZANIE DANYMI I BAZĄ ---
def wczytaj_pozycje():
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                dane = json.load(f)
                # Kompatybilność wsteczna: jeśli gotówka była podzielona, sumujemy ją do wspólnej puli
                if "wolna_gotowka" not in dane:
                    stara_gotowka = dane.get("xtb_gotowka", 0.0) + dane.get("mbank_gotowka", 0.0)
                    dane["wolna_gotowka"] = stara_gotowka
                return dane
        except:
            pass
    
    return {
        "wolna_gotowka": 4700.0,
        "xtb_pozycje": [
            {"ticker": "NVDA", "sztuki": 12.0, "cena": 125.00, "typ": "Akcje"},
            {"ticker": "AAPL", "sztuki": 15.0, "cena": 175.00, "typ": "Akcje"},
            {"ticker": "MSFT", "sztuki": 6.0, "cena": 415.00, "typ": "Akcje"},
            {"ticker": "ALE.WA", "sztuki": 200.0, "cena": 34.20, "typ": "Akcje"},
            {"ticker": "BTC-USD", "sztuki": 0.15, "cena": 62000.0, "typ": "Krypto"}
        ],
        "mbank_pozycje": [
            {"ticker": "VWCE.DE", "sztuki": 45.0, "cena": 112.00, "typ": "ETF"},
            {"ticker": "PKN.WA", "sztuki": 250.0, "cena": 68.50, "typ": "Akcje"},
            {"ticker": "KGH.WA", "sztuki": 80.0, "cena": 142.00, "typ": "Akcje"},
            {"ticker": "PKO.WA", "sztuki": 150.0, "cena": 56.00, "typ": "Akcje"},
            {"ticker": "ETFSP500.WA", "sztuki": 60.0, "cena": 210.00, "typ": "ETF"}
        ]
    }

def zapisz_pozycje(dane):
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(dane, f, ensure_ascii=False, indent=4)

def wczytaj_historie():
    if os.path.exists(HISTORY_FILE):
        try:
            df = pd.read_csv(HISTORY_FILE)
            df['Data'] = pd.to_datetime(df['Data'])
            return df
        except:
            pass
    
    dzis = datetime.now()
    demo_historia = [
        # XTB
        {"Data": (dzis - timedelta(days=210)).strftime("%Y-%m-%d"), "Konto": "XTB", "Wartość Konta": 35000.0, "Dopłata w Miesiącu": 2000.0, "Zysk": 1500.0, "Dokupione Aktywa": "NVDA, AAPL"},
        {"Data": (dzis - timedelta(days=180)).strftime("%Y-%m-%d"), "Konto": "XTB", "Wartość Konta": 42000.0, "Dopłata w Miesiącu": 1500.0, "Zysk": 7000.0, "Dokupione Aktywa": "BTC-USD"},
        {"Data": (dzis - timedelta(days=150)).strftime("%Y-%m-%d"), "Konto": "XTB", "Wartość Konta": 36500.0, "Dopłata w Miesiącu": 1000.0, "Zysk": -3000.0, "Dokupione Aktywa": "NVDA"},
        {"Data": (dzis - timedelta(days=120)).strftime("%Y-%m-%d"), "Konto": "XTB", "Wartość Konta": 35800.0, "Dopłata w Miesiącu": 500.0,  "Zysk": -4200.0, "Dokupione Aktywa": "ALE.WA"},
        {"Data": (dzis - timedelta(days=90)).strftime("%Y-%m-%d"),  "Konto": "XTB", "Wartość Konta": 38200.0, "Dopłata w Miesiącu": 2000.0, "Zysk": -1100.0, "Dokupione Aktywa": "MSFT, AAPL"},
        {"Data": (dzis - timedelta(days=60)).strftime("%Y-%m-%d"),  "Konto": "XTB", "Wartość Konta": 44500.0, "Dopłata w Miesiącu": 1500.0, "Zysk": 3800.0, "Dokupione Aktywa": "BTC-USD"},
        {"Data": (dzis - timedelta(days=30)).strftime("%Y-%m-%d"),  "Konto": "XTB", "Wartość Konta": 43100.0, "Dopłata w Miesiącu": 0.0,    "Zysk": 2400.0, "Dokupione Aktywa": "Brak"},
        {"Data": dzis.strftime("%Y-%m-%d"),                       "Konto": "XTB", "Wartość Konta": 47900.0, "Dopłata w Miesiącu": 2500.0, "Zysk": 6200.0, "Dokupione Aktywa": "BTC-USD, NVDA"},

        # EMERYTURA
        {"Data": (dzis - timedelta(days=210)).strftime("%Y-%m-%d"), "Konto": "Emerytura", "Wartość Konta": 28000.0, "Dopłata w Miesiącu": 1000.0, "Zysk": 800.0,  "Dokupione Aktywa": "VWCE.DE"},
        {"Data": (dzis - timedelta(days=180)).strftime("%Y-%m-%d"), "Konto": "Emerytura", "Wartość Konta": 30500.0, "Dopłata w Miesiącu": 1000.0, "Zysk": 1700.0, "Dokupione Aktywa": "ETFSP500.WA"},
        {"Data": (dzis - timedelta(days=150)).strftime("%Y-%m-%d"), "Konto": "Emerytura", "Wartość Konta": 29200.0, "Dopłata w Miesiącu": 1000.0, "Zysk": -1100.0, "Dokupione Aktywa": "PKN.WA"},
        {"Data": (dzis - timedelta(days=120)).strftime("%Y-%m-%d"), "Konto": "Emerytura", "Wartość Konta": 29800.0, "Dopłata w Miesiącu": 500.0,  "Zysk": -800.0,  "Dokupione Aktywa": "KGH.WA"},
        {"Data": (dzis - timedelta(days=90)).strftime("%Y-%m-%d"),  "Konto": "Emerytura", "Wartość Konta": 31200.0, "Dopłata w Miesiącu": 1000.0, "Zysk": 100.0,   "Dokupione Aktywa": "VWCE.DE"},
        {"Data": (dzis - timedelta(days=60)).strftime("%Y-%m-%d"),  "Konto": "Emerytura", "Wartość Konta": 32000.0, "Dopłata w Miesiącu": 500.0,  "Zysk": 400.0,   "Dokupione Aktywa": "PKO.WA"},
        {"Data": (dzis - timedelta(days=30)).strftime("%Y-%m-%d"),  "Konto": "Emerytura", "Wartość Konta": 31500.0, "Dopłata w Miesiącu": 0.0,    "Zysk": -100.0,  "Dokupione Aktywa": "Brak"},
        {"Data": dzis.strftime("%Y-%m-%d"),                       "Konto": "Emerytura", "Wartość Konta": 34100.0, "Dopłata w Miesiącu": 1000.0, "Zysk": 1800.0, "Dokupione Aktywa": "VWCE.DE, ETFSP500.WA"}
    ]
    df_demo = pd.DataFrame(demo_historia)
    df_demo['Data'] = pd.to_datetime(df_demo['Data'])
    return df_demo

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

def wczytaj_historie_gotowki():
    if os.path.exists(CASH_HISTORY_FILE):
        try:
            df = pd.read_csv(CASH_HISTORY_FILE)
            df['Data'] = pd.to_datetime(df['Data'])
            return df
        except:
            pass
    
    dzis = datetime.now()
    demo_gotowka = [
        {"Data": (dzis - timedelta(days=120)).strftime("%Y-%m-%d"), "Kwota": 2000.0, "Bank": "mBank", "Lokata / Info": "Konto Oszczędnościowe 5%"},
        {"Data": (dzis - timedelta(days=90)).strftime("%Y-%m-%d"),  "Kwota": 3500.0, "Bank": "PKO BP", "Lokata / Info": "Lokata 3-miesięczna 4.5%"},
        {"Data": (dzis - timedelta(days=60)).strftime("%Y-%m-%d"),  "Kwota": 4100.0, "Bank": "Santander", "Lokata / Info": "Lokata elastyczna"},
        {"Data": dzis.strftime("%Y-%m-%d"),                       "Kwota": 4700.0, "Bank": "mBank", "Lokata / Info": "Gotówka na lokatę 3M"}
    ]
    df_demo = pd.DataFrame(demo_gotowka)
    df_demo['Data'] = pd.to_datetime(df_demo['Data'])
    return df_demo

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

# Pobieranie kursów
@st.cache_data(ttl=1800)
def pobierz_kurs(ticker):
    if not ticker:
        return 0.0
    try:
        dane = yf.Ticker(ticker.strip().upper())
        return float(dane.fast_info['lastPrice'])
    except:
        return 0.0

KURS_EUR_PLN = pobierz_kurs("EURPLN=X") or 4.30
KURS_USD_PLN = pobierz_kurs("USDPLN=X") or 3.90

zapisane_dane = wczytaj_pozycje()

# Zastrzeżenia globalne / wiadomości makroekonomiczne powiązane z rynkiem
GLOBALNE_WYDARZENIA = {
    "2026-03": "⚠️ Marzec 2026: Napięcia geopolityczne na Bliskim Wschodzie wywołały krótkoterminową korektę na rynkach surowcowych i akcyjnych.",
    "2026-04": "🚀 Kwiecień 2026: Silne odbicie napędzane optymizmem wokół sektora sztucznej inteligencji (AI) i zapowiedziami złagodzenia polityki stóp.",
    "2026-06": "📉 Czerwiec 2026: Wakacyjna korekta na giełdach (WIG testował niższe poziomy), schłodzenie nastrojów wokół przemysłu w Europie.",
    "default": "🌐 Otoczenie rynkowe: Banki centralne utrzymują ostrożną politykę stóp procentowych, co sprzyja dywersyfikacji w bezpieczne aktywa."
}

def pobierz_komentarz_rynkowy(data_str):
    klucz = data_str[:7] # Format YYYY-MM
    return GLOBALNE_WYDARZENIA.get(klucz, GLOBALNE_WYDARZENIA["default"])

# Styling zoptymalizowany pod brak scrollowania na stronie głównej
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
        border-left: 5px solid #10b981; padding: 14px 18px; border-radius: 12px;
        margin-bottom: 12px; border: 1px solid #e5dfd5;
    }
    .quote-box {
        margin-top: 8px; padding-top: 8px;
        border-top: 1px dashed #cbd5e1; font-style: italic; color: #475569; font-size: 0.85rem;
    }
    div[data-testid="stMetric"] {
        background: #ffffff; border: 1px solid #e2ded5; border-radius: 12px; padding: 12px;
    }
    .stButton>button {
        background: #10b981; color: #ffffff !important; font-weight: 700 !important;
        border-radius: 8px; padding: 8px 18px; border: none;
    }
    .nav-card {
        background: #ffffff; border: 2px solid #e2ded5; border-radius: 12px; padding: 14px; text-align: center;
    }
    .macro-news-box {
        background: #fffbeb; border-left: 4px solid #f59e0b; padding: 10px 14px; border-radius: 8px;
        font-size: 0.9rem; color: #92400e; margin-bottom: 10px;
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

# Obliczenia portfelowe
def oblicz_stan_portfela(dane_input):
    def przetworz(pozycje):
        dane_tabeli = []
        wartosc_akt, zysk_razem, koszt_razem = 0.0, 0.0, 0.0
        temp_items = []
        for item in pozycje:
            t = item["ticker"].strip().upper()
            szt, sr_cena = float(item["sztuki"]), float(item["cena"])
            typ = item.get("typ", "Akcje")
            if t and szt > 0:
                cena_rkt = pobierz_kurs(t) or (sr_cena * 1.15)
                cena_pln = cena_rkt * KURS_EUR_PLN if ".DE" in t else (cena_rkt * KURS_USD_PLN if t in ["AAPL", "NVDA", "MSFT", "BTC-USD"] else cena_rkt)
                wartosc = szt * cena_pln
                koszt = szt * sr_cena
                zysk = wartosc - koszt
                wartosc_akt += wartosc
                koszt_razem += koszt
                zysk_razem += zysk
                temp_items.append({"t": t, "szt": szt, "sr_cena": sr_cena, "cena_pln": cena_pln, "wartosc": wartosc, "koszt": koszt, "zysk": zysk, "typ": typ})
        
        for x in temp_items:
            zysk_pct = (x["zysk"] / x["koszt"] * 100) if x["koszt"] > 0 else 0.0
            status_str = f"🟢 +{x['zysk']:,.2f} PLN (+{zysk_pct:.1f}%)" if x['zysk'] >= 0 else f"🔴 {x['zysk']:,.2f} PLN ({zysk_pct:.1f}%)"
            dane_tabeli.append({
                "Ticker": x["t"], "Typ": x["typ"], "Sztuki": f"{x['szt']:.4f}".rstrip('0').rstrip('.'),
                "Śr. Cena": f"{x['sr_cena']:.2f} PLN", "Akt. Kurs": f"{x['cena_pln']:.2f} PLN",
                "Wartość": f"{x['wartosc']:,.2f} PLN".replace(",", " "), "Zysk/Strata": status_str,
                "Wartość_raw": x["wartosc"], "Zysk_raw": x["zysk"]
            })
        pct_konta = (zysk_razem / koszt_razem * 100) if koszt_razem > 0 else 0.0
        return wartosc_akt, zysk_razem, pct_konta, dane_tabeli

    aktywa_xtb, zysk_xtb, pct_xtb, tab_xtb = przetworz(dane_input["xtb_pozycje"])
    aktywa_emerytura, zysk_emerytura, pct_emerytura, tab_emerytura = przetworz(dane_input["mbank_pozycje"])
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
    df_konta = df_h[df_h["Konto"] == nazwa_konta].copy()
    
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

        # Pokazanie kontekstu rynkowego dla najnowszego okresu
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
        st.info("Brak historii wpisów.")

# ----------------------------------------------------
# 1. STRONA GŁÓWNA (Zaprojektowana pod jeden ekran bez scrollowania)
# ----------------------------------------------------
if st.session_state.page == "🏠 Główna":
    losowy_cytat = random.choice(CYTATY_INWESTYCYJNE)
    
    st.markdown(f"""
    <div class="welcome-header">
        <h2 style="margin:0; color: #1e293b;">Cześć Karol! 👋</h2>
        <div class="quote-box">💡 <i>„{losowy_cytat['cytat']}”</i> — <b>{losowy_cytat['autor']}</b></div>
    </div>
    """, unsafe_allow_html=True)
    
    c_main, c_xtb, c_emerytura, c_cash = st.columns(4)
    with c_main:
        st.metric("ŁĄCZNY MAJĄTEK", f"{stan['laczny_majatek']:,.2f} PLN".replace(",", " "))
    with c_xtb:
        st.metric("📈 XTB", f"{stan['calosc_xtb']:,.2f} PLN".replace(",", " "), delta=f"{stan['pct_xtb']:.1f}%")
    with c_emerytura:
        st.metric("🛡️ IKZE", f"{stan['calosc_emerytura']:,.2f} PLN".replace(",", " "), delta=f"{stan['pct_emerytura']:.1f}%")
    with c_cash:
        st.metric("💵 GOTÓWKA", f"{stan['wolna_gotowka']:,.2f} PLN".replace(",", " "))

    st.markdown("<h4 style='margin-bottom:0; margin-top:5px;'>📊 Alokacja Majątku</h4>", unsafe_allow_html=True)
    
    df_main_pie = pd.DataFrame([
        {"Składnik": "XTB", "Wartość": stan["aktywa_xtb"]},
        {"Składnik": "Emerytura (IKZE)", "Wartość": stan["aktywa_emerytura"]},
        {"Składnik": "Wolna Gotówka", "Wartość": stan["wolna_gotowka"]}
    ])
    
    fig_main_pie = px.pie(df_main_pie, values="Wartość", names="Składnik", hole=0.45,
                          color="Składnik",
                          color_discrete_map={"XTB": "#10b981", "Emerytura (IKZE)": "#3b82f6", "Wolna Gotówka": "#f59e0b"})
    fig_main_pie.update_layout(height=230, paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", margin=dict(l=10, r=10, t=10, b=10))
    st.plotly_chart(fig_main_pie, use_container_width=True)

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
        st.info("Brak wpisów w historii gotówki. Dodaj wpis w zakładce 'Dane'.")

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
            st.subheader("📈 XTB - Pozycje")
            for i in range(5):
                st.caption(f"Pozycja XTB #{i+1}")
                prev = zapisane_dane["xtb_pozycje"][i] if i < len(zapisane_dane["xtb_pozycje"]) else {"ticker": "", "sztuki": 0.0, "cena": 0.0, "typ": "Akcje"}
                c1, c2, c3, c4 = st.columns(4)
                t = c1.text_input("Ticker", value=prev["ticker"], key=f"x_t_{i}").strip().upper()
                s = c2.number_input("Sztuki", min_value=0.0, value=float(prev["sztuki"]), key=f"x_s_{i}")
                p = c3.number_input("Śr. cena", min_value=0.0, value=float(prev["cena"]), key=f"x_p_{i}")
                typ = c4.selectbox("Typ", kategorie_opcje, index=kategorie_opcje.index(prev.get("typ", "Akcje")), key=f"x_cat_{i}")
                nowe_dane["xtb_pozycje"].append({"ticker": t, "sztuki": s, "cena": p, "typ": typ})

        with col_m:
            st.subheader("🛡️ Emerytura (IKZE) - Pozycje")
            for i in range(5):
                st.caption(f"Pozycja IKZE #{i+1}")
                prev = zapisane_dane["mbank_pozycje"][i] if i < len(zapisane_dane["mbank_pozycje"]) else {"ticker": "", "sztuki": 0.0, "cena": 0.0, "typ": "ETF"}
                c1, c2, c3, c4 = st.columns(4)
                t = c1.text_input("Ticker", value=prev["ticker"], key=f"m_t_{i}").strip().upper()
                s = c2.number_input("Sztuki", min_value=0.0, value=float(prev["sztuki"]), key=f"m_s_{i}")
                p = c3.number_input("Śr. cena", min_value=0.0, value=float(prev["cena"]), key=f"m_p_{i}")
                typ = c4.selectbox("Typ", kategorie_opcje, index=kategorie_opcje.index(prev.get("typ", "ETF")), key=f"m_cat_{i}")
                nowe_dane["mbank_pozycje"].append({"ticker": t, "sztuki": s, "cena": p, "typ": typ})
                
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
        bank_g = c_g3.text_input("Nazwa banku (np. mBank, PKO BP):", value="mBank")
        lokata_g = c_g4.text_input("Lokata / Szczegóły (np. Lokata 3M 4.5%):", value="Konto Oszczędnościowe")
        
        if st.button("💾 ZAPISZ STAN GOTÓWKI I LOKATY", use_container_width=True):
            # Aktualizacja bieżącej gotówki w głównym configu
            zapisane_dane["wolna_gotowka"] = kwota_g
            zapisz_pozycje(zapisane_dane)
            # Dodanie wpisu do historii gotówki
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
        st.subheader("📥 Kopia Zapasowa (Backup)")
        col_b1, col_b2 = st.columns(2)
        if os.path.exists(CONFIG_FILE):
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                col_b1.download_button("⬇️ Pobierz pozycje (.JSON)", f.read(), "pozycje_portfela.json", "application/json")
        if os.path.exists(HISTORY_FILE):
            with open(HISTORY_FILE, "r", encoding="utf-8") as f:
                col_b2.download_button("⬇️ Pobierz historię (.CSV)", f.read(), "historia_portfela.csv", "text/csv")
        
        st.markdown("<hr>", unsafe_allow_html=True)
        up_json = st.file_uploader("Wgraj plik `pozycje_portfela.json`", type=["json"])
        if up_json is not None:
            with open(CONFIG_FILE, "wb") as f:
                f.write(up_json.getbuffer())
            st.success("Przywrócono dane!")
