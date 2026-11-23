# PRD: Pipeline Otomatis Penggabungan Data Cuaca dan Gempa

| Item | Keterangan |
| --- | --- |
| Mata kuliah | Workshop Akuisisi Data, Proyek Akhir |
| Topik | Topik 5. Log dan Pipeline Otomatis |
| Studi kasus | Cuaca dan gempa digabung menurut waktu dan lokasi |

---

## 1. Ringkasan

Proyek ini membangun pipeline data otomatis yang mengambil data cuaca per jam dari Open-Meteo (JSON) dan katalog gempa dari USGS (CSV) untuk wilayah Indonesia. Kedua data divalidasi, dibersihkan, diselaraskan menurut jam dan lokasi, dianalisis, lalu dijadikan laporan otomatis. Pipeline juga mendeteksi lonjakan anomali dengan aturan batas dinamis (moving average + k·σ) dan mengukur kualitasnya dengan precision dan recall terhadap berkas kunci anomali yang terpisah.

Fokus penilaian ada pada kualitas pipeline: validasi, ketahanan terhadap galat, pencatatan log, dan keterulangan. Fokusnya bukan pada pembuktian hubungan sebab akibat antara cuaca dan gempa.

## 2. Tujuan dan Non-Tujuan

### 2.1 Tujuan
1. Mengakuisisi dua sumber data berformat berbeda secara otomatis dengan timeout, retry, dan penyimpanan salinan mentah.
2. Menggabungkan data cuaca dan gempa dengan benar menurut stempel waktu (zona Asia/Jakarta) dan lokasi.
3. Mendeteksi lonjakan anomali dan mengukur akurasinya secara objektif.
4. Menjamin pipeline tahan galat dan dapat dijalankan ulang dengan satu perintah.
5. Menjawab empat pertanyaan eksplorasi pada proposal.

### 2.2 Non-Tujuan
- Memprediksi gempa. Korelasi hanya dianalisis secara eksploratif beserta batasannya.
- Memakai model machine learning, model pre-trained, atau layanan AI eksternal (dilarang oleh aturan proyek).
- Membuat antarmuka web atau dasbor interaktif.

## 3. Pertanyaan Eksplorasi

| No | Pertanyaan | Dijawab oleh |
| --- | --- | --- |
| P1 | Seberapa akurat penyelarasan skema dan stempel waktu antara cuaca per jam dan log gempa berdasarkan jendela waktu dan radius? | Modul `merge`, laporan validasi join |
| P2 | Apakah jumlah baris dan kelengkapan kolom utama sesuai ekspektasi tanpa kehilangan entitas penting? | Modul `validate`, uji `assert` |
| P3 | Seberapa kuat korelasi antara parameter meteorologi dan frekuensi atau magnitudo gempa, dan apa batasannya? | Modul `analyze`, bagian batasan di laporan |
| P4 | Pada jam berapa lonjakan anomali paling sering terdeteksi, dan bagaimana precision serta recall detektor? | Modul `detect` dan `evaluate` |

## 4. Sumber Data

### 4.1 Cuaca: Open-Meteo Historical Weather API
- Endpoint: `https://archive-api.open-meteo.com/v1/archive`
- Format: JSON, tanpa API key.
- Variabel per jam: `temperature_2m`, `relative_humidity_2m`, `surface_pressure`, `precipitation`.
- Zona waktu: `Asia/Jakarta`.
- Sifat data: reanalisis ERA5 atau ERA5-Land (estimasi model, bukan pengukuran stasiun). Ada keterlambatan sekitar 5 hari, sehingga rentang tanggal harus berakhir minimal seminggu sebelum hari pengambilan.
- Lisensi: CC BY 4.0, wajib mencantumkan atribusi.

### 4.2 Gempa: USGS FDSN Event API
- Endpoint: `https://earthquake.usgs.gov/fdsnws/event/1/query`
- Format: CSV (`format=csv`).
- Parameter utama: `starttime`, `endtime`, `minmagnitude`, serta batas wilayah (`minlatitude`, `maxlatitude`, `minlongitude`, `maxlongitude`) atau `latitude`, `longitude`, `maxradiuskm`.
- Waktu kejadian dalam UTC dan harus dikonversi ke Asia/Jakarta.
- Alasan memilih USGS: menyediakan katalog historis berdasarkan rentang tanggal. Data terbuka BMKG hanya memuat gempa terbaru, daftar 15 gempa M 5.0+, dan 15 gempa dirasakan, sehingga tidak cukup untuk analisis korelasi.

