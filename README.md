# Pipeline Otomatis Cuaca dan Gempa

Pipeline ini mengambil cuaca per jam dari [Open-Meteo](https://open-meteo.com/)
dan katalog gempa dari [USGS](https://earthquake.usgs.gov/), menormalisasi waktu
ke `Asia/Jakarta`, memetakan gempa ke titik cuaca dengan haversine, mendeteksi
anomali tekanan, mengevaluasi hasil terhadap kunci sintetis, dan membuat laporan.

## Menjalankan

```bash
python -m pip install -r requirements.txt
python main.py
```

Konfigurasi operasional ada di `config/config.json`. Respons mentah disimpan di
`data/raw/`, log di `logs/pipeline.log`, dan hasil di `output/`. Jika jaringan
gagal, respons mentah yang sudah ada digunakan kembali. Rentang data Open-Meteo
sebaiknya berakhir setidaknya tujuh hari sebelum tanggal eksekusi.

## Pengujian

```bash
python -m pytest -q
```

## Sumber

Data cuaca berasal dari Open-Meteo Historical Weather API (CC BY 4.0), sedangkan
data gempa berasal dari USGS FDSN Event API. Pipeline tidak memakai data pribadi,
model machine learning, atau layanan AI eksternal. Korelasi yang dilaporkan
bersifat eksploratif dan bukan bukti hubungan sebab-akibat.
