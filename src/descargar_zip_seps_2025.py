# src/descargar_zip_seps_2025.py

import os
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin

URL_SEPS = "https://estadisticas.seps.gob.ec/index.php/estadisticas-sfps/"
CARPETA_DESCARGAS = "data/processed/boletines_segmento1"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; ml-cooperativas-bot/0.1)"
}


def obtener_url_zip_2025():
    """Busca en la pagina de estadisticas SFPS el link al ZIP de 2025."""
    print("Conectando a SEPS...")
    resp = requests.get(URL_SEPS, headers=HEADERS, timeout=30)
    if resp.status_code != 200:
        print("Error al acceder a la pagina:", resp.status_code)
        return None

    soup = BeautifulSoup(resp.text, "html.parser")

    # 1) Intento principal: buscar el texto de Bases de Datos 2025
    for a in soup.find_all("a", href=True):
        texto = a.get_text(strip=True)
        if "Estados Financieros Mensuales" in texto and "2025" in texto:
            return urljoin(URL_SEPS, a["href"])

    # 2) Fallback: cualquier link de descarga con download_id y texto 2025
    for a in soup.find_all("a", href=True):
        texto = a.get_text(strip=True)
        if "2025" in texto and "download_id" in a["href"]:
            return urljoin(URL_SEPS, a["href"])

    print("No se encontro el link al ZIP 2025 en la pagina.")
    return None


def descargar_zip(url_zip):
    """Descarga el ZIP y lo guarda en CARPETA_DESCARGAS."""
    os.makedirs(CARPETA_DESCARGAS, exist_ok=True)

    print("Descargando ZIP desde:", url_zip)
    resp = requests.get(url_zip, headers=HEADERS, stream=True, timeout=60)
    if resp.status_code != 200:
        print("Error al descargar el ZIP:", resp.status_code)
        return None

    # Intentar obtener el nombre real desde el header
    nombre = "estados_financieros_2025.zip"
    cd = resp.headers.get("Content-Disposition", "")
    if "filename=" in cd:
        # Ejemplo: attachment; filename="archivo.zip"
        nombre = cd.split("filename=")[-1].strip().strip('"')

    ruta_destino = os.path.join(CARPETA_DESCARGAS, nombre)

    with open(ruta_destino, "wb") as f:
        for chunk in resp.iter_content(chunk_size=8192):
            if chunk:
                f.write(chunk)

    print("Archivo guardado en:", ruta_destino)
    return ruta_destino


def main():
    url_zip = obtener_url_zip_2025()
    if not url_zip:
        return
    descargar_zip(url_zip)


if __name__ == "__main__":
    main()
