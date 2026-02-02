import pandas as pd
import re
from functools import lru_cache

# ============================================================
# YER PARSER (kurallara göre - FINAL)
# - Girdi: turkiye_depremler_v2.xlsx + Yer sütunu
# - Çıktı: mahalle, ilce, il, ulke, deniz, detay, rule
# - Excel çıktısı: turkiye_depremler_parsed.xlsx (AKTİF)
#
# PATCH (senin istediğin):
# 1) main = ... rstrip()  -> A0 (X- (IL)) tireyi kaybetmesin
# 2) A0 kesin: main.endswith("-") ise mahalle=main[:-1], ilce=NaN
# 3) MERSIN ACIKLARI-MERSIN (AKDENIZ):
#    F kuralında: left_clean == right_il ise ilce=NaN, il=right
# ============================================================

# ----------------------------
# 1) Sabit listeler / sözlükler
# ----------------------------
provinces = {
    'ADANA','ADIYAMAN','AFYONKARAHISAR','AGRI','AMASYA','ANKARA','ANTALYA','ARTVIN','AYDIN','BALIKESIR','BILECIK',
    'BINGOL','BITLIS','BOLU','BURDUR','BURSA','CANAKKALE','CANKIRI','CORUM','DENIZLI','DIYARBAKIR','EDIRNE','ELAZIG',
    'ERZINCAN','ERZURUM','ESKISEHIR','GAZIANTEP','GIRESUN','GUMUSHANE','HAKKARI','HATAY','ISPARTA','MERSIN','ISTANBUL',
    'IZMIR','KARS','KASTAMONU','KAYSERI','KIRKLARELI','KIRSEHIR','KOCAELI','KONYA','KUTAHYA','MALATYA','MANISA',
    'KAHRAMANMARAS','MARDIN','MUGLA','MUS','NEVSEHIR','NIGDE','ORDU','RIZE','SAKARYA','SAMSUN','SIIRT','SINOP','SIVAS',
    'TEKIRDAG','TOKAT','TRABZON','TUNCELI','SANLIURFA','USAK','VAN','YOZGAT','ZONGULDAK','AKSARAY','BAYBURT','KARAMAN',
    'KIRIKKALE','BATMAN','SIRNAK','BARTIN','ARDAHAN','IGDIR','YALOVA','KARABUK','KILIS','OSMANIYE','DUZCE'
}

ulkeler = {
    "IRAN","SURIYE","ERMENISTAN","KIBRIS","IRAK","GURCISTAN","AZERBAYCAN","TURKIYE","BULGARISTAN","YUNANISTAN"
}

# Deniz normalize: EGE-DENIZI gibi varyantlar varsa normalize etsin.
deniz_normalize = {
    "EGE-DENIZI": "EGE DENIZI",
    "DOGU AKDENIZ": "DOGU AKDENIZ",
    "AKDENIZ": "AKDENIZ",
    "EGE DENIZI": "EGE DENIZI",
    "MARMARA DENIZI": "MARMARA DENIZI",
    "KARADENIZ": "KARADENIZ",
}

denizler = set(deniz_normalize.keys()) | set(deniz_normalize.values())

# Göller (whitelist)
goller_whitelist = {"VAN GOLU", "KUS GOLU", "ULUBAT GOLU", "IZNIK GOLU"}

# Ada / ilçe özel kuralları
ada_gorunumlu_ilceler = {"BOZCAADA", "GOKCEADA", "ZEYTINADA", "IGNEADA", "KUSADASI"}
ada_detay = {"MIDILLI ADASI", "SISAM ADASI", "GIRIT ADASI", "RODOS ADASI", "KOS ADASI", "SAKIZ ADASI"}

# ----------------------------
# 2) Yardımcı fonksiyonlar
# ----------------------------
TR_MAP = str.maketrans({
    "Ç":"C","Ğ":"G","İ":"I","Ö":"O","Ş":"S","Ü":"U",
    "ç":"C","ğ":"G","ı":"I","i":"I","ö":"O","ş":"S","ü":"U"
})

