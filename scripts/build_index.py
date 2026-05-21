#!/usr/bin/env python3
"""
Reconstrói index.html com os dados atualizados dos JSON.
Substitui CHUNKS, FULL_CHUNKS e STRUCTURE mantendo o resto do app intacto.
Uso: python3 scripts/build_index.py
"""
import json, re, html as hl, datetime
from pathlib import Path

ROOT = Path(__file__).parent.parent
SCRIPTS = Path(__file__).parent

# ── NT table formatter (inline — same logic as nt_parser) ─────────────────
def format_nt_chunk(text):
    HEADER_PATH = 'CAMINHO NO XML CAMPO ELE TIPO OCOR. TAM. DESCRIÇÃO'
    HEADER_FLAT = 'CAMPO ELE TIPO OCOR. TAM. DESCRIÇÃO'
    has_path = HEADER_PATH in text
    marker   = HEADER_PATH if has_path else HEADER_FLAT
    if marker not in text or '<table' in text:
        return text  # already HTML or no table

    ELE  = r'(?:G G|ID|E|G|CG|CE)'
    TIPO = r'(?:N|C|D|A|–)'
    OCOR = r'(?:\d+-\d+|\d+-[Nn]|0-[Nn]|–|\d+)'
    TAM  = r'(?:\d+[A-Z]?\d*(?:-\d+[A-Z]?\d*)?|–)'
    ANCHOR = re.compile(r'('+ELE+r')\s+('+TIPO+r')\s+('+OCOR+r')\s+('+TAM+r')\s*')
    CAMPO_SUFFIX = re.compile(
        r'((?:\w[\w.]*)'
        r'(?:\s+→\s+\w[\w.]*)*'
        r'(?:\s+★(?:\s+\w[\w.]*)?)?)\s*$'
    )

    def ele_bg(e): return {'G':'#dbeafe','G G':'#dbeafe','CG':'#e0e7ff','CE':'#ede9fe','E':'#f0fdf4','ID':'#fef9c3'}.get(e,'#f8fafc')
    def ocor_html(v):
        c = ('#dcfce7','#166534') if v=='1-1' else (('#fef9c3','#713f12') if v.startswith('0') else ('#f1f5f9','#475569'))
        return f'<span style="background:{c[0]};color:{c[1]};border-radius:3px;padding:1px 5px;font-size:.75em">{hl.escape(v)}</span>'

    intro_raw, table_raw = text.split(marker, 1)
    table_raw = table_raw.strip()
    anchors = list(ANCHOR.finditer(table_raw))
    if not anchors: return text

    rows = []
    for idx, m in enumerate(anchors):
        ele, tipo, ocor, tam = m.group(1), m.group(2), m.group(3), m.group(4)
        prev_end = anchors[idx-1].end() if idx > 0 else 0
        pre = table_raw[prev_end:m.start()]
        cm = CAMPO_SUFFIX.search(pre)
        campo = cm.group(1).strip() if cm else (pre.strip().split()[-1] if pre.strip() else '?')
        campo_start = cm.start() if cm else len(pre) - len(campo)
        if idx > 0 and rows:
            p,c,e,ti,o,ta,_ = rows[-1]
            rows[-1] = (p,c,e,ti,o,ta, table_raw[anchors[idx-1].end():prev_end+campo_start].strip())
        path = ''
        if has_path and idx == 0:
            pm = re.match(r'(\S+/\S*)\s+', pre[:campo_start] if cm else pre)
            path = pm.group(1) if pm else ''
        rows.append((path, campo, ele, tipo, ocor, tam, ''))
    if rows:
        p,c,e,ti,o,ta,_ = rows[-1]
        rows[-1] = (p,c,e,ti,o,ta, table_raw[anchors[-1].end():].strip())

    cols = (['Caminho XML'] if has_path else []) + ['Campo','ELE','Tipo','Ocor.','Tam.','Descrição']
    hdr = ''.join(f'<th style="padding:5px 8px;text-align:left;white-space:nowrap">{c}</th>' for c in cols)
    tbl = ('<div style="overflow-x:auto;margin:10px 0"><table style="width:100%;border-collapse:collapse;font-size:.82em">'
           '<thead><tr style="background:#1e40af;color:#fff">'+hdr+'</tr></thead><tbody>')
    for i,(path,campo,ele,tipo,ocor,tam,desc) in enumerate(rows):
        bg = '#f8fafc' if i%2 else '#fff'
        cd = hl.escape(campo).replace('★','<span style="color:#d97706;font-weight:700">★</span>')
        cells = []
        if has_path:
            cells.append(f'<td style="padding:4px 8px;color:#9ca3af;font-size:.77em;white-space:nowrap">{hl.escape(path)}</td>')
        cells += [
            f'<td style="padding:4px 8px;font-weight:700;white-space:nowrap;background:{ele_bg(ele)};font-family:monospace">{cd}</td>',
            f'<td style="padding:4px 8px;text-align:center;color:#6b7280">{hl.escape(ele)}</td>',
            f'<td style="padding:4px 8px;text-align:center;color:#6b7280">{hl.escape(tipo)}</td>',
            f'<td style="padding:4px 8px;text-align:center">{ocor_html(ocor)}</td>',
            f'<td style="padding:4px 8px;text-align:center;color:#6b7280;white-space:nowrap">{hl.escape(tam)}</td>',
            f'<td style="padding:4px 8px;color:#374151">{hl.escape(desc)}</td>',
        ]
        tbl += f'<tr style="background:{bg};border-bottom:1px solid #e5e7eb">{"".join(cells)}</tr>'
    tbl += '</tbody></table></div>'
    intro_html = ''.join(
        f'<p style="margin:0 0 6px;color:#374151">{hl.escape(ln)}</p>'
        for ln in intro_raw.strip().split('\n') if ln.strip()
    ) if intro_raw.strip() else ''
    return intro_html + tbl


