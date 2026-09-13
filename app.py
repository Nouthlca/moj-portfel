import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import yfinance as yf
import json
import os
from datetime import datetime

st.set_page_config(page_title="Portfel Inwestycyjny", layout="wide")

DATA_FILE = "/app/data/portfolio.json"
BACKUP_DIR = "/app/data/backups"
os.makedirs(os.path.dirname(DATA_FILE), exist_ok=True)
os.makedirs(BACKUP_DIR, exist_ok=True)

# ----------------- DANE I CACHE -----------------
def load_data():
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {"xtb": [], "ikze": [], "cash": [], "doplaty": []}

def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

@st.cache_data(ttl=300)
def get_live_data(tickers):
    prices = {}
    if not tickers:
        return prices
    for t in set(tickers):
        try:
            # Kursy walut i aktywów przez yfinance
            ticker_obj = yf.Ticker(t)
            hist = ticker_obj.history(period="2d")
            if not hist.empty:
                prices[t] = hist['Close'].iloc[-1]
            else:
                prices[t] = 0.0
        except Exception:
            prices[t] = 0.0
    return prices

data = load_data()

# ----------------- MENU GÓRNE -----------------
tabs = ["🏠 Główna", "📈 Portfel XTB", "🛡️ Emerytura (IKZE)", "💵 Wolna Gotówka", "⚙️ Dane"]
selected_tab = st.radio("Nawigacja", tabs, horizontal=True, label_visibility="collapsed")

# ----------------- PRZETWARZANIE DANYCH -----------------
def process_portfolio(raw_items):
    if not raw_items:
        return pd.DataFrame(columns=[
            "Ticker", "Typ", "Data Zakupu", "Sztuki", "Wydano (PLN)",
            "Akt. Kurs", "Wartość (Obecna)", "Zysk/Strata", "Zysk/Strata %"
        ])
    
    df = pd.DataFrame(raw_items)
    tickers = df["Ticker"].dropna().unique().tolist()
    rates = get_live_data(tickers)
    
    df["Akt. Kurs"] = df["Ticker"].map(rates).fillna(0.0)
    df["Wartość (Obecna)"] = df["Sztuki"] * df["Akt. Kurs"]
    df["Zysk/Strata"] = df["Wartość (Obecna)"] - df["Wydano (PLN)"]
    df["Zysk/Strata %"] = (df["Zysk/Strata"] / df["Wydano (PLN)"].replace(0, 1)) * 100
    return df

df_xtb = process_portfolio(data.get("xtb", []))
df_ikze = process_portfolio(data.get("ikze", []))

# ----------------- 1. STRONA GŁÓWNA -----------------
if selected_tab == "🏠 Główna":
    st.markdown("## Cześć Karol! 👋")
    st.caption("💡 *„Bądź chciwy, gdy inni się boją, i bój się, gdy inni są chciwi.”* — Warren Buffett")
    st.write("---")
    
    val_xtb = df_xtb["Wartość (Obecna)"].sum() if not df_xtb.empty else 0.0
    val_ikze = df_ikze["Wartość (Obecna)"].sum() if not df_ikze.empty else 0.0
    total_val = val_xtb + val_ikze

    st.markdown("#### 📊 Alokacja Kont")
    if total_val > 0:
        alloc_data = pd.DataFrame({
            "Konto": ["Portfel XTB", "Emerytura (IKZE)"],
            "Wartość": [val_xtb, val_ikze]
        })
        fig_alloc = px.pie(alloc_data, names="Konto", values="Wartość", hole=0.55,
                           color_discrete_sequence=["#0066cc", "#00cc96"])
        fig_alloc.update_traces(textposition='inside', textinfo='percent+label')
        st.plotly_chart(fig_alloc, use_container_width=True)
    else:
        st.info("Brak aktywnych pozycji w portfelach do wyświetlenia alokacji.")

