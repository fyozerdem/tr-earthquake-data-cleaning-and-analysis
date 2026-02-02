import pandas as pd

# 1) Dosya yolunu tanımla
dosya_yolu = "turkiye_depremler_1900_2025.xlsx"
df = pd.read_excel(dosya_yolu)

# --- 2) Tarih ve Saati Tek Seferde Birleştir ve Parse Et ---
# Tarih ve zamanı birleştirip direkt datetime objesine çeviriyoruz.
# .str[:8] ile zaman kısmındaki salise/milisaniyeleri (örn: .58) buduyoruz.
dt_utc = pd.to_datetime(
    df["Olus tarihi"].astype(str).str.strip() + " " + 
    df["Olus zamani"].astype(str).str.strip().str[:8], 
    format="%Y.%m.%d %H:%M:%S", 
    errors="coerce"
)

# --- 3) Türkiye Saatine Dönüştürme (Tek Satırda) ---
# 2016 öncesi/sonrası ayrımını manuel yapmak yerine 'Europe/Istanbul' kütüphanesine bırakıyoruz.
# Bu kütüphane 2016'dan sonrasının sabit +3 olduğunu zaten biliyor.
dt_tr = dt_utc.dt.tz_localize("UTC").dt.tz_convert("Europe/Istanbul").dt.tz_localize(None)

# --- 4) Kolonları Güncelle ---
df["Olus tarihi"] = dt_tr.dt.date
df["Olus zamani"] = dt_tr.dt.time

# --- 5) Kaydet ---
df.to_excel("turkiye_depremler_v2.xlsx", index=False)