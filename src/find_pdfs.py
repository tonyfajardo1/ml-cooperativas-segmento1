import re
import requests
from pathlib import Path
from bs4 import BeautifulSoup

URLS_COOPERATIVAS = Path("data/processed/urls_cooperativas.txt")
OUTPUT_PDFS = Path("data/raw/urls_pdfs.txt")

KEYWORDS = [
    "financ",
    "estado",
    "balance",
    "indicad",
    "memoria",
    "seps",
    "2023",
    "2024",
    "2025"
]


def load_websites():
    """Lee los URLs de las cooperativas desde urls_cooperativas.txt"""
    if not URLS_COOPERATIVAS.exists():
        raise FileNotFoundError(f"No existe {URLS_COOPERATIVAS}")

    websites = []

    with open(URLS_COOPERATIVAS, "r", encoding="utf-8") as f:
        for line in f:
            if "->" in line:
                name, url = line.split("->")
                url = url.strip()
                if url.startswith("http"):
                    websites.append((name.strip(), url))

    return websites


def extract_pdfs_from_site(url: str):
    """Descarga una página web y detecta links PDF relevantes."""
    print(f"🔍 Revisando: {url}")

    try:
        r = requests.get(url, timeout=12)
    except:
        print("⚠️ Error de conexión")
        return []

    if r.status_code != 200:
        print(f"⚠️ Error HTTP {r.status_code}")
        return []

    soup = BeautifulSoup(r.text, "html.parser")

    pdf_links = set()

    for link in soup.find_all("a", href=True):
        href = link["href"].lower()

        # solo PDFs
        if ".pdf" not in href:
            continue

        # debe tener alguna palabra clave
        if not any(k in href for k in KEYWORDS):
            continue

        # normalizar rutas relativas
        if href.startswith("http"):
            pdf_links.add(href)
        else:
            base = url.rstrip("/")
            pdf_links.add(base + "/" + href.lstrip("/"))

    return list(pdf_links)


def main():
    websites = load_websites()
    print(f"🔎 Cargando {len(websites)} sitios web de cooperativas...")

    all_pdf_links = []

    for name, site in websites:
        print(f"\n🏦 Cooperativa: {name}")
        links = extract_pdfs_from_site(site)
        print(f"   📄 PDFs encontrados: {len(links)}")

        for l in links:
            all_pdf_links.append(l)

    # Eliminar duplicados
    all_pdf_links = sorted(set(all_pdf_links))

    OUTPUT_PDFS.parent.mkdir(parents=True, exist_ok=True)

    with open(OUTPUT_PDFS, "w", encoding="utf-8") as f:
        for pdf in all_pdf_links:
            f.write(pdf + "\n")

    print("\n✅ Enlaces PDF guardados en:")
    print(f"   {OUTPUT_PDFS.resolve()}")
    print(f"   Total PDFs detectados: {len(all_pdf_links)}")


if __name__ == "__main__":
    main()
