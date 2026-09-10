import datetime
import pandas as pd
import plotly.express as px
import streamlit as st

# Konfiguracja strony
st.set_page_config(
    page_title="Mój Portfel Inwestycyjny", page_icon="📈", layout="wide"
)

# Inicjalizacja stanu sesji (przykładowe dane startowe zgodne z Twoim screenem)
if "pozycje_xtb" not in st.session_state:
  st.session_state.pozycje_xtb = pd.DataFrame([
      {
          "Ticker": "ALE.WA",
          "Typ": "Akcje",
          "Data Zakupu": datetime.date(2026, 9, 8),
          "Sztuki": 4.32,
          "Sr. Cena": 0.00,
          "Akt. Kurs": 45.00,
      }
  ])

if "doplaty_xtb" not in st.session_state:
  # Puste lub z przykładową dopłatą
  st.session_state.doplaty_xtb = pd.DataFrame(columns=["Data", "Kwota"])

# Górny pasek nawigacji (zakładki)
menu = st.radio(
    "Nawigacja",
    [
        "Główna",
        "Portfel XTB",
        "Emerytura (IKZE)",
        "Wolna Gotówka",
        "📝 Dane",
    ],
    horizontal=True,
)

# ----------------------------------------------------
# SEKCJA: DANE (Dodawanie dopłat / edycja)
# ----------------------------------------------------
if menu == "📝 Dane":
  st.subheader("Zarządzanie Danymi")

  tab1, tab2 = st.tabs(["➕ Dopłaty do Historii", "💼 Edycja Pozycji XTB"])

  with tab1:
    st.write(
        "Tutaj możesz dodać ręczne dopłaty (opcjonalnie, jeśli chcesz zasilić"
        " portfel gotówką)."
    )
    with st.form("form_doplata"):
      data_doplaty = st.date_input("Data dopłaty", datetime.date.today())
      kwota_doplaty = st.number_input("Kwota (PLN)", min_value=0.0, value=200.0)
      submit_doplata = st.form_submit_button("📈 ZAPISZ WPIS HISTORII")

      if submit_doplata:
        nowy_wpis = pd.DataFrame(
            [{"Data": data_doplaty, "Kwota": kwota_doplaty}]
        )
        st.session_state.doplaty_xtb = pd.concat(
            [st.session_state.doplaty_xtb, nowy_wpis], ignore_index=True
        )
        st.success("Dodano wpis historii!")

    if not st.session_state.doplaty_xtb.empty:
      st.write("Aktualne wpisy dopłat:")
      st.dataframe(st.session_state.doplaty_xtb, use_container_width=True)

  with tab2:
    st.write("Dodaj nową pozycję do portfela XTB:")
    with st.form("form_pozycja"):
      t_ticker = st.text_input("Ticker (np. CDR.WA)")
      t_typ = st.selectbox("Typ", ["Akcje", "ETF"])
      t_data = st.date_input("Data Zakupu", datetime.date.today())
      t_sztuki = st.number_input("Sztuki", min_value=0.01, value=1.0)
      t_cena = st.number_input("Cena zakupu / Aktualny kurs", value=50.0)
      submit_poz = st.form_submit_button("Dodaj pozycję")

      if submit_poz and t_ticker:
        nowa_akcja = pd.DataFrame([
            {
                "Ticker": t_ticker.upper(),
                "Typ": t_typ,
                "Data Zakupu": t_data,
                "Sztuki": t_sztuki,
                "Sr. Cena": 0.0,
                "Akt. Kurs": t_cena,
            }
        ])
        st.session_state.pozycje_xtb = pd.concat(
            [st.session_state.pozycje_xtb, nowa_akcja], ignore_index=True
        )
        st.success(f"Dodano {t_ticker}!")
        st.rerun()

