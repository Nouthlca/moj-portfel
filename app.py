import pandas as pd
import datetime

# Załóżmy, że masz dataframe z pozycjami w portfelu (np. df_pozycji) 
# oraz dataframe z historią dopłat (np. df_historia).
# Poniżej znajduje się uniwersalna logika do wklejenia w miejscu, gdzie rysujesz wykres "Historia i Wzrost".

def przygotuj_dane_historii(df_pozycje, df_doplaty):
    # Zbierz wszystkie unikalne daty z zakupów aktywów
    daty_zakupow = []
    if not df_pozycje.empty and 'Data Zakupu' in df_pozycje.columns:
        daty_zakupow = pd.to_datetime(df_pozycje['Data Zakupu']).dropna().tolist()
    
    # Zbierz daty z dopłat
    daty_doplat = []
    if not df_doplaty.empty and 'Data' in df_doplaty.columns:
        daty_doplat = pd.to_datetime(df_doplaty['Data']).dropna().tolist()
        
    # Połącz wszystkie ważne daty + dodaj dzisiejszy dzień
    wszystkie_daty = sorted(list(set(daty_zakupow + daty_doplat + [pd.Timestamp(datetime.date.today())])))
    
    if not wszystkie_daty:
        return pd.DataFrame()

    # Tworzymy siatkę historyczną dzień po dniu lub dla kluczowych dat
    zakres_dat = pd.date_range(start=min(wszystkie_daty), end=datetime.date.today())
    
    historia_lista = []
    
    for d in zakres_dat:
        d_str = d.strftime('%Y-%m-%d')
        
        # 1. Oblicz wartość aktywów posiadanych w dniu 'd' 
        # (akcje kupione w tym dniu lub wcześniej)
        wartosc_aktywow_dnia = 0
        if not df_pozycje.empty:
            # Filtrujemy akcje kupione na dzień 'd' lub wcześniej
            akcje_w_dniu = df_pozycje[pd.to_datetime(df_pozycje['Data Zakupu']) <= d]
            for _, row in akcje_w_dniu.iterrows():
                # Używamy ceny zakupu lub aktualnego kursu w zależności od dostępności w Twoim skrypcie
                cena_do_wyceny = row.get('Akt. Kurs', row.get('Sr. Cena', 0))
                sztuki = row.get('Sztuki', 0)
                wartosc_aktywow_dnia += sztuki * cena_do_wyceny

        # 2. Oblicz sumę dopłat do dnia 'd'
        suma_doplat_dnia = 0
        if not df_doplaty.empty:
            doplaty_w_dniu = df_doplaty[pd.to_datetime(df_doplaty['Data']) <= d]
            suma_doplat_dnia = doplaty_w_dniu['Kwota'].sum() if 'Kwota' in doplaty_w_dniu.columns else 0

        # Całkowita wartość portfela w tym dniu to max z dopłat lub wyceny aktywów
        calkowita_wartosc = max(wartosc_aktywow_dnia, suma_doplat_dnia)
        
        if calkowita_wartosc > 0:
            historia_lista.append({
                'Data': d,
                'Wartość': calkowita_wartosc,
                'Wpłaty': suma_doplat_dnia
            })
            
    return pd.DataFrame(historia_lista)

# Przykład użycia w Streamlit (np. z użyciem Plotly):
# df_hist_wykres = przygotuj_dane_historii(df_akcje_xtb, df_doplaty_xtb)
# if not df_hist_wykres.empty:
#     fig = px.line(df_hist_wykres, x='Data', y='Wartość', title="Historia Portfela XTB")
#     st.plotly_chart(fig, use_container_width=True)
# else:
#     st.info("Brak wystarczających danych do wygenerowania wykresu.")
