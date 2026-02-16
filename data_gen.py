def generate_demand_3y(
    start_date="2023-01-01",
    years=3,
    mean_daily=120,
    sigma_daily=25,
    season_amp=0.10,
    weekend_factor=0.75,
    shock_windows=None,
    seed=42,
    round_to=1
):
    rng = np.random.default_rng(seed)
    days = int(365 * years)
    dates = pd.date_range(start=start_date, periods=days, freq="D")

    t = np.arange(days)

    # Stagionalità annuale
    seasonal = 1.0 + season_amp * np.sin(2 * np.pi * t / 365)

    # Domanda base casuale
    base = rng.normal(loc=mean_daily, scale=sigma_daily, size=days)
    base = np.clip(base, 0, None)

    # Effetto weekend
    weekday = dates.weekday
    weekly = np.where(weekday < 5, 1.0, weekend_factor)

    # Shock temporanei
    shock = np.ones(days)
    if shock_windows:
        for (a, b, m) in shock_windows:
            shock[a:b] *= m

    demand = base * seasonal * weekly * shock
    demand = np.clip(demand, 0, None)

    if round_to is not None:
        demand = np.round(demand, round_to)

    df = pd.DataFrame({
        "date": dates,
        "demand": demand
    })

    return df
