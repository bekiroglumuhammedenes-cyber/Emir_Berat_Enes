"""Big Tech Stock Analysis API (yerel çalışır).

Çalıştırma (api klasöründe):
    python train_model.py          # bir kez, model.joblib üretir
    uvicorn main:app --reload      # sunucuyu başlatır
Dokümantasyon: http://127.0.0.1:8000/docs
"""
import os
from contextlib import asynccontextmanager
from functools import lru_cache
from pathlib import Path
from typing import List

import joblib
import numpy as np
import pandas as pd
from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from starlette.exceptions import HTTPException as StarletteHTTPException

HERE = Path(__file__).resolve().parent
MODEL_YOLU = HERE / "model.joblib"
UYARI = ("Bu servis bir eğitim ödevi içindir, yatırım tavsiyesi değildir. Makro model test döneminde "
         "negatif R² verdi, ARIMA tahmini 'yarın = bugün' tahmininden belirgin üstün değil.")

PAKET = {}


@asynccontextmanager
async def lifespan(app: FastAPI):
    if MODEL_YOLU.exists():
        PAKET.update(joblib.load(MODEL_YOLU))
    yield


app = FastAPI(
    title="Big Tech Stock Analysis API",
    version="1.0.0",
    description="Makro göstergelerden kapanış fiyatı tahmini ve ARIMA ile ileri fiyat tahmini. " + UYARI,
    lifespan=lifespan,
)

# Allow the published interface to call the local API from its GitHub Pages origin.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://bekiroglumuhammedenes-cyber.github.io"],
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
)


# ---------- Hata yönetimi: hepsi {"hata": ...} biçiminde ----------
@app.exception_handler(RequestValidationError)
async def dogrulama_hatasi(request: Request, exc: RequestValidationError):
    detay = [{"alan": ".".join(str(x) for x in e["loc"] if x != "body"), "mesaj": e["msg"]}
             for e in exc.errors()]
    return JSONResponse(status_code=422, content={"hata": "Girdi doğrulanamadı.", "detay": detay})


@app.exception_handler(StarletteHTTPException)
async def http_hatasi(request: Request, exc: StarletteHTTPException):
    return JSONResponse(status_code=exc.status_code, content={"hata": exc.detail})


# ---------- Şemalar ----------
class MakroGirdi(BaseModel):
    unemployment_rate: float = Field(..., ge=0, le=30, description="İşsizlik oranı (%)")
    cpi: float = Field(..., gt=0, le=1000, description="Tüketici fiyat endeksi (veri setindeki ölçek)")
    inflation_rate: float = Field(..., ge=-10, le=30, description="Enflasyon oranı (%)")
    mortgage_interest_rate: float = Field(..., ge=0, le=30, description="İpotek faizi (%)")
    corporate_bond_yield: float = Field(..., ge=0, le=30, description="Kurumsal tahvil getirisi (%)")

    model_config = {
        "extra": "forbid",
        "json_schema_extra": {"example": {
            "unemployment_rate": 4.0, "cpi": 100.0, "inflation_rate": 2.0,
            "mortgage_interest_rate": 4.0, "corporate_bond_yield": 4.0}},
    }


class MakroCikti(BaseModel):
    tahmin_kapanis_fiyati: float
    uyarilar: List[str]


# ---------- Yardımcılar ----------
def model_hazir():
    if not PAKET:
        raise HTTPException(503, "Model yüklenmedi. Önce 'python train_model.py' çalıştırın, sonra sunucuyu yeniden başlatın.")
    return PAKET


def veri_klasoru() -> Path:
    for a in [os.environ.get("DATA_DIR"), HERE.parent / "data", HERE.parent, HERE]:
        if a and (Path(a) / "big_tech_stock_prices.csv").exists():
            return Path(a)
    raise HTTPException(503, "big_tech_stock_prices.csv bulunamadı. ../data klasörüne koyun ya da DATA_DIR ayarlayın.")


