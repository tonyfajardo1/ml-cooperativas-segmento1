import requests
from pathlib import Path

# Carpeta base del proyecto (ml-cooperativas-ecuador)
BASE_DIR = Path(__file__).resolve().parent.parent
RAW_DIR = BASE_DIR / "data" / "raw"
URLS_FILE = RAW_DIR / "urls_pdfs.txt"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Proyecto ML Cooperativas - uso académico)"
}

def download_pdfs():
    # Leer URLs desde urls_pdfs.txt
    with open(URLS_FILE, "r", encoding="utf-8") as f:
        urls = [line.strip() for line in f if line.strip()]

    # Descargar cada PDF
    for url in urls:
        file_name = url.split("/")[-1]      # nombre del archivo.pdf
        out_path = RAW_DIR / file_name

        if out_path.exists():
            print(f"[SKIP] {file_name} ya existe")
            continue

        print(f"[DESCARGANDO] {url}")
        resp = requests.get(url, headers=HEADERS)
        if resp.status_code == 200:
            with open(out_path, "wb") as pdf_file:
                pdf_file.write(resp.content)
            print(f"  -> Guardado en {out_path}")
        else:
            print(f"[ERROR] {url} status {resp.status_code}")

if __name__ == "__main__":
    download_pdfs()
