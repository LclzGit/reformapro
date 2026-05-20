# 📋 Handoff Completo: Projeto ReformaPro

> Use este único arquivo para contextualizar qualquer novo chat sobre este projeto.

---

## 🧭 O que é o ReformaPro

Aplicação web **single-file** (HTML + CSS + JS puro, sem backend, sem dependências externas) para estudo da Reforma Tributária brasileira — IBS, CBS e Imposto Seletivo. Funciona 100% no navegador.

**Tagline:** *"Sua plataforma de estudos da Reforma Tributária brasileira."*

---

## 🏗️ Arquitetura atual do ReformaPro

- **Tipo:** Single-file HTML (~4MB, ~1.107 linhas)
- **Stack:** HTML5 + CSS3 + Vanilla JS (sem frameworks, sem npm, sem fetch)
- **Persistência:** `localStorage` — chaves `rp_theme` e `rp_notes`
- **Dados:** 1.902 artigos **hardcoded** como arrays JS dentro do próprio HTML

### Módulos existentes

| Módulo | Funções principais |
|---|---|
| Buscador | `bRun()`, `find()`, `score()`, `hl()`, `bOpen()` |
| Leitor com anotações | `rdRenderArticle()`, `rdNav()`, `rdSave()`, `rdExport()`, `rdImport()` |
| Painel de anotações | `notaRender()`, `notaSearch()`, `notaDeleteAll()` |
| Tema | `toggleTheme()`, `applyLight()` |

### Variáveis JS principais

```js
CHUNKS        // Array com todos os artigos para busca { s, a, t }
FULL_CHUNKS   // Array com artigos completos para o leitor
TOPIC_CHUNKS  // Chunks temáticos
STRUCTURE     // Objeto de navegação hierárquica
PAGES         // Auxiliar de navegação
srcs          // ['LCP 214', 'LCP 227', 'Regulamento CBS', 'Regulamento IBS']
```

### Estrutura de cada chunk

```js
{ s: "nome da fonte", a: "Art. X ou título", t: "texto em HTML" }
```

O campo `t` aceita HTML inline — o leitor usa `innerHTML` para renderizar.

---

## 📚 Fontes de dados do projeto

### Legislação

| Fonte | URL original | Situação atual |
|---|---|---|
| LC 214/2025 | https://www.planalto.gov.br/ccivil_03/leis/lcp/lcp214.htm | ⚠️ Encoding windows-1252 quebrado no fetch |
| LC 227/2026 | https://www.planalto.gov.br/ccivil_03/leis/lcp/lcp227.htm | ⚠️ Mesmo problema |
| Regulamento CBS | https://www.planalto.gov.br/ccivil_03/_ato2023-2026/2026/decreto/d12955.htm | ⚠️ Mesmo problema |
| Regulamento IBS | Resolução CGIBS nº 6/2026 | ✅ Já hardcoded no ReformaPro (604 artigos) |

### Notas Técnicas NFS-e (todos PDFs públicos acessíveis via fetch)

| NT | URL | Chunks gerados | Conteúdo |
|---|---|---|---|
| NT 001 | https://www.gov.br/nfse/pt-br/biblioteca/documentacao-tecnica/rtc/nota-tecnica-001-se-cgnfse-novo-layout-rtc.pdf | ✅ 17 chunks | Layout v1 NFS-e para IBS/CBS/IS (ago/2024) |
| NT 002 | https://www.gov.br/nfse/pt-br/biblioteca/documentacao-tecnica/rtc/nota-tecnica-se-cgnfs-e-no-002-de-28-de-fevereiro-de-2025 | ✅ 15 chunks | Layout v2, baseado na LC 214 (fev/2025) |
| NT 003 | https://www.gov.br/nfse/pt-br/biblioteca/documentacao-tecnica/rtc/nt-003-1-2-se-cgnfse-novo-layout-rtc.pdf | ✅ 12 chunks | Layout v3, maior reestruturação (jul/2025) |
| NT 004 | https://www.gov.br/nfse/pt-br/biblioteca/documentacao-tecnica/producao-restrita/nt-004-se-cgnfse-novo-layout-rtc-v2-00-20251210.pdf | ✅ 14 chunks | Layout v4, **versão em produção jan/2026** |
| NT 005 | https://www.gov.br/nfse/pt-br/biblioteca/documentacao-tecnica/rtc/nt-005-se-cgnfse-novo-layout-rtc.pdf | ✅ 12 chunks | Layout v5, aguardando implantação |
| NT 006 | https://www.gov.br/nfse/pt-br/biblioteca/documentacao-tecnica/rtc/nt-006-se-cgnfse-leiaute-nfse-via.pdf | ✅ 8 chunks | NFS-e Via (concessionárias de rodovias) |
| NT 007 | https://www.gov.br/nfse/pt-br/biblioteca/documentacao-tecnica/rtc/nt-007-se-cgnfse-v1-0.pdf | ❌ Não processada | Atualizações e esclarecimentos (fev/2026) |
| NT 008 | https://www.gov.br/nfse/pt-br/biblioteca/documentacao-tecnica/rtc/nt-008-se-cgnfse-danfse-20260505.pdf | ❌ Não processada | Especificações técnicas do DANFSe (mai/2026) |

