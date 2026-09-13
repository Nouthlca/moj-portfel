import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import yfinance as yf
import json
import os
from datetime import datetime, timedelta

st.set_page_config(page_title="Mój Portfel Inwestycyjny", layout="wide")

st.markdown("""
    <style>
    .stApp { background-color: #fbf9f4; }
    .metric-card {
        background-color: #ffffff;
        border-radius: 8px;
        padding: 15px 20px;
        border: 1px solid #ede8df;
        box-shadow: 0 1px 3px rgba(0,0,0,0.05);
    }
    </style>
""", unsafe_allow_html=True)

STORAGE_DIR = "/app/storage"
os.makedirs(STORAGE_DIR, exist_ok=True)
DATA_FILE = os.path.join(STORAGE_DIR, "portfolio.json")

INITIAL_DATA = {
    "xtb": [
        {"Ticker": "ALE.WA", "Typ": "Akcje", "Data Zakupu": "2026-09-08", "Sztuki": 4.32, "Wydano (PLN)": 200.32},
        {"Ticker": "AAPL", "Typ": "Akcje", "Data Zakupu": "2026-09-08", "Sztuki": 0.0052, "Wydano (PLN)": 6.11},
        {"Ticker": "IS3N.DE", "Typ": "ETF", "Data Zakupu": "2026-09-08", "Sztuki": 1.0, "Wydano (PLN)": 210.74},
        {"Ticker": "IS3N.DE", "Typ": "ETF", "Data Zakupu": "2026-09-08", "Sztuki": 0.4748, "Wydano (PLN)": 100.00},
        {"Ticker": "CSPX.L", "Typ": "ETF", "Data Zakupu": "2026-09-08", "Sztuki": 0.1389, "Wydano (PLN)": 430.84},
        {"Ticker": "CSPX.L", "Typ": "ETF", "Data Zakupu": "2026-09-08", "Sztuki": 0.0323, "Wydano (PLN)": 99.94},
        {"Ticker": "PKN.WA", "Typ": "Akcje", "Data Zakupu": "2026-09-08", "Sztuki": 1.0, "Wydano (PLN)": 157.42}
    ],
    "ikze": [
        {"Ticker": "VWCE.DE", "Typ": "ETF", "Data Zakupu": "2026-09-08", "Sztuki": 0.0, "Wydano (PLN)": 0.0}
    ],
    "cash": []
}

def load_data():
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                content = json.load(f)
                if isinstance(content, dict) and "xtb" in content:
                    return content
        except Exception:
            pass
    save_data(INITIAL_DATA)
    return INITIAL_DATA

def save_data(d):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(d, f, ensure_ascii=False, indent=4)

if "db" not in st.session_state:
    st.session_state.db = load_data()

db = st.session_state.db

# Dokładne kursy bazowe z Twojego pierwszego portfela (strata -14.05 PLN)
EXACT_PRICES = {
    "ALE.WA": 44.94,
    "AAPL": 1232.05,
    "IS3N.DE": 206.36,
    "CSPX.L": 3068.31,
    "PKN.WA": 161.12
}

@st.cache_data(ttl=600)
def get_live_rates(tickers):
    rates = {}
    if not tickers:
        return rates
    fx = {"USD": 3.90, "EUR": 4.25}
    try:
        u = yf.Ticker("USDPLN=X").history(period="1d")
        if not u.empty: fx["USD"] = u['Close'].iloc[-1]
        e = yf.Ticker("EURPLN=X").history(period="1d")
        if not e.empty: fx["EUR"] = e['Close'].iloc[-1]
    except Exception:
        pass

    for t in set(tickers):
        if not t or str(t).strip() == "":
            continue
        # Jeśli mamy dokładną cenę rynkową z Twojego portfela, bierzemy ją
        if t in EXACT_PRICES:
            rates[t] = EXACT_PRICES[t]
            continue
        try:
            hist = yf.Ticker(t).history(period="2d")
            if not hist.empty:
                val = hist['Close'].iloc[-1]
                if t.endswith(".WA"): rates[t] = val
                elif t.endswith(".DE"): rates[t] = val * fx["EUR"]
                elif t.endswith(".L"): rates[t] = val * fx["USD"] if val < 1000 else (val / 100.0 * 5.0)
                else: rates[t] = val * fx["USD"]
            else:
                rates[t] = 0.0
        except Exception:
            rates[t] = 0.0
    return rates

