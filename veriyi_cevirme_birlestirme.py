import pandas as pd

dfs = []

for i in range(1, 8):
    txt_file = f"data{i}.txt"
    
    df = pd.read_csv(
        txt_file,
        sep=None,
        engine="python",
        encoding="latin-1"
    )
    dfs.append(df)

# Birleştir
df_all = pd.concat(dfs, ignore_index=True)

# Duplicate sil
unique_cols = ["Olus tarihi", "Olus zamani", "Enlem", "Boylam","Yer"]
df_all = df_all.drop_duplicates(subset=unique_cols).reset_index(drop=True)

# Excel'e yaz
output_path = "turkiye_depremler_1900_2025_DENEME.xlsx"
df_all.to_excel(output_path, index=False)

print("Bitti! Duplicate'ler temizlenmiş veri oluşturuldu.")
