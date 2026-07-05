"""Generate sample datasets for Python/ML practice.

Run once (or to reset):  python data/make_data.py
Deterministic (seeded) so expected answers stay stable.
"""
import os
import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
rng = np.random.default_rng(42)
N = 3000

# Customer churn dataset: realistic mix of numeric/categorical + a signal
tenure = rng.integers(1, 72, N)
monthly = np.round(rng.normal(70, 25, N).clip(15, 150), 2)
plan = rng.choice(["basic", "standard", "premium"], N, p=[0.5, 0.3, 0.2])
support_calls = rng.poisson(1.2, N)
contract = rng.choice(["monthly", "annual"], N, p=[0.65, 0.35])

# churn probability driven by short tenure, high support calls, monthly contract
logit = (-2.0
         - 0.03 * tenure
         + 0.35 * support_calls
         + 0.9 * (contract == "monthly")
         + 0.004 * monthly)
p = 1 / (1 + np.exp(-logit))
churn = (rng.random(N) < p).astype(int)

df = pd.DataFrame({
    "customer_id": np.arange(1, N + 1),
    "tenure_months": tenure,
    "monthly_charge": monthly,
    "plan": plan,
    "support_calls": support_calls,
    "contract": contract,
    "churned": churn,
})
# inject a few missing values to practice cleaning
df.loc[rng.choice(N, 60, replace=False), "monthly_charge"] = np.nan

out = os.path.join(HERE, "customers.csv")
df.to_csv(out, index=False)
print(f"Wrote {out}  ({len(df)} rows, churn rate {churn.mean():.1%})")
