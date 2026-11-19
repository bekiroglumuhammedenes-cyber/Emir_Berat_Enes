"""API'yi çalışırken test eder. Önce sunucuyu başlatın (uvicorn main:app), sonra:  python test_api.py"""
import requests

BASE = "http://127.0.0.1:8000"
GECERLI = {"unemployment_rate": 4.0, "cpi": 100.0, "inflation_rate": 2.0,
           "mortgage_interest_rate": 4.0, "corporate_bond_yield": 4.0}

vakalar = [
    ("Sağlık kontrolü", "GET", "/health", None, 200),
    ("Sembol listesi", "GET", "/symbols", None, 200),
    ("Model bilgisi", "GET", "/model-info", None, 200),
    ("Geçerli makro tahmini", "POST", "/predict/macro", GECERLI, 200),
    ("Eğitim aralığı dışı girdi (uyarılı 200)", "POST", "/predict/macro",
     {**GECERLI, "cpi": 123.3, "inflation_rate": 8.6}, 200),
    ("Mantıksız işsizlik oranı", "POST", "/predict/macro", {**GECERLI, "unemployment_rate": 99}, 422),
    ("Eksik alan", "POST", "/predict/macro", {k: v for k, v in GECERLI.items() if k != "cpi"}, 422),
    ("Fazladan alan", "POST", "/predict/macro", {**GECERLI, "bilinmeyen": 1}, 422),
    ("Yanlış tür (metin)", "POST", "/predict/macro", {**GECERLI, "cpi": "yüksek"}, 422),
    ("AAPL 5 günlük ARIMA tahmini", "GET", "/forecast/AAPL?days=5", None, 200),
    ("Küçük harfli sembol", "GET", "/forecast/msft?days=3", None, 200),
    ("Olmayan sembol", "GET", "/forecast/XYZ", None, 404),
    ("days sınırı aşıldı", "GET", "/forecast/AAPL?days=500", None, 422),
]

basarili = 0
for ad, metot, yol, govde, beklenen in vakalar:
    r = requests.request(metot, BASE + yol, json=govde, timeout=120)
    ok = r.status_code == beklenen
    basarili += ok
    print(f"[{'GEÇTİ' if ok else 'KALDI'}] {ad}: beklenen {beklenen}, gelen {r.status_code}")
    print("   ", r.text[:300].replace("\n", " "))
print(f"\n{basarili}/{len(vakalar)} test geçti")