### 4.3 Wilayah Pengamatan (default, dapat diubah di konfigurasi)
- Gempa: Jawa–Bali dan zona subduksi selatannya, dengan batas wilayah sekitar lintang -12 sampai -5 dan bujur 105 sampai 117.
- Cuaca: 3 titik koordinat (Banten, Yogyakarta, Bali). Setiap gempa dipetakan ke titik cuaca terdekat dalam radius yang ditentukan di konfigurasi.
- Rentang waktu default: 1 tahun terakhir yang lengkap. Dapat diperpanjang lewat konfigurasi bila jumlah gempa kurang.
- Ambang magnitudo default: 4.0, dapat diturunkan lewat konfigurasi.

## 5. Kebutuhan Fungsional

### 5.1 Akuisisi (`src/acquire.py`)
- FR-01: Mengambil data Open-Meteo dan USGS sesuai konfigurasi.
- FR-02: Menerapkan timeout, `try-except`, dan retry otomatis dengan jeda bertahap.
- FR-03: Menyimpan respons mentah ke `data/raw/` pada percobaan pertama yang berhasil.
- FR-04: Bila jaringan gagal dan salinan mentah tersedia, pipeline memakai salinan lokal dan mencatatnya di log.

### 5.2 Validasi skema (`src/validate.py`)
- FR-05: Memeriksa keberadaan file input dan konfigurasi sebelum proses lain berjalan.
- FR-06: Minimal 3 uji `assert`: jumlah kolom, tipe data dan rentang nilai valid, serta non-null pada kunci penggabungan.
- FR-07: Menandai baris rusak dan menghentikan analisis secara teratur bila kolom kunci tidak ada.

### 5.3 Pembersihan (`src/clean.py`)
- FR-08: Membersihkan teks dan format waktu dengan ekspresi reguler (regex).
- FR-09: Menyeragamkan semua stempel waktu ke Asia/Jakarta.
- FR-10: Menghapus duplikat pada kunci (titik, timestamp).

### 5.4 Penggabungan (`src/merge.py`)
- FR-11: Membulatkan waktu gempa ke jam terdekat.
- FR-12: Memetakan gempa ke titik cuaca terdekat berdasarkan jarak (rumus haversine) dan radius pada konfigurasi.
- FR-13: Menghasilkan tabel gabungan per jam yang memuat kolom timestamp, titik, suhu, kelembapan, tekanan, curah hujan, jumlah gempa, dan magnitudo maksimum.
- FR-14: Mencatat jumlah gempa yang tidak berhasil dipetakan agar tidak hilang tanpa jejak.

### 5.5 Analisis (`src/analyze.py`)
- FR-15: Menghitung statistik per jam (rata-rata, simpangan baku, minimum, maksimum).
- FR-16: Menghitung korelasi (Pearson dan Spearman, memakai `scipy`) antara parameter meteorologi dan frekuensi atau magnitudo gempa, disertai nilai p.
- FR-17: Menyertakan teks batasan korelasi di laporan (reanalisis bukan pengukuran, resolusi spasial kasar, jumlah gempa kecil, tidak ada bukti kausalitas).

### 5.6 Deteksi anomali (`src/detect.py`)
- FR-18: Menghitung moving average dan simpangan baku bergulir pada deret terpilih (default: perubahan tekanan per jam).
- FR-19: Menandai jam anomali bila nilai melebihi `rata-rata + k·σ`. Ukuran jendela dan k dibaca dari konfigurasi.
- FR-20: Modul ini tidak boleh membaca berkas kunci anomali.
- FR-21: Menghasilkan histogram jumlah deteksi per jam dalam sehari (menjawab P4).

### 5.7 Berkas kunci anomali dan evaluasi (`src/inject.py`, `src/evaluate.py`)
- FR-22: Skrip `inject.py` menyuntikkan lonjakan sintetis pada jam acak dengan seed tetap, menyimpan data bersuntikan, dan menulis daftar jam anomali ke `data/ground_truth/anomaly_key.csv`.
- FR-23: `evaluate.py` adalah satu-satunya modul yang membaca berkas kunci. Modul ini menghitung TP, FP, FN, precision, dan recall.
- FR-24: Hasil evaluasi disimpan ke `output/metrics.csv`.