# ----------------- 2. PORTFEL XTB -----------------
elif selected_tab == "📈 Portfel XTB":
    st.markdown("## 📈 PORTFEL XTB")
    
    wydano = df_xtb["Wydano (PLN)"].sum() if not df_xtb.empty else 0.0
    wartosc = df_xtb["Wartość (Obecna)"].sum() if not df_xtb.empty else 0.0
    zysk = wartosc - wydano
    zysk_proc = (zysk / wydano * 100) if wydano > 0 else 0.0
    
    k1, k2, k3 = st.columns(3)
    k1.metric("WYDANO NA ZAKUPY", f"{wydano:,.2f} PLN".replace(",", " "))
    k2.metric("OBECNA WARTOŚĆ RYNKOWA", f"{wartosc:,.2f} PLN".replace(",", " "))
    k3.metric("ZYSK / STRATA", f"{zysk:,.2f} PLN", f"{zysk_proc:+.1f}%")
    st.write("---")
    
    c_table, c_pie1, c_pie2 = st.columns([3, 1.5, 1.5])
    
    with c_table:
        st.markdown("#### 📋 Aktywa")
        if not df_xtb.empty:
            df_disp = df_xtb.copy()
            df_disp["Wydano (PLN)"] = df_disp["Wydano (PLN)"].map(lambda x: f"{x:.2f} PLN")
            df_disp["Akt. Kurs"] = df_disp["Akt. Kurs"].map(lambda x: f"{x:.2f} PLN")
            df_disp["Wartość (Obecna)"] = df_disp["Wartość (Obecna)"].map(lambda x: f"{x:.2f} PLN")
            df_disp["Zysk/Strata"] = df_disp.apply(lambda r: f"{r['Zysk/Strata']:+.2f} PLN ({r['Zysk/Strata %']:+.1f}%)", axis=1)
            st.dataframe(df_disp.drop(columns=["Zysk/Strata %"]), hide_index=True, use_container_width=True)
        else:
            st.info("Brak wpisanych aktywów w portfelu XTB.")
            
    with c_pie1:
        st.markdown("#### Struktura")
        if not df_xtb.empty and wartosc > 0:
            fig_struct = px.pie(df_xtb, names="Ticker", values="Wartość (Obecna)", hole=0.5)
            fig_struct.update_traces(textposition='inside', textinfo='percent')
            st.plotly_chart(fig_struct, use_container_width=True)
            
    with c_pie2:
        st.markdown("#### Podział Klas Aktywów")
        if not df_xtb.empty and wartosc > 0 and "Typ" in df_xtb.columns:
            df_typ = df_xtb.groupby("Typ")["Wartość (Obecna)"].sum().reset_index()
            fig_kat = px.pie(df_typ, names="Typ", values="Wartość (Obecna)", hole=0.5,
                             color_discrete_sequence=px.colors.qualitative.Set2)
            fig_kat.update_traces(textposition='inside', textinfo='percent+label')
            st.plotly_chart(fig_kat, use_container_width=True)

    st.write("---")
    st.markdown("#### 📉 Wykres Historyczny (XTB)")
    if not df_xtb.empty:
        # Przykładowy przebieg wartości
        chart_data = pd.DataFrame({
            "Data": pd.date_range(start="2026-09-08", periods=5),
            "Wartość Rynkowa": [1195, 1187, 1180, 1192, wartosc if wartosc > 0 else 1191.32]
        })
        fig_hist = px.line(chart_data, x="Data", y="Wartość Rynkowa", color_discrete_sequence=["#00aa66"])
        fig_hist.update_layout(yaxis_title="PLN (Wartość Aktywów)", xaxis_title="")
        st.plotly_chart(fig_hist, use_container_width=True)

# ----------------- 3. EMERYTURA (IKZE) -----------------
elif selected_tab == "🛡️ Emerytura (IKZE)":
    st.markdown("## 🛡️ EMERYTURA (IKZE)")
    
    wydano_ikze = df_ikze["Wydano (PLN)"].sum() if not df_ikze.empty else 0.0
    wartosc_ikze = df_ikze["Wartość (Obecna)"].sum() if not df_ikze.empty else 0.0
    zysk_ikze = wartosc_ikze - wydano_ikze
    zysk_ikze_proc = (zysk_ikze / wydano_ikze * 100) if wydano_ikze > 0 else 0.0
    
    k1, k2, k3 = st.columns(3)
    k1.metric("WYDANO NA ZAKUPY", f"{wydano_ikze:,.2f} PLN".replace(",", " "))
    k2.metric("OBECNA WARTOŚĆ RYNKOWA", f"{wartosc_ikze:,.2f} PLN".replace(",", " "))
    k3.metric("ZYSK / STRATA", f"{zysk_ikze:,.2f} PLN", f"{zysk_ikze_proc:+.1f}%")
    st.write("---")
    
    c_table, c_pie1, c_pie2 = st.columns([3, 1.5, 1.5])
    
    with c_table:
        st.markdown("#### 📋 Aktywa IKZE")
        if not df_ikze.empty:
            df_disp = df_ikze.copy()
            df_disp["Wydano (PLN)"] = df_disp["Wydano (PLN)"].map(lambda x: f"{x:.2f} PLN")
            df_disp["Akt. Kurs"] = df_disp["Akt. Kurs"].map(lambda x: f"{x:.2f} PLN")
            df_disp["Wartość (Obecna)"] = df_disp["Wartość (Obecna)"].map(lambda x: f"{x:.2f} PLN")
            df_disp["Zysk/Strata"] = df_disp.apply(lambda r: f"{r['Zysk/Strata']:+.2f} PLN ({r['Zysk/Strata %']:+.1f}%)", axis=1)
            st.dataframe(df_disp.drop(columns=["Zysk/Strata %"]), hide_index=True, use_container_width=True)
        else:
            st.info("Brak wpisanych aktywów w portfelu IKZE.")
            
    with c_pie1:
        st.markdown("#### Struktura")
        if not df_ikze.empty and wartosc_ikze > 0:
            fig_struct = px.pie(df_ikze, names="Ticker", values="Wartość (Obecna)", hole=0.5)
            fig_struct.update_traces(textposition='inside', textinfo='percent')
            st.plotly_chart(fig_struct, use_container_width=True)
            
    with c_pie2:
        st.markdown("#### Podział Klas Aktywów")
        if not df_ikze.empty and wartosc_ikze > 0 and "Typ" in df_ikze.columns:
            df_typ = df_ikze.groupby("Typ")["Wartość (Obecna)"].sum().reset_index()
            fig_kat = px.pie(df_typ, names="Typ", values="Wartość (Obecna)", hole=0.5,
                             color_discrete_sequence=px.colors.qualitative.Safe)
            fig_kat.update_traces(textposition='inside', textinfo='percent+label')
            st.plotly_chart(fig_kat, use_container_width=True)

