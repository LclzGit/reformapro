#!/usr/bin/env python3
"""
Busca as leis do planalto.gov.br e converte para o formato de chunks do ReformaPro.
Uso: python3 scripts/fetch_laws.py [lcp214|lcp227|reg_cbs|all]
"""
import sys, re, json, time, urllib.request, urllib.error
from pathlib import Path

ROOT = Path(__file__).parent.parent

SOURCES = {
    'lcp214': {
        'url': 'https://www.planalto.gov.br/ccivil_03/leis/lcp/lcp214.htm',
        'source': 'LCP 214',
        'out': 'lcp214.json',
    },
    'lcp227': {
        'url': 'https://www.planalto.gov.br/ccivil_03/leis/lcp/lcp227.htm',
        'source': 'LCP 227',
        'out': 'lcp227.json',
    },
    'reg_cbs': {
        'url': 'https://www.planalto.gov.br/ccivil_03/_ato2023-2026/2026/decreto/d12955.htm',
        'source': 'Regulamento CBS',
        'out': 'reg_cbs.json',
    },
}

HEADERS = {
    'User-Agent': (
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
        'AppleWebKit/537.36 (KHTML, like Gecko) '
        'Chrome/124.0.0.0 Safari/537.36'
    ),
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'pt-BR,pt;q=0.9,en;q=0.8',
    'Accept-Encoding': 'gzip, deflate, br',
    'Connection': 'keep-alive',
}


def fetch_html(url: str) -> str:
    req = urllib.request.Request(url, headers=HEADERS)
    for attempt in range(3):
        try:
            with urllib.request.urlopen(req, timeout=60) as resp:
                raw = resp.read()
                # Handle gzip/br encoding transparently
                ct = resp.headers.get('Content-Type', '')
                enc = resp.headers.get('Content-Encoding', '')
                if 'gzip' in enc:
                    import gzip
                    raw = gzip.decompress(raw)
                elif 'br' in enc:
                    import brotli
                    raw = brotli.decompress(raw)
                charset = 'utf-8'
                if 'charset=' in ct:
                    charset = ct.split('charset=')[-1].split(';')[0].strip()
                return raw.decode(charset, errors='replace')
        except urllib.error.HTTPError as e:
            print(f'  HTTP {e.code} on attempt {attempt+1}')
            if attempt < 2:
                time.sleep(5 * (attempt + 1))
            else:
                raise
        except Exception as e:
            print(f'  Error on attempt {attempt+1}: {e}')
            if attempt < 2:
                time.sleep(5 * (attempt + 1))
            else:
                raise


def clean_text(text: str) -> str:
    """Remove excess whitespace and normalize."""
    text = re.sub(r'\xa0', ' ', text)           # non-breaking spaces
    text = re.sub(r'[ \t]+', ' ', text)          # multiple spaces
    text = re.sub(r'\n{3,}', '\n\n', text)       # multiple blank lines
    return text.strip()


