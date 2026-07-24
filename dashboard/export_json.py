"""Export compact aggregates to dashboard/data.json for the HTML dashboard.
A formulation-type (pack_type) slicer filters the overview; the gap,
manufacturer, and category views are cross-cutting (all formulations)."""

import json
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(r"D:\medicine-price-gap")
df = pd.read_csv(ROOT / "data" / "medicines_clean.csv")

AFF_BINS = list(range(1, 11)) + [15, 20, 999]  # affordability-index bin edges


def aff_hist(sub):
    counts, _ = np.histogram(sub["affordability_index"].clip(upper=20), bins=AFF_BINS)
    return [int(c) for c in counts]


def overview(sub):
    n = len(sub)
    return {
        "count": int(n),
        "median_ppu": round(float(sub["price_per_unit"].median()), 2),
        "pct2": round(100 * (sub["affordability_index"] > 2).mean(), 1),
        "pct5": round(100 * (sub["affordability_index"] > 5).mean(), 1),
        "pct10": round(100 * (sub["affordability_index"] > 10).mean(), 1),
        "affHist": aff_hist(sub),
    }


data = {}
data["meta"] = {
    "medicines": int(len(df)),
    "compositions": int(df.full_composition.nunique()),
    "manufacturers": int(df.manufacturer_name.nunique()),
    "salts": int(df.salt_name.nunique()),
}
data["affBins"] = AFF_BINS

top_types = df.pack_type.value_counts().head(8).index.tolist()
data["packTypes"] = ["All"] + top_types
data["byPackType"] = {"All": overview(df)}
for pt in top_types:
    data["byPackType"][pt] = overview(df[df.pack_type == pt])

data["formulationMix"] = [
    {"k": pt, "v": int(c)} for pt, c in df.pack_type.value_counts().head(8).items()
]

# cross-cutting: per composition+formulation gap stats
g = df.groupby("comp_and_type").agg(
    brands=("name", "count"),
    mn=("price_per_unit", "min"),
    mx=("price_per_unit", "max"),
    therapy=("therapy_category", "first"),
).reset_index()
g = g[(g.brands >= 5) & (g.mn > 0)]
g["ratio"] = (g.mx / g.mn).round(1)

top = g[g.brands >= 30].sort_values("ratio", ascending=False).head(20)
data["topGaps"] = [
    {"k": r.comp_and_type[:46], "brands": int(r.brands), "ratio": float(r.ratio)}
    for r in top.itertuples()
]

bins = [(5, 10, "5-10"), (11, 25, "11-25"), (26, 50, "26-50"),
        (51, 100, "51-100"), (101, 500, "101-500"), (501, 10 ** 9, "500+")]
data["competition"] = [
    {"k": lbl, "v": round(float(g[(g.brands >= lo) & (g.brands <= hi)].ratio.median()), 1)}
    for lo, hi, lbl in bins
]

data["therapyGaps"] = [
    {"k": cat, "v": round(float(sub[sub.brands >= 10].ratio.median()), 1),
     "n": int((sub.brands >= 10).sum())}
    for cat, sub in g.groupby("therapy")
    if (sub.brands >= 10).sum() >= 5
]
data["therapyGaps"].sort(key=lambda d: -d["v"])

mfg = df.groupby("manufacturer_name").agg(
    products=("name", "count"), premium=("premium_ratio", "mean")
).reset_index()
mfg = mfg[mfg.products >= 50]
data["mfgExpensive"] = [
    {"k": r.manufacturer_name[:28], "v": round(float(r.premium), 2), "n": int(r.products)}
    for r in mfg.sort_values("premium", ascending=False).head(12).itertuples()
]
data["mfgAffordable"] = [
    {"k": r.manufacturer_name[:28], "v": round(float(r.premium), 2), "n": int(r.products)}
    for r in mfg.sort_values("premium").head(12).itertuples()
]

commons = ["Paracetamol", "Cetirizine", "Omeprazole", "Metformin", "Atorvastatin",
           "Azithromycin", "Amoxycillin", "Pantoprazole", "Amlodipine", "Telmisartan"]
sav = []
for mol in commons:
    sub = df[df.salt_name.str.lower() == mol.lower()]
    if len(sub) < 5:
        continue
    sav.append({"k": mol, "brands": int(len(sub)),
                "cheapest": round(float(sub.price_per_unit.min()), 2),
                "costliest": round(float(sub.price_per_unit.max()), 2),
                "v": round(float(sub.price_per_unit.max() - sub.price_per_unit.min()), 2)})
data["moleculeSavings"] = sorted(sav, key=lambda d: -d["v"])

out = ROOT / "dashboard" / "data.json"
out.parent.mkdir(exist_ok=True)
out.write_text(json.dumps(data, separators=(",", ":")), encoding="utf-8")
print("wrote", out, f"({out.stat().st_size/1024:.0f} KB)")
for k in data:
    v = data[k]
    print(f"  {k}: {len(v) if isinstance(v,(list,dict)) else v}")