def load_json(path):
    with open(path, encoding='utf-8') as f:
        return json.load(f)

def compact(obj):
    return json.dumps(obj, ensure_ascii=False, separators=(',', ':'))


def build_structure_for_law(key):
    """Load pre-built structure from scripts/{key}_structure.json if available."""
    struct_path = SCRIPTS / f'{key}_structure.json'
    if struct_path.exists():
        return load_json(struct_path)
    return None


def build():
    html_path = ROOT / 'index.html'
    with open(html_path, encoding='utf-8') as f:
        lines = f.readlines()

    # ── Base law data ──────────────────────────────────────────
    law_configs = [
        ('lcp214',  'LCP 214',          'lcp214.json'),
        ('lcp227',  'LCP 227',          'lcp227.json'),
        ('reg_cbs', 'Regulamento CBS',  'reg_cbs.json'),
        ('reg_ibs', 'Regulamento IBS',  'reg_ibs.json'),
    ]

    all_law_chunks = []
    all_structure  = []
    for key, source, fname in law_configs:
        chunks = load_json(ROOT / fname)
        all_law_chunks.extend(chunks)
        struct = build_structure_for_law(key)
        if struct:
            all_structure.append(struct)
        else:
            # Flat fallback: no livro/titulo metadata
            arts = [{'art': c['a'], 'livro': '', 'titulo': source,
                     'capitulo': '', 'preview': c['t'][:120], 's': source}
                    for c in chunks]
            all_structure.append({'source': source, 'articles': arts})

    # ── NT data ───────────────────────────────────────────────
    nt_meta = [
        ('nt001', 'NT 001 NFS-e',     'SE/CGNFS-e · NT 001 · ago/2024',    '📄'),
        ('nt002', 'NT 002 NFS-e',     'SE/CGNFS-e · NT 002 · fev/2025',    '📄'),
        ('nt003', 'NT 003 NFS-e',     'SE/CGNFS-e · NT 003 · jul/2025',    '📄'),
        ('nt004', 'NT 004 NFS-e',     'SE/CGNFS-e · NT 004 · dez/2025',    '📄'),
        ('nt005', 'NT 005 NFS-e',     'SE/CGNFS-e · NT 005 · nov/2025',    '📄'),
        ('nt006', 'NT 006 NFS-e Via', 'SE/CGNFS-e · NT 006 Via · jan/2026','🛣️'),
        ('nt007', 'NT 007 NFS-e',     'SE/CGNFS-e · NT 007 · fev/2026',    '📄'),
        ('nt008', 'NT 008 NFS-e',     'SE/CGNFS-e · NT 008 · mai/2026',    '📄'),
    ]
    nt_var_chunks = []
    for key, source, sub, icon in nt_meta:
        path = ROOT / f'{key}.json'
        if not path.exists():
            print(f'  WARNING: {path} not found, skipping')
            continue
        chunks = load_json(path)
        # Apply HTML formatting to table chunks
        for c in chunks:
            c['t'] = format_nt_chunk(c['t'])
        nt_var_chunks.append((key.upper(), source, sub, chunks))

        # Add to structure
        plain = lambda t: re.sub(r'<[^>]+>', ' ', t).strip()[:150]
        arts = [{'art': c['a'], 'livro': '', 'titulo': source,
                 'capitulo': '', 'preview': plain(c['t']), 's': source}
                for c in chunks]
        all_structure.append({'source': source, 'articles': arts})

    # ── Build replacement lines ────────────────────────────────

    # CHUNKS (law only — NTs added via push below)
    chunks_line = 'const CHUNKS=' + compact(all_law_chunks) + ';\n'

    # FULL_CHUNKS (same as CHUNKS for now)
    full_line = 'const FULL_CHUNKS=' + compact(all_law_chunks) + ';\n'

    # STRUCTURE (law entries only — NTs pushed below)
    structure_line = 'const STRUCTURE=' + compact(all_structure[:4]) + ';\n'

    # NT block
    nt_block = ['// ── Notas Técnicas NFS-e ──────────────────────────\n']
    nt_vars = []
    for var, source, sub, chunks in nt_var_chunks:
        nt_block.append(f'const {var}_CHUNKS=' + compact(chunks) + ';\n')
        nt_vars.append(f'{var}_CHUNKS')
    push_args = ','.join(f'...{v}' for v in nt_vars)
    nt_block.append(f'CHUNKS.push({push_args});\n')
    nt_block.append(f'FULL_CHUNKS.push({push_args});\n')
    nt_struct = compact(all_structure[4:])
    nt_block.append(f'STRUCTURE.push(...{nt_struct});\n')
    nt_block.append('// ─────────────────────────────────────────────────\n')

    # ── Replace lines in HTML ──────────────────────────────────
    def replace_line(lines, prefix, new_content):
        for i, l in enumerate(lines):
            if l.startswith(prefix):
                lines[i] = new_content
                return True
        return False

    if not replace_line(lines, 'const CHUNKS=[', chunks_line):
        print('WARNING: CHUNKS line not found')
    if not replace_line(lines, 'const FULL_CHUNKS=[', full_line):
        print('WARNING: FULL_CHUNKS line not found')
    if not replace_line(lines, 'const STRUCTURE=[', structure_line):
        print('WARNING: STRUCTURE line not found')
    if not replace_line(lines, 'const DATA_DATE=', f"const DATA_DATE='{datetime.date.today().isoformat()}';\n"):
        print('WARNING: DATA_DATE line not found')

    # Replace NT block
    nt_start = nt_end = None
    for i, l in enumerate(lines):
        if '// ── Notas Técnicas NFS-e' in l:
            nt_start = i
        if nt_start and '// ─────────────────────────' in l and i > nt_start:
            nt_end = i
            break
    if nt_start is not None and nt_end is not None:
        lines[nt_start:nt_end+1] = nt_block
    else:
        print('WARNING: NT block not found — appending after PAGES')

    with open(html_path, 'w', encoding='utf-8') as f:
        f.writelines(lines)

    size_mb = sum(len(l) for l in lines) / 1024 / 1024
    print(f'Built index.html — {len(lines)} lines, {size_mb:.2f} MB')


if __name__ == '__main__':
    build()
    print('Done.')
