import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import json
import os
from datetime import datetime, timedelta

# Konfiguracja strony
st.set_page_config(page_title="Finanse Karola", layout="wide", page_icon="⚡")

CONFIG_FILE = "pozycje_portfela.json"
HISTORY_FILE = "historia_portfela.csv"

# --- ZARZĄDZANIE DANYMI I BAZĄ ---
def wczytaj_pozycje():
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            pass
    
    return {
        "xtb_gotowka": 4200.0,
        "mbank_gotowka": 1800.0,
        "xtb_pozycje": [
            {"ticker": "NVDA", "sztuki": 12.0, "cena": 115.00, "typ": "Akcje"},
            {"ticker": "AAPL", "sztuki": 15.0, "cena": 185.00, "typ": "Akcje"},
            {"ticker": "MSFT", "sztuki": 6.0, "cena": 410.00, "typ": "Akcje"},
            {"ticker": "ALE.WA", "sztuki": 200.0, "cena": 31.20, "typ": "Akcje"},
            {"ticker": "BTC-USD", "sztuki": 0.15, "cena": 58000.0, "typ": "Krypto"}
        ],
        "mbank_pozycje": [
            {"ticker": "VWCE.DE", "sztuki": 45.0, "cena": 108.00, "typ": "ETF"},
            {"ticker": "PKN.WA", "sztuki": 250.0, "cena": 64.50, "typ": "Akcje"},
            {"ticker": "KGH.WA", "sztuki": 80.0, "cena": 135.00, "typ": "Akcje"},
            {"ticker": "PKO.WA", "sztuki": 150.0, "cena": 52.00, "typ": "Akcje"},
            {"ticker": "ETFSP500.WA", "sztuki": 60.0, "cena": 205.00, "typ": "ETF"}
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
        {"Data": (dzis - timedelta(days=90)).strftime("%Y-%m-%d"), "Konto": "XTB", "Wartość Konta": 38200.0, "Dopłata w Miesiącu": 2000.0, "Zysk": 3100.0, "Dokupione Aktywa": "NVDA, AAPL"},
        {"Data": (dzis - timedelta(days=60)).strftime("%Y-%m-%d"), "Konto": "XTB", "Wartość Konta": 41400.0, "Dopłata w Miesiącu": 1500.0, "Zysk": 4800.0, "Dokupione Aktywa": "MSFT, ALE.WA"},
        {"Data": (dzis - timedelta(days=30)).strftime("%Y-%m-%d"), "Konto": "XTB", "Wartość Konta": 43100.0, "Dopłata w Miesiącu": 1000.0, "Zysk": 5500.0, "Dokupione Aktywa": "NVDA, BTC-USD"},
        {"Data": dzis.strftime("%Y-%m-%d"),                       "Konto": "XTB", "Wartość Konta": 45900.0, "Dopłata w Miesiącu": 2500.0, "Zysk": 6200.0, "Dokupione Aktywa": "BTC-USD, NVDA, AAPL"},
        
        {"Data": (dzis - timedelta(days=90)).strftime("%Y-%m-%d"), "Konto": "Emerytura", "Wartość Konta": 30000.0, "Dopłata w Miesiącu": 1000.0, "Zysk": 1000.0, "Dokupione Aktywa": "VWCE.DE"},
        {"Data": (dzis - timedelta(days=60)).strftime("%Y-%m-%d"), "Konto": "Emerytura", "Wartość Konta": 31000.0, "Dopłata w Miesiącu": 1000.0, "Zysk": 1200.0, "Dokupione Aktywa": "PKN.WA, ETFSP500.WA"},
        {"Data": (dzis - timedelta(days=30)).strftime("%Y-%m-%d"), "Konto": "Emerytura", "Wartość Konta": 31600.0, "Dopłata w Miesiącu": 500.0,  "Zysk": 1400.0, "Dokupione Aktywa": "KGH.WA, PKO.WA"},
        {"Data": dzis.strftime("%Y-%m-%d"),                       "Konto": "Emerytura", "Wartość Konta": 33000.0, "Dopłata w Miesiącu": 1000.0, "Zysk": 1800.0, "Dokupione Aktywa": "VWCE.DE, ETFSP500.WA"}
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

# Styling
st.markdown("""
<style>
    .stApp { background-color: #f7f4ed; color: #2c3e50; font-family: 'Segoe UI', sans-serif; }
    div[data-testid="stRadio"] > div { flex-direction: row; gap: 12px; }
    div[data-testid="stRadio"] label {
        background: #ffffff; border: 2px solid #dcd6cd; padding: 10px 20px;
        border-radius: 12px; font-weight: 700 !important; color: #2c3e50 !important;
    }
    div[data-testid="stRadio"] label:hover { border-color: #10b981; background-color: #f0fdf4; }
    .welcome-header {
        background: linear-gradient(135deg, #ffffff 0%, #efebe4 100%);
        border-left: 6px solid #10b981; padding: 22px; border-radius: 16px;
        margin-bottom: 20px; border: 1px solid #e5dfd5;
    }
    div[data-testid="stMetric"] {
        background: #ffffff; border: 1px solid #e2ded5; border-radius: 16px; padding: 18px;
    }
    .stButton>button {
        background: #10b981; color: #ffffff !important; font-weight: 700 !important;
        border-radius: 10px; padding: 10px 24px; border: none;
    }
    .nav-card {
        background: #ffffff; border: 2px solid #e2ded5; border-radius: 16px; padding: 20px; text-align: center;
    }
</style>
""", unsafe_allow_html=True)

if "page" not in st.session_state:
    st.session_state.page = "🏠 Główna"

st.session_state.page = st.radio(
    "Nawigacja",
    ["🏠 Główna", "📈 Portfel XTB", "🛡️ Emerytura (IKZE)", "✏️ Edycja & Dopłaty"],
    index=["🏠 Główna", "📈 Portfel XTB", "🛡️ Emerytura (IKZE)", "✏️ Edycja & Dopłaty"].index(st.session_state.page),
    label_visibility="collapsed"
)

# Obliczenia
def oblicz_stan_portfela(dane_input):
    def przetworz(pozycje, gotowka):
        dane_tabeli = []
        wartosc_akt, zysk_razem, koszt_razem = 0.0, 0.0, 0.0
        
        # Obliczenie sumarycznej wartości do wyliczenia udziału %
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
        
        calosc_z_gotowka = wartosc_akt + gotowka
        
        for x in temp_items:
            zysk_pct = (x["zysk"] / x["koszt"] * 100) if x["koszt"] > 0 else 0.0
            udzial_pct = (x["wartosc"] / calosc_z_gotowka * 100) if calosc_z_gotowka > 0 else 0.0
            status_str = f"🟢 +{x['zysk']:,.2f} PLN (+{zysk_pct:.1f}%)" if x['zysk'] >= 0 else f"🔴 {x['zysk']:,.2f} PLN ({zysk_pct:.1f}%)"
            
            dane_tabeli.append({
                "Ticker": x["t"],
                "Typ": x["typ"],
                "Sztuki": f"{x['szt']:.4f}".rstrip('0').rstrip('.'),
                "Śr. Cena Zakupu": f"{x['sr_cena']:.2f} PLN",
                "Aktualny Kurs": f"{x['cena_pln']:.2f} PLN",
                "Wartość Łączna": f"{x['wartosc']:,.2f} PLN".replace(",", " "),
                "Zysk / Strata": status_str,
                "Udział w Portfelu (%)": f"{udzial_pct:.2f}%",
                "Wartość_raw": x["wartosc"],
                "Zysk_raw": x["zysk"]
            })
            
        pct_konta = (zysk_razem / koszt_razem * 100) if koszt_razem > 0 else 0.0
        return calosc_z_gotowka, wartosc_akt, zysk_razem, pct_konta, dane_tabeli

    calosc_xtb, aktywa_xtb, zysk_xtb, pct_xtb, tab_xtb = przetworz(dane_input["xtb_pozycje"], dane_input["xtb_gotowka"])
    calosc_emerytura, aktywa_emerytura, zysk_emerytura, pct_emerytura, tab_emerytura = przetworz(dane_input["mbank_pozycje"], dane_input["mbank_gotowka"])
    
    return {
        "laczny_majatek": calosc_xtb + calosc_emerytura,
        "laczny_zysk": zysk_xtb + zysk_emerytura,
        "laczna_gotowka": dane_input["xtb_gotowka"] + dane_input["mbank_gotowka"],
        "calosc_xtb": calosc_xtb, "calosc_emerytura": calosc_emerytura,
        "aktywa_xtb": aktywa_xtb, "aktywa_emerytura": aktywa_emerytura,
        "zysk_xtb": zysk_xtb, "pct_xtb": pct_xtb,
        "zysk_emerytura": zysk_emerytura, "pct_emerytura": pct_emerytura,
        "tab_xtb": tab_xtb, "tab_emerytura": tab_emerytura
    }

stan = oblicz_stan_portfela(zapisane_dane)

def pokaz_wykres_i_historie_konta(nazwa_konta, kolor_glowny, dane_tabeli):
    df_h = wczytaj_historie()
    df_konta = df_h[df_h["Konto"] == nazwa_konta].copy()
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    c_head1, c_head2 = st.columns([2, 1])
    with c_head1:
        st.subheader(f"📈 Trend Wzrostowy & Skumulowany Wzrost ({nazwa_konta})")
    with c_head2:
        horyzont = st.selectbox("⏳ Horyzont czasowy:", ["Miesiące", "Tygodnie", "Dni"], key=f"horiz_{nazwa_konta}")

    if not df_konta.empty:
        # Agregacja w zależności od horyzontu czasowego
        if horyzont == "Miesiące":
            df_konta['Okres'] = df_konta['Data'].dt.strftime('%Y-%m')
        elif horyzont == "Tygodnie":
            df_konta['Okres'] = df_konta['Data'].dt.strftime('%Y-W%U')
        else:
            df_konta['Okres'] = df_konta['Data'].dt.strftime('%Y-%m-%d')

        df_grouped = df_konta.groupby('Okres').agg({
            'Wartość Konta': 'last',
            'Dopłata w Miesiącu': 'sum',
            'Zysk': 'last',
            'Dokupione Aktywa': lambda x: ", ".join(set([str(item) for item in x if pd.notnull(item)]))
        }).reset_index()

        # Skumulowana wartość dopłat + zysk
        df_grouped['Skumulowane Dopłaty'] = df_grouped['Dopłata w Miesiącu'].cumsum()
        df_grouped['Skumulowana Wartość (Dopłaty + Zysk)'] = df_grouped['Skumulowane Dopłaty'] + df_grouped['Zysk']

        fig = go.Figure()

        # Słupki skumulowane (Dopłaty + Zysk)
        fig.add_trace(go.Bar(
            x=df_grouped['Okres'],
            y=df_grouped['Skumulowana Wartość (Dopłaty + Zysk)'],
            name='Skumulowane (Dopłaty + Zysk)',
            marker_color='#f59e0b',
            opacity=0.75,
            text=df_grouped['Dokupione Aktywa'],
            hovertemplate="<b>Okres: %{x}</b><br>Suma (Dopłaty+Zysk): %{y:,.2f} PLN<br>Dokupiono aktywa: %{text}<extra></extra>"
        ))

        # Linia całkowitej wartości konta
        fig.add_trace(go.Scatter(
            x=df_grouped['Okres'],
            y=df_grouped['Wartość Konta'],
            name='Łączna Wartość Konta',
            mode='lines+markers',
            line=dict(color=kolor_glowny, width=4),
            marker=dict(size=10)
        ))

        fig.update_layout(
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            xaxis=dict(title="Okres"),
            yaxis=dict(title="Wartość w PLN", showgrid=True),
            legend=dict(orientation="h", y=1.15),
            margin=dict(l=20, r=20, t=30, b=20)
        )

        st.plotly_chart(fig, use_container_width=True)
        
        # --- ROZWIJANA SEKCJIA Z HISTORIĄ I PRZEKROJEM ---
        with st.expander(f"📜 Pokaż szczegółową historię i przekrój aktywów dla {nazwa_konta}"):
            st.markdown("### 🔍 Przekrój Aktywów i Filtrowanie")
            
            df_tab = pd.DataFrame(dane_tabeli)
            if not df_tab.empty:
                kat_list = ["Wszystkie"] + list(df_tab["Typ"].unique())
                wybrana_kat = st.selectbox("Filtruj wg typu aktywa:", kat_list, key=f"filter_{nazwa_konta}")
                
                if wybrana_kat != "Wszystkie":
                    df_tab_filtered = df_tab[df_tab["Typ"] == wybrana_kat]
                else:
                    df_tab_filtered = df_tab
                
                st.dataframe(df_tab_filtered.drop(columns=["Wartość_raw", "Zysk_raw"]), use_container_width=True, hide_index=True)
            
            st.markdown("<br>", unsafe_allow_html=True)
            st.markdown("### 🏛️ Rejestr Transakcji i Dopłat")
            st.dataframe(df_konta.sort_values(by="Data", ascending=False)[["Data", "Wartość Konta", "Dopłata w Miesiącu", "Zysk", "Dokupione Aktywa"]], use_container_width=True, hide_index=True)

    else:
        st.info("Brak historii wpisów dla tego konta.")

# ----------------------------------------------------
# 1. STRONA GŁÓWNA
# ----------------------------------------------------
if st.session_state.page == "🏠 Główna":
    st.markdown("""
    <div class="welcome-header">
        <h1 style="margin:0; font-size: 2.2rem; color: #1e293b;">Cześć Karol! 👋</h1>
        <p style="color: #64748b; margin-top: 5px;">Podsumowanie Twoich finansów i alokacji środków.</p>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("### 💰 Majątek i Status Kont")
    c_main, c_xtb, c_emerytura = st.columns([1.2, 1, 1])
    
    with c_main:
        st.metric("ŁĄCZNY MAJĄTEK", f"{stan['laczny_majatek']:,.2f} PLN".replace(",", " "), delta=f"{stan['laczny_zysk']:,.2f} PLN (Łączny Zysk)".replace(",", " "))
    with c_xtb:
        d_x = "+" if stan['zysk_xtb'] >= 0 else ""
        st.metric("📈 PORTFEL XTB", f"{stan['calosc_xtb']:,.2f} PLN".replace(",", " "), delta=f"{d_x}{stan['zysk_xtb']:,.2f} PLN ({stan['pct_xtb']:.1f}%)".replace(",", " "))
    with c_emerytura:
        d_e = "+" if stan['zysk_emerytura'] >= 0 else ""
        st.metric("🛡️ EMERYTURA (IKZE)", f"{stan['calosc_emerytura']:,.2f} PLN".replace(",", " "), delta=f"{d_e}{stan['zysk_emerytura']:,.2f} PLN ({stan['pct_emerytura']:.1f}%)".replace(",", " "))

    st.markdown("<br>", unsafe_allow_html=True)
    st.subheader("📊 Podział Aktywów i Poduszki Finansowej")
    
    df_main_pie = pd.DataFrame([
        {"Składnik": "Inwestycje XTB", "Wartość": stan["aktywa_xtb"]},
        {"Składnik": "Inwestycje Emerytura (IKZE)", "Wartość": stan["aktywa_emerytura"]},
        {"Składnik": "Poduszka Finansowa (Gotówka)", "Wartość": stan["laczna_gotowka"]}
    ])
    
    fig_main_pie = px.pie(df_main_pie, values="Wartość", names="Składnik", hole=0.45,
                          color="Składnik",
                          color_discrete_map={"Inwestycje XTB": "#10b981", "Inwestycje Emerytura (IKZE)": "#3b82f6", "Poduszka Finansowa (Gotówka)": "#f59e0b"})
    fig_main_pie.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
    st.plotly_chart(fig_main_pie, use_container_width=True)
    
    st.markdown("<br><hr style='border-color: #e2ded5;'><br>", unsafe_allow_html=True)
    st.subheader("🚀 Przejdź do szczegółów portfela:")
    col_card1, col_card2 = st.columns(2)
    
    with col_card1:
        st.markdown(f'<div class="nav-card"><h2>📈 PORTFEL XTB</h2><p style="font-size: 1.3rem; font-weight: bold; color: #10b981;">{stan["calosc_xtb"]:,.2f} PLN</p></div>', unsafe_allow_html=True)
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("👉 Otwórz Portfel XTB", use_container_width=True):
            st.session_state.page = "📈 Portfel XTB"
            st.rerun()

    with col_card2:
        st.markdown(f'<div class="nav-card"><h2>🛡️ EMERYTURA (IKZE)</h2><p style="font-size: 1.3rem; font-weight: bold; color: #3b82f6;">{stan["calosc_emerytura"]:,.2f} PLN</p></div>', unsafe_allow_html=True)
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("👉 Otwórz Portfel Emerytura", use_container_width=True):
            st.session_state.page = "🛡️ Emerytura (IKZE)"
            st.rerun()

# ----------------------------------------------------
# 2. PORTFEL XTB
# ----------------------------------------------------
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
            fig_xtb = px.pie(pd.DataFrame(stan["tab_xtb"]), values="Wartość_raw", names="Ticker", hole=0.4)
            fig_xtb.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
            st.plotly_chart(fig_xtb, use_container_width=True)
            
    with col_info:
        st.subheader("📋 Posiadane Aktywa i Status")
        if stan["tab_xtb"]:
            st.dataframe(pd.DataFrame(stan["tab_xtb"]).drop(columns=["Wartość_raw", "Zysk_raw"]), use_container_width=True, hide_index=True)

    st.markdown("<hr style='border-color: #e2ded5;'>", unsafe_allow_html=True)
    pokaz_wykres_i_historie_konta("XTB", "#10b981", stan["tab_xtb"])

# ----------------------------------------------------
# 3. PORTFEL EMERYTURA (IKZE)
# ----------------------------------------------------
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
            fig_em = px.pie(pd.DataFrame(stan["tab_emerytura"]), values="Wartość_raw", names="Ticker", hole=0.4)
            fig_em.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
            st.plotly_chart(fig_em, use_container_width=True)
            
    with col_info:
        st.subheader("📋 Posiadane Aktywa i Status")
        if stan["tab_emerytura"]:
            st.dataframe(pd.DataFrame(stan["tab_emerytura"]).drop(columns=["Wartość_raw", "Zysk_raw"]), use_container_width=True, hide_index=True)

    st.markdown("<hr style='border-color: #e2ded5;'>", unsafe_allow_html=True)
    pokaz_wykres_i_historie_konta("Emerytura", "#3b82f6", stan["tab_emerytura"])

# ----------------------------------------------------
# 4. EDYCJA & DOPŁATY
# ----------------------------------------------------
elif st.session_state.page == "✏️ Edycja & Dopłaty":
    st.title("✏️ EDYCJA AKTYWÓW I DOKONANIE DOPŁAT")
    
    tab1, tab2 = st.tabs(["📝 Aktualizuj Aktywa", "➕ Dodaj Nowy Wpis z Dopłatą"])
    
    kategorie_opcje = ["Akcje", "ETF", "Obligacje", "Krypto", "Inne"]
    
    with tab1:
        col_x, col_m = st.columns(2)
        nowe_dane = {"xtb_gotowka": 0.0, "mbank_gotowka": 0.0, "xtb_pozycje": [], "mbank_pozycje": []}
        
        with col_x:
            st.subheader("🔴 KONTO XTB")
            nowe_dane["xtb_gotowka"] = st.number_input("XTB: Gotówka (PLN)", min_value=0.0, value=float(zapisane_dane.get("xtb_gotowka", 0.0)), key="in_x_c")
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
            st.subheader("🔵 PORTFEL EMERYTURA (IKZE)")
            nowe_dane["mbank_gotowka"] = st.number_input("Emerytura: Gotówka (PLN)", min_value=0.0, value=float(zapisane_dane.get("mbank_gotowka", 0.0)), key="in_m_c")
            for i in range(5):
                st.caption(f"Pozycja Emerytura #{i+1}")
                prev = zapisane_dane["mbank_pozycje"][i] if i < len(zapisane_dane["mbank_pozycje"]) else {"ticker": "", "sztuki": 0.0, "cena": 0.0, "typ": "ETF"}
                c1, c2, c3, c4 = st.columns(4)
                t = c1.text_input("Ticker", value=prev["ticker"], key=f"m_t_{i}").strip().upper()
                s = c2.number_input("Sztuki", min_value=0.0, value=float(prev["sztuki"]), key=f"m_s_{i}")
                p = c3.number_input("Śr. cena", min_value=0.0, value=float(prev["cena"]), key=f"m_p_{i}")
                typ = c4.selectbox("Typ", kategorie_opcje, index=kategorie_opcje.index(prev.get("typ", "ETF")), key=f"m_cat_{i}")
                nowe_dane["mbank_pozycje"].append({"ticker": t, "sztuki": s, "cena": p, "typ": typ})
                
        if st.button("💾 ZAPISZ AKTUALNE AKTYWA", use_container_width=True):
            zapisz_pozycje(nowe_dane)
            st.success("Zapisano aktywa!")
            st.rerun()

    with tab2:
        st.subheader("➕ Wpisz nową dopłatę do historii")
        c_d1, c_d2 = st.columns(2)
        data_wpisu = c_d1.date_input("📅 Data wpisu:", value=datetime.now())
        wybrane_konto = c_d2.selectbox("Konto:", ["XTB", "Emerytura"])
        
        c_d3, c_d4 = st.columns(2)
        kwota_doplata = c_d3.number_input("Dopłacona kwota (PLN):", min_value=0.0, step=100.0)
        dokupione_aktywa = c_d4.text_input("Dokupione Aktywa (rozdziel po przecinku, np. NVDA, AAPL):").strip().upper()
        
        st_aktualny = oblicz_stan_portfela(zapisane_dane)
        val_konta = st_aktualny["calosc_xtb"] if wybrane_konto == "XTB" else st_aktualny["calosc_emerytura"]
        zysk_konta = st_aktualny["zysk_xtb"] if wybrane_konto == "XTB" else st_aktualny["zysk_emerytura"]
        
        st.info(f"Wprowadzana wartość końcowa konta {wybrane_konto}: **{val_konta:,.2f} PLN** | Całkowity Zysk: **{zysk_konta:,.2f} PLN**")
        
        if st.button("📈 ZAPISZ DOPŁATĘ DO HISTORII", use_container_width=True):
            zapisz_wpis_historii(data_wpisu, wybrane_konto, val_konta, kwota_doplata, zysk_konta, dokupione_aktywa)
            st.success(f"Dodano wpis dla {wybrane_konto}!")
            st.rerun()
