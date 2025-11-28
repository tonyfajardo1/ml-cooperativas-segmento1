# -*- coding: utf-8 -*-

import os
import pandas as pd
import numpy as np

# Carpeta donde tienes los XLSM del SEPS
CARPETA_XLSM = "data/processed/boletines_segmento1/csv_2025/2025-EEFF-MEN"

# Carpeta de salida para CSVs
CARPETA_SALIDA = "data/processed/segmento1_csv"


# ======================================================
# 1) Buscar archivo del Segmento 1
# ======================================================
def encontrar_archivo_segmento1():
    """
    Busca dentro de CARPETA_XLSM el archivo del Segmento 1.
    Si hay varios, toma el último alfabéticamente.
    """
    if not os.path.isdir(CARPETA_XLSM):
        print(f"❌ Carpeta no encontrada: {CARPETA_XLSM}")
        return None

    candidatos = []
    for nombre in os.listdir(CARPETA_XLSM):
        nl = nombre.lower()
        if nl.endswith(".xlsm") and "segmento 1" in nl:
            candidatos.append(nombre)

    if not candidatos:
        print("❌ No se encontró ningún .xlsm de Segmento 1 en la carpeta.")
        return None

    candidatos.sort()
    archivo_elegido = candidatos[-1]
    ruta = os.path.join(CARPETA_XLSM, archivo_elegido)
    print(f"✅ Archivo de Segmento 1 encontrado: {archivo_elegido}")
    return ruta


# ======================================================
# 2) Leer hoja de indicadores y guardar CSV crudo
# ======================================================
def leer_hoja_indicadores(ruta_xlsm: str) -> str:
    """
    Lee la hoja '5. INDICADORES FINANCIEROS' del XLSM
    y guarda un CSV crudo (tal cual sale de Excel).
    """
    os.makedirs(CARPETA_SALIDA, exist_ok=True)

    print("📖 Leyendo hoja '5. INDICADORES FINANCIEROS' (crudo)...")
    # header=None para no usar ninguna fila como encabezado todavía
    df_raw = pd.read_excel(
        ruta_xlsm,
        sheet_name="5. INDICADORES FINANCIEROS",
        header=None
    )

    ruta_csv_crudo = os.path.join(CARPETA_SALIDA, "segmento1_2025_indicadores_crudo.csv")
    df_raw.to_csv(ruta_csv_crudo, index=False)
    print(f"✅ CSV crudo generado correctamente: {ruta_csv_crudo}")
    print("Shape crudo:", df_raw.shape)

    return ruta_csv_crudo


# ======================================================
# 3) Construir dataset limpio (cooperativas x indicadores)
# ======================================================
def construir_dataset_limpio(ruta_csv_crudo: str) -> str:
    """
    A partir del CSV crudo:
    - Detecta fila con nombres de cooperativas.
    - Detecta filas con valores numéricos (indicadores).
    - Construye tabla final con filas = cooperativas, columnas = indicadores.
    """
    print("\n🧹 Construyendo dataset limpio de indicadores por cooperativa...")
    df_raw = pd.read_csv(ruta_csv_crudo, header=None)

    # 3.1 Eliminar filas y columnas completamente vacías
    df = df_raw.dropna(how="all").dropna(axis=1, how="all")

    # 3.2 Detectar la fila que contiene los nombres de las cooperativas
    def contar_strings(fila):
        return sum(isinstance(x, str) and x.strip() != "" for x in fila)

    conteo_strings = df.apply(contar_strings, axis=1)
    fila_coops = conteo_strings.idxmax()

    nombres_coops = df.iloc[fila_coops].tolist()
    # La primera celda suele ser algo como número/empty; ignoramos col 0
    nombres_coops = ["Indicador"] + nombres_coops[1:]

    print(f"➡ Fila con nombres de cooperativas: {fila_coops}")
    print("Ejemplo de nombres de cooperativas:", nombres_coops[1:6])

    # 3.3 Quedarnos con las filas por debajo (posibles indicadores)
    df_ind = df.iloc[fila_coops + 1:].copy()

    # La primera columna será el nombre del indicador
    df_ind.rename(columns={df_ind.columns[0]: "Indicador"}, inplace=True)

    # 3.4 Filtrar filas que tengan suficientes números (indicadores reales)
    def contar_numericos(row):
        vals = pd.to_numeric(row[1:], errors="coerce")
        return vals.notna().sum()

    df_ind["num_numericos"] = df_ind.apply(contar_numericos, axis=1)
    # Umbral: al menos 5 cooperativas con número
    df_ind = df_ind[df_ind["num_numericos"] > 5].drop(columns=["num_numericos"])

    # 3.5 Asignar nombres de columnas correctos (Indicador + cooperativas)
    df_ind.columns = nombres_coops[: len(df_ind.columns)]

    # 3.6 Guardar tabla en formato indicadores x cooperativas (por si acaso)
    ruta_wide = os.path.join(CARPETA_SALIDA, "segmento1_2025_indicadores_por_indicador.csv")
    df_ind.to_csv(ruta_wide, index=False)
    print(f"✅ Tabla indicadores x cooperativas guardada en: {ruta_wide}")

    # 3.7 Transponer → filas = cooperativas, columnas = indicadores
    df_t = df_ind.set_index("Indicador").T.reset_index()
    df_t.rename(columns={"index": "Cooperativa"}, inplace=True)

    # 3.8 Convertir todas las columnas (menos Cooperativa) a numérico
    for col in df_t.columns[1:]:
        df_t[col] = pd.to_numeric(df_t[col], errors="coerce")

    print("\n📊 Info de la tabla final (cooperativas x indicadores):")
    print(df_t.info())

    ruta_final = os.path.join(CARPETA_SALIDA, "segmento1_2025_indicadores_limpio.csv")
    df_t.to_csv(ruta_final, index=False)
    print(f"\n✅ Tabla final lista: {ruta_final}")

    return ruta_final


# ======================================================
# MAIN
# ======================================================
def procesar_segmento1():
    print("== Procesando archivo de Segmento 1 ==")

    ruta_xlsm = encontrar_archivo_segmento1()
    if ruta_xlsm is None:
        return

    ruta_crudo = leer_hoja_indicadores(ruta_xlsm)
    ruta_final = construir_dataset_limpio(ruta_crudo)

    print("\n🎉 Proceso terminado con éxito.")
    print("   - CSV crudo :", ruta_crudo)
    print("   - CSV final :", ruta_final)


if __name__ == "__main__":
    procesar_segmento1()