---

## ✅ O que já foi feito

- [x] Chunks das NT 001–006 gerados e validados (78 chunks total)
- [x] Preview interativo de renderização testado
- [x] Diagnóstico de todas as fontes de dados
- [x] Arquitetura de migração para fetch definida

### Chunks prontos (arquivos .js para converter em .json)

| Arquivo | Chunks | Fonte |
|---|---|---|
| `nt001_chunks.js` | 17 | NT 001 NFS-e |
| `nt002_chunks.js` | 15 | NT 002 NFS-e |
| `nt003_chunks.js` | 12 | NT 003 NFS-e |
| `nt004_chunks.js` | 14 | NT 004 NFS-e |
| `nt005_chunks.js` | 12 | NT 005 NFS-e |
| `nt006_chunks.js` | 8 | NT 006 NFS-e Via |

---

## 🚀 Fase 2: Migração para fetch (próximo passo)

### Por que não buscar direto nas fontes originais?

O portal **não pode** buscar nas URLs originais em tempo real porque:
- Planalto tem encoding `windows-1252` quebrado e ausência de CORS
- PDFs não são pesquisáveis como chunks — precisam ser parseados
- Instabilidade dos servidores governamentais

### Arquitetura alvo

```
Fontes originais (Planalto + gov.br)
        ↓
   scraper.js (roda localmente, você decide quando atualizar)
        ↓
   JSONs no GitHub (estáticos, rápidos, sem CORS)
        ↓
   ReformaPro faz fetch() dos JSONs + cache em localStorage
```

### Repositório GitHub para os dados

Criar repositório público `reformapro-data` com esta estrutura:

```
reformapro-data/
├── lcp214.json
├── lcp227.json
├── reg_cbs.json
├── reg_ibs.json       ← extraído do HTML, não precisa scraping
├── nt001.json
├── nt002.json
├── nt003.json
├── nt004.json
├── nt005.json
├── nt006.json
├── nt007.json         ← scraper busca o PDF automaticamente
├── nt008.json         ← scraper busca o PDF automaticamente
└── index.json         ← manifesto com metadados
```

### Script scraper.js (o Claude monta no próximo chat)

```
Para LC 214, LC 227, Reg. CBS (Planalto):
  fetch → arrayBuffer → TextDecoder('windows-1252') → cheerio → quebra por artigo → JSON

Para Reg. IBS:
  ler ReformaPro.html → extrair array JS existente → salvar como JSON

Para NT 001–006 (já temos os .js):
  converter os arrays JS para JSON puro (tirar "const NT001_CHUNKS = " e o ";")

Para NT 007 e NT 008 (PDFs públicos):
  fetch do PDF → pdf-parse → quebra por seção → JSON
```

**Dependências Node.js:**
```json
{
  "dependencies": {
    "cheerio": "^1.0.0",
    "pdf-parse": "^1.1.1",
    "node-fetch": "^3.0.0"
  }
}
```

### Modificação no ReformaPro.html