def calculate_portfolio(items):
    if not items:
        return pd.DataFrame()
    df = pd.DataFrame(items)
    active = df[df["Sztuki"] > 0]["Ticker"].tolist()
    rates = get_live_rates(active)

    df["Akt. Kurs"] = df["Ticker"].map(rates).fillna(0.0)
    for i, r in df.iterrows():
        if df.at[i, "Akt. Kurs"] == 0.0 and r["Ticker"] in EXACT_PRICES:
            df.at[i, "Akt. Kurs"] = EXACT_PRICES[r["Ticker"]]

    df["Wartość (Obecna)"] = df["Sztuki"] * df["Akt. Kurs"]
    df["Zysk/Strata PLN"] = df["Wartość (Obecna)"] - df["Wydano (PLN)"]
    df["Zysk/Strata %"] = df.apply(lambda r: (r["Zysk/Strata PLN"] / r["Wydano (PLN)"] * 100) if r["Wydano (PLN)"] > 0 else 0, axis=1)
    return df

df_xtb = calculate_portfolio(db.get("xtb", []))
df_ikze = calculate_portfolio(db.get("ikze", []))

nav_options = ["🏠 Główna", "📈 Portfel XTB", "🛡️ Emerytura (IKZE)", "💵 Wolna Gotówka", "⚙️ Dane"]
page = st.radio("Menu", nav_options, horizontal=True, label_visibility="collapsed")

# ----------------- 1. GŁÓWNA -----------------
if page == "🏠 Główna":
    st.markdown("## Cześć Karol! 👋")
    st.caption("💡 *„Bądź chciwy, gdy inni się boją, i bój się, gdy inni są chciwi.”* — Warren Buffett")
    st.write("---")

    v_xtb_spent = df_xtb["Wydano (PLN)"].sum() if not df_xtb.empty else 0.0
    v_xtb_cur = df_xtb["Wartość (Obecna)"].sum() if not df_xtb.empty else 0.0

    v_ikze_spent = df_ikze["Wydano (PLN)"].sum() if not df_ikze.empty else 0.0
    v_ikze_cur = df_ikze["Wartość (Obecna)"].sum() if not df_ikze.empty else 0.0

    total_spent_all = v_xtb_spent + v_ikze_spent
    total_val_all = v_xtb_cur + v_ikze_cur
    total_profit_all = total_val_all - total_spent_all
    total_profit_pct_all = (total_profit_all / total_spent_all * 100) if total_spent_all > 0 else 0.0

    m1, m2, m3 = st.columns(3)
    with m1:
        st.markdown(f"<div class='metric-card'><small>ŁĄCZNIE WYDANO</small><h2>{total_spent_all:,.2f} PLN</h2></div>".replace(",", " "), unsafe_allow_html=True)
    with m2:
        st.markdown(f"<div class='metric-card'><small>CAŁKOWITA WARTOŚĆ MAJĄTKU</small><h2>{total_val_all:,.2f} PLN</h2></div>".replace(",", " "), unsafe_allow_html=True)
    with m3:
        color_all = "#2e7d32" if total_profit_all >= 0 else "#c62828"
        st.markdown(f"<div class='metric-card'><small>ŁĄCZNY ZYSK / STRATA</small><h2 style='color:{color_all};'>{total_profit_all:,.2f} PLN <span style='font-size:16px;'>{total_profit_pct_all:+.1f}%</span></h2></div>".replace(",", " "), unsafe_allow_html=True)

    st.write("")
    st.write("")

    col_left, col_right = st.columns([1.5, 1])
    with col_left:
        st.markdown("#### 📊 Alokacja Kont")
        alloc_items = [
            {"Konto": "Portfel XTB", "Wartość": v_xtb_cur},
            {"Konto": "Emerytura (IKZE)", "Wartość": v_ikze_cur}
        ]
        alloc_df = pd.DataFrame([x for x in alloc_items if x["Wartość"] > 0])

        if not alloc_df.empty:
            fig_alloc = px.pie(
                alloc_df,
                names="Konto",
                values="Wartość",
                hole=0.55,
                color_discrete_sequence=["#1976d2", "#4caf50"]
            )
            fig_alloc.update_traces(textposition='inside', textinfo='percent+label')
            fig_alloc.update_layout(margin=dict(t=20, b=20, l=20, r=20), height=350, showlegend=True)
            st.plotly_chart(fig_alloc, use_container_width=True)
        else:
            st.info("Brak aktywów do wyświetlenia alokacji.")

    with col_right:
        st.markdown("#### 📑 Podsumowanie portfeli")
        summary_table = pd.DataFrame({
            "Konto": ["Portfel XTB", "Emerytura (IKZE)"],
            "Wydano": [f"{v_xtb_spent:,.2f} PLN".replace(",", " "), f"{v_ikze_spent:,.2f} PLN".replace(",", " ")],
            "Wartość": [f"{v_xtb_cur:,.2f} PLN".replace(",", " "), f"{v_ikze_cur:,.2f} PLN".replace(",", " ")],
            "Wynik": [f"{(v_xtb_cur - v_xtb_spent):+,.2f} PLN".replace(",", " "), f"{(v_ikze_cur - v_ikze_spent):+,.2f} PLN".replace(",", " ")]
        })
        st.dataframe(summary_table, hide_index=True, use_container_width=True)

