"""Run every query in sql/analysis.sql, print results, and export
dashboard-ready CSVs. Registers a MEDIAN aggregate (SQLite has none)."""

import re
import sqlite3
import statistics
from pathlib import Path

import pandas as pd

ROOT = Path(r"D:\medicine-price-gap")
DB = ROOT / "data" / "medicines.db"
DASH = ROOT / "dashboard"


class Median:
    def __init__(self):
        self.vals = []

    def step(self, v):
        if v is not None:
            self.vals.append(v)

    def finalize(self):
        return statistics.median(self.vals) if self.vals else None


def connect():
    con = sqlite3.connect(DB)
    con.create_aggregate("MEDIAN", 1, Median)
    return con


def split_queries(sql_text):
    out = []
    for block in re.split(r";\s*\n", sql_text):
        block = block.strip()
        if not block or all(l.strip().startswith("--") for l in block.splitlines()):
            continue
        label = "query"
        for line in block.splitlines():
            m = re.match(r"--\s*(Q\d+\..*)", line.strip())
            if m:
                label = m.group(1)
                break
        out.append((label, block))
    return out


def main():
    con = connect()
    sql = (ROOT / "sql" / "analysis.sql").read_text(encoding="utf-8")
    DASH.mkdir(exist_ok=True)
    for label, q in split_queries(sql):
        df = pd.read_sql_query(q, con)
        print(f"\n=== {label}  ({len(df)} rows) ===")
        print(df.head(8).to_string(index=False))
        df.to_csv(DASH / f"{label.split('.')[0].lower()}.csv", index=False)
    con.close()
    print(f"\nAll queries ran. Dashboard CSVs -> {DASH}")


if __name__ == "__main__":
    main()