```js
// Substituir os arrays hardcoded por:
const BASE_URL = 'https://raw.githubusercontent.com/SEU-USUARIO/reformapro-data/main/';

const FONTES = {
  'LCP 214':         'lcp214.json',
  'LCP 227':         'lcp227.json',
  'Regulamento CBS': 'reg_cbs.json',
  'Regulamento IBS': 'reg_ibs.json',
  'NT 001 NFS-e':    'nt001.json',
  'NT 002 NFS-e':    'nt002.json',
  'NT 003 NFS-e':    'nt003.json',
  'NT 004 NFS-e':    'nt004.json',
  'NT 005 NFS-e':    'nt005.json',
  'NT 006 NFS-e Via':'nt006.json',
  'NT 007 NFS-e':    'nt007.json',
  'NT 008 NFS-e':    'nt008.json',
};

let CHUNKS = [];

async function loadData() {
  const CACHE_KEY = 'rp_chunks_v2';
  const cached = localStorage.getItem(CACHE_KEY);
  if (cached) {
    CHUNKS = JSON.parse(cached);
    initApp(); // função que inicializa o buscador/leitor
    return;
  }
  // Mostra loading
  document.getElementById('loading').style.display = 'block';
  
  const results = await Promise.all(
    Object.values(FONTES).map(f =>
      fetch(BASE_URL + f).then(r => r.json())
    )
  );
  CHUNKS = results.flat();
  localStorage.setItem(CACHE_KEY, JSON.stringify(CHUNKS));
  document.getElementById('loading').style.display = 'none';
  initApp();
}

// Chamar no DOMContentLoaded em vez de inicializar direto
document.addEventListener('DOMContentLoaded', loadData);
```

---

## 📋 Checklist para o próximo chat

### Você prepara antes
- [ ] Criar repositório público `reformapro-data` no GitHub
- [ ] Ter Node.js v18+ instalado
- [ ] Ter os 6 arquivos `nt00X_chunks.js` salvos

### O Claude faz no próximo chat
- [ ] `package.json` + `scraper.js` completo
- [ ] Extrator do Reg. IBS do HTML
- [ ] Conversor dos .js das NTs para .json
- [ ] Modificação do `ReformaPro.html` para fetch + cache
- [ ] Loading state na UI

### Você faz depois
- [ ] `npm install && node scraper.js`
- [ ] Revisar os JSONs (spot-check)
- [ ] Subir para o GitHub
- [ ] Atualizar a URL base no HTML
- [ ] Testar

---

## 💡 Prompt para o próximo chat

```
Tenho um projeto chamado ReformaPro — aplicação web single-file para
estudo da Reforma Tributária brasileira.

Sobe o arquivo: handoff_reformapro_completo.md
E também os arquivos: nt001_chunks.js, nt002_chunks.js, nt003_chunks.js,
nt004_chunks.js, nt005_chunks.js, nt006_chunks.js

Preciso que você monte:

1. package.json + scraper.js em Node.js que:
   - Raspa LC 214, LC 227 e Reg. CBS do Planalto (encoding windows-1252)
   - Extrai o array do Reg. IBS que está hardcoded no ReformaPro.html
   - Converte os 6 arquivos .js das NTs prontas para .json
   - Faz fetch e parseia NT 007 e NT 008 dos PDFs públicos:
     NT 007: https://www.gov.br/nfse/pt-br/biblioteca/documentacao-tecnica/rtc/nt-007-se-cgnfse-v1-0.pdf
     NT 008: https://www.gov.br/nfse/pt-br/biblioteca/documentacao-tecnica/rtc/nt-008-se-cgnfse-danfse-20260505.pdf
   - Salva tudo como JSONs prontos para o GitHub

2. Modificação no ReformaPro.html para carregar os JSONs via fetch
   com cache em localStorage, substituindo os arrays hardcoded

Comece pelo scraper.js.
```

---

## 🔗 Links de referência

| Recurso | URL |
|---|---|
| Portal NFS-e | https://www.gov.br/nfse/pt-br/biblioteca/documentacao-tecnica |
| Portal NFS-e Via | https://www.gov.br/nfse/pt-br/nfse-via/documentacao-tecnica |
| Portal CGIBS | https://cgibs.gov.br/regulamentos |
| Portal Concessionárias | https://via.nfse.gov.br/concessionarias/login |
| Planalto LC 214 | https://www.planalto.gov.br/ccivil_03/leis/lcp/lcp214.htm |
| Planalto LC 227 | https://www.planalto.gov.br/ccivil_03/leis/lcp/lcp227.htm |
| Planalto Reg. CBS | https://www.planalto.gov.br/ccivil_03/_ato2023-2026/2026/decreto/d12955.htm |

---

*Atualizado em 19/mai/2026*