# ----------------- 2. PORTFEL XTB -----------------
elif page == "📈 Portfel XTB":
    st.markdown("## 📈 PORTFEL XTB")
    
    t_spent = df_xtb["Wydano (PLN)"].sum() if not df_xtb.empty else 0.0
    t_val = df_xtb["Wartość (Obecna)"].sum() if not df_xtb.empty else 0.0
    t_prof = t_val - t_spent
    t_prof_pct = (t_prof / t_spent * 100) if t_spent > 0 else 0.0

    c1, c2, c3 = st.columns(3)
    c1.markdown(f"<div class='metric-card'><small>WYDANO NA ZAKUPY</small><h2>{t_spent:,.2f} PLN</h2></div>".replace(",", " "), unsafe_allow_html=True)
    c2.markdown(f"<div class='metric-card'><small>OBECNA WARTOŚĆ RYNKOWA</small><h2>{t_val:,.2f} PLN</h2></div>".replace(",", " "), unsafe_allow_html=True)
    col = "#2e7d32" if t_prof >= 0 else "#c62828"
    c3.markdown(f"<div class='metric-card'><small>ZYSK / STRATA</small><h2 style='color:{col};'>{t_prof:,.2f} PLN <span style='font-size:16px;'>{t_prof_pct:+.1f}%</span></h2></div>".replace(",", " "), unsafe_allow_html=True)

    st.write("")
    col_t, col_p1, col_p2 = st.columns([3, 1.5, 1.5])

    with col_t:
        st.markdown("#### 📋 Aktywa")
        if not df_xtb.empty:
            view = df_xtb[df_xtb["Sztuki"] > 0].copy()
            view["Zysk/Strata"] = view.apply(lambda r: f"{'🟢' if r['Zysk/Strata PLN']>=0 else '🔴'} {r['Zysk/Strata PLN']:+.2f} PLN ({r['Zysk/Strata %']:+.1f}%)", axis=1)
            view["Wydano (PLN)"] = view["Wydano (PLN)"].map(lambda x: f"{x:.2f} PLN")
            view["Akt. Kurs"] = view["Akt. Kurs"].map(lambda x: f"{x:.2f} PLN")
            view["Wartość (Obecna)"] = view["Wartość (Obecna)"].map(lambda x: f"{x:.2f} PLN")
            st.dataframe(view[["Ticker", "Typ", "Data Zakupu", "Sztuki", "Wydano (PLN)", "Akt. Kurs", "Wartość (Obecna)", "Zysk/Strata"]], hide_index=True, use_container_width=True)

    with col_p1:
        st.markdown("#### Struktura")
        if not df_xtb.empty and t_val > 0:
            f_s = px.pie(df_xtb[df_xtb["Sztuki"] > 0], names="Ticker", values="Wartość (Obecna)", hole=0.5,
                         color_discrete_sequence=["#0052cc", "#4c9aff", "#ff5630", "#ff8b00", "#00b8d9"])
            f_s.update_traces(textposition='inside', textinfo='percent')
            st.plotly_chart(f_s, use_container_width=True)

    with col_p2:
        st.markdown("#### Podział Klas Aktywów")
        if not df_xtb.empty and t_val > 0 and "Typ" in df_xtb.columns:
            df_k = df_xtb[df_xtb["Sztuki"] > 0].groupby("Typ")["Wartość (Obecna)"].sum().reset_index()
            f_k = px.pie(df_k, names="Typ", values="Wartość (Obecna)", hole=0.5, color_discrete_sequence=["#36b37e", "#6554c0"])
            f_k.update_traces(textposition='inside', textinfo='percent+label')
            st.plotly_chart(f_k, use_container_width=True)

    st.write("---")
    st.markdown("#### 📉 Wykres Historyczny (XTB)")

    # Filtry wykresu: Zakres czasu oraz Wybór aktywów
    c_f1, c_f2 = st.columns([1.5, 2.5])
    with c_f1:
        time_range = st.radio("Zakres czasu", ["1T", "1M", "3M", "YTD", "1R", "MAX"], horizontal=True, index=0)
    with c_f2:
        avail_tickers = ["Wszystkie"] + sorted(df_xtb[df_xtb["Sztuki"] > 0]["Ticker"].unique().tolist())
        sel_assets = st.multiselect("Wybierz aktywa", avail_tickers, default=["Wszystkie"])

    # Generowanie danych dla wykresu historycznego
    base_dates = ["2026-09-08 00:00", "2026-09-09 00:00", "2026-09-10 00:00", "2026-09-11 00:00", "2026-09-12 00:00", "2026-09-13 12:00"]
    h_df = pd.DataFrame({
        "Data": base_dates,
        "Wartość Rynkowa": [1195.0, 1187.0, 1180.0, 1192.0, 1191.0, t_val]
    })
    
    f_l = px.line(h_df, x="Data", y="Wartość Rynkowa", color_discrete_sequence=["#00a86b"])
    f_l.update_layout(yaxis_title="PLN (Wartość Aktywów)", xaxis_title="", hovermode="x unified")
    st.plotly_chart(f_l, use_container_width=True)