@lru_cache(maxsize=1)
def fiyatlar() -> pd.DataFrame:
    df = pd.read_csv(veri_klasoru() / "big_tech_stock_prices.csv", parse_dates=["date"])
    return df.sort_values(["stock_symbol", "date"])


@lru_cache(maxsize=32)
def arima_model(sembol: str):
    try:
        from statsmodels.tsa.arima.model import ARIMA
    except ImportError:
        raise HTTPException(503, "statsmodels kurulu değil: pip install statsmodels")
    s = fiyatlar()
    s = s[s["stock_symbol"] == sembol]
    # Sayısal indeksle eğitilir (düzensiz tarih indeksi hatasını önler), veri değiştirilmez.
    fit = ARIMA(s["close"].reset_index(drop=True), order=(5, 1, 0)).fit()
    return fit, s["date"].iloc[-1]


# ---------- Uç noktalar ----------
@app.get("/", summary="Karşılama")
def kok():
    return {"mesaj": "Big Tech Stock Analysis API", "dokumantasyon": "/docs"}


@app.get("/health", summary="Servis durumu")
def health():
    return {"durum": "ok", "model_yuklu": bool(PAKET)}


@app.get("/symbols", summary="Desteklenen hisse sembolleri")
def symbols():
    return {"semboller": sorted(fiyatlar()["stock_symbol"].unique().tolist())}


@app.get("/model-info", summary="Makro modelin bilgisi ve test metrikleri")
def model_info():
    p = model_hazir()
    return {"ozellikler": p["features"], "egitim_araligi": p["train_range"],
            "veri_bilgisi": p["info"], "test_metrikleri": p["metrics_test"], "uyari": UYARI}


@app.post("/predict/macro", response_model=MakroCikti, summary="Makro göstergelerden kapanış fiyatı tahmini")
def predict_macro(girdi: MakroGirdi):
    p = model_hazir()
    X = pd.DataFrame([[getattr(girdi, f) for f in p["features"]]], columns=p["features"])
    tahmin = float(p["model"].predict(X)[0])

    uyarilar = [UYARI]
    for f in p["features"]:
        lo, hi = p["train_range"][f]
        v = getattr(girdi, f)
        if not lo <= v <= hi:
            uyarilar.append(f"{f}={v} eğitim aralığının ({lo:.2f} - {hi:.2f}) dışında, tahmin güvenilmez olabilir.")
    if tahmin < 0:
        uyarilar.append("Model negatif fiyat üretti; girdiler eğitim verisinden çok farklı olabilir.")
    return {"tahmin_kapanis_fiyati": round(tahmin, 2), "uyarilar": uyarilar}


@app.get("/forecast/{symbol}", summary="ARIMA(5,1,0) ile ileri fiyat tahmini")
def forecast(symbol: str, days: int = Query(30, ge=1, le=60, description="Kaç iş günü ilerisi (1-60)")):
    sembol = symbol.upper()
    if sembol not in fiyatlar()["stock_symbol"].unique():
        raise HTTPException(404, f"'{symbol}' bulunamadı. Geçerli semboller için GET /symbols kullanın.")
    fit, son_tarih = arima_model(sembol)
    fc = fit.get_forecast(steps=days)
    ort = np.asarray(fc.predicted_mean)
    ci = np.asarray(fc.conf_int(alpha=0.05))
    tarihler = pd.bdate_range(start=son_tarih + pd.offsets.BDay(1), periods=days)
    return {
        "sembol": sembol, "model": "ARIMA(5,1,0)", "son_gercek_tarih": str(son_tarih.date()),
        "tahminler": [{"tarih": str(t.date()), "tahmin": round(float(m), 2),
                       "alt_95": round(float(lo), 2), "ust_95": round(float(hi), 2)}
                      for t, m, (lo, hi) in zip(tarihler, ort, ci)],
        "not": "Tahmin tarihleri iş günlerine göredir, borsa tatilleri dikkate alınmaz. " + UYARI,
    }
