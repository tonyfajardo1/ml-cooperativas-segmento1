import os
import json
from pathlib import Path

import pandas as pd
from dotenv import load_dotenv
from groq import Groq
from PyPDF2 import PdfReader

# ---------------------------------------------------------
# Configuración de rutas
# ---------------------------------------------------------
BASE_DIR = Path(__file__).resolve().parent.parent
RAW_DIR = BASE_DIR / "data" / "raw"
PROC_DIR = BASE_DIR / "data" / "processed"

# ---------------------------------------------------------
# Cargar variables de entorno y crear cliente de Groq
# ---------------------------------------------------------
load_dotenv()
client = Groq(api_key=os.getenv("GROQ_API_KEY"))

PROC_DIR.mkdir(parents=True, exist_ok=True)


# ---------------------------------------------------------
# Leer texto desde PDF
# ---------------------------------------------------------
def read_pdf_text(pdf_path: Path) -> str:
    reader = PdfReader(str(pdf_path))
    text = []
    for page in reader.pages:
        page_text = page.extract_text() or ""
        text.append(page_text)
    return "\n".join(text)


# ---------------------------------------------------------
# PDF -> JSON (vía Groq) -> DataFrame
# ---------------------------------------------------------
def extract_table_from_pdf(pdf_path: Path) -> pd.DataFrame:
    text = read_pdf_text(pdf_path)

    prompt = f"""
Eres un analista financiero profesional. Recibirás el texto de un PDF que contiene
indicadores financieros de cooperativas del Ecuador, segmento 1.

Tarea:
1. Identifica cada COOPERATIVA.
2. Extrae todos los indicadores financieros disponibles.
3. Devuelve SOLO un JSON válido con la estructura EXACTA:

{{
  "data": [
    {{
      "cooperativa": "...",
      "segmento": "1",
      "rating": "A/B/C/null",
      "periodo": "YYYY-MM o null",
      "activos_improductivos_sobre_total_activos": número o null,
      "activos_productivos_sobre_pasivo_con_costo": número o null,
      "morosidad_total": número o null,
      "cobertura_cartera_problematica": número o null,
      "gastos_operacion_sobre_activo_productivo": número o null,
      "gastos_personal_sobre_activo_promedio": número o null,
      "roa": número o null,
      "roe": número o null,
      "cartera_bruta_sobre_depositos": número o null,
      "fondos_disponibles_sobre_depositos_corto_plazo": número o null,
      "cartera_improductiva_descubierta_sobre_patrimonio": número o null
    }}
  ]
}}

Reglas:
- Devuelve únicamente JSON válido.
- Los porcentajes deben ser números (3.4 si es 3.4%).
- Si un dato no está, usa null.
- NO añadas explicación ni comentarios.

Texto del PDF:
{text[:15000]}
"""

    # -------------------------------
    # Llamada a la API usando Groq
    # -------------------------------
    response = client.chat.completions.create(
        model="qwen/qwen3-32b",
        messages=[{"role": "user", "content": prompt}],
        temperature=0,
    )

    output_text = response.choices[0].message.content

    # Intentar parsear JSON
    try:
        data = json.loads(output_text)
    except json.JSONDecodeError:
        # Limpieza automática si el modelo agrega texto extra
        start = output_text.find("{")
        end = output_text.rfind("}") + 1
        if start != -1 and end != -1:
            cleaned = output_text[start:end]
            data = json.loads(cleaned)
        else:
            raise ValueError("La respuesta del modelo no es JSON válido:\n" + output_text)

    df = pd.DataFrame(data["data"])
    return df


# ---------------------------------------------------------
# Procesar todos los PDFs
# ---------------------------------------------------------
def process_all_pdfs():
    pdf_files = list(RAW_DIR.glob("*.pdf"))
    all_dfs = []

    if not pdf_files:
        print("[WARN] No se encontraron PDFs en data/raw")
        return

    for pdf in pdf_files:
        print(f"[LLM] Procesando {pdf.name}")
        try:
            df = extract_table_from_pdf(pdf)
            out_csv = PROC_DIR / f"{pdf.stem}.csv"
            df.to_csv(out_csv, index=False)
            print(f"  -> Guardado {out_csv}")
            all_dfs.append(df)
        except Exception as e:
            print(f"[ERROR] {pdf.name}: {e}")

    if all_dfs:
        full = pd.concat(all_dfs, ignore_index=True)
        full.to_csv(PROC_DIR / "cooperativas_segmento1_full.csv", index=False)
        print(f"[OK] Consolidado en data/processed/cooperativas_segmento1_full.csv")


# ---------------------------------------------------------
# Main
# ---------------------------------------------------------
if __name__ == "__main__":
    process_all_pdfs()
