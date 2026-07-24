"""Clean the raw Indian medicines dataset and engineer the fields the SQL
analysis and dashboard need. Reproduces the methodology from the EDA notebook:

  - drop discontinued products and non-positive prices
  - price_per_unit = price / pack quantity  (fair comparison, not raw MRP)
  - pack_type      = formulation (tablet / capsule / syrup / injection / ...)
  - full_composition, salt_name, is_combination_drug
  - affordability_index = price_per_unit / cheapest per-unit for that composition
  - premium_ratio       = price_per_unit / median per-unit for that composition
  - therapy_category    = coarse therapeutic bucket from the salt

Output: data/medicines_clean.csv
"""

import re
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(r"D:\medicine-price-gap")

PACK_TYPE_RE = re.compile(
    r"(tablets?|capsules?|dry syrups?|syrups?|injections?|creams?|gels?|drops?|"
    r"powders?|solutions?|ointments?|oral suspensions?|suspensions?|vials?|"
    r"tubes?|sachets?|ampoules?|eye drops?)",
    re.IGNORECASE,
)
PACK_TYPE_FIX = {"dry syrup": "syrup", "oral suspension": "suspension",
                 "eye drop": "drop", "ampoule": "injection"}

THERAPY = {
    "Pain/Fever": ["paracetamol", "ibuprofen", "aceclofenac", "diclofenac",
                   "aspirin", "nimesulide", "tramadol", "naproxen"],
    "Antibiotic": ["amoxycillin", "amoxicillin", "azithromycin", "cefixime",
                   "ciprofloxacin", "metronidazole", "ofloxacin", "cephalexin",
                   "cefpodoxime", "levofloxacin", "doxycycline", "clavulanic"],
    "Diabetes": ["metformin", "glimepiride", "insulin", "sitagliptin",
                 "vildagliptin", "gliclazide", "teneligliptin", "dapagliflozin"],
    "Cardiac/BP": ["amlodipine", "telmisartan", "atorvastatin", "losartan",
                   "metoprolol", "rosuvastatin", "ramipril", "clopidogrel",
                   "olmesartan", "cilnidipine", "bisoprolol"],
    "Gastro": ["omeprazole", "pantoprazole", "rabeprazole", "ranitidine",
               "domperidone", "esomeprazole", "ondansetron"],
    "Allergy/Resp": ["cetirizine", "levocetirizine", "montelukast",
                     "fexofenadine", "salbutamol", "ambroxol", "levosalbutamol"],
    "Vitamin/Supplement": ["vitamin", "calcium", "folic", "iron", "multivitamin",
                           "zinc", "methylcobalamin", "cholecalciferol"],
}


def salt_of(comp):
    if pd.isna(comp):
        return None
    comp = str(comp).strip()
    return comp[: comp.index("(")].strip() if "(" in comp else comp


def therapy_of(salt):
    s = (salt or "").lower()
    for cat, keys in THERAPY.items():
        if any(k in s for k in keys):
            return cat
    return "Other"


def main():
    df = pd.read_csv(ROOT / "data" / "indian_medicines.csv")
    df = df.rename(columns={"price(₹)": "price"})

    n0 = len(df)
    df = df[df["Is_discontinued"] != True].copy()          # noqa: E712
    df = df[df["price"] > 0].copy()
    df = df.drop(columns=["Is_discontinued"])

    # composition / salt
    df["salt_name"] = df["short_composition1"].apply(salt_of)
    df = df.dropna(subset=["salt_name"]).copy()
    df["is_combination_drug"] = df["short_composition2"].notna()
    df["full_composition"] = np.where(
        df["short_composition2"].notna(),
        df["short_composition1"].str.strip() + " + " + df["short_composition2"].str.strip(),
        df["short_composition1"].str.strip(),
    )

    # pack quantity + per-unit price
    df["pack_qty"] = df["pack_size_label"].str.extract(r"(\d+\.?\d*)").astype(float)
    df = df[df["pack_qty"] > 0].copy()
    df["price_per_unit"] = (df["price"] / df["pack_qty"]).round(4)

    # formulation type
    pt = df["pack_size_label"].str.extract(PACK_TYPE_RE, expand=False).str.lower()
    pt = pt.str.rstrip("s").replace(PACK_TYPE_FIX).fillna("other")
    df["pack_type"] = pt

    df["therapy_category"] = df["salt_name"].apply(therapy_of)
    df["comp_and_type"] = df["full_composition"] + " | " + df["pack_type"]

    # premium flag (investigated, not deleted)
    hi = df["price"].quantile(0.999)
    df["is_premium_priced"] = df["price"] > hi

    # per-composition benchmarks
    g = df.groupby("full_composition")["price_per_unit"]
    df["comp_min_ppu"] = g.transform("min")
    df["comp_median_ppu"] = g.transform("median")
    df["affordability_index"] = (df["price_per_unit"] / df["comp_min_ppu"]).round(2)
    df["premium_ratio"] = (df["price_per_unit"] / df["comp_median_ppu"]).round(3)

    out = ROOT / "data" / "medicines_clean.csv"
    df.to_csv(out, index=False)
    print(f"raw {n0:,} -> clean {len(df):,} rows")
    print(f"unique salts: {df.salt_name.nunique():,} | compositions: {df.full_composition.nunique():,}")
    print(f"pack types: {df.pack_type.value_counts().head(6).to_dict()}")
    print(f"2x+ overpriced: {(df.affordability_index > 2).mean():.1%}")
    print(f"saved -> {out}")


if __name__ == "__main__":
    main()
