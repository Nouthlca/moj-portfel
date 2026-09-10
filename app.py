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
            st.dataframe(pd.DataFrame(stan["tab_xtb"]).drop(columns=["Wartość_raw"]), use_container_width=True, hide_index=True)

    st.markdown("<hr style='border-color: #e2ded5;'>", unsafe_allow_html=True)
    pokaz_wykres_i_historie_konta("XTB", "#10b981")

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
            st.dataframe(pd.DataFrame(stan["tab_emerytura"]).drop(columns=["Wartość_raw"]), use_container_width=True, hide_index=True)

    st.markdown("<hr style='border-color: #e2ded5;'>", unsafe_allow_html=True)
    pokaz_wykres_i_historie_konta("Emerytura", "#3b82f6")

# ----------------------------------------------------
# 4. EDYCJA & DOPŁATY
# ----------------------------------------------------
elif st.session_state.page == "✏️ Edycja & Dopłaty":
    st.title("✏️ EDYCJA AKTYWÓW I DOKONANIE DOPŁAT")
    
    tab1, tab2 = st.tabs(["📝 Aktualizuj Aktywa", "➕ Dodaj Nowy Wpis z Dopłatą"])
    
    with tab1:
        col_x, col_m = st.columns(2)
        nowe_dane = {"xtb_gotowka": 0.0, "mbank_gotowka": 0.0, "xtb_pozycje": [], "mbank_pozycje": []}
        
        with col_x:
            st.subheader("🔴 KONTO XTB")
            nowe_dane["xtb_gotowka"] = st.number_input("XTB: Gotówka (PLN)", min_value=0.0, value=float(zapisane_dane.get("xtb_gotowka", 0.0)), key="in_x_c")
            for i in range(5):
                st.caption(f"Pozycja XTB #{i+1}")
                prev = zapisane_dane["xtb_pozycje"][i] if i < len(zapisane_dane["xtb_pozycje"]) else {"ticker": "", "sztuki": 0.0, "cena": 0.0}
                c1, c2, c3 = st.columns(3)
                t = c1.text_input("Ticker", value=prev["ticker"], key=f"x_t_{i}").strip().upper()
                s = c2.number_input("Sztuki", min_value=0.0, value=float(prev["sztuki"]), key=f"x_s_{i}")
                p = c3.number_input("Śr. cena", min_value=0.0, value=float(prev["cena"]), key=f"x_p_{i}")
                nowe_dane["xtb_pozycje"].append({"ticker": t, "sztuki": s, "cena": p})

        with col_m:
            st.subheader("🔵 PORTFEL EMERYTURA (IKZE)")
            nowe_dane["mbank_gotowka"] = st.number_input("Emerytura: Gotówka (PLN)", min_value=0.0, value=float(zapisane_dane.get("mbank_gotowka", 0.0)), key="in_m_c")
            for i in range(5):
                st.caption(f"Pozycja Emerytura #{i+1}")
                prev = zapisane_dane["mbank_pozycje"][i] if i < len(zapisane_dane["mbank_pozycje"]) else {"ticker": "", "sztuki": 0.0, "cena": 0.0}
                c1, c2, c3 = st.columns(3)
                t = c1.text_input("Ticker", value=prev["ticker"], key=f"m_t_{i}").strip().upper()
                s = c2.number_input("Sztuki", min_value=0.0, value=float(prev["sztuki"]), key=f"m_s_{i}")
                p = c3.number_input("Śr. cena", min_value=0.0, value=float(prev["cena"]), key=f"m_p_{i}")
                nowe_dane["mbank_pozycje"].append({"ticker": t, "sztuki": s, "cena": p})
                
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
        dokupione_aktywo = c_d4.text_input("Dokupione Aktywo (np. NVDA):").strip().upper()
        
        st_aktualny = oblicz_stan_portfela(zapisane_dane)
        val_konta = st_aktualny["calosc_xtb"] if wybrane_konto == "XTB" else st_aktualny["calosc_emerytura"]
        zysk_konta = st_aktualny["zysk_xtb"] if wybrane_konto == "XTB" else st_aktualny["zysk_emerytura"]
        
        st.info(f"Wprowadzana wartość końcowa konta {wybrane_konto}: **{val_konta:,.2f} PLN** | Całkowity Zysk: **{zysk_konta:,.2f} PLN**")
        
        if st.button("📈 ZAPISZ DOPŁATĘ DO HISTORII", use_container_width=True):
            zapisz_wpis_historii(data_wpisu, wybrane_konto, val_konta, kwota_doplata, zysk_konta, dokupione_aktywo)
            st.success(f"Dodano wpis dla {wybrane_konto}!")
            st.rerun()
