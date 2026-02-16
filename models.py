import math
from typing import Optional, Dict

# ============================================================
# MODELLO EOQ + ROP (con e senza scorta di sicurezza)
#
# Nota IMPORTANTISSIMA sulle unità:
# - D è domanda annua (unità/anno)
# - d e sigma_d devono essere riferiti allo STESSO periodo (es. giorno)
# - L deve essere espresso nello STESSO periodo di d (es. giorni)
#
# Esempio coerente:
#   d = domanda media giornaliera
#   sigma_d = deviazione std giornaliera
#   L = lead time in giorni
# ============================================================


def eoq(D: float, S: float, H: float) -> float:
    """
    Lotto Economico di Ordinazione (EOQ).

    EOQ = sqrt((2 * D * S) / H)

    Parametri:
    - D: domanda annua (unità/anno)
    - S: costo fisso per ordine/setup (€ / ordine)
    - H: costo annuo di mantenimento per unità (€ / unità / anno)

    Output:
    - EOQ (unità per ordine)

    Assunzioni:
    - domanda deterministica e costante (modello classico EOQ)
    """
    if D <= 0 or S <= 0 or H <= 0:
        raise ValueError("D, S, H devono essere > 0")
    return math.sqrt((2.0 * D * S) / H)


def safety_stock(z: float, sigma_d: float, L: float) -> float:
    """
    Scorta di Sicurezza (SS) - modello base:
    - domanda variabile
    - lead time considerato costante

    Formula:
        SS = z * sigma_d * sqrt(L)

    Parametri:
    - z: z-score associato al livello di servizio (es. 1.65 ~ 95%)
    - sigma_d: deviazione standard della domanda (stesso periodo di d)
    - L: lead time espresso nello stesso periodo (es. giorni)

    Output:
    - SS (unità)

    Nota:
    - Se sigma_d è giornaliero, L deve essere in giorni.
    """
    if z < 0 or sigma_d < 0 or L <= 0:
        raise ValueError("z>=0, sigma_d>=0, L>0")

    # La variabilità della domanda durante il lead time cresce con sqrt(L)
    return z * sigma_d * math.sqrt(L)


def safety_stock_demand_and_lt(
    z: float,
    d: float,
    sigma_d: float,
    L: float,
    sigma_L: float
) -> float:
    """
    Scorta di Sicurezza (SS) - modello esteso:
    - domanda variabile
    - lead time variabile

    Formula:
        SS = z * sqrt( (sigma_d^2 * L) + (d^2 * sigma_L^2) )

    Parametri:
    - z       : z-score associato al livello di servizio desiderato
    - d       : domanda media per periodo (es. unità/giorno)
    - sigma_d : deviazione standard della domanda per periodo
    - L       : lead time medio (in periodi coerenti con d)
    - sigma_L : deviazione standard del lead time (stesso periodo di L)

    Output:
    - SS (unità)

    Assunzione:
    - indipendenza tra variabilità della domanda e del lead time.
    """
    if z < 0 or d < 0 or sigma_d < 0 or L <= 0 or sigma_L < 0:
        raise ValueError("z>=0, d>=0, sigma_d>=0, L>0, sigma_L>=0")

    variance_total = (sigma_d ** 2) * L + (d ** 2) * (sigma_L ** 2)
    return z * math.sqrt(variance_total)


def reorder_point(d: float, L: float, SS: float) -> float:
    """
    Punto di riordino (ROP).

    Formula:
        ROP = d * L + SS

    Parametri:
    - d : domanda media per periodo (es. unità/giorno)
    - L : lead time nello stesso periodo (es. giorni)
    - SS: scorta di sicurezza (unità)

    Output:
    - ROP (unità)

    Interpretazione:
    - quando lo stock scende sotto ROP, scatta l'ordine.
    """
    if d < 0 or L <= 0 or SS < 0:
        raise ValueError("d>=0, L>0, SS>=0")
    return d * L + SS


def compute_policy(
    D: float,
    S: float,
    H: float,
    d: float,
    sigma_d: float,
    L: float,
    z: float,
    variable_lt: bool = False,
    sigma_L: Optional[float] = None
) -> Dict[str, float]:
    """
    Calcola EOQ, SS e ROP.
    Default: lead time fisso (variable_lt=False).

    Se variable_lt=True, usa il modello esteso con sigma_L.
    """

    Q = eoq(D, S, H)

    # ROP classico (senza SS)
    rop_classic = reorder_point(d, L, 0.0)

    # SS: modello base o esteso
    if not variable_lt:
        SS = safety_stock(z, sigma_d, L)
    else:
        if sigma_L is None:
            raise ValueError("Se variable_lt=True devi fornire sigma_L")
        SS = safety_stock_demand_and_lt(z, d, sigma_d, L, sigma_L)

    rop_with_ss = reorder_point(d, L, SS)

    return {
        "EOQ": Q,
        "SS": SS,
        "ROP_classic": rop_classic,
        "ROP_with_SS": rop_with_ss,
        "ROP_delta": rop_with_ss - rop_classic  # utile in UI e nel report
    }