# Big Tech Hisse Analizi

Kastamonu Üniversitesi Tosya Meslek Yüksekokulu Robotik ve Yapay Zeka Bölümü, Yapay Zeka Uygulamaları dersi için hazırlanmış öğrenci projesi.

**Etkileşimli arayüz:** [Big Tech Hisse Analizi](https://bekiroglumuhammedenes-cyber.github.io/Emir_Berat_Enes/)  
**GitHub deposu:** [bekiroglumuhammedenes-cyber/Emir_Berat_Enes](https://github.com/bekiroglumuhammedenes-cyber/Emir_Berat_Enes)

![Proje arayüzünü açan QR kod](slides/qr-code.png)

[QR kodu GitHub deposunu doğrudan açsın](slides/qr-repository.png).

> Arayüzü ilk kez yayınlamak için GitHub deposunda **Settings → Pages → Build and deployment → Source: GitHub Actions** seçin. `Publish GitHub Pages` iş akışı `main` dalına gelen her güncellemede sayfayı yayınlar. İlk dağıtım tamamlanınca yukarıdaki sayfa bağlantısını ve QR kodu deneyin.

## Proje içeriği

- [14 şirketin günlük hisse verileri](data/big_tech_stock_prices.csv)
- [Makroekonomik veri dosyası](data/DATA.csv)
- [Temizlenmiş ve aylık makro verileriyle birleştirilmiş veri](data/big_tech_stock_macro_cleaned.csv)
- [Çıktıları temizlenmiş Colab notebook'u](notebooks/big_tech_stock_analysis_clean.ipynb)
- [FastAPI kodu, kurulum ve uç noktalar](api/README.md)
- [API ekran görüntüleri](api/screenshots/)
- [Sunum](slides/borsa_big_tech_sunum.html)
- [Veri hazırlama kodu](scripts/prepare_data.py)

## Arayüz

Sayfa, depodaki hisse CSV'sini tarayıcıda okur. Seçilen şirketlerin düzeltilmiş kapanış fiyatlarını ortak bir 100 başlangıç değerine endeksleyerek gösterir. Korelasyon tablosu günlük fiyat seviyelerini değil aylık getirileri karşılaştırır.

Makro tahmini ve ARIMA uçları FastAPI servisini kullanır. API paketi varsayılan olarak yerel bilgisayarda çalışır; sayfadaki API adresini çalışan servise göre ayarlayın. Başlatma adımları ve CORS yapılandırması [API rehberinde](api/README.md) bulunur. Makro model test döneminde negatif R² üretmiştir; sonuçlar yatırım tavsiyesi değildir.

## Veri kaynakları

- Hisse verisi: [Kaggle — Big Tech Stock Prices](https://www.kaggle.com/datasets/evangower/big-tech-stock-prices). Kaynak veri 14 sembolün 2010–2023 arasındaki günlük OHLC, düzeltilmiş kapanış ve hacim alanlarını içerir.
- Projede temel alınan çalışma: [Kaggle — Big Tech Stock Analysis](https://www.kaggle.com/code/pinuto/big-tech-stock-analysis).
- Makro verisi: [Kaggle — US Macro-Economic Factors data from 2002–2022](https://www.kaggle.com/datasets/sagarvarandekar/macroeconomic-factors-affecting-us-housing-prices).

Notebook'ta `DATA.csv` tarihleri gün-ay-yıl biçiminde olduğundan `dayfirst=True` ile okunur. Hisse ve makro tabloları ay anahtarına göre birleştirilir; temizlenmiş çıktı `scripts/prepare_data.py` ile yeniden üretilebilir.

## GitHub Pages

Depo varsayılan dalı `main` olduğunda Actions iş akışı siteyi yayımlar. İlk etkinleştirmede depo sahibi GitHub'da **Settings → Pages** sayfasını açıp kaynak olarak **GitHub Actions**'ı seçmelidir. Yayın durumunu **Actions** sekmesinden izleyebilirsiniz.



