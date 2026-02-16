# app.py
import pandas as pd
import streamlit as st

from models import compute_policy
from inventory import simulate_inventory


# --- Config pagina ---
st.set_page_config(
    page_title="Gestione Scorte Magazzino",
    page_icon="📦",
    layout="wide",
)

# --- Titolo + descrizione breve (user-first) ---
st.title("📦 Gestione scorte magazzino")
st.caption("Imposta i parametri a sinistra e confronta riordino classico vs riordino con scorta extra di sicurezza.")
st.divider()


# --- Caricamento dati (CSV 3 anni) ---
@st.cache_data
def load_data(path: str = "demand_3y.csv") -> pd.DataFrame:
    df_ = pd.read_csv(path)
    df_["date"] = pd.to_datetime(df_["date"])
    df_ = df_.sort_values("date")
    return df_


df = load_data()

# Statistiche dalla serie giornaliera (calcolate dal dataset)
d_mean = float(df["demand"].mean())
sigma_d = float(df["demand"].std(ddof=1))


# --- Sidebar: input utente (etichette chiare, poche sigle) ---
st.sidebar.header("Impostazioni")

with st.sidebar.expander("Costi", expanded=True):
    S = st.number_input(
        "Costo per emettere un ordine (€)",
        min_value=0.01,
        value=80.0,
        step=5.0,
        format="%.2f",
    )
    H = st.number_input(
        "Costo annuo per tenere 1 unità a magazzino (€/unità/anno)",
        min_value=0.01,
        value=2.5,
        step=0.1,
        format="%.2f",
    )

with st.sidebar.expander("Tempi e affidabilità", expanded=True):
    L_days = st.slider(
        "Giorni medi di consegna",
        min_value=1,
        max_value=30,
        value=7,
        step=1,
    )

    service_level = st.selectbox(
        "Livello di servizio desiderato",
        ["90%", "95%", "97%", "98%", "99%"],
        index=1,
    )
    z_map = {"90%": 1.28, "95%": 1.65, "97%": 1.88, "98%": 2.05, "99%": 2.33}
    z = float(z_map[service_level])

    variable_lt = st.toggle("I tempi di consegna variano?", value=False)

    sigma_L = None
    if variable_lt:
        sigma_L = st.slider(
            "Quanto variano i giorni di consegna? (circa)",
            min_value=0.0,
            max_value=10.0,
            value=1.5,
            step=0.5,
        )

with st.sidebar.expander("Domanda annua", expanded=False):
    use_auto_D = st.toggle("Usa la domanda stimata dai dati", value=True)
    if use_auto_D:
        D = float(d_mean * 365.0)
        st.caption(f"Domanda annua stimata: {D:,.0f} unità/anno")
    else:
        D = float(st.number_input(
            "Domanda annua (unità/anno)",
            min_value=1.0,
            value=float(d_mean * 365.0),
            step=100.0,
        ))

st.sidebar.divider()
st.sidebar.caption("La domanda (media e variabilità) viene stimata automaticamente dal dataset (3 anni).")


# --- Calcoli principali (EOQ, scorta extra, punti di riordino) ---
try:
    res = compute_policy(
        D=D,
        S=float(S),
        H=float(H),
        d=d_mean,
        sigma_d=sigma_d,
        L=float(L_days),
        z=z,
        variable_lt=variable_lt,
        sigma_L=sigma_L,
    )
except Exception as e:
    st.error(f"Errore nei parametri: {e}")
    st.stop()

Q = float(res["EOQ"])
SS = float(res["SS"])
ROP_classic = float(res["ROP_classic"])
ROP_safety = float(res["ROP_with_SS"])
ROP_delta = float(res.get("ROP_delta", ROP_safety - ROP_classic))


# --- Tabs ---
tab1, tab2, tab3 = st.tabs(["📌 Risultati", "📊 Confronto", "🗂️ Dati"])


# =========================
# TAB 1: RISULTATI
# =========================
with tab1:
    st.subheader("Risultati principali")

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Quantità consigliata per ordine", f"{Q:.0f} unità")
    c2.metric("Scorta extra di sicurezza", f"{SS:.0f} unità")
    c3.metric("Punto riordino (senza scorta extra)", f"{ROP_classic:.0f} unità")
    c4.metric("Punto riordino (con scorta extra)", f"{ROP_safety:.0f} unità")

    st.caption(f"Aumento del punto di riordino grazie alla scorta extra: **+{ROP_delta:.0f} unità**")

    if variable_lt:
        st.info("Modalità: tempi di consegna **variabili** (la scorta extra include anche questa incertezza).")
    else:
        st.info("Modalità: tempi di consegna **fissi** (default).")


