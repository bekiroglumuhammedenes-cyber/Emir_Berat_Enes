# Big Tech Stock Analysis API

Eğitilen modelleri yerelde HTTP servisi olarak sunan küçük bir FastAPI uygulaması.

- `POST /predict/macro`: 5 makro göstergeden kapanış fiyatı tahmini (Doğrusal Regresyon, 2020 öncesi veriyle eğitildi)
- `GET /forecast/{symbol}`: ARIMA(5,1,0) ile ileri iş günü fiyat tahmini
- `GET /symbols`, `GET /model-info`, `GET /health`

> **Uyarı:** Eğitim ödevi içindir, yatırım tavsiyesi değildir. Makro modelin test R² değeri −0,174 (baseline −0,88), yani test döneminde fiyatları açıklayamıyor. ARIMA tahmini de "yarın = bugün" tahmininden belirgin üstün değil.

## Kurulum ve çalıştırma
Python 3.10+ gerekir. `api` klasöründe:

```bash
pip install -r requirements.txt
```

CSV dosyaları (`big_tech_stock_prices.csv`, `DATA.csv`) reponun kökünde ya da `data/` klasöründe olmalı. Başka yerdeyse `DATA_DIR` ortam değişkeniyle klasörü belirtin.

```bash
python train_model.py          # model.joblib üretir (bir kez)
uvicorn main:app --reload      # sunucuyu başlatır
```

Etkileşimli dokümantasyon (Swagger): <http://127.0.0.1:8000/docs>
Çalışırken test için başka bir terminalde: `python test_api.py`

## GitHub Pages arayüzü

Arayüz depodaki `index.html` dosyasıdır. API varsayılan olarak yalnızca yerel bilgisayarda çalışır; sayfadaki API adresini çalışan servise göre ayarlayın. Başka cihazların tahmin uçlarına erişmesi için API'yi ayrıca internete açık bir sunucuda barındırmak gerekir. CORS, yayımlanan `https://bekiroglumuhammedenes-cyber.github.io` kaynağına izin verir.

## Uç noktalar

### POST /predict/macro
```bash
curl -X POST http://127.0.0.1:8000/predict/macro -H "Content-Type: application/json" \
  -d '{"unemployment_rate":6.0,"cpi":100.0,"inflation_rate":2.0,"mortgage_interest_rate":4.0,"corporate_bond_yield":3.5}'
```
Yanıt (200):
```json
{"tahmin_kapanis_fiyati": 65.28,
 "uyarilar": ["Bu servis bir eğitim ödevi içindir, yatırım tavsiyesi değildir. Makro model test döneminde negatif R² verdi, ARIMA tahmini 'yarın = bugün' tahmininden belirgin üstün değil."]}
```
Girdi eğitim aralığının dışındaysa yanıta ek uyarı eklenir. Örnek: `cpi=123.3` (eğitimde en yüksek 108,58).

| Alan | Kabul edilen aralık |
|---|---|
| unemployment_rate | 0 - 30 |
| cpi | 0'dan büyük, en çok 1000 |
| inflation_rate | −10 - 30 |
| mortgage_interest_rate | 0 - 30 |
| corporate_bond_yield | 0 - 30 |

### GET /forecast/{symbol}?days=30
`days` 1 ile 60 arasında (iş günü). Sembol büyük/küçük harf fark etmez. Örnek istek ve gerçek yanıt (`GET /forecast/AAPL?days=5`, ilk 4 gün gösterilmiştir):
```json
{
  "sembol": "AAPL",
  "model": "ARIMA(5,1,0)",
  "son_gercek_tarih": "2022-12-29",
  "tahminler": [
    {"tarih": "2022-12-30", "tahmin": 129.41, "alt_95": 126.66, "ust_95": 132.16},
    {"tarih": "2023-01-02", "tahmin": 129.42, "alt_95": 125.65, "ust_95": 133.2},
    {"tarih": "2023-01-03", "tahmin": 129.23, "alt_95": 124.68, "ust_95": 133.77},
    {"tarih": "2023-01-04", "tahmin": 129.03, "alt_95": 123.87, "ust_95": 134.19}
  ]
}
```
Yanıtın sonunda bir `not` alanı da bulunur. Tahmin tarihleri borsa tatillerini dikkate almaz.

### Diğerleri
- `GET /symbols`: 14 sembolün listesi
- `GET /model-info`: özellikler, eğitim aralığı, veri bilgisi, test metrikleri
- `GET /health`: `{"durum": "ok", "model_yuklu": true}`

## Hata yönetimi
Tüm hatalar `{"hata": ...}` biçiminde döner.

| Durum | Kod | Örnek |
|---|---|---|
| Eksik / fazla / yanlış tür / aralık dışı alan | 422 | `{"hata":"Girdi doğrulanamadı.","detay":[{"alan":"unemployment_rate","mesaj":"Input should be less than or equal to 30"}]}` |
| Bilinmeyen sembol | 404 | `{"hata":"'XYZ' bulunamadı. Geçerli semboller için GET /symbols kullanın."}` |
| Model ya da CSV yok | 503 | `{"hata":"Model yüklenmedi. Önce 'python train_model.py' çalıştırın, ..."}` |

## Tasarım notları
- Makro model, notebook'taki tarihe göre bölmeyle (2020-01-01 öncesi eğitim) aynıdır. Test metrikleri `model-info` içinde görülebilir.
- Makro veri aylıktır ve ilgili ayın her gününe bağlanmıştır.
- Test dönemindeki makro değerler (ör. 2022 enflasyonu) eğitim aralığının dışındadır. API bu durumda uyarı verir.
- ARIMA, veri değiştirilmeden sayısal indeksle eğitilir. Tahmin tarihleri borsa tatillerini dikkate almaz.
- ARIMA modeli ilk istekte eğitilir (birkaç saniye), sonra önbellekten gelir.