# ----------------------------------------------------
# SEKCJA: PORTFEL XTB (Główny widok ze screena)
# ----------------------------------------------------
elif menu == "Portfel XTB":
  st.markdown("## 📈 PORTFEL XTB")

  df_pozycje = st.session_state.pozycje_xtb
  df_doplaty = st.session_state.doplaty_xtb

  # Obliczenia wartości
  if not df_pozycje.empty:
    df_pozycje["Wartość"] = df_pozycje["Sztuki"] * df_pozycje["Akt. Kurs"]
    calkowita_wartosc = df_pozycje["Wartość"].sum()
    calkowity_zysk = (
        calkowita_wartosc  # Uproszczone przy cenie zakupu 0 lub wg logiki
    )
  else:
    calkowita_wartosc = 0.0
    calkowity_zysk = 0.0

  # Górne kafelki podsumowania
  col1, col2 = st.columns(2)
  with col1:
    st.markdown("WARTOŚĆ XTB")
    st.markdown(f"### **{calkowita_wartosc:.2f} PLN**")
  with col2:
    st.markdown("ZYSK / STRATA")
    st.markdown(
        f"### **{calkowita_wartosc:.2f} PLN** <span"
        ' style="color:green;font-size:16px;">↑ 0.0%</span>',
        unsafe_allow_html=True,
    )

  st.markdown("---")
  st.markdown("### 📄 Aktywa")

  if not df_pozycje.empty:
    # Wyświetlenie tabeli aktywów w ładnym formacie
    tabela_wyswietlanie = df_pozycje.copy()
    if "Data Zakupu" in tabela_wyswietlanie.columns:
      tabela_wyswietlanie["Data Zakupu"] = pd.to_datetime(
          tabela_wyswietlanie["Data Zakupu"]
      ).dt.strftime("%Y-%m-%d")

    # Układ tabeli aktywów a obok struktura (kołowy)
    col_tabela, col_wykres = st.columns([2, 1])

    with col_tabela:
      st.dataframe(tabela_wyswietlanie, use_container_width=True)

    with col_wykres:
      st.markdown("### Struktura")
      if not df_pozycje.empty:
        fig_pie = px.pie(
            df_pozycje,
            names="Ticker",
            values="Wartość",
            hole=0.4,
            color_discrete_sequence=px.colors.sequential.RdBu,
        )
        fig_pie.update_layout(
            margin=dict(t=0, b=0, l=0, r=0),
            height=250,
            showlegend=True,
        )
        st.plotly_chart(fig_pie, use_container_width=True)
  else:
    st.info("Brak aktywów w portfelu XTB.")

  st.markdown("---")
  st.markdown("### 📈 Historia i Wzrost (XTB)")

  # --- AUTOMATYCZNA GENERACJA HISTORII (Łącząca zakupy akcji i dopłaty) ---
  daty_wszystkie = []

  if not df_pozycje.empty and "Data Zakupu" in df_pozycje.columns:
    daty_wszystkie.extend(
        pd.to_datetime(df_pozycje["Data Zakupu"]).dropna().tolist()
    )

  if not df_doplaty.empty and "Data" in df_doplaty.columns:
    daty_wszystkie.extend(
        pd.to_datetime(df_doplaty["Data"]).dropna().tolist()
    )

  # Dodaj dzisiejszy dzień, żeby wykres dochodził do nowości
  daty_wszystkie.append(pd.Timestamp(datetime.date.today()))

  if daty_wszystkie:
    min_data = min(daty_wszystkie)
    max_data = pd.Timestamp(datetime.date.today())

    # Stwórz ciąg dni od pierwszej aktywności do dzisiaj
    zakres_dni = pd.date_range(start=min_data, end=max_data)
    dane_historii = []

    for dzien in zakres_dni:
      # Wartość aktywów w danym dniu (akcje kupione w tym dniu lub wcześniej)
      wartosc_dnia = 0
      if not df_pozycje.empty:
        akcje_w_dniu = df_pozycje[
            pd.to_datetime(df_pozycje["Data Zakupu"]) <= dzien
        ]
        for _, row in akcje_w_dniu.iterrows():
          wval = row.get("Sztuki", 0) * row.get("Akt. Kurs", 0)
          wartosc_dnia += wval

      # Suma dopłat do tego dnia (jeśli jakieś były)
      doplaty_dnia = 0
      if not df_doplaty.empty:
        d_filtered = df_doplaty[pd.to_datetime(df_doplaty["Data"]) <= dzien]
        if not d_filtered.empty:
          doplaty_dnia = d_filtered["Kwota"].sum()

      # Ostateczna wartość portfela w danym dniu to wartość aktywów lub dopłat (bierzemy większą)
      calkowita_w_dniu = max(wartosc_dnia, doplaty_dnia)

      if calkowita_w_dniu > 0:
        dane_historii.append(
            {"Data": dzien, "Wartość Portfela": calkowita_w_dniu}
        )

    df_hist_final = pd.DataFrame(dane_historii)

    if not df_hist_final.empty:
      fig_hist = px.line(
          df_hist_final,
          x="Data",
          y="Wartość Portfela",
          markers=True,
          line_shape="spline",
      )
      fig_hist.update_layout(
          xaxis_title="",
          yaxis_title="Wartość (PLN)",
          margin=dict(t=10, b=10, l=0, r=0),
          height=300,
      )
      st.plotly_chart(fig_hist, use_container_width=True)
    else:
      st.info(
          "Brak wystarczających danych do wygenerowania wykresu historycznego."
      )
  else:
    st.info(
        "Brak historii wpisów. Dodaj pozycję z datą zakupu lub wpis w zakładce"
        " 📝 Dane -> ➕ Dopłaty do Historii."
    )

elif menu == "Główna":
  st.title("Strona Główna")
  st.write("Wybierz zakładkę Portfel XTB w menu powyżej.")

elif menu == "Emerytura (IKZE)":
  st.title("Portfel Emerytura (IKZE)")
  st.write("Tutaj będzie widok IKZE.")

elif menu == "Wolna Gotówka":
  st.title("Wolna Gotówka")
  st.write("Tutaj będzie widok wolnej gotówki.")