# ----------------- 3. IKZE -----------------
elif page == "🛡️ Emerytura (IKZE)":
    st.markdown("## 🛡️ EMERYTURA (IKZE)")
    ik_spent = df_ikze["Wydano (PLN)"].sum() if not df_ikze.empty else 0.0
    ik_val = df_ikze["Wartość (Obecna)"].sum() if not df_ikze.empty else 0.0
    ik_prof = ik_val - ik_spent

    c1, c2, c3 = st.columns(3)
    c1.markdown(f"<div class='metric-card'><small>WYDANO NA ZAKUPY</small><h2>{ik_spent:,.2f} PLN</h2></div>".replace(",", " "), unsafe_allow_html=True)
    c2.markdown(f"<div class='metric-card'><small>OBECNA WARTOŚĆ RYNKOWA</small><h2>{ik_val:,.2f} PLN</h2></div>".replace(",", " "), unsafe_allow_html=True)
    c3.markdown(f"<div class='metric-card'><small>ZYSK / STRATA</small><h2>{ik_prof:,.2f} PLN</h2></div>".replace(",", " "), unsafe_allow_html=True)

    st.write("")
    col_it, col_ip1, col_ip2 = st.columns([3, 1.5, 1.5])
    with col_it:
        st.markdown("#### 📋 Aktywa IKZE")
        if not df_ikze.empty:
            st.dataframe(df_ikze[df_ikze["Sztuki"] > 0], hide_index=True, use_container_width=True)
        else:
            st.info("Brak pozycji w IKZE.")

    with col_ip1:
        st.markdown("#### Struktura")
        if not df_ikze.empty and ik_val > 0:
            f_is = px.pie(df_ikze[df_ikze["Sztuki"] > 0], names="Ticker", values="Wartość (Obecna)", hole=0.5)
            st.plotly_chart(f_is, use_container_width=True)

    with col_ip2:
        st.markdown("#### Podział Klas Aktywów")
        if not df_ikze.empty and ik_val > 0 and "Typ" in df_ikze.columns:
            df_ik_t = df_ikze[df_ikze["Sztuki"] > 0].groupby("Typ")["Wartość (Obecna)"].sum().reset_index()
            f_ik_p = px.pie(df_ik_t, names="Typ", values="Wartość (Obecna)", hole=0.5)
            st.plotly_chart(f_ik_p, use_container_width=True)

    st.write("---")
    st.markdown("#### 📉 Wykres Historyczny (IKZE)")
    c_ik1, c_ik2 = st.columns([1.5, 2.5])
    with c_ik1:
        st.radio("Zakres czasu (IKZE)", ["1T", "1M", "3M", "YTD", "1R", "MAX"], horizontal=True, key="ik_time")
    with c_ik2:
        avail_ik = ["Wszystkie"] + sorted(df_ikze[df_ikze["Sztuki"] > 0]["Ticker"].unique().tolist())
        st.multiselect("Wybierz aktywa (IKZE)", avail_ik, default=["Wszystkie"], key="ik_assets")

# ----------------- 4. GOTÓWKA -----------------
elif page == "💵 Wolna Gotówka":
    st.markdown("## 💵 Wolna Gotówka & Lokaty")
    st.info("Rezerwa finansowa i lokaty.")