dash_regex = re.compile(r"[–—−]")
bracket_km_regex = re.compile(r"\[[^\]]*\]")
multi_space_regex = re.compile(r"\s+")
last_paren_regex = re.compile(r"\(([^()]*)\)\s*$")

border_word_regex = re.compile(r"\bSINIR\b|\bSINIRI\b|\bSINIR BOLGESI\b")

def normalize_text(s: str) -> str:
    if s is None:
        return ""
    s = str(s)
    s = bracket_km_regex.sub("", s)
    s = dash_regex.sub("-", s)
    s = s.replace("--", "-")
    s = s.translate(TR_MAP)
    s = s.upper()
    s = multi_space_regex.sub(" ", s).strip()
    return s

def normalize_deniz(x: str) -> str:
    x = x.strip().upper().translate(TR_MAP)
    x = x.replace("--", "-")
    x = multi_space_regex.sub(" ", x).strip()
    return deniz_normalize.get(x, x)

def clean_aciklari(x: str) -> str:
    x = x.strip()
    x = re.sub(r"\s+ACIKLARI\s*$", "", x).strip()
    return x

def has_country_context(s: str) -> bool:
    tokens = set(re.findall(r"[A-Z0-9]+", s))
    return any(c in tokens for c in ulkeler)

def is_lake_phrase(x: str) -> bool:
    if not x:
        return False
    if x in goller_whitelist:
        return True
    return bool(re.search(r"\bGOLU\b", x))  # TR normalize sonrası GOLÜ -> GOLU

def split_dash_parts(s: str):
    parts = [p.strip() for p in s.split("-")]
    parts = [p for p in parts if p != ""]
    return parts