### 5.8 Visualisasi dan laporan (`src/report.py`)
- FR-25: Minimal 3 grafik, masing-masing dengan judul, label sumbu, dan satuan. Rencana:
  1. Deret waktu tekanan udara dengan titik anomali ditandai.
  2. Histogram deteksi anomali per jam dalam sehari.
  3. Sebaran korelasi antara parameter cuaca dan frekuensi atau magnitudo gempa.
  4. Peta sebaran gempa dan titik cuaca (opsional).
- FR-26: Menyimpan tabel kejadian anomali ke `output/anomaly_events.csv`.
- FR-27: Menghasilkan laporan evaluasi otomatis (`output/report.md`) berisi statistik per jam, metrik precision dan recall, hasil korelasi, dan batasan.

### 5.9 Logging dan orkestrasi (`main.py`)
- FR-28: Semua tahap mencatat log ke `logs/pipeline.log` dengan tingkat INFO, WARNING, dan ERROR.
- FR-29: `main.py` menjalankan seluruh tahap berurutan dengan satu perintah dan berhenti teratur bila tahap kritis gagal.

## 6. Kebutuhan Nonfungsional

| Kode | Kebutuhan | Cara verifikasi |
| --- | --- | --- |
| NFR-01 | Tidak ada parameter tertanam di kode. Semua nilai operasional ada di `config/config.json`. | Tinjauan kode |
| NFR-02 | Program tidak berhenti tanpa pesan bila file hilang, jaringan gagal, atau data kosong. | Uji 3 skenario gagal |
| NFR-03 | Library terbatas pada numpy, pandas, scipy, matplotlib, requests, Pillow, opencv-python, serta modul bawaan Python. | Pemeriksaan `requirements.txt` |
| NFR-04 | Ukuran folder proyek dan data uji maksimal 20 MB. | Pemeriksaan ukuran folder |
| NFR-05 | Dapat diulang dari folder bersih dengan satu perintah. | Uji jalan ulang |
| NFR-06 | Etika: sumber data dicantumkan, tidak ada data pribadi atau wajah. | Tinjauan README dan laporan |

## 7. Struktur Proyek

```
proyek/
├── config/
│   └── config.json
├── src/
│   ├── acquire.py
│   ├── validate.py
│   ├── clean.py
│   ├── merge.py
│   ├── analyze.py
│   ├── detect.py
│   ├── inject.py
│   ├── evaluate.py
│   └── report.py
├── data/
│   ├── raw/
│   └── ground_truth/
├── logs/
├── tests/
├── output/
├── main.py
├── requirements.txt
└── README.md
```

## 8. Skema Konfigurasi (`config/config.json`)

```json
{
  "timezone": "Asia/Jakarta",
  "date_range": {"start": "YYYY-MM-DD", "end": "YYYY-MM-DD"},
  "weather": {
    "endpoint": "https://archive-api.open-meteo.com/v1/archive",
    "points": [{"name": "titik_1", "lat": 0.0, "lon": 0.0}],
    "hourly": ["temperature_2m", "relative_humidity_2m", "surface_pressure", "precipitation"]
  },
  "quake": {
    "endpoint": "https://earthquake.usgs.gov/fdsnws/event/1/query",
    "bbox": {"minlat": -12, "maxlat": -5, "minlon": 105, "maxlon": 117},
    "min_magnitude": 4.0,
    "match_radius_km": 300
  },
  "network": {"timeout_s": 15, "max_retries": 3, "backoff_s": 2},
  "detector": {"series": "pressure_delta", "window": 24, "k": 3.0},
  "inject": {"seed": 42, "n_anomalies": 30, "magnitude_sigma": 5.0},
  "paths": {
    "raw_dir": "data/raw",
    "ground_truth": "data/ground_truth/anomaly_key.csv",
    "log_file": "logs/pipeline.log",
    "output_dir": "output"
  }
}
```

Nilai koordinat dan tanggal diisi sesuai keputusan kelompok.

## 9. Ukuran Kualitas dan Kriteria Penerimaan