def parse_planalto(html: str, source_name: str):
    """
    Parse planalto.gov.br HTML into chunks [{s, a, t}].
    Tracks current Livro/Título/Capítulo for STRUCTURE generation.
    """
    try:
        from bs4 import BeautifulSoup
    except ImportError:
        raise RuntimeError('beautifulsoup4 not installed: pip install beautifulsoup4 lxml')

    soup = BeautifulSoup(html, 'lxml')

    # Remove scripts, styles, nav elements
    for tag in soup(['script', 'style', 'nav', 'header', 'footer', 'noscript']):
        tag.decompose()

    # Find main content — planalto uses various containers
    content = (
        soup.find('div', class_='texto') or
        soup.find('div', id='conteudo') or
        soup.find('div', class_='textoNorma') or
        soup.find('div', id='texto') or
        soup.body or soup
    )

    chunks = []
    structure_articles = []

    # State: current section hierarchy
    livro = ''
    titulo = ''
    capitulo = ''

    # Patterns
    art_re = re.compile(
        r'^(Art\.?\s*\d+[º°]?(?:-[A-Z])?)'  # Art. 1º, Art. 12-A
        r'(.*)$', re.DOTALL
    )
    section_re = re.compile(
        r'^(LIVRO|TÍTULO|TITULO|CAPÍTULO|CAPITULO|SEÇÃO|SECAO|SUBSEÇÃO|PARTE)\s',
        re.IGNORECASE
    )
    roman_re = re.compile(r'^(LIVRO|TÍTULO|TITULO)\s+([IVXLCDM]+|[0-9]+)', re.IGNORECASE)

    current_art_label = None
    current_art_lines = []

    def flush_article():
        nonlocal current_art_label, current_art_lines
        if current_art_label and current_art_lines:
            text = clean_text(' '.join(current_art_lines))
            if len(text) > 10:
                chunks.append({'s': source_name, 'a': current_art_label, 't': text})
                structure_articles.append({
                    'art': current_art_label,
                    'livro': livro,
                    'titulo': titulo,
                    'capitulo': capitulo,
                    'preview': text[:120],
                    's': source_name,
                })
        current_art_label = None
        current_art_lines = []

    def update_section(text: str):
        nonlocal livro, titulo, capitulo
        t = text.strip().upper()
        if t.startswith('LIVRO'):
            livro = text.strip()
            titulo = ''
            capitulo = ''
        elif t.startswith('TÍTULO') or t.startswith('TITULO'):
            titulo = text.strip()
            capitulo = ''
        elif t.startswith('CAPÍTULO') or t.startswith('CAPITULO'):
            capitulo = text.strip()

    # Walk all text-bearing elements
    for el in content.find_all(['p', 'h1', 'h2', 'h3', 'h4', 'span', 'div'], recursive=True):
        # Skip nested (we process leaves)
        if el.find(['p', 'h1', 'h2', 'h3', 'h4']):
            continue

        raw = el.get_text(' ', strip=True)
        if not raw or len(raw) < 3:
            continue

        # Section header?
        if section_re.match(raw) and len(raw) < 120:
            flush_article()
            update_section(raw)
            continue

        # Article start?
        m = art_re.match(raw)
        if m:
            flush_article()
            current_art_label = m.group(1).strip()
            # Normalize: "Art. 1º" → "Art. 1"
            current_art_label = re.sub(r'[º°]', '', current_art_label).strip()
            rest = m.group(2).strip()
            if rest:
                current_art_lines.append(raw)
            else:
                current_art_lines.append(current_art_label)
            continue

        # Continuation of current article
        if current_art_label:
            current_art_lines.append(raw)

    flush_article()

    print(f'  Parsed {len(chunks)} chunks from {source_name}')
    return chunks, structure_articles


def fetch_source(key: str):
    cfg = SOURCES[key]
    print(f'\n→ Fetching {key} from {cfg["url"]}')
    html = fetch_html(cfg['url'])
    print(f'  Downloaded {len(html):,} chars')
    chunks, structure = parse_planalto(html, cfg['source'])

    if not chunks:
        print(f'  WARNING: No chunks parsed for {key} — aborting update')
        return None, None

    out_path = ROOT / cfg['out']
    with open(out_path, 'w', encoding='utf-8') as f:
        json.dump(chunks, f, ensure_ascii=False, separators=(',', ':'))
    print(f'  Saved {len(chunks)} chunks → {cfg["out"]}')

    struct_path = ROOT / 'scripts' / f'{key}_structure.json'
    with open(struct_path, 'w', encoding='utf-8') as f:
        json.dump({'source': cfg['source'], 'articles': structure}, f,
                  ensure_ascii=False, separators=(',', ':'))
    print(f'  Saved structure → scripts/{key}_structure.json')

    return chunks, structure


if __name__ == '__main__':
    targets = sys.argv[1:] if len(sys.argv) > 1 else ['all']
    if targets == ['all']:
        targets = list(SOURCES.keys())

    for t in targets:
        if t not in SOURCES:
            print(f'Unknown source: {t}. Available: {list(SOURCES.keys())}')
            continue
        try:
            fetch_source(t)
        except Exception as e:
            print(f'  FAILED: {e}')
            sys.exit(1)

    print('\nDone.')