# ----------------------------
# 3) Parser
# ----------------------------
@lru_cache(maxsize=250000)
def parse_yer(raw: str):
    out = {"mahalle": pd.NA, "ilce": pd.NA, "il": pd.NA, "ulke": pd.NA, "deniz": pd.NA, "detay": pd.NA, "rule": pd.NA}

    s = normalize_text(raw)
    if s == "" or s.lower() == "nan":
        out["rule"] = "NA_EMPTY"
        return out

    # KIBRIS minimal
    if "KIBRIS" in s:
        out["ulke"] = "KIBRIS"
        m = last_paren_regex.search(s)
        if m:
            par = normalize_deniz(m.group(1))
            if par in denizler or "DENIZ" in par:
                out["deniz"] = par
        out["rule"] = "OVERRIDE_KIBRIS"
        return out

    # SINIR override (ülke bağlamlı)
    if border_word_regex.search(s) and has_country_context(s):
        out["detay"] = s
        out["rule"] = "OVERRIDE_BORDER"
        return out

    # Parantez varsa (son parantez)
    m_last = last_paren_regex.search(s)
    if m_last:
        par_content = m_last.group(1).strip()

        # -------------------------
        # PATCH 1: strip -> rstrip
        # Tireyi korumak için sağ boşlukları temizle, son "-" kaybolmasın.
        # -------------------------
        main = s[:m_last.start()].rstrip()

        par_norm = normalize_text(par_content)
        par_deniz = normalize_deniz(par_norm)

        # 3A) Parantez içi IL
        if par_norm in provinces:
            out["il"] = par_norm

            # -------------------------
            # PATCH 2: A0 kesin yakalama
            # main "X-" ise mahalle = X, ilce = NaN
            # Bu kontrol split'ten ÖNCE yapılır (deterministik).
            # -------------------------
            if main.endswith("-"):
                left = main[:-1].strip()
                if left != "":
                    out["mahalle"] = left
                out["ilce"] = pd.NA
                out["rule"] = "A0_MAHALLE_ONLY_IL"
                return out

            parts = split_dash_parts(main)

            # D: il(il)
            if len(parts) == 1 and parts[0] == par_norm:
                out["rule"] = "D_IL_IL"
                return out

            # C: ilce (il)
            if len(parts) == 1:
                out["ilce"] = parts[0]
                out["rule"] = "C_ILCE_IL"
                return out

            # A1: mahalle-ilce (il)
            if len(parts) == 2:
                out["mahalle"] = parts[0]
                out["ilce"] = parts[1]
                out["rule"] = "A1_MAHALLE_ILCE_IL"
                return out

            # B / A2: 2+ tire
            if len(parts) >= 3:
                first = parts[0]
                if is_lake_phrase(first) or first in goller_whitelist:
                    out["detay"] = first
                    out["mahalle"] = parts[1]
                    out["ilce"] = parts[2]
                    out["rule"] = "B_GOL_MAHALLE_ILCE_IL"
                    return out

                out["mahalle"] = parts[0]
                out["ilce"] = parts[1]
                out["detay"] = "-".join(parts[2:]) if len(parts) > 2 else pd.NA
                out["rule"] = "A2_MULTI_PART_IL"
                return out

        # 3B) Parantez içi DENIZ
        is_deniz = (par_deniz in denizler) or ("DENIZ" in par_deniz)
        if is_deniz:
            out["deniz"] = par_deniz
            parts = split_dash_parts(main)

            # E / E2: tire yok
            if len(parts) == 1:
                only = parts[0].strip()

                # E2: IL ACIKLARI (DENIZ)
                if re.search(r"\bACIKLARI\b\s*$", only):
                    cand_il = clean_aciklari(only)
                    if cand_il in provinces:
                        out["il"] = cand_il
                        out["detay"] = pd.NA
                        out["rule"] = "E2_IL_ACIKLARI_DENIZ"
                        return out

                out["detay"] = only
                out["rule"] = "E_DETAY_DENIZ"
                return out

            # F: ilce aciklari - il (deniz)
            if len(parts) == 2:
                left_raw = parts[0].strip()
                right_raw = parts[1].strip()

                left_clean = clean_aciklari(left_raw)
                right_clean = clean_aciklari(right_raw)

                # Sağ taraf il olabilir
                if right_clean in provinces:
                    out["il"] = right_clean

                    # -------------------------
                    # PATCH 3: MERSIN ACIKLARI-MERSIN (AKDENIZ) özel-case
                    # left_clean == right_il ise ilce boş kalmalı.
                    # -------------------------
                    if left_clean == right_clean:
                        out["ilce"] = pd.NA
                        out["detay"] = pd.NA
                        out["rule"] = "F_IL_ACIKLARI_IL_DENIZ"
                        return out

                    # Normal F: ilce = left_clean
                    out["ilce"] = left_clean if left_clean != "" else pd.NA
                    out["rule"] = "F_ILCE_ACIKLARI_IL_DENIZ"
                    return out

                # il değilse fallback
                out["ilce"] = left_clean if left_clean != "" else pd.NA
                out["detay"] = right_clean if right_clean != "" else pd.NA
                out["rule"] = "F_FALLBACK_IL_NOT_FOUND"
                return out

            # G: mahalle-ilce-il aciklari (deniz) + varyantlar
            if len(parts) >= 3:
                out["mahalle"] = parts[0] if parts[0] != "" else pd.NA
                out["ilce"] = parts[1] if parts[1] != "" else pd.NA

                third = parts[2]
                if len(parts) >= 4 and parts[3] == "ACIKLARI":
                    third = f"{third} ACIKLARI"

                il_candidate = clean_aciklari(third)

                if il_candidate in provinces:
                    out["il"] = il_candidate
                    out["rule"] = "G_MAHALLE_ILCE_IL_ACIKLARI_DENIZ"
                    return out
                else:
                    tail = parts[2:]
                    if len(tail) >= 2 and tail[1] == "ACIKLARI":
                        tail = [f"{tail[0]} ACIKLARI"] + tail[2:]
                    out["detay"] = "-".join([p.strip() for p in tail]) if tail else pd.NA
                    out["rule"] = "G_FALLBACK_IL_NOT_FOUND"
                    return out

        # Parantez var ama il/deniz değil
        out["detay"] = s
        out["rule"] = "PAREN_UNKNOWN_BUCKET"
        return out

    # 4) Parantez yok (H grubu)
    # Deniz: sadece exact match veya "... DENIZI" bitişi (DENIZLI kaçmasın)
    if s in denizler or s.endswith(" DENIZI"):
        out["deniz"] = normalize_deniz(s)
        out["rule"] = "H1_ONLY_DENIZ"
        return out

    if s in ulkeler:
        out["ulke"] = s
        out["rule"] = "H2_ONLY_ULKE"
        return out

    if s in provinces:
        out["il"] = s
        out["rule"] = "H3_ONLY_IL"
        return out

    if s in goller_whitelist or is_lake_phrase(s):
        out["detay"] = s
        out["rule"] = "H4_ONLY_GOL_DETAY"
        return out

    if s in ada_gorunumlu_ilceler:
        out["ilce"] = s
        out["rule"] = "H5_ONLY_ILCE_ADA_GORUNUMLU"
        return out

    out["detay"] = s
    out["rule"] = "H9_FALLBACK_DETAY"
    return out


