import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

from models import compute_policy


def simulate_inventory(
    demand_df: pd.DataFrame,
    Q: float,
    ROP: float,
    L_days: int,
    initial_stock: float = None,
    # Opzionale: lead time variabile
    variable_lt: bool = False,
    sigma_L: float = 0.0,
    seed: int = 42,
):
    """
    Simulazione semplice di inventario (lost sales):
    - ogni giorno si sottrae la domanda dalla giacenza (on_hand)
    - se on_hand <= ROP si piazza un ordine di quantità Q
    - l'ordine arriva dopo un lead time:
        - fisso: L_days
        - variabile: campionato attorno a L_days con dev.std sigma_L
    - se on_hand va sotto 0, si registra stockout e si riporta a 0

    Parametri principali:
    - demand_df: DataFrame con colonne almeno ["date", "demand"]
    - Q: quantità ordinata
    - ROP: reorder point
    - L_days: lead time medio (giorni). Se variable_lt=False è fisso.
    - initial_stock: giacenza iniziale; default = Q

    Modalità lead time variabile:
    - variable_lt: se True, per ogni ordine si campiona un lead time L_i
    - sigma_L: dev. std del lead time (giorni), usata solo se variable_lt=True
    - seed: per rendere riproducibile la simulazione

    Nota:
    - Il lead time campionato viene arrotondato a intero e "troncato" a minimo 1 giorno.
    """
    df = demand_df.copy()
    df["demand"] = df["demand"].astype(float)

    if initial_stock is None:
        initial_stock = float(Q)

    if L_days < 1:
        raise ValueError("L_days deve essere >= 1")
    if Q <= 0:
        raise ValueError("Q deve essere > 0")
    if ROP < 0:
        raise ValueError("ROP deve essere >= 0")

    if variable_lt and sigma_L < 0:
        raise ValueError("sigma_L deve essere >= 0")

    rng = np.random.default_rng(seed)

    on_hand = float(initial_stock)

    # ordini in pipeline: lista di tuple (arrival_index, qty)
    pipeline = []

    on_hand_list = []
    stockout_list = []
    orders_placed = 0

    for i in range(len(df)):
        # 1) Arrivo ordini previsti per oggi
        arrived_qty = 0.0
        if pipeline:
            arrived_qty = sum(qty for (arr_i, qty) in pipeline if arr_i == i)
            if arrived_qty > 0:
                on_hand += arrived_qty
            pipeline = [(arr_i, qty) for (arr_i, qty) in pipeline if arr_i != i]

        # 2) Soddisfazione domanda
        d = float(df.loc[i, "demand"])
        on_hand -= d

        # 3) Stockout (lost sales)
        if on_hand < 0:
            stockout_list.append(1)
            on_hand = 0.0
        else:
            stockout_list.append(0)

        # 4) Regola di riordino
        if on_hand <= ROP:
            # lead time fisso o variabile
            if not variable_lt:
                lead_i = int(L_days)
            else:
                # Campionamento normale attorno a L_days, arrotondo e tronco a min 1
                lead_i = int(round(rng.normal(loc=L_days, scale=sigma_L)))
                lead_i = max(1, lead_i)

            arrival_day = i + lead_i
            pipeline.append((arrival_day, float(Q)))
            orders_placed += 1

        on_hand_list.append(on_hand)

    df["on_hand"] = on_hand_list
    df["stockout"] = stockout_list

    kpi = {
        "orders_placed": int(orders_placed),
        "stockout_days": int(df["stockout"].sum()),
        "service_level_days": float(1.0 - df["stockout"].mean()),
        "avg_on_hand": float(df["on_hand"].mean()),
    }
    return df, kpi


