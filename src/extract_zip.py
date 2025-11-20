import zipfile
import os

ZIP_PATH = "data/processed/boletines_segmento1/estados_financieros_2025.zip"
OUTPUT_FOLDER = "data/processed/boletines_segmento1/csv_2025/"

os.makedirs(OUTPUT_FOLDER, exist_ok=True)

def extraer_zip():
    print(f"📦 Extrayendo ZIP: {ZIP_PATH}")
    with zipfile.ZipFile(ZIP_PATH, "r") as zip_ref:
        zip_ref.extractall(OUTPUT_FOLDER)
    print(f"✅ Archivos extraídos en: {OUTPUT_FOLDER}")

if __name__ == "__main__":
    extraer_zip()