# =========================
# TAB 2: CONFRONTO
# =========================
with tab2:
    st.subheader("Confronto su 3 anni di domanda simulata")

    if variable_lt:
        st.info(f"Scenario B: tempi di consegna variabili (variazione impostata: {float(sigma_L):.1f} giorni).")
    else:
        st.info("Scenario B: tempi di consegna fissi (default).")

    # Scenario A: baseline (sempre lead time fisso)
    simA, kpiA = simulate_inventory(
        df,
        Q=Q,
        ROP=ROP_classic,
        L_days=int(L_days),
        variable_lt=False,
        sigma_L=0.0,
        seed=42,
    )

    # Scenario B: con scorta extra (LT fisso o variabile in base al toggle)
    simB, kpiB = simulate_inventory(
        df,
        Q=Q,
        ROP=ROP_safety,
        L_days=int(L_days),
        variable_lt=variable_lt,
        sigma_L=float(sigma_L or 0.0),
        seed=42,
    )

    # --- Sintesi immediata (sicurezza guadagnata) ---
    stockout_a = int(kpiA.get("stockout_days", 0))
    stockout_b = int(kpiB.get("stockout_days", 0))
    avoided_stockouts = stockout_a - stockout_b

    svc_a = float(kpiA.get("service_level_days", 0.0))
    svc_b = float(kpiB.get("service_level_days", 0.0))
    svc_gain_pp = (svc_b - svc_a) * 100  # punti percentuali

    avg_a = float(kpiA.get("avg_on_hand", 0.0))
    avg_b = float(kpiB.get("avg_on_hand", 0.0))
    avg_delta = avg_b - avg_a

    c1, c2, c3 = st.columns(3)
    c1.metric("Stockout evitati", f"{max(0, avoided_stockouts)} giorni")
    c2.metric("Servizio guadagnato", f"+{svc_gain_pp:.2f} punti %")
    c3.metric("Scorta media in più", f"+{avg_delta:.0f} unità")

    st.divider()

    # --- Tabella KPI (con intestazioni user-friendly) ---
    kpi_table = pd.DataFrame([
        {"Scenario": "A) Riordino classico (senza scorta extra)", **kpiA},
        {"Scenario": "B) Riordino con scorta extra", **kpiB},
    ])

    kpi_table = kpi_table.rename(columns={
        "orders_placed": "Ordini emessi (n.)",
        "stockout_days": "Giorni in stockout (n.)",
        "service_level_days": "Giorni senza stockout (%)",
        "avg_on_hand": "Giacenza media (unità)"
    })

    if "Giorni senza stockout (%)" in kpi_table.columns:
        kpi_table["Giorni senza stockout (%)"] = (kpi_table["Giorni senza stockout (%)"] * 100).round(2)

    if "Giacenza media (unità)" in kpi_table.columns:
        kpi_table["Giacenza media (unità)"] = kpi_table["Giacenza media (unità)"].round(0).astype(int)

    st.markdown("### Indicatori principali")
    st.dataframe(kpi_table, use_container_width=True, hide_index=True)

    st.caption("Più sicurezza = meno stockout e più servizio, ma spesso aumenta la giacenza media.")

    # --- Grafico andamento scorte ---
    st.markdown("### Andamento della scorta (estratto)")
    days_to_show = st.slider(
        "Giorni da visualizzare",
        min_value=60,
        max_value=365,
        value=180,
        step=30,
    )

    chart_df = pd.DataFrame({
        "date": simA["date"].iloc[:days_to_show],
        "Riordino classico": simA["on_hand"].iloc[:days_to_show].values,
        "Con scorta extra": simB["on_hand"].iloc[:days_to_show].values,
    }).set_index("date")

    st.line_chart(chart_df)


# =========================
# TAB 3: DATI
# =========================
with tab3:
    st.subheader("Dati di domanda (anteprima)")

    st.write(
        f"Domanda media giornaliera: **{d_mean:.2f}** unità — "
        f"Variabilità giornaliera (dev. std): **{sigma_d:.2f}** unità"
    )

    st.dataframe(df.head(20), use_container_width=True)