def run_comparison(
    csv_path: str = "demand_3y.csv",
    D: float = None,
    S: float = 80.0,
    H: float = 2.5,
    L_days: int = 7,
    z: float = 1.65,
    # confronto con lead time variabile opzionale
    variable_lt: bool = False,
    sigma_L: float = 0.0,
    seed: int = 42,
):
    """
    Esegue confronto tra:
    - Scenario A: EOQ + ROP classico (SS=0)
    - Scenario B: EOQ + ROP con SS (modello base o esteso in base a variable_lt)

    Se variable_lt=True:
    - SS viene calcolata con il modello esteso (include sigma_L)
    - la simulazione usa lead time campionato per ogni ordine
    """

    # Leggo i dati simulati
    demand_df = pd.read_csv(csv_path)
    demand_df["date"] = pd.to_datetime(demand_df["date"])
    demand_df = demand_df.sort_values("date")

    # Statistiche dalla serie (giornaliera)
    d_mean = float(demand_df["demand"].mean())
    sigma_d = float(demand_df["demand"].std(ddof=1))

    # Se D non è fornito, stimiamo la domanda annua
    if D is None:
        D = float(d_mean * 365.0)

    # Calcoli EOQ, SS, ROP (coerenti con la modalità LT)
    res = compute_policy(
        D=D, S=S, H=H,
        d=d_mean, sigma_d=sigma_d,
        L=float(L_days), z=float(z),
        variable_lt=variable_lt,
        sigma_L=(sigma_L if variable_lt else None)
    )

    Q = float(res["EOQ"])
    SS = float(res["SS"])
    ROP_classic = float(res["ROP_classic"])
    ROP_safety = float(res["ROP_with_SS"])

    # Simulazioni
    simA, kpiA = simulate_inventory(
        demand_df, Q=Q, ROP=ROP_classic, L_days=int(L_days),
        variable_lt=False, sigma_L=0.0, seed=seed
    )
    simB, kpiB = simulate_inventory(
        demand_df, Q=Q, ROP=ROP_safety, L_days=int(L_days),
        variable_lt=variable_lt, sigma_L=float(sigma_L), seed=seed
    )

    # Stampa confronto
    print("\n=== PARAMETRI STIMATI DAI DATI ===")
    print(f"Domanda media giornaliera d = {d_mean:.2f}")
    print(f"Deviazione standard sigma_d = {sigma_d:.2f}")
    print(f"Domanda annua D (stimata) = {D:.2f}")

    print("\n=== CALCOLI MODELLO ===")
    print(f"EOQ (Q*) = {Q:.2f}")
    print(f"Safety Stock (SS) = {SS:.2f}")
    print(f"ROP classico (senza SS) = {ROP_classic:.2f}")
    print(f"ROP con SS = {ROP_safety:.2f}")
    if variable_lt:
        print(f"(Lead time variabile attivo) sigma_L = {sigma_L:.2f} giorni")

    print("\n=== KPI CONFRONTO ===")
    print("Scenario A) EOQ + ROP classico (SS=0)")
    print(kpiA)
    print("Scenario B) EOQ + ROP con Safety Stock")
    print(kpiB)

    # Salvataggio risultati
    simA_out = simA.copy()
    simA_out["scenario"] = "A_classic"
    simB_out = simB.copy()
    simB_out["scenario"] = "B_safetystock"
    out = pd.concat([simA_out, simB_out], ignore_index=True)
    out.to_csv("inventory_results.csv", index=False)

    # Grafico (estratto primi 180 giorni)
    days_to_show = 180
    fig = plt.figure()
    plt.plot(simA["date"].iloc[:days_to_show], simA["on_hand"].iloc[:days_to_show], label="Scenario A")
    plt.plot(simB["date"].iloc[:days_to_show], simB["on_hand"].iloc[:days_to_show], label="Scenario B")
    plt.xticks(rotation=30)
    plt.ylabel("Giacenza (unità)")
    plt.xlabel("Data")
    plt.title("Andamento scorta (primi 180 giorni)")
    plt.legend()
    plt.tight_layout()
    plt.savefig("inventory_plot.png", dpi=150)

    print("\nCreati file: inventory_results.csv e inventory_plot.png")


if __name__ == "__main__":
    # Esempio:
    # - default: lead time fisso
    run_comparison(S=80.0, H=2.5, L_days=7, z=1.65)

    # Per provare LT variabile:
    # run_comparison(S=80.0, H=2.5, L_days=7, z=1.65, variable_lt=True, sigma_L=1.5)
