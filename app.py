import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.express as px
import json
import os
from datetime import datetime, timedelta

# Konfiguracja strony
st.set_page_config(page_title="Finanse Karola", layout="wide", page_icon="⚡")

CONFIG_FILE = "pozycje_portfela.json"
HISTORY_FILE = "historia_portfela.csv"

# --- ZARZĄDZANIE TRWAŁOŚCIĄ DANYCH ---
def wczytaj_pozycje():
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            pass
    return {
        "xtb_gotowka": 0.0,
        "mbank_gotowka": 0.0,
        "xtb_pozycje": [{"ticker": "", "sztuki": 0.0, "cena": 0.0} for _ in range(5)],
        "mbank_pozycje": [{"ticker": "", "sztuki": 0.0, "cena": 0.0} for _ in range(5)]
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
    return pd.DataFrame(columns=["Data", "Łączny Majątek", "Zysk / Strata", "Wolna Gotówka", "XTB Wartość", "IKZE Wartość"])

def zapisz_wpis_historii(data_wpisu, laczny_majatek, laczny_zysk, laczna_gotowka, calosc_xtb, calosc_mbank):
    df = wczytaj_historie()
    nowy_wpis = pd.DataFrame([{
        "Data": pd.to_datetime(data_wpisu),
        "Łączny Majątek": laczny_majatek,
        "Zysk / Strata": laczny_zysk,
        "Wolna Gotówka": laczna_gotowka,
        "XTB Wartość": calosc_xtb,
        "IKZE Wartość": calosc_mbank
    }])
    df = pd.concat([df, nowy_wpis], ignore_index=True).drop_duplicates(subset=["Data"], keep="last")
    df = df.sort_values(by="Data")
    df.to_csv(HISTORY_FILE, index=False)

# --- STYLIZACJA NEONOWA & STYLES ---
st.markdown("""
<style>
    .stApp {
        background-color: #05070a;
        color: #ffffff;
        font-size: 1.1rem;
    }
    
    /* Nawigacja radiowa imitująca ikony/przyciskowe menu */
    div[data-testid="stRadio"] > div {
        flex-direction: row;
        gap: 15px;
    }
    div[data-testid="stRadio"] label {
        background: #0b131d;
        border: 2px solid #00bfff;
        padding: 12px 24px;
        border-radius: 12px;
        cursor: pointer;
        font-weight: 800 !important;
        font-size: 1.1rem !important;
        transition: all 0.3s ease;
    }
    div[data-testid="stRadio"] label:hover {
        border-color: #00ff9d;
        box-shadow: 0 0 15px rgba(0,255,157,0.4);
    }

    /* Baner Powitalny */
    .welcome-header {
        background: linear-gradient(90deg, #0d1b2a 0%, #1b263b 100%);
        border-left: 6px solid #00ff9d;
        padding: 25px;
        border-radius: 15px;
        margin-bottom: 25px;
        box-shadow: 0 0 20px rgba(0, 255, 157, 0.15);
    }
    
    /* Karty metryczne */
    div[data-testid="stMetric"] {
        background: linear-gradient(135deg, #0b131d 0%, #111c2b 100%);
        border: 2px solid #00ff9d;
        border-radius: 16px;
        padding: 20px;
        box-shadow: 0 0 20px rgba(0, 255, 157, 0.2);
    }
    div[data-testid="stMetricLabel"] > label {
        color: #ffffff !important;
        font-size: 1.1rem !important;
        font-weight: 900 !important;
    }
    div[data-testid="stMetricValue"] {
        background: linear-gradient(90deg, #00ff9d, #00e5ff);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-size: 2.3rem !important;
        font-weight: 900 !important;
    }

    /* Przycisk akcji */
    .stButton>button {
        background: linear-gradient(90deg, #00ff9d 0%, #00bfff 100%);
        color: #000000 !important;
        font-weight: 900 !important;
        font-size: 1.2rem !important;
        border-radius: 12px;
        padding: 12px 30px;
        border: none;
        box-shadow: 0 0 15px rgba(0, 255, 157, 0.4);
    }
    
    h1, h2, h3 {
        color: #00e5ff !important;
        font-weight: 900 !important;
    }
</style>
""", unsafe_allow_html=True)

# Pobieranie kursów
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

# Wczytanie zapisanych danych
zapisane_dane = wczytaj_pozycje()

# --- MENU NAWIGACYJNE Z IKONAMI ---
wybrana_strona = st.radio(
    "Nawigacja",
    ["🏠 Główna", "✏️ Wprowadzanie Danych", "📈 Historia i Podsumowania"],
    label_visibility="collapsed"
)

# Przetwarzanie wartości portfela
def oblicz_stan_portfela(dane_input):
    def przetworz(pozycje, gotowka, konto):
        dane_tabeli, dane_wykres = [], []
        wartosc_akt, zysk_razem = 0.0, 0.0
        
        for item in pozycje:
            t = item["ticker"].strip().upper()
            szt = float(item["sztuki"])
            sr_cena = float(item["cena"])
            
            if t and szt > 0:
                cena_rkt = pobierz_kurs(t)
                if ".DE" in t:
                    cena_pln = cena_rkt * KURS_EUR_PLN
                elif ".WA" in t:
                    cena_pln = cena_rkt
                elif t in ["AAPL", "NVDA", "MSFT", "AMZN", "GOOGL", "TSLA", "META"]:
                    cena_pln = cena_rkt * KURS_USD_PLN
                else:
                    cena_pln = cena_rkt
                    
                wartosc = szt * cena_pln
                koszt = szt * sr_cena
                zysk = wartosc - koszt
                
                wartosc_akt += wartosc
                zysk_razem += zysk
                
                dane_tabeli.append({
                    "Ticker": t, "Sztuki": f"{szt:.4f}",
                    "Śr. Cena Zakupu": f"{sr_cena:.2f} PLN",
                    "Aktualny Kurs": f"{cena_pln:.2f} PLN",
                    "Wartość": f"{wartosc:,.2f} PLN".replace(",", " "),
                    "Zysk / Strata": f"{zysk:,.2f} PLN".replace(",", " ")
                })
                dane_wykres.append({"Nazwa": f"{t} ({konto})", "Wartość PLN": wartosc})
                
        if gotowka > 0:
            dane_wykres.append({"Nazwa": f"Gotówka ({konto})", "Wartość PLN": gotowka})
            
        return wartosc_akt + gotowka, wartosc_akt, zysk_razem, dane_tabeli, dane_wykres

    calosc_xtb, aktywa_xtb, zysk_xtb, tab_xtb, wyk_xtb = przetworz(dane_input["xtb_pozycje"], dane_input["xtb_gotowka"], "XTB")
    calosc_mb, aktywa_mb, zysk_mb, tab_mb, wyk_mb = przetworz(dane_input["mbank_pozycje"], dane_input["mbank_gotowka"], "IKZE")
    
    return {
        "laczny_majatek": calosc_xtb + calosc_mb,
        "laczny_zysk": zysk_xtb + zysk_mb,
        "laczna_gotowka": dane_input["xtb_gotowka"] + dane_input["mbank_gotowka"],
        "calosc_xtb": calosc_xtb, "calosc_mbank": calosc_mb,
        "tab_xtb": tab_xtb, "tab_mbank": tab_mb,
        "wykres_dane": wyk_xtb + wyk_mb
    }

stan = oblicz_stan_portfela(zapisane_dane)

# ==========================================
# 1. STRONA GŁÓWNA (POWITANIE & PRZEGLĄD)
# ==========================================
if wybrana_strona == "🏠 Główna":
    st.markdown("""
    <div class="welcome-header">
        <h1 style="margin:0; font-size: 2.5rem;">Cześć Karol, to Twoje finanse! 👋</h1>
        <p style="color: #a0aec0; margin-top: 5px; font-size: 1.1rem;">Oto podsumowanie stanu Twojego majątku i alokacji aktywów.</p>
    </div>
    """, unsafe_allow_html=True)
    
    c1, c2, c3 = st.columns(3)
    c1.metric("ŁĄCZNY PORTFEL", f"{stan['laczny_majatek']:,.2f} PLN".replace(",", " "))
    c2.metric("ZYSK / STRATA", f"{stan['laczny_zysk']:,.2f} PLN".replace(",", " "), delta=f"{stan['laczny_zysk']:,.2f} PLN".replace(",", " "))
    c3.metric("WOLNA GOTÓWKA", f"{stan['laczna_gotowka']:,.2f} PLN".replace(",", " "))
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    col_g1, col_g2 = st.columns(2)
    with col_g1:
        st.subheader("📊 Podział Aktywów (Wykres Kołowy)")
        if stan["wykres_dane"]:
            df_pie = pd.DataFrame(stan["wykres_dane"])
            fig_pie = px.pie(
                df_pie, values="Wartość PLN", names="Nazwa", hole=0.5,
                color_discrete_sequence=["#00ff9d", "#00e5ff", "#00bfff", "#0072ff", "#39ff14"]
            )
            fig_pie.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", font=dict(color="#fff", size=14))
            st.plotly_chart(fig_pie, use_container_width=True)
        else:
            st.info("Brak wprowadzonych pozycji. Przejdź do zakładki 'Wprowadzanie Danych', aby dodać akcje.")
            
    with col_g2:
        st.subheader("🏦 Udział Kont Inwestycyjnych")
        df_konta = pd.DataFrame([
            {"Konto": "XTB", "Wartość PLN": stan["calosc_xtb"]},
            {"Konto": "IKZE mBank", "Wartość PLN": stan["calosc_mbank"]}
        ])
        fig_bar = px.bar(
            df_konta, x="Konto", y="Wartość PLN", color="Konto", text_auto='.2f',
            color_discrete_sequence=["#00ff9d", "#00e5ff"]
        )
        fig_bar.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", font=dict(color="#fff", size=14))
        st.plotly_chart(fig_bar, use_container_width=True)

# ==========================================
# 2. STRONA WPROWADZANIA DANYCH
# ==========================================
elif wybrana_strona == "✏️ Wprowadzanie Danych":
    st.title("✏️ ZARZĄDZANIE POZYCJAMI I DATA")
    st.caption("Wpisz aktualne pozycje. Wprowadź ticker (np. ALE.WA dla Allegro, AAPL dla Apple), liczbę sztuk oraz średnią cenę.")
    
    data_wpisu = st.date_input("📅 Data wpisu do historii:", value=datetime.now())
    
    st.markdown("---")
    col_x, col_m = st.columns(2)
    
    nowe_dane = {"xtb_gotowka": 0.0, "mbank_gotowka": 0.0, "xtb_pozycje": [], "mbank_pozycje": []}
    
    with col_x:
        st.subheader("🔴 KONTO XTB")
        gotowka_x = st.number_input("XTB: Gotówka (PLN)", min_value=0.0, value=float(zapisane_dane.get("xtb_gotowka", 0.0)), key="in_xtb_cash")
        nowe_dane["xtb_gotowka"] = gotowka_x
        
        st.markdown("**Pozycje Akcji/ETF:**")
        for i in range(5):
            st.caption(f"Pozycja #{i+1}")
            prev = zapisane_dane["xtb_pozycje"][i] if i < len(zapisane_dane["xtb_pozycje"]) else {"ticker": "", "sztuki": 0.0, "cena": 0.0}
            c1, c2, c3 = st.columns(3)
            t = c1.text_input("Ticker", value=prev["ticker"], key=f"x_t_{i}").strip().upper()
            s = c2.number_input("Sztuki", min_value=0.0, value=float(prev["sztuki"]), step=0.0001, format="%.4f", key=f"x_s_{i}")
            p = c3.number_input("Śr. cena", min_value=0.0, value=float(prev["cena"]), step=0.01, format="%.2f", key=f"x_p_{i}")
            nowe_dane["xtb_pozycje"].append({"ticker": t, "sztuki": s, "cena": p})

    with col_m:
        st.subheader("🟢 KONTO IKZE MBANK")
        gotowka_m = st.number_input("IKZE: Gotówka (PLN)", min_value=0.0, value=float(zapisane_dane.get("mbank_gotowka", 0.0)), key="in_mbank_cash")
        nowe_dane["mbank_gotowka"] = gotowka_m
        
        st.markdown("**Pozycje Akcji/ETF:**")
        for i in range(5):
            st.caption(f"Pozycja #{i+1}")
            prev = zapisane_dane["mbank_pozycje"][i] if i < len(zapisane_dane["mbank_pozycje"]) else {"ticker": "", "sztuki": 0.0, "cena": 0.0}
            c1, c2, c3 = st.columns(3)
            t = c1.text_input("Ticker", value=prev["ticker"], key=f"m_t_{i}").strip().upper()
            s = c2.number_input("Sztuki", min_value=0.0, value=float(prev["sztuki"]), step=0.0001, format="%.4f", key=f"m_s_{i}")
            p = c3.number_input("Śr. cena", min_value=0.0, value=float(prev["cena"]), step=0.01, format="%.2f", key=f"m_p_{i}")
            nowe_dane["mbank_pozycje"].append({"ticker": t, "sztuki": s, "cena": p})
            
    st.markdown("<br>", unsafe_allow_html=True)
    
    col_btn1, col_btn2 = st.columns(2)
    if col_btn1.button("💾 ZAPISZ AKTUALNE POZYCJE"):
        zapisz_pozycje(nowe_dane)
        st.success("Zapisano pozycje portfela na stałe!")
        st.rerun()
        
    if col_btn2.button("📈 ZAPISZ WPIS DO HISTORII"):
        zapisz_pozycje(nowe_dane)
        st_aktualny = oblicz_stan_portfela(nowe_dane)
        zapisz_wpis_historii(
            data_wpisu,
            st_aktualny["laczny_majatek"],
            st_aktualny["laczny_zysk"],
            st_aktualny["laczna_gotowka"],
            st_aktualny["calosc_xtb"],
            st_aktualny["calosc_mbank"]
        )
        st.success(f"Dodano wpis do historii z datą {data_wpisu}!")

# ==========================================
# 3. STRONA HISTORII I PODSUMOWAŃ
# ==========================================
elif wybrana_strona == "📈 Historia i Podsumowania":
    st.title("📈 HISTORIA I ANALIZA W CZASIE")
    
    df_hist = wczytaj_historie()
    
    if df_hist.empty:
        st.warning("Brak wpisów w historii! Wejdź w zakładkę 'Wprowadzanie Danych' i kliknij 'ZAPISZ WPIS DO HISTORII'.")
    else:
        # Podmenu filtrowania
        okres = st.radio("Wybierz zakres czasu:", ["Ostatni Tydzień", "Ostatni Miesiąc", "Ostatni Rok", "Wszystko"], horizontal=True)
        
        teraz = datetime.now()
        if okres == "Ostatni Tydzień":
            df_filtered = df_hist[df_hist['Data'] >= (teraz - timedelta(days=7))]
        elif okres == "Ostatni Miesiąc":
            df_filtered = df_hist[df_hist['Data'] >= (teraz - timedelta(days=30))]
        elif okres == "Ostatni Rok":
            df_filtered = df_hist[df_hist['Data'] >= (teraz - timedelta(days=365))]
        else:
            df_filtered = df_hist

        st.subheader("📍 Wykres Punktowo-Liniowy Majątku")
        fig_line = px.line(
            df_filtered, x="Data", y="Łączny Majątek", markers=True,
            title="Zmiana Wartości Portfela w Czasie (PLN)",
            color_discrete_sequence=["#00ff9d"]
        )
        fig_line.update_traces(marker=dict(size=10, color="#00e5ff"))
        fig_line.update_layout(
            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
            font=dict(color="#fff", size=14)
        )
        st.plotly_chart(fig_line, use_container_width=True)
        
        st.subheader("📋 Tabela Podsumowująca Historia")
        st.dataframe(df_filtered.sort_values(by="Data", ascending=False), use_container_width=True)
