#!/usr/bin/env python3
"""
download_vatican_images.py

Script para baixar automaticamente as 24 obras dos Museus Vaticanos
a partir da API pública do Wikimedia Commons, salvando cada arquivo
com a nomenclatura exata solicitada.

Requisitos: Apenas Python 3 padrão (nenhuma biblioteca externa necessária).
Uso: python3 download_vatican_images.py [pasta_destino]
"""

import os
import sys
import json
import time
import urllib.request
import urllib.parse
from pathlib import Path

# Lista das 24 obras com o nome de arquivo desejado e o termo de busca no Wikimedia Commons
WORKS = [
    ("01_triptico_stefaneschi", "Stefaneschi Triptych Giotto"),
    ("02_anjos_musicos_melozzo", "Melozzo da Forli angel musician Vatican"),
    ("03_transfiguracao_rafael", "Transfiguration Raphael Vatican"),
    ("04_sao_jeronimo_leonardo", "Saint Jerome Leonardo da Vinci Vatican"),
    ("05_deposicao_caravaggio", "Entombment Caravaggio Vatican"),
    ("06_pinha_bronze", "Pigna Cortile della Pigna Vatican"),
    ("07_laocoonte", "Laocoon and His Sons Vatican"),
    ("08_apolo_belvedere", "Apollo Belvedere Vatican"),
    ("09_torso_belvedere", "Belvedere Torso Vatican"),
    ("10_sala_redonda", "Sala Rotonda Vatican Museums"),
    ("11_sarcofago_santa_helena", "Sarcophagus Helena Constantina Vatican"),
    ("12_galeria_candelabros", "Galleria dei Candelabri Vatican"),
    ("13_tapecaria_ressurreicao", "Resurrection tapestry Vatican Galleria degli Arazzi"),
    ("14_galeria_mapas", "Galleria delle Carte Geografiche Vatican"),
    ("15_escola_de_atenas", "School of Athens Raphael"),
    ("16_disputa_sacramento", "Disputation of the Holy Sacrament Raphael"),
    ("17_libertacao_sao_pedro", "Liberation of Saint Peter Raphael Stanza di Eliodoro"),
    ("18_incendio_do_borgo", "Fire in the Borgo Raphael"),
    ("19_batalha_ponte_milvia", "Battle of the Milvian Bridge Sala di Costantino"),
    ("20_pinturicchio_sala_santos", "Pinturicchio Sala dei Santi Borgia Apartments"),
    ("21_teto_sistina_visao_geral", "Sistine Chapel ceiling Michelangelo"),
    ("22_criacao_de_adao", "Creation of Adam Michelangelo"),
    ("23_juizo_final", "Last Judgement Michelangelo Sistine"),
    ("24_entrega_das_chaves_perugino", "Delivery of the Keys Perugino Sistine"),
]

# User-Agent descritivo exigido pelas políticas de API da Wikimedia
USER_AGENT = "VaticanArtDownloader/1.0 (Personal/Educational tool; urllib-python)"

def search_wikimedia_image(query: str):
    """
    Busca o primeiro arquivo de imagem correspondente na API do Wikimedia Commons.
    Retorna (url_imagem, titulo_arquivo) ou (None, None).
    """
    params = {
        "action": "query",
        "generator": "search",
        "gsrsearch": query,
        "gsrnamespace": "6",  # Espaço reservado para arquivos de mídia (File:)
        "gsrlimit": "3",      # Analisa até 3 resultados para filtrar imagens
        "prop": "imageinfo",
        "iiprop": "url|mime",
        "format": "json"
    }
    api_url = f"https://commons.wikimedia.org/w/api.php?{urllib.parse.urlencode(params)}"

    req = urllib.request.Request(api_url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except Exception as e:
        print(f"  [!] Erro ao consultar a API: {e}")
        return None, None

    pages = data.get("query", {}).get("pages", {})
    if not pages:
        return None, None

    # Encontra a primeira imagem válida (JPEG, PNG, WebP, etc.)
    for page_id, page_info in pages.items():
        image_info = page_info.get("imageinfo", [])
        if not image_info:
            continue
        first_info = image_info[0]
        mime = first_info.get("mime", "")
        file_url = first_info.get("url")
        title = page_info.get("title", "")
        if mime.startswith("image/") and file_url:
            return file_url, title

    return None, None

def download_file(url: str, dest_path: Path):
    """Baixa o arquivo binário a partir da URL e salva no caminho indicado."""
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=30) as resp, open(dest_path, "wb") as f:
        while True:
            chunk = resp.read(65536)
            if not chunk:
                break
            f.write(chunk)

def main():
    dest_dir_name = sys.argv[1] if len(sys.argv) > 1 else "imagens_vaticano"
    dest_dir = Path(dest_dir_name)
    dest_dir.mkdir(parents=True, exist_ok=True)

    print("=" * 65)
    print(f"Iniciando download de {len(WORKS)} imagens dos Museus Vaticanos")
    print(f"Pasta de destino: {dest_dir.resolve()}")
    print("=" * 65)

    sucessos = 0
    falhas = 0

    for idx, (target_name, query) in enumerate(WORKS, start=1):
        print(f"\n[{idx:02d}/{len(WORKS):02d}] Buscando: {target_name} ({query})...")
        image_url, file_title = search_wikimedia_image(query)

        if not image_url:
            print(f"  [X] Nenhuma imagem encontrada para o termo: '{query}'")
            falhas += 1
            continue

        # Determina a extensão do arquivo a partir da URL
        parsed = urllib.parse.urlparse(image_url)
        ext = os.path.splitext(parsed.path)[1].lower()
        if not ext or len(ext) > 5:
            ext = ".jpg"

        dest_file = dest_dir / f"{target_name}{ext}"
        print(f"  Origem: {file_title}")
        print(f"  Salvando como: {dest_file.name}")

        try:
            download_file(image_url, dest_file)
            size_kb = dest_file.stat().st_size / 1024
            print(f"  [OK] Concluído com sucesso ({size_kb:.1f} KB)")
            sucessos += 1
        except Exception as e:
            print(f"  [!] Falha no download: {e}")
            falhas += 1

        # Respeita o rate limit do Wikimedia Commons
        time.sleep(0.5)

    print("\n" + "=" * 65)
    print(f"Processo finalizado!")
    print(f"Sucessos: {sucessos} | Falhas: {falhas} | Total: {len(WORKS)}")
    print(f"Arquivos salvos em: {dest_dir.resolve()}")
    print("=" * 65)

if __name__ == "__main__":
    main()
