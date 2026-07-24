"""Load the cleaned medicines table into a SQLite database (medicines.db)."""

import sqlite3
from pathlib import Path

import pandas as pd

ROOT = Path(r"D:\medicine-price-gap")
DB = ROOT / "data" / "medicines.db"


def build():
    df = pd.read_csv(ROOT / "data" / "medicines_clean.csv")
    con = sqlite3.connect(DB)
    df.to_sql("medicines", con, if_exists="replace", index=False)
    con.executescript(
        """
        CREATE INDEX IF NOT EXISTS idx_comp ON medicines(full_composition);
        CREATE INDEX IF NOT EXISTS idx_compt ON medicines(comp_and_type);
        CREATE INDEX IF NOT EXISTS idx_salt ON medicines(salt_name);
        CREATE INDEX IF NOT EXISTS idx_mfg ON medicines(manufacturer_name);
        """
    )
    con.commit()
    con.close()
    print(f"built {DB}  ({len(df):,} medicines)")


if __name__ == "__main__":
    build()
