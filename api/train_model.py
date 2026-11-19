"""Makro göstergelerden kapanış fiyatı tahmin modelini eğitir ve model.joblib olarak kaydeder.

Notebook'taki B1 hücresiyle aynı yöntem: 2020-01-01 öncesi eğitim, sonrası test (tarihe göre bölme).
Çalıştırma:  python train_model.py
CSV dosyaları için sırayla şu yerlere bakılır: DATA_DIR ortam değişkeni, ../data, .., bu klasör.
"""
import os
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.dummy import DummyRegressor
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

FEATURES = ["unemployment_rate", "cpi", "inflation_rate",
            "mortgage_interest_rate", "corporate_bond_yield"]
KESIM = "2020-01-01"
HERE = Path(__file__).resolve().parent


def veri_klasoru() -> Path:
    adaylar = [os.environ.get("DATA_DIR"), HERE.parent / "data", HERE.parent, HERE]
    for a in adaylar:
        if a and (Path(a) / "big_tech_stock_prices.csv").exists() and (Path(a) / "DATA.csv").exists():
            return Path(a)
    raise FileNotFoundError(
        "big_tech_stock_prices.csv ve DATA.csv bulunamadı. Dosyaları ../data klasörüne koyun "
        "ya da DATA_DIR ortam değişkenini ayarlayın.")


def mape(y, p):
    y, p = np.array(y), np.array(p)
    return float(np.mean(np.abs((y - p) / y)) * 100)


def metrikler(y, p):
    return {"rmse": float(mean_squared_error(y, p) ** 0.5),
            "mae": float(mean_absolute_error(y, p)),
            "mape": mape(y, p),
            "r2": float(r2_score(y, p))}


def main():
    d = veri_klasoru()
    fiyat = pd.read_csv(d / "big_tech_stock_prices.csv", parse_dates=["date"])
    makro = pd.read_csv(d / "DATA.csv")
    makro = makro.rename(columns={
        "UNRATE(%)": "unemployment_rate", "CPIALLITEMS": "cpi", "INFLATION(%)": "inflation_rate",
        "MORTGAGE INT. MONTHLY AVG(%)": "mortgage_interest_rate",
        "CORP. BOND YIELD(%)": "corporate_bond_yield", "DATE": "date"})
    # DATA.csv tarihleri gün-ay-yıl biçiminde (ör. 01-05-2022 = 1 Mayıs 2022)
    makro["date"] = pd.to_datetime(makro["date"], dayfirst=True)
    makro["ay"] = makro["date"].dt.to_period("M")
    fiyat["ay"] = fiyat["date"].dt.to_period("M")
    df = pd.merge(fiyat, makro[["ay"] + FEATURES], on="ay", how="inner").sort_values("date")

    train, test = df[df["date"] < KESIM], df[df["date"] >= KESIM]
    X_tr, y_tr, X_te, y_te = train[FEATURES], train["close"], test[FEATURES], test["close"]

    baseline = DummyRegressor(strategy="mean").fit(X_tr, y_tr)
    model = LinearRegression().fit(X_tr, y_tr)

    paket = {
        "model": model,
        "features": FEATURES,
        "train_range": {f: [float(X_tr[f].min()), float(X_tr[f].max())] for f in FEATURES},
        "metrics_test": {"linear_regression": metrikler(y_te, model.predict(X_te)),
                         "baseline_mean": metrikler(y_te, baseline.predict(X_te))},
        "info": {"train_rows": int(len(train)), "test_rows": int(len(test)),
                 "train_period": [str(train["date"].min().date()), str(train["date"].max().date())],
                 "test_period": [str(test["date"].min().date()), str(test["date"].max().date())],
                 "split": f"tarihe göre, kesim {KESIM}"},
    }
    joblib.dump(paket, HERE / "model.joblib")
    print("Kaydedildi:", HERE / "model.joblib")
    print("Eğitim:", paket["info"]["train_rows"], "| Test:", paket["info"]["test_rows"])
    for ad, m in paket["metrics_test"].items():
        print(ad, {k: round(v, 3) for k, v in m.items()})


if __name__ == "__main__":
    main()
