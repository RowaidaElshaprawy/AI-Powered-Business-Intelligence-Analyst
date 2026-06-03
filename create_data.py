"""
Run this once to generate business_data.csv in the project root.
Usage: python create_data.py
"""
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from pathlib import Path

dates    = [datetime(2025, 1, 1) + timedelta(days=i) for i in range(90)]
products = ['Laptop', 'Mouse', 'Keyboard', 'Monitor']
regions  = ['North', 'South', 'East', 'West']

rng  = np.random.default_rng(42)
rows = []
for date in dates:
    for product in products:
        for region in regions:
            rows.append({
                'date':    date.strftime('%Y-%m-%d'),
                'product': product,
                'region':  region,
                'revenue': int(rng.integers(100, 1000)),
                'profit':  int(rng.integers(10,  200)),
            })

df = pd.DataFrame(rows)
out = Path(__file__).parent / "business_data.csv"
df.to_csv(out, index=False)
print(f"✓ Created {out}  ({len(df):,} rows)")