# ----------------- 4. WOLNA GOTÓWKA -----------------
elif selected_tab == "💵 Wolna Gotówka":
    st.markdown("## 💵 Wolna Gotówka & Lokaty")
    st.info("Zarządzaj rezerwą finansową i lokatami.")

# ----------------- 5. ZARZĄDZANIE DANYMI -----------------
elif selected_tab == "⚙️ Dane":
    st.markdown("## 📝 ZARZĄDZANIE DANYMI")
    subtabs = ["💼 Portfele Aktywów", "💵 Wolna Gotówka & Lokaty", "➕ Dopłaty", "💾 Kopia Zapasowa"]
    sub_sel = st.radio("Zarządzanie", subtabs, horizontal=True, label_visibility="collapsed")
    
    if sub_sel == "💼 Portfele Aktywów":
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("### 📈 XTB")
            st.caption("Wskazówka: Zostaw puste lub wpisz '0' w Sztukach, by usunąć akcję z bazy.")
            raw_xtb = data.get("xtb", [])
            df_edit_xtb = pd.DataFrame(raw_xtb if raw_xtb else [{"Ticker": "", "Sztuki": 0.0, "Wydano (PLN)": 0.0, "Typ": "Akcje", "Data Zakupu": datetime.today().strftime('%Y-%m-%d')}])
            edited_xtb = st.data_editor(df_edit_xtb, num_rows="dynamic", key="editor_xtb", use_container_width=True)
            
        with col2:
            st.markdown("### 🛡️ IKZE")
            st.caption("Wskazówka: Zostaw puste lub wpisz '0' w Sztukach, by usunąć akcję z bazy.")
            raw_ikze = data.get("ikze", [])
            df_edit_ikze = pd.DataFrame(raw_ikze if raw_ikze else [{"Ticker": "", "Sztuki": 0.0, "Wydano (PLN)": 0.0, "Typ": "ETF", "Data Zakupu": datetime.today().strftime('%Y-%m-%d')}])
            edited_ikze = st.data_editor(df_edit_ikze, num_rows="dynamic", key="editor_ikze", use_container_width=True)
            
        if st.button("💾 ZAPISZ PORTFELE", use_container_width=True):
            clean_xtb = edited_xtb[edited_xtb["Ticker"].str.strip() != ""].to_dict(orient="records")
            clean_ikze = edited_ikze[edited_ikze["Ticker"].str.strip() != ""].to_dict(orient="records")
            data["xtb"] = clean_xtb
            data["ikze"] = clean_ikze
            save_data(data)
            st.success("Portfele zapisane pomyślnie!")
            st.rerun()

    elif sub_sel == "💾 Kopia Zapasowa":
        st.markdown("### 💾 Kopie Zapasowe")
        if st.button("📁 Utwórz pełną kopię na dysku"):
            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
            b_path = os.path.join(BACKUP_DIR, f"backup_{ts}.json")
            with open(b_path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=4)
            st.success(f"Utworzono kopię zapasową: {b_path}")
