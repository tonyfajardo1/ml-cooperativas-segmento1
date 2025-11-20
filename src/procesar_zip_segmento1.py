# -*- coding: utf-8 -*-

import os
import pandas as pd

# Carpeta donde TÚ tienes los xlsm del SEPS
CARPETA_XLSM = "data/processed/boletines_segmento1/csv_2025/2025-EEFF-MEN"

# Carpeta donde queremos dejar el CSV final
CARPETA_SALIDA = "data/processed/segmento1_csv"


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
    print("== Procesando archivo de Segmento 1 ==")

    os.makedirs(CARPETA_SALIDA, exist_ok=True)

    ruta_xlsm = encontrar_archivo_segmento1()
    if ruta_xlsm is None:
        return

    print("📖 Leyendo hoja '5. INDICADORES FINANCIEROS'...")
    # Ojo: necesitas tener instalado openpyxl:
    # pip install openpyxl
    df = pd.read_excel(
        ruta_xlsm,
        sheet_name="5. INDICADORES FINANCIEROS"
        # si hiciera falta saltar filas de encabezado se puede ajustar con header / skiprows
    )

    nombre_csv_salida = "segmento1_2025_indicadores.csv"
    ruta_csv_salida = os.path.join(CARPETA_SALIDA, nombre_csv_salida)

    df.to_csv(ruta_csv_salida, index=False)
    print(f"✅ CSV generado correctamente: {ruta_csv_salida}")
    print("🎉 Proceso terminado con éxito")


if __name__ == "__main__":
    procesar_segmento1()
