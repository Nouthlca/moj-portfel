# ----------------- 1. STRONA GŁÓWNA -----------------
if page == "🏠 Główna":
    st.markdown("## Cześć Karol! 👋")
    st.caption("💡 *„Bądź chciwy, gdy inni się boją, i bój się, gdy inni są chciwi.”* — Warren Buffett")
    st.write("---")

    # Obliczenia sumaryczne dla całego portfela
    v_xtb_spent = df_xtb["Wydano (PLN)"].sum() if not df_xtb.empty else 0.0
    v_xtb_cur = df_xtb["Wartość (Obecna)"].sum() if not df_xtb.empty else 0.0

    v_ikze_spent = df_ikze["Wydano (PLN)"].sum() if not df_ikze.empty else 0.0
    v_ikze_cur = df_ikze["Wartość (Obecna)"].sum() if not df_ikze.empty else 0.0

    total_spent_all = v_xtb_spent + v_ikze_spent
    total_val_all = v_xtb_cur + v_ikze_cur
    total_profit_all = total_val_all - total_spent_all
    total_profit_pct_all = (total_profit_all / total_spent_all * 100) if total_spent_all > 0 else 0.0

    # 3 Główne kafelki podsumowujące cały majątek
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

    # Zgrabny układ 2-kolumnowy na dole zamiast wielkiego pustego koła
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
                color_discrete_sequence=["#1976d2", "#4caf50", "#fbc02d"]
            )
            fig_alloc.update_traces(textposition='inside', textinfo='percent+label')
            fig_alloc.update_layout(
                margin=dict(t=20, b=20, l=20, r=20),
                height=350,
                showlegend=True
            )
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
