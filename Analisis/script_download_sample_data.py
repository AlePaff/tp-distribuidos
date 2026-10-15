import os
import zipfile
import kagglehub
import pandas as pd
import pyarrow.parquet as pq

# ================= CONFIGURACIÓN =================
DATASET_BASE = "wikimedia-foundation/wikipedia-structured-contents"
EN_BASE = "enwiki/data/enwiki_namespace_0_"
FR_BASE = "frwiki/data/frwiki_namespace_0_"

# Shards a descargar (suficiente para 5 GB comprimidos)
EN_SHARDS = 10   # ~4 GB
FR_SHARDS = 3    # ~1.1 GB

TARGET_SIZES_MB = [10, 100, 1024] #, 5120]

WORK_DIR = "wikipedia_lotes"
EN_DIR = os.path.join(WORK_DIR, "en_shards")
FR_DIR = os.path.join(WORK_DIR, "fr_shards")
OUT_DIR = os.path.join(WORK_DIR, "output")

os.makedirs(EN_DIR, exist_ok=True)
os.makedirs(FR_DIR, exist_ok=True)
os.makedirs(OUT_DIR, exist_ok=True)

# ================= DESCARGA =================
def shard_exists(output_dir, filename):
    """Verifica si el shard ya fue descargado en output_dir o subcarpetas."""
    for root, _, files in os.walk(output_dir):
        if filename in files:
            return True
    return False

print("Descargando shards de inglés...")
for i in range(EN_SHARDS):
    filename = f"enwiki_namespace_0_{i:05}.parquet"
    if shard_exists(EN_DIR, filename):
        print(f"  [SKIP] {filename} ya existe")
        continue
    file_path = f"{EN_BASE}{i:05}.parquet"
    print(f"  -> {file_path}")
    kagglehub.dataset_download(DATASET_BASE, path=file_path, output_dir=EN_DIR)

print("Descargando shards de francés...")
for i in range(FR_SHARDS):
    filename = f"frwiki_namespace_0_{i:05}.parquet"
    if shard_exists(FR_DIR, filename):
        print(f"  [SKIP] {filename} ya existe")
        continue
    file_path = f"{FR_BASE}{i:05}.parquet"
    print(f"  -> {file_path}")
    kagglehub.dataset_download(DATASET_BASE, path=file_path, output_dir=FR_DIR)


# ================= LISTAR ARCHIVOS =================
def list_parquet_files(directory):
    files = []
    for root, _, filenames in os.walk(directory):
        for f in filenames:
            if f.endswith('.parquet'):
                files.append(os.path.join(root, f))
    return files

en_files = list_parquet_files(EN_DIR)
fr_files = list_parquet_files(FR_DIR)
print(f"Archivos EN: {len(en_files)}, FR: {len(fr_files)}")

# ================= TAMAÑO PROMEDIO COMPRIMIDO POR FILA =================
def avg_row_size(files):
    total_size = sum(os.path.getsize(f) for f in files)
    total_rows = sum(pq.read_metadata(f).num_rows for f in files)
    return total_size / total_rows

avg_en = avg_row_size(en_files)
avg_fr = avg_row_size(fr_files)
print(f"Tamaño promedio comprimido por fila EN: {avg_en:.2f} bytes, FR: {avg_fr:.2f} bytes")

# Proporción de tamaño
total_en_size = sum(os.path.getsize(f) for f in en_files)
total_fr_size = sum(os.path.getsize(f) for f in fr_files)
total_size = total_en_size + total_fr_size
PROP_EN = total_en_size / total_size
PROP_FR = total_fr_size / total_size
print(f"Proporción EN: {PROP_EN:.4f}, FR: {PROP_FR:.4f}")

# ================= MUESTREO =================
def sample_from_files(files, target_rows):
    if target_rows <= 0:
        return pd.DataFrame()
    file_rows = [pq.read_metadata(f).num_rows for f in files]
    total_rows = sum(file_rows)
    rows_per_file = [int(target_rows * (r / total_rows)) for r in file_rows]
    # Ajustar suma exacta
    diff = target_rows - sum(rows_per_file)
    if diff > 0:
        for i in range(diff):
            rows_per_file[i % len(rows_per_file)] += 1
    elif diff < 0:
        for i in range(-diff):
            rows_per_file[i % len(rows_per_file)] -= 1
    
    dfs = []
    for f, n in zip(files, rows_per_file):
        if n > 0:
            df = pd.read_parquet(f)
            if n < len(df):
                df = df.sample(n=n, random_state=42)
            dfs.append(df)
    return pd.concat(dfs, ignore_index=True) if dfs else pd.DataFrame()

# ================= GENERAR LOTES =================
for size_mb in TARGET_SIZES_MB:
    print(f"\nGenerando lote de {size_mb} MB...")
    target_bytes = size_mb * 1024 * 1024
    en_bytes = target_bytes * PROP_EN
    fr_bytes = target_bytes * PROP_FR
    en_rows = int(en_bytes / avg_en)
    fr_rows = int(fr_bytes / avg_fr)
    print(f"  Filas necesarias: EN={en_rows}, FR={fr_rows}")
    
    df_en = sample_from_files(en_files, en_rows)
    df_fr = sample_from_files(fr_files, fr_rows)
    
    df = pd.concat([df_en, df_fr], ignore_index=True)
    df = df.sample(frac=1, random_state=42).reset_index(drop=True)
    
    out_parquet = os.path.join(OUT_DIR, f"lote_{size_mb}MB.parquet")
    df.to_parquet(out_parquet, index=False)
    actual_size = os.path.getsize(out_parquet)
    print(f"  Parquet generado: {out_parquet} ({actual_size / 1024 / 1024:.2f} MB)")
    
    # zip_file = os.path.join(OUT_DIR, f"lote_{size_mb}MB.zip")
    # with zipfile.ZipFile(zip_file, 'w', zipfile.ZIP_DEFLATED) as zf:
    #     zf.write(out_parquet, os.path.basename(out_parquet))
    # print(f"  ZIP creado: {zip_file}")
    # os.remove(out_parquet)

print("\n¡Listo! Los archivos están en:", OUT_DIR)