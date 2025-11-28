# -*- coding: utf-8 -*-

import os
import pandas as pd
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin

# ============================================================
# CONFIGURACIÓN
# ============================================================

# Carpeta donde TÚ tienes los xlsm del SEPS
CARPETA_XLSM = "data/processed/boletines_segmento1/csv_2025/2025-EEFF-MEN"

# Carpeta donde queremos dejar el CSV final
CARPETA_SALIDA = "data/processed/segmento1_csv"

# Página principal de estadísticas SFPS
URL_SEPS = "https://estadisticas.seps.gob.ec/index.php/estadisticas-sfps/"

# Carpeta donde se guardará el ZIP descargado
CARPETA_DESCARGAS = "data/processed/boletines_segmento1"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; ml-cooperativas-bot/0.1)"
}

# ============================================================
# PARTE 1: DESCARGAR ZIP 2025
# (ANTES estaba en descargar_zip_seps_2025.py)
# ============================================================

def obtener_url_zip_2025():
    """Busca en la pagina de estadisticas SFPS el link al ZIP de 2025."""
    print("Conectando a SEPS...")
    resp = requests.get(URL_SEPS, headers=HEADERS, timeout=30)
    if resp.status_code != 200:
        print("Error al acceder a la pagina:", resp.status_code)
        return None

    soup = BeautifulSoup(resp.text, "html.parser")

    # 1) Intento principal: buscar el texto de Estados Financieros Mensuales 2025
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

# ============================================================
# PARTE 2: BUSCAR XLSM DE SEGMENTO 1 Y GENERAR CSV
# (ANTES estaba en procesar_segmento1.py)
# ============================================================

def encontrar_archivo_segmento1():
    """
    Busca dentro de CARPETA_XLSM el archivo del Segmento 1.
    Si hay varios meses, se queda con el "más grande" alfabéticamente
    (normalmente será el último mes).
    """
    if not os.path.isdir(CARPETA_XLSM):
        print(f"❌ Carpeta no encontrada: {CARPETA_XLSM}")
        return None

    candidatos = []
    for nombre in os.listdir(CARPETA_XLSM):
        nombre_lower = nombre.lower()
        if nombre_lower.endswith(".xlsm") and "segmento 1" in nombre_lower:
            candidatos.append(nombre)

    if not candidatos:
        print("❌ No se encontró ningún .xlsm de Segmento 1 en la carpeta.")
        return None

    candidatos.sort()
    archivo_elegido = candidatos[-1]  # el "último" => normalmente el mes más reciente
    ruta = os.path.join(CARPETA_XLSM, archivo_elegido)

    print(f"✅ Archivo de Segmento 1 encontrado: {archivo_elegido}")
    return ruta


def procesar_segmento1():
    """
    Lee la hoja '5. INDICADORES FINANCIEROS' del archivo XLSM de Segmento 1
    y genera el CSV final.
    """
    print("== Procesando archivo de Segmento 1 ==")

    os.makedirs(CARPETA_SALIDA, exist_ok=True)

    ruta_xlsm = encontrar_archivo_segmento1()
    if ruta_xlsm is None:
        return

    print("📖 Leyendo hoja '5. INDICADORES FINANCIEROS'...")
    df = pd.read_excel(
        ruta_xlsm,
        sheet_name="5. INDICADORES FINANCIEROS"
    )

    nombre_csv_salida = "segmento1_2025_indicadores.csv"
    ruta_csv_salida = os.path.join(CARPETA_SALIDA, nombre_csv_salida)

    df.to_csv(ruta_csv_salida, index=False)
    print(f"✅ CSV generado correctamente: {ruta_csv_salida}")
    print("🎉 Proceso terminado con éxito")

# ============================================================
# PIPELINE UNIFICADO
# ============================================================

def pipeline_segmento1_2025():
    """
    1) Busca y descarga el ZIP 2025 desde la página de SEPS.
    2) (Opcionalmente tú lo descomprimes donde corresponda).
    3) Procesa el archivo XLSM de Segmento 1 y genera el CSV final.
    """
    url_zip = obtener_url_zip_2025()
    if not url_zip:
        return

    ruta_zip = descargar_zip(url_zip)
    if not ruta_zip:
        return

    # OJO: este script NO descomprime ni mueve el XLSM.
    # Sigue esperando que el XLSM de Segmento 1 exista en CARPETA_XLSM,
    # igual que en tu flujo original.
    procesar_segmento1()


if __name__ == "__main__":
    pipeline_segmento1_2025()
