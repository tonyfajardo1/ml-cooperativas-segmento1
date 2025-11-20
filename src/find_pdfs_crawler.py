import re
import time
from pathlib import Path
from urllib.parse import urlparse, parse_qs, unquote, urlencode

import requests
from bs4 import BeautifulSoup

# ==========================
# CONFIGURACIÓN
# ==========================

COOPS_URLS_FILE = Path("data/processed/urls_cooperativas.txt")
OUT_URLS_PDFS_FILE = Path("data/raw/urls_pdfs.txt")

REQUEST_SLEEP = 1.0  # segundos entre búsquedas, para no spamear el buscador

HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; ML-Cooperativas/1.0)"
}

# Meses en español
MESES = {
    "enero": 1,
    "febrero": 2,
    "marzo": 3,
    "abril": 4,
    "mayo": 5,
    "junio": 6,
    "julio": 7,
    "agosto": 8,
    "septiembre": 9,
    "setiembre": 9,
    "octubre": 10,
    "noviembre": 11,
    "diciembre": 12,
}


# --------------------------
# Utilidades generales
# --------------------------

def parse_coop_line(line: str):
    """
    Lineas del tipo:
    'COOPERATIVA XYZ SEGMENTO 1 -> https://www.sitio.com/'
    """
    if "->" not in line:
        return None, None
    name, url = line.split("->", 1)
    return name.strip(), url.strip()


def limpiar_nombre_para_busqueda(coop_name: str) -> str:
    """
    Quita 'SEGMENTO X', guiones raros, etc., para usar en el query.
    """
    # Eliminar 'SEGMENTO <numero>'
    name = re.sub(r"SEGMENTO\s+\d+", "", coop_name, flags=re.IGNORECASE)
    # Eliminar guiones raros dobles, etc.
    name = name.replace("–", " ").replace("-", " ")
    return " ".join(name.split())


def extract_year(text: str):
    """Busca años entre 2010 y 2039 y devuelve el mayor."""
    years = re.findall(r"(20[1-3][0-9])", text)
    if not years:
        return None
    return max(int(y) for y in years)


def extract_month(text: str):
    """Detecta el mes a partir de nombre o número en la URL."""
    low = text.lower()

    # nombre del mes
    for nombre, num in MESES.items():
        if nombre in low:
            return num

    # /2025/09/
    m = re.search(r"/20[1-3][0-9]/(0?[1-9]|1[0-2])/", low)
    if m:
        return int(m.group(1))

    # 2025-09 o 2025_09
    m = re.search(r"20[1-3][0-9][\-_](0?[1-9]|1[0-2])", low)
    if m:
        return int(m.group(1))

    return None


def choose_latest_pdf(candidates):
    """
    Elige el PDF con mayor (year, month). month puede ser None -> se toma 0.
    """
    if not candidates:
        return None, None, None

    with_year = [c for c in candidates if c["year"] is not None]

    if with_year:
        def key(c):
            m = c["month"] if c["month"] is not None else 0
            return (c["year"], m)

        best = max(with_year, key=key)
        return best["url"], best["year"], best["month"]

    # Ninguno tiene año → devolvemos el primero
    first = candidates[0]
    return first["url"], first["year"], first["month"]


# --------------------------
# Búsqueda en DuckDuckGo
# --------------------------

def decode_ddg_link(href: str) -> str:
    """
    Los links de resultados de DuckDuckGo suelen ser:
    https://duckduckgo.com/l/?uddg=<url_codificada>
    Esta función devuelve la URL real del sitio.
    """
    if "duckduckgo.com/l/?" not in href:
        return href
    parsed = urlparse(href)
    qs = parse_qs(parsed.query)
    if "uddg" in qs:
        return unquote(qs["uddg"][0])
    return href