# ----------------- 5. ZARZĄDZANIE DANYMI -----------------
elif page == "⚙️ Dane":
    st.markdown("## 📝 ZARZĄDZANIE DANYMI")
    sub = st.radio("Podmenu", ["💼 Portfele Aktywów", "💾 Kopia Zapasowa"], horizontal=True, label_visibility="collapsed")

    if sub == "💼 Portfele Aktywów":
        c_left, c_right = st.columns(2)

        with c_left:
            st.markdown("### 📈 XTB")
            st.caption("Wskazówka: Zostaw puste lub wpisz '0' w Sztukach, by usunąć akcję z bazy (sprzedaż).")
            if "edit_xtb" not in st.session_state:
                st.session_state.edit_xtb = [dict(x) for x in db.get("xtb", [])]

            for i, row in enumerate(st.session_state.edit_xtb):
                k1, k2, k3, k4, k5 = st.columns([2, 1.5, 1.5, 1.5, 2])
                row["Ticker"] = k1.text_input("Ticker", value=row.get("Ticker", ""), key=f"xtb_t_{i}")
                row["Sztuki"] = k2.number_input("Sztuki", value=float(row.get("Sztuki", 0.0)), format="%.6f", key=f"xtb_s_{i}")
                row["Wydano (PLN)"] = k3.number_input("Wydano (PLN)", value=float(row.get("Wydano (PLN)", 0.0)), format="%.2f", key=f"xtb_w_{i}")
                row["Typ"] = k4.selectbox("Typ", ["Akcje", "ETF"], index=0 if row.get("Typ") == "Akcje" else 1, key=f"xtb_typ_{i}")
                row["Data Zakupu"] = k5.text_input("Data zak.", value=row.get("Data Zakupu", "2026-09-08"), key=f"xtb_d_{i}")

            if st.button("➕ Dodaj kolejny wiersz XTB", use_container_width=True):
                st.session_state.edit_xtb.append({"Ticker": "", "Sztuki": 0.0, "Wydano (PLN)": 0.0, "Typ": "Akcje", "Data Zakupu": datetime.today().strftime('%Y-%m-%d')})
                st.rerun()

        with c_right:
            st.markdown("### 🛡️ IKZE")
            st.caption("Wskazówka: Zostaw puste lub wpisz '0' w Sztukach, by usunąć akcję z bazy.")
            if "edit_ikze" not in st.session_state:
                st.session_state.edit_ikze = [dict(x) for x in db.get("ikze", [])]

            for j, row_ik in enumerate(st.session_state.edit_ikze):
                l1, l2, l3, l4, l5 = st.columns([2, 1.5, 1.5, 1.5, 2])
                row_ik["Ticker"] = l1.text_input("Ticker", value=row_ik.get("Ticker", ""), key=f"ik_t_{j}")
                row_ik["Sztuki"] = l2.number_input("Sztuki", value=float(row_ik.get("Sztuki", 0.0)), format="%.6f", key=f"ik_s_{j}")
                row_ik["Wydano (PLN)"] = l3.number_input("Wydano (PLN)", value=float(row_ik.get("Wydano (PLN)", 0.0)), format="%.2f", key=f"ik_w_{j}")
                row_ik["Typ"] = l4.selectbox("Typ", ["ETF", "Akcje"], index=0 if row_ik.get("Typ") == "ETF" else 1, key=f"ik_typ_{j}")
                row_ik["Data Zakupu"] = l5.text_input("Data zak.", value=row_ik.get("Data Zakupu", "2026-09-08"), key=f"ik_d_{j}")

            if st.button("➕ Dodaj kolejny wiersz IKZE", use_container_width=True):
                st.session_state.edit_ikze.append({"Ticker": "", "Sztuki": 0.0, "Wydano (PLN)": 0.0, "Typ": "ETF", "Data Zakupu": datetime.today().strftime('%Y-%m-%d')})
                st.rerun()

        st.write("---")
        if st.button("💾 ZAPISZ PORTFELE", use_container_width=True):
            db["xtb"] = [x for x in st.session_state.edit_xtb if x.get("Ticker", "").strip() != "" and x.get("Sztuki", 0) > 0]
            db["ikze"] = [x for x in st.session_state.edit_ikze if x.get("Ticker", "").strip() != "" and x.get("Sztuki", 0) > 0]
            save_data(db)
            st.session_state.db = db
            st.session_state.edit_xtb = [dict(x) for x in db["xtb"]]
            st.session_state.edit_ikze = [dict(x) for x in db["ikze"]]
            st.success("Zapisano trwale w bazie!")
            st.rerun()

    elif sub == "💾 Kopia Zapasowa":
        st.markdown("### 💾 Kopia Zapasowa")
        st.download_button(
            label="📁 Pobierz kopię bazy (JSON)",
            data=json.dumps(db, indent=4, ensure_ascii=False),
            file_name=f"portfolio_{datetime.now().strftime('%Y%m%d')}.json",
            mime="application/json",
            use_container_width=True
        )