def apply_post_rules(df: pd.DataFrame) -> pd.DataFrame:
    """
    Son dokunuş:
    - Ada görünümlü ilçe yanlışlıkla detay'a düşerse ilçe'ye al
    - Ada detay listesi yanlışlıkla ilce'ye düşerse detay'a al
    """
    mask_ilce_from_detay = df["detay"].isin(ada_gorunumlu_ilceler) & df["ilce"].isna()
    df.loc[mask_ilce_from_detay, "ilce"] = df.loc[mask_ilce_from_detay, "detay"]
    df.loc[mask_ilce_from_detay, "detay"] = pd.NA
    df.loc[mask_ilce_from_detay, "rule"] = "POST_FIX_ADA_GORUNUMLU_ILCE"

    mask_detay_from_ilce = df["ilce"].isin(ada_detay) & df["detay"].isna()
    df.loc[mask_detay_from_ilce, "detay"] = df.loc[mask_detay_from_ilce, "ilce"]
    df.loc[mask_detay_from_ilce, "ilce"] = pd.NA
    df.loc[mask_detay_from_ilce, "rule"] = "POST_FIX_ADA_DETAY"

    return df


# ----------------------------
# 4) Çalıştırma
# ----------------------------
path = r"turkiye_depremler_v2.xlsx"
df = pd.read_excel(path)

if "Yer" not in df.columns:
    raise ValueError("Excel'de 'Yer' sütunu bulunamadı. Sütun adını kontrol et.")

parsed = df["Yer"].apply(parse_yer).apply(pd.Series)

for col in ["mahalle", "ilce", "il", "ulke", "deniz", "detay", "rule"]:
    df[col] = parsed[col]

df = apply_post_rules(df)

# ----------------------------
# 5) Audit: dağılım + örnekler
# ----------------------------
print("\n=== RULE DAĞILIMI (adet) ===")
print(df["rule"].value_counts(dropna=False))

print("\n=== HER RULE'DAN 5 ÖRNEK (Yer) ===")
for rule, g in df.groupby("rule", dropna=False):
    print(f"\n--- {rule} ---")
    sample = g[["Yer", "mahalle", "ilce", "il", "ulke", "deniz", "detay"]].head(5)
    print(sample.to_string(index=False))

print("\n=== PATCH KONTROL ÖRNEKLERİ ===")
tests = [
    "OSMANIYE- (CORUM) [East 1.5 km]",
    "KARAMAN- (BALIKESIR) [East 1.5 km]",
    "BATMAN- (TUNCELI) [East 1.5 km]",
    "MERSIN ACIKLARI-MERSIN (AKDENIZ)",
    "DENIZ- (CORUM) [East 1.5 km]",
]
for t in tests:
    print(t, "->", parse_yer(t))

# ----------------------------
# 6) Excel çıktısı (AKTİF)
# ----------------------------
df.to_excel("turkiye_depremler_parsed.xlsx", index=False)
print("\nOK: turkiye_depremler_parsed.xlsx yazıldı.")
