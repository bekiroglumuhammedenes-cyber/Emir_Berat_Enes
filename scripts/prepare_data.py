"""Prepare the project-level merged stock and macro dataset."""
from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
FEATURES = ["unemployment_rate", "cpi", "inflation_rate", "mortgage_interest_rate", "corporate_bond_yield"]


def main():
    stock = pd.read_csv(DATA / "big_tech_stock_prices.csv", parse_dates=["date"])
    stock = stock.dropna(subset=["stock_symbol", "date", "close", "adj_close"])
    stock = stock.drop_duplicates(subset=["stock_symbol", "date"])
    stock["month"] = stock["date"].dt.to_period("M")

    macro = pd.read_csv(DATA / "DATA.csv")
    macro = macro.rename(columns={
        "DATE": "date", "UNRATE(%)": "unemployment_rate", "CPIALLITEMS": "cpi",
        "INFLATION(%)": "inflation_rate", "MORTGAGE INT. MONTHLY AVG(%)": "mortgage_interest_rate",
        "CORP. BOND YIELD(%)": "corporate_bond_yield",
    })
    # DATA.csv uses day-month-year strings (for example, 01-05-2022 is 1 May).
    macro["date"] = pd.to_datetime(macro["date"], dayfirst=True)
    macro["month"] = macro["date"].dt.to_period("M")
    macro = macro[["month", *FEATURES]].dropna(subset=FEATURES).drop_duplicates(subset=["month"])

    merged = stock.merge(macro, on="month", how="inner", validate="many_to_one")
    merged = merged.dropna(subset=FEATURES).sort_values(["date", "stock_symbol"])
    columns = ["date", "stock_symbol", "open", "high", "low", "close", "adj_close", "volume", *FEATURES]
    output = DATA / "big_tech_stock_macro_cleaned.csv"
    merged[columns].to_csv(output, index=False, date_format="%Y-%m-%d")
    print(f"Saved {len(merged):,} rows to {output.name}; {merged['date'].min().date()} to {merged['date'].max().date()}")


if __name__ == "__main__":
    main()