def search_pdfs_ddg(query: str, max_results: int = 10):
    """
    Hace una búsqueda en DuckDuckGo y devuelve una lista de PDFs candidatos:
    [{url, title, snippet, year, month}, ...]
    """
    params = {
        "q": query,
        "ia": "web",
    }
    url = f"https://duckduckgo.com/html/?{urlencode(params)}"

    resp = requests.get(url, headers=HEADERS, timeout=30)
    resp.raise_for_status()

    soup = BeautifulSoup(resp.text, "html.parser")
    candidates = []

    # Cada resultado suele tener <a class="result__a">Título</a>
    for result in soup.select("div.result__body"):
        a = result.select_one("a.result__a")
        if not a:
            continue

        href = a.get("href", "")
        title = a.get_text(" ", strip=True) or ""
        link = decode_ddg_link(href)

        # snippet
        snippet_el = result.select_one(".result__snippet")
        snippet = snippet_el.get_text(" ", strip=True) if snippet_el else ""

        if ".pdf" not in link.lower():
            # solo queremos PDFs directos (porque usamos filetype:pdf)
            continue

        text_for_time = f"{title} {snippet} {link}"
        year = extract_year(text_for_time)
        month = extract_month(text_for_time)

        candidates.append(
            {
                "url": link,
                "title": title,
                "snippet": snippet,
                "year": year,
                "month": month,
            }
        )

        if len(candidates) >= max_results:
            break

    return candidates


def get_latest_pdf_for_coop(coop_name: str):
    """
    Construye el query tipo:
    "<coop limpia>" estados financieros filetype:pdf
    y devuelve el PDF más reciente encontrado en DuckDuckGo.
    """
    nombre_limpio = limpiar_nombre_para_busqueda(coop_name)
    query = f'"{nombre_limpio}" estados financieros filetype:pdf'

    print(f"   🔍 Query: {query}")

    try:
        candidates = search_pdfs_ddg(query, max_results=10)
    except Exception as e:
        print(f"   ⚠️ Error al buscar en DuckDuckGo: {e}")
        return None, None, None

    print(f"   📑 PDFs candidatos encontrados: {len(candidates)}")

    pdf_url, year, month = choose_latest_pdf(candidates)
    return pdf_url, year, month


# --------------------------
# MAIN
# --------------------------

def main():
    if not COOPS_URLS_FILE.exists():
        print(f"❌ No se encontró {COOPS_URLS_FILE}")
        return

    OUT_URLS_PDFS_FILE.parent.mkdir(parents=True, exist_ok=True)

    with open(COOPS_URLS_FILE, "r", encoding="utf-8") as f:
        lines = [l.strip() for l in f if l.strip()]

    print(f"📄 Se encontraron {len(lines)} cooperativas en {COOPS_URLS_FILE}.\n")

    results = []

    for i, line in enumerate(lines, 1):
        coop_name, website = parse_coop_line(line)
        if not coop_name or not website:
            print(f"[{i}] Línea inválida, se omite: {line}")
            continue

        # 🔴 FILTRO: solo cooperativas de SEGMENTO 1
        if "SEGMENTO 1" not in coop_name.upper():
            print(f"[{i}] {coop_name} no es SEGMENTO 1, se omite.")
            continue

        print(f"[{i}/{len(lines)}] Buscando PDF de último corte para:")
        print(f"   🏦 {coop_name}")

        pdf_url, year, month = get_latest_pdf_for_coop(coop_name)

        if pdf_url:
            y = year if year is not None else "?"
            m = month if month is not None else "?"
            print(f"   ✅ PDF elegido: {pdf_url} (año={y}, mes={m})")
            results.append((coop_name, y, m, pdf_url))
        else:
            print("   ❌ No se encontró PDF de estados financieros.\n")

        print()
        time.sleep(REQUEST_SLEEP)

    # Guardar resultados solo de SEGMENTO 1
    with open(OUT_URLS_PDFS_FILE, "w", encoding="utf-8") as f:
        for coop_name, y, m, pdf_url in results:
            f.write(f"{coop_name} | {y} | {m} | {pdf_url}\n")

    print("💾 Resultados guardados en:")
    print(f"   {OUT_URLS_PDFS_FILE.resolve()}")
    print(f"   Total de cooperativas SEGMENTO 1 con PDF encontrado: {len(results)}")


if __name__ == "__main__":
    main()
