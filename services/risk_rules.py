def lot_tiers(balance: float):
    """Return (min, max_per_trade, max_cumulative)."""
    tiers = [
        (30,100,(0.01,0.03,0.04)),
        (100,200,(0.02,0.05,0.07)),
        (200,400,(0.04,0.06,0.10)),
        (400,700,(0.05,0.10,0.15)),
        (700,1100,(0.07,0.16,0.20)),
        (1100,float("inf"),(0.08,0.17,0.25)),
    ]
    for lo,hi,(a,b,c) in tiers:
        if lo <= balance < hi: return a,b,c
    return 0.01,0.03,0.04