| Kode | Kriteria | Ambang lulus |
| --- | --- | --- |
| AC-01 | Jumlah baris data terproses | Minimal 5.000 baris |
| AC-02 | Kolom utama pada tabel gabungan | Minimal 4 kolom utama, tanpa duplikat kunci |
| AC-03 | Uji otomatis berbasis `assert` | Minimal 3 uji lulus |
| AC-04 | Precision dan recall detektor | Dihitung terhadap berkas kunci terpisah. Target awal precision dan recall masing-masing minimal 0,70 (disesuaikan setelah uji awal) |
| AC-05 | Ketahanan galat | 3 skenario gagal tertangani dengan pesan jelas di log, tanpa crash tak terkendali |
| AC-06 | Keterulangan | Satu perintah dari folder bersih menghasilkan laporan akhir |
| AC-07 | Grafik | Minimal 3 grafik lengkap dengan judul, label sumbu, dan satuan |
| AC-08 | Sumber data | Tercantum di README dan laporan |

## 10. Skenario Pengujian Galat

| Skenario | Cara simulasi | Perilaku yang diharapkan |
| --- | --- | --- |
| S1. File input atau konfigurasi hilang | Ganti nama `config.json` sementara | Log ERROR memuat path file yang dicari, program berhenti teratur |
| S2. Kolom wajib tidak lengkap | Hapus satu kolom kunci dari data uji | Validasi gagal dengan pesan kolom yang hilang, tahap analisis tidak dijalankan |
| S3. Koneksi terputus atau timeout | Set URL salah atau `timeout_s` sangat kecil | Retry sesuai konfigurasi, lalu memakai salinan lokal atau berhenti dengan pesan jelas |

Uji otomatis disimpan di folder `tests/`.

## 11. Alur Pipeline

```
config.json
    |
    v
[Akuisisi] --> data/raw/ (salinan mentah)
    |
    v
[Validasi skema] --> log
    |
    v
[Pembersihan] --> regex, zona waktu, hapus duplikat
    |
    v
[Penggabungan] --> tabel gabungan per jam
    |
    v
[Analisis] --> statistik per jam, korelasi
    |
    v
[Injeksi anomali] --> data bersuntikan + berkas kunci (terpisah)
    |
    v
[Deteksi] --> daftar jam anomali (tanpa baca berkas kunci)
    |
    v
[Evaluasi] --> precision, recall (baca berkas kunci)
    |
    v
[Laporan] --> grafik, CSV, report.md
```

## 12. Pembagian Tugas

| Anggota | Tanggung jawab |
| --- | --- |
| Raihan | `acquire.py`, retry, penyimpanan data mentah, `config.json` |
| Dika | `validate.py`, `clean.py`, `merge.py` |
| Diwa | `analyze.py`, `detect.py`, `inject.py`, `evaluate.py` |
| Aiko | `report.py`, logging, folder `tests/`, README, laporan akhir |

## 13. Rencana Kerja

| Tahap | Kegiatan | Keluaran |
| --- | --- | --- |
| 1 | Siapkan repositori, struktur folder, `config.json`, uji API manual | Kerangka proyek |
| 2 | Akuisisi, validasi, pembersihan | Data bersih |
| 3 | Penggabungan dan analisis | Tabel gabungan, korelasi |
| 4 | Deteksi, injeksi, evaluasi | Metrik precision dan recall |
| 5 | Laporan otomatis, logging, uji 3 skenario gagal | Laporan, log contoh |
| 6 | README, uji jalan ulang dari folder bersih, laporan, presentasi dan demo | Paket akhir |

## 14. Risiko dan Mitigasi

| Risiko | Mitigasi |
| --- | --- |
| Jaringan mati, API lambat, atau rate limit | Retry dengan jeda bertahap, log informatif, salinan mentah untuk mode offline |
| File input atau konfigurasi hilang | Pemeriksaan di awal dan graceful exit dengan path pada log |
| Kolom wajib kurang atau skema sumber berubah | Validasi sebelum pembersihan, tandai baris rusak, hentikan analisis |
| Jumlah gempa terlalu sedikit untuk korelasi | Perluas wilayah, turunkan ambang magnitudo, atau perpanjang rentang waktu lewat konfigurasi |
| Data cuaca terbaru belum tersedia (keterlambatan ERA5) | Akhiri rentang tanggal minimal 7 hari sebelum hari pengambilan |
| Korelasi lemah atau tidak signifikan | Dilaporkan apa adanya beserta batasannya, bukan dipaksakan |

## 15. Keluaran Akhir

- Folder proyek lengkap sesuai Bagian 7 (maksimal 20 MB).
- `README.md` berisi sumber data, cara instal, dan satu perintah menjalankan program.
- `logs/pipeline.log` contoh dari satu eksekusi penuh.
- `output/anomaly_events.csv`, `output/metrics.csv`, `output/report.md`, dan grafik.
