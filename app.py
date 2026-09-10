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

# --- ZARZĄDZANIE DANYM I BAZĄ ---
def wczytaj_pozycje():
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            pass
    
    # 5 Przykładowych Aktywów dla XTB i 5 dla EMERYTURY (IKZE)
    return {
        "xtb_gotowka": 4200.0,
        "mbank_gotowka": 1800.0,
        "xtb_pozycje": [
            {"ticker": "NVDA", "sztuki": 12.0, "cena": 115.00},      # Nvidia
            {"ticker": "AAPL", "sztuki": 15.0, "cena": 185.00},      # Apple
            {"ticker": "MSFT", "sztuki": 6.0, "cena": 410.00},       # Microsoft
            {"ticker": "ALE.WA", "sztuki": 200.0, "cena": 31.20},    # Allegro
            {"ticker": "BTC-USD", "sztuki": 0.15, "cena": 58000.0}   # Bitcoin
        ],
        "mbank_pozycje": [
            {"ticker": "VWCE.DE", "sztuki": 45.0, "cena": 108.00},   # Vanguard All-World ETF
            {"ticker": "PKN.WA", "sztuki": 250.0, "cena": 64.50},    # Orlen
            {"ticker": "KGH.WA", "sztuki": 80.0, "cena": 135.00},    # KGHM
            {"ticker": "PKO.WA", "sztuki": 150.0, "cena": 52.00},    # PKO BP
            {"ticker": "ETFSP500.WA", "sztuki": 60.0, "cena": 205.00}# Lyxor S&P500 ETF
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
        {"Data": (dzis - timedelta(days=90)).strftime("%Y-%m-%d"), "Łączny Majątek": 68200.0, "Zysk / Strata": 4100.0, "Wolna Gotówka": 7000.0, "XTB Wartość": 38200.0, "Emerytura Wartość": 30000.0},
        {"Data": (dzis - timedelta(days=60)).strftime("%Y-%m-%d"), "Łączny Majątek": 71400.0, "Zysk / Strata": 5800.0, "Wolna Gotówka": 6000.0, "XTB Wartość": 40400.0, "Emerytura Wartość": 31000.0},
        {"Data": (dzis - timedelta(days=30)).strftime("%Y-%m-%d"), "Łączny Majątek": 74100.0, "Zysk / Strata": 7900.0, "Wolna Gotówka": 6000.0, "XTB Wartość": 42500.0, "Emerytura Wartość": 31600.0},
        {"Data": dzis.strftime("%Y-%m-%d"),                       "Łączny Majątek": 78900.0, "Zysk / Strata": 9200.0, "Wolna Gotówka": 6000.0, "XTB Wartość": 45900.0, "Emerytura Wartość": 33000.0}
    ]
    df_demo = pd.DataFrame(demo_historia)
    df_demo['Data'] = pd.to_datetime(df_demo['Data'])
    return df_demo

def zapisz_wpis_historii(data_wpisu, laczny_majatek, laczny_zysk, laczna_gotowka, calosc_xtb, calosc_mbank):
    df = wczytaj_historie()
    nowy_wpis = pd.DataFrame([{
        "Data": pd.to_datetime(data_wpisu),
        "Łączny Majątek": laczny_majatek,
        "Zysk / Strata": laczny_zysk,
        "Wolna Gotówka": laczna_gotowka,
        "XTB Wartość": calosc_xtb,
        "Emerytura Wartość": calosc_mbank
    }])
    df = pd.concat([df, nowy_wpis], ignore_index=True).drop_duplicates(subset=["Data"], keep="last")
    df = df.sort_values(by="Data")
    df.to_csv(HISTORY_FILE, index=False)

# Pobieranie kursów rynkowych
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

zapisane_dane = wczytaj_pozycje()

# --- STYLIZACJA ---
st.markdown("""
<style>
    .stApp {
        background-color: #f7f4ed;
        color: #2c3e50;
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    }
    
    /* Nawigacja */
    div[data-testid="stRadio"] > div {
        flex-direction: row;
        gap: 12px;
    }
    div[data-testid="stRadio"] label {
        background: #ffffff;
        border: 2px solid #dcd6cd;
        padding: 10px 20px;
        border-radius: 12px;
        cursor: pointer;
        font-weight: 700 !important;
        color: #2c3e50 !important;
        box-shadow: 0 3px 6px rgba(0,0,0,0.03);
    }
    div[data-testid="stRadio"] label:hover {
        border-color: #10b981;
        background-color: #f0fdf4;
    }

    /* Baner Powitalny */
    .welcome-header {
        background: linear-gradient(135deg, #ffffff 0%, #efebe4 100%);
        border-left: 6px solid #10b981;
        padding: 22px;
        border-radius: 16px;
        margin-bottom: 20px;
        box-shadow: 0 4px 10px rgba(0,0,0,0.04);
        border: 1px solid #e5dfd5;
    }
    
    /* Metryki */
    div[data-testid="stMetric"] {
        background: #ffffff;
        border: 1px solid #e2ded5;
        border-radius: 16px;
        padding: 18px;
        box-shadow: 0 4px 10px rgba(0,0,0,0.03);
    }

    /* Przycisk akcji */
    .stButton>button {
        background: #10b981;
        color: #ffffff !important;
        font-weight: 700 !important;
        border-radius: 10px;
        padding: 10px 24px;
        border: none;
        box-shadow: 0 4px 10px rgba(16, 185, 129, 0.2);
    }
    
    /* Karty Nawigacyjne do Kont */
    .nav-card {
        background: #ffffff;
        border: 2px solid #e2ded5;
        border-radius: 16px;
        padding: 20px;
        text-align: center;
        box-shadow: 0 4px 12px rgba(0,0,0,0.04);
    }
</style>
""", unsafe_allow_html=True)

# Inicjalizacja stanu nawigacji
if "page" not in st.session_state:
    st.session_state.page = "🏠 Główna"

def idz_do_strony(nazwa_strony):
    st.session_state.page = nazwa_strony

# Nawigacja górna
st.session_state.page = st.radio(
    "Nawigacja",
    ["🏠 Główna", "📈 Portfel XTB", "🛡️ Emerytura (IKZE)", "✏️ Edycja & Historia"],
    index=["🏠 Główna", "📈 Portfel XTB", "🛡️ Emerytura (IKZE)", "✏️ Edycja & Historia"].index(st.session_state.page),
    label_visibility="collapsed"
)

# --- OBLICZENIA I PRZETWARZANIE ---
def oblicz_stan_portfela(dane_input):
    def przetworz(pozycje, gotowka, konto):
        dane_tabeli = []
        wartosc_akt, zysk_razem, koszt_razem = 0.0, 0.0, 0.0
        
        for item in pozycje:
            t = item["ticker"].strip().upper()
            szt = float(item["sztuki"])
            sr_cena = float(item["cena"])
            
            if t and szt > 0:
                cena_rkt = pobierz_kurs(t)
                if cena_rkt == 0.0:
                    cena_rkt = sr_cena * 1.15
                    
                if ".DE" in t:
                    cena_pln = cena_rkt * KURS_EUR_PLN
                elif ".WA" in t:
                    cena_pln = cena_rkt
                elif t in ["AAPL", "NVDA", "MSFT", "AMZN", "GOOGL", "TSLA", "META", "BTC-USD"]:
                    cena_pln = cena_rkt * KURS_USD_PLN
                else:
                    cena_pln = cena_rkt
                    
                wartosc = szt * cena_pln
                koszt = szt * sr_cena
                zysk = wartosc - koszt
                zysk_pct = (zysk / koszt * 100) if koszt > 0 else 0.0
                
                wartosc_akt += wartosc
                koszt_razem += koszt
                zysk_razem += zysk
                
                status_str = f"🟢 +{zysk:,.2f} PLN (+{zysk_pct:.1f}%)" if zysk >= 0 else f"🔴 {zysk:,.2f} PLN ({zysk_pct:.1f}%)"
                
                dane_tabeli.append({
                    "Ticker": t,
                    "Liczba Sztuk": f"{szt:.4f}".rstrip('0').rstrip('.'),
                    "Śr. Cena Zakupu": f"{sr_cena:.2f} PLN",
                    "Aktualny Kurs": f"{cena_pln:.2f} PLN",
                    "Wartość Łączna": f"{wartosc:,.2f} PLN".replace(",", " "),
                    "Status (Zysk/Strata)": status_str,
                    "Wartość_raw": wartosc
                })
                
        pct_konta = (zysk_razem / koszt_razem * 100) if koszt_razem > 0 else 0.0
        return wartosc_akt + gotowka, wartosc_akt, zysk_razem, pct_konta, dane_tabeli

    calosc_xtb, aktywa_xtb, zysk_xtb, pct_xtb, tab_xtb = przetworz(dane_input["xtb_pozycje"], dane_input["xtb_gotowka"], "XTB")
    calosc_emerytura, aktywa_emerytura, zysk_emerytura, pct_emerytura, tab_emerytura = przetworz(dane_input["mbank_pozycje"], dane_input["mbank_gotowka"], "Emerytura")
    
    laczna_gotowka = dane_input["xtb_gotowka"] + dane_input["mbank_gotowka"]
    
    return {
        "laczny_majatek": calosc_xtb + calosc_emerytura,
        "laczny_zysk": zysk_xtb + zysk_emerytura,
        "laczna_gotowka": laczna_gotowka,
        "calosc_xtb": calosc_xtb, 
        "calosc_emerytura": calosc_emerytura,
        "aktywa_xtb": aktywa_xtb,
        "aktywa_emerytura": aktywa_emerytura,
        "zysk_xtb": zysk_xtb,
        "pct_xtb": pct_xtb,
        "zysk_emerytura": zysk_emerytura,
        "pct_emerytura": pct_emerytura,
        "tab_xtb": tab_xtb, 
        "tab_emerytura": tab_emerytura
    }

stan = oblicz_stan_portfela(zapisane_dane)

# ==========================================
# 1. STRONA GŁÓWNA
# ==========================================
if st.session_state.page == "🏠 Główna":
    st.markdown("""
    <div class="welcome-header">
        <h1 style="margin:0; font-size: 2.2rem; color: #1e293b;">Cześć Karol! 👋</h1>
        <p style="color: #64748b; margin-top: 5px; font-size: 1.05rem;">Przegląd Twojego majątku i alokacji środków.</p>
    </div>
    """, unsafe_allow_html=True)
    
    # 1. Główna sekcja z Łącznym Majątkiem i Rozbiciem na konta
    st.markdown("### 💰 Majątek i Status Kont")
    
    # Główny stan majątku
    c_main, c_xtb, c_emerytura = st.columns([1.2, 1, 1])
    
    with c_main:
        st.metric(
            label="ŁĄCZNY MAJĄTEK", 
            value=f"{stan['laczny_majatek']:,.2f} PLN".replace(",", " "),
            delta=f"{stan['laczny_zysk']:,.2f} PLN (Zysk łączny)".replace(",", " ")
        )

    with c_xtb:
        delta_sign_xtb = "+" if stan['zysk_xtb'] >= 0 else ""
        st.metric(
            label="📈 PORTFEL XTB", 
            value=f"{stan['calosc_xtb']:,.2f} PLN".replace(",", " "),
            delta=f"{delta_sign_xtb}{stan['zysk_xtb']:,.2f} PLN ({stan['pct_xtb']:.1f}%)".replace(",", " ")
        )

    with c_emerytura:
        delta_sign_em = "+" if stan['zysk_emerytura'] >= 0 else ""
        st.metric(
            label="🛡️ EMERYTURA (IKZE)", 
            value=f"{stan['calosc_emerytura']:,.2f} PLN".replace(",", " "),
            delta=f"{delta_sign_em}{stan['zysk_emerytura']:,.2f} PLN ({stan['pct_emerytura']:.1f}%)".replace(",", " ")
        )

    st.markdown("<br>", unsafe_allow_html=True)
    
    # 2. Wykres Kołowy ze składnikami: Aktywa XTB, Aktywa Emerytura, Poduszka Finansowa (Gotówka)
    st.subheader("📊 Podział Aktywów i Poduszki Finansowej")
    
    df_main_pie = pd.DataFrame([
        {"Składnik": "Inwestycje XTB", "Wartość": stan["aktywa_xtb"]},
        {"Składnik": "Inwestycje Emerytura (IKZE)", "Wartość": stan["aktywa_emerytura"]},
        {"Składnik": "Poduszka Finansowa (Gotówka)", "Wartość": stan["laczna_gotowka"]}
    ])
    
    fig_main_pie = px.pie(
        df_main_pie, 
        values="Wartość", 
        names="Składnik", 
        hole=0.45,
        color="Składnik",
        color_discrete_map={
            "Inwestycje XTB": "#10b981", 
            "Inwestycje Emerytura (IKZE)": "#3b82f6",
            "Poduszka Finansowa (Gotówka)": "#f59e0b"
        }
    )
    fig_main_pie.update_layout(
        paper_bgcolor="rgba(0,0,0,0)", 
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#2c3e50", size=14),
        legend=dict(orientation="h", y=-0.1)
    )
    st.plotly_chart(fig_main_pie, use_container_width=True)
    
    st.markdown("<br><hr style='border-color: #e2ded5;'><br>", unsafe_allow_html=True)
    
    # 3. Kafelki nawigacyjne do szczegółów
    st.subheader("🚀 Przejdź do szczegółów portfela:")
    col_card1, col_card2 = st.columns(2)
    
    with col_card1:
        st.markdown(f"""
        <div class="nav-card">
            <h2>📈 PORTFEL XTB</h2>
            <p style="font-size: 1.3rem; font-weight: bold; color: #10b981;">{stan['calosc_xtb']:,.2f} PLN</p>
            <p style="color: #64748b;">Pozycji w aktywach: <b>{len(stan['tab_xtb'])}</b></p>
        </div>
        """, unsafe_allow_html=True)
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("👉 Otwórz Portfel XTB", use_container_width=True):
            idz_do_strony("📈 Portfel XTB")
            st.rerun()

    with col_card2:
        st.markdown(f"""
        <div class="nav-card">
            <h2>🛡️ EMERYTURA (IKZE)</h2>
            <p style="font-size: 1.3rem; font-weight: bold; color: #3b82f6;">{stan['calosc_emerytura']:,.2f} PLN</p>
            <p style="color: #64748b;">Pozycji w aktywach: <b>{len(stan['tab_emerytura'])}</b></p>
        </div>
        """, unsafe_allow_html=True)
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("👉 Otwórz Portfel Emerytura", use_container_width=True):
            idz_do_strony("🛡️ Emerytura (IKZE)")
            st.rerun()

# ==========================================
# 2. DEDYROWANA STRONA: XTB
# ==========================================
elif st.session_state.page == "📈 Portfel XTB":
    st.title("📈 PORTFEL XTB")
    
    c1, c2, c3 = st.columns(3)
    c1.metric("WARTOŚĆ KONTA XTB", f"{stan['calosc_xtb']:,.2f} PLN".replace(",", " "))
    c2.metric("ZYSK / STRATA", f"{stan['zysk_xtb']:,.2f} PLN".replace(",", " "), delta=f"{stan['zysk_xtb']:,.2f} PLN ({stan['pct_xtb']:.1f}%)".replace(",", " "))
    c3.metric("GOTÓWKA XTB", f"{zapisane_dane['xtb_gotowka']:,.2f} PLN".replace(",", " "))
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    col_chart, col_info = st.columns([1, 2])
    with col_chart:
        st.subheader("Alokacja w XTB")
        if stan["tab_xtb"]:
            df_xtb_pie = pd.DataFrame(stan["tab_xtb"])
            fig_xtb = px.pie(df_xtb_pie, values="Wartość_raw", names="Ticker", hole=0.4,
                             color_discrete_sequence=["#10b981", "#059669", "#34d399", "#6ee7b7", "#a7f3d0"])
            fig_xtb.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
            st.plotly_chart(fig_xtb, use_container_width=True)
            
    with col_info:
        st.subheader("📋 Posiadane Aktywa i Status")
        if stan["tab_xtb"]:
            df_display = pd.DataFrame(stan["tab_xtb"]).drop(columns=["Wartość_raw"])
            st.dataframe(df_display, use_container_width=True, hide_index=True)
        else:
            st.info("Brak pozycji na koncie XTB.")

# ==========================================
# 3. DEDYROWANA STRONA: EMERYTURA (IKZE)
# ==========================================
elif st.session_state.page == "🛡️ Emerytura (IKZE)":
    st.title("🛡️ PORTFEL EMERYTURA (IKZE)")
    
    c1, c2, c3 = st.columns(3)
    c1.metric("WARTOŚĆ EMERYTURY", f"{stan['calosc_emerytura']:,.2f} PLN".replace(",", " "))
    c2.metric("ZYSK / STRATA", f"{stan['zysk_emerytura']:,.2f} PLN".replace(",", " "), delta=f"{stan['zysk_emerytura']:,.2f} PLN ({stan['pct_emerytura']:.1f}%)".replace(",", " "))
    c3.metric("GOTÓWKA IKZE", f"{zapisane_dane['mbank_gotowka']:,.2f} PLN".replace(",", " "))
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    col_chart, col_info = st.columns([1, 2])
    with col_chart:
        st.subheader("Alokacja w Emerytura")
        if stan["tab_emerytura"]:
            df_em_pie = pd.DataFrame(stan["tab_emerytura"])
            fig_em = px.pie(df_em_pie, values="Wartość_raw", names="Ticker", hole=0.4,
                            color_discrete_sequence=["#3b82f6", "#2563eb", "#60a5fa", "#93c5fd", "#bfdbfe"])
            fig_em.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
            st.plotly_chart(fig_em, use_container_width=True)
            
    with col_info:
        st.subheader("📋 Posiadane Aktywa i Status")
        if stan["tab_emerytura"]:
            df_display = pd.DataFrame(stan["tab_emerytura"]).drop(columns=["Wartość_raw"])
            st.dataframe(df_display, use_container_width=True, hide_index=True)
        else:
            st.info("Brak pozycji w portfelu emerytalnym.")

# ==========================================
# 4. EDYCJA I HISTORIA
# ==========================================
elif st.session_state.page == "✏️ Edycja & Historia":
    st.title("✏️ ZARZĄDZANIE POZYCJAMI I HISTORIA")
    
    tab1, tab2 = st.tabs(["📝 Edycja Aktywów", "📈 Wykres i Historia"])
    
    with tab1:
        data_wpisu = st.date_input("📅 Data wpisu do historii:", value=datetime.now())
        st.markdown("---")
        col_x, col_m = st.columns(2)
        
        nowe_dane = {"xtb_gotowka": 0.0, "mbank_gotowka": 0.0, "xtb_pozycje": [], "mbank_pozycje": []}
        
        with col_x:
            st.subheader("🔴 KONTO XTB")
            gotowka_x = st.number_input("XTB: Gotówka (PLN)", min_value=0.0, value=float(zapisane_dane.get("xtb_gotowka", 0.0)), key="in_x_c")
            nowe_dane["xtb_gotowka"] = gotowka_x
            
            for i in range(5):
                st.caption(f"Pozycja XTB #{i+1}")
                prev = zapisane_dane["xtb_pozycje"][i] if i < len(zapisane_dane["xtb_pozycje"]) else {"ticker": "", "sztuki": 0.0, "cena": 0.0}
                c1, c2, c3 = st.columns(3)
                t = c1.text_input("Ticker", value=prev["ticker"], key=f"x_t_{i}").strip().upper()
                s = c2.number_input("Sztuki", min_value=0.0, value=float(prev["sztuki"]), step=0.0001, format="%.4f", key=f"x_s_{i}")
                p = c3.number_input("Śr. cena", min_value=0.0, value=float(prev["cena"]), step=0.01, format="%.2f", key=f"x_p_{i}")
                nowe_dane["xtb_pozycje"].append({"ticker": t, "sztuki": s, "cena": p})

        with col_m:
            st.subheader("🔵 PORTFEL EMERYTURA (IKZE)")
            gotowka_m = st.number_input("Emerytura: Gotówka (PLN)", min_value=0.0, value=float(zapisane_dane.get("mbank_gotowka", 0.0)), key="in_m_c")
            nowe_dane["mbank_gotowka"] = gotowka_m
            
            for i in range(5):
                st.caption(f"Pozycja Emerytura #{i+1}")
                prev = zapisane_dane["mbank_pozycje"][i] if i < len(zapisane_dane["mbank_pozycje"]) else {"ticker": "", "sztuki": 0.0, "cena": 0.0}
                c1, c2, c3 = st.columns(3)
                t = c1.text_input("Ticker", value=prev["ticker"], key=f"m_t_{i}").strip().upper()
                s = c2.number_input("Sztuki", min_value=0.0, value=float(prev["sztuki"]), step=0.0001, format="%.4f", key=f"m_s_{i}")
                p = c3.number_input("Śr. cena", min_value=0.0, value=float(prev["cena"]), step=0.01, format="%.2f", key=f"m_p_{i}")
                nowe_dane["mbank_pozycje"].append({"ticker": t, "sztuki": s, "cena": p})
                
        st.markdown("<br>", unsafe_allow_html=True)
        col_b1, col_b2 = st.columns(2)
        if col_b1.button("💾 ZAPISZ POZYCJE"):
            zapisz_pozycje(nowe_dane)
            st.success("Zapisano pozycje portfela!")
            st.rerun()
            
        if col_b2.button("📈 ZAPISZ WPIS W HISTORII"):
            zapisz_pozycje(nowe_dane)
            st_aktualny = oblicz_stan_portfela(nowe_dane)
            zapisz_wpis_historii(
                data_wpisu,
                st_aktualny["laczny_majatek"],
                st_aktualny["laczny_zysk"],
                st_aktualny["laczna_gotowka"],
                st_aktualny["calosc_xtb"],
                st_aktualny["calosc_emerytura"]
            )
            st.success(f"Zapisano punkt w historii pod datą {data_wpisu}!")

    with tab2:
        df_hist = wczytaj_historie()
        if not df_hist.empty:
            st.subheader("📍 Zmiana Majątku w Czasie")
            fig_line = px.line(df_hist, x="Data", y="Łączny Majątek", markers=True, color_discrete_sequence=["#10b981"])
            fig_line.update_traces(marker=dict(size=10, color="#059669"))
            fig_line.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
            st.plotly_chart(fig_line, use_container_width=True)
            
            st.subheader("📋 Tabela Historii Wpisów")
            st.dataframe(df_hist.sort_values(by="Data", ascending=False), use_container_width=True)
