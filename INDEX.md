# 📑 Índice Consolidado — Projeto pyanatem

**Data de atualização:** 2026-07-09  
**Versão mais recente:** `v0.14.2`  
**Status:** Em desenvolvimento ativo

---

## 🎯 O que é pyanatem?

**Biblioteca Python** para geração, manipulação, parsing e execução automatizada de arquivos `.stb` (casos de simulação) do simulador **ANATEM** (CEPEL — Centro de Pesquisas de Energia Elétrica).

- ✅ Lê e escreve arquivos `.stb` com garantia de *roundtrip* (exportar → ler → re-exportar sem perdas)
- ✅ API Python fluente para criar/editar casos programaticamente  
- ✅ Suporte a CDU (Controladores Definidos pelo Usuário)
- ✅ Validação contra manual ANATEM v12.10
- ✅ Execução em lotes (contingências, ensaios paralelos)

**Dependências:** Python ≥ 3.9 (sem obrigatórias além da stdlib; `pandas` é opcional)

---

## 📂 Estrutura de Pastas

```
ana-estatica/ (Repositório Git — v0.14.2)
│
├── 📄 LICENSE                        • MIT License
├── 📄 README.md                      ⭐ Documentação principal (v0.14.2)
├── 📄 INDEX.md                       ← Você está aqui (mapa consolidado)
├── 📄 pyproject.toml                 • Configuração Python (v0.14.2)
├── 📄 .gitignore                     • Regras git
│
├── 📚 pyanatem/                      ⭐ Código-fonte v0.14.2 (pronto para usar)
│   ├── __init__.py                   • Exports públicos (CasoAnatem, etc.)
│   ├── caso.py                       • Classe CasoAnatem (API fluente)
│   ├── blocos.py                     • Dataclasses para cada bloco STB
│   ├── ensaio.py                     • EnsaioAnatem (automação lotes)
│   ├── posprocessamento.py           • LeitorPLT, LeitorRelatorio, LeitorSAV
│   ├── anarede.py                    • Validação STB ↔ SAV
│   ├── cdu/                          • DSL para Controladores Definidos
│   ├── parser/                       • ParserSTB (lê .stb e reconstrói)
│   ├── eventos/                      • Placeholder reservado
│   └── modelos/                      • Placeholder reservado
│
├── 🧪 tests/                         • Suite de 280 testes (v1.10.2)
│   ├── test_pynatem.py               • Testes unitários e integração
│   ├── test_conformidade_manual.py   • Conformidade com o manual oficial
│   └── ...
│
├── 📖 markdowns_reference/           • Referências técnicas (Manual ANATEM 12.10)
│   ├── INDEX.md                      • Navegação por capítulo (comece aqui)
│   ├── 07_cap7 ... 30_cap46          • Transcrições organizadas por capítulo
│   └── (fonte oficial online: https://see.cepel.br/manual/anatem/)
│
├── 📦 .versions/                     • Histórico de versões (referência)
│   ├── v0.6.0/                       • Primeira versão (marcos iniciais)
│   ├── v0.8.0/                       • Etapa 0.8 (features intermediárias)
│   ├── v0.11.3/                      • Etapa 0.11 (polimento, type hints)
│   └── v0.14.2/                      • Snapshot histórico (ciclo 0.x)
│       ├── README.md
│       ├── CHANGELOG.md
│       ├── ROADMAP_v7.md, ROADMAP_v8.md
│       ├── pyanatem/
│       ├── tests/
│       ├── markdowns_referencia/
│       └── ...
│
└── 📋 Documentação de Referência
    ├── CHANGELOG.md                  • Histórico de versões v0.6–v0.14.2
    ├── ROADMAP.md                    • Planejamento estratégico
    ├── CONTRIBUTING.md               • Guia de contribuição
    ├── SECURITY.md                   • Política de segurança
    ├── SETUP_INICIAL.md              • Como começar do v0.6.0
    └── SOBRE_INDEX.md                • Como usar este INDEX.md

```

---

## 📖 Como Navegar

### Para iniciantes: primeiros passos
1. **Leia** `v0.14.2/README.md` (seções "Uso rápido" + "API pública")  
2. **Explore** os exemplos (gerar STB do zero, editar STB existente, rodar lote)  
3. **Entenda a arquitetura** (seção "Arquitetura" no README)

### Para referencias técnicas (Manual ANATEM)
- **Estrutura de simulação:** `markdowns_reference/DSIM.md`, `DARQ.md`
- **Eventos (curtos, aberturas, etc.):** `markdowns_reference/DEVT_completo.md`
- **Variáveis de plotagem:** `markdowns_reference/DPLT_completo.md`
- **Controladores CDU:** `markdowns_reference/DCDU.md` + `blocos_CDU_completo.md`
- **FACTS/HVDC:** `v0.14.2/markdowns_referencia/novos_md/09_Geracao_renovavel_10_FACTS_e_HVDC.md`
- **Formato arquivo:** `v0.14.2/markdowns_referencia/novos_md/04__anatem_file_format.md`

### Para desenvolvimento / manutenção
- **Mudanças entre versões:** `v0.14.2/CHANGELOG.md` (histórico consolidado)
- **Roadmap e decisões:** `v0.14.2/ROADMAP_v7.md` (versionamento)  
- **Falhas conhecidas / futuro:** `v0.14.2/ROADMAP_v8.md`
- **Código-fonte:** `v0.14.2/src/pyanatem/` (seguir imports a partir de `__init__.py`)

### Para validação de confiança
Consulte tabela em `v0.14.2/README.md` seção "Confiabilidade dos códigos":
- ✅ **Alta** — Consolidada + manual confirmado  
- ✅ **Média** — Testada sinteticamente (roundtrip)  
- ⚠️ **Best-effort** — Engenharia reversa; use `linha_bruta()` se dúvida

---

## 🧩 Componentes Principais (v0.14.2)

| Classe / Símbolo | Módulo | Descrição | Desde |
|---|---|---|---|
| `CasoAnatem` | `caso.py` | Caso completo (`.stb`); API fluente + serialização + validação | v0.4.0 |
| `CasoAnatem.ler()` | `caso.py` | Abre `.stb` existente, reconstrói árvore de blocos | v0.4.0 |
| `CasoAnatem.exportar()` | `caso.py` | Serializa para `.stb` (latin-1 garantido) | v0.4.0 |
| `CasoAnatem.validar()` | `caso.py` | Lista avisos de consistência | v0.4.0 |
| `CasoAnatem.validar_contra_sav()` | `anarede.py` | Cruza barras/circuitos STB ↔ SAV | v0.4.7 |
| `CasoAnatem.salvar_cdu()` | `caso.py` | Exporta bloco DCDU para arquivo `.cdu` | v0.6.3 |
| `CasoAnatem.curto_barra()` | `caso.py` | Helper: evento curto em barra | — |
| `CasoAnatem.curto_circuito()` | `caso.py` | Helper: evento curto em linha | — |
| `EnsaioAnatem` | `ensaio.py` | Automação: lotes sequenciais e paralelos | v0.4.0 |
| `EnsaioAnatem.de_contingencias()` | `ensaio.py` | Gera N casos (um por contingência) a partir de caso-base | v0.4.6 |
| `EnsaioAnatem.executar_contingencias()` | `ensaio.py` | Roda casos, valida critérios | — |
| **Blocos STB** | `blocos.py` | Dataclass para cada seção do `.stb` | — |
| `BlocoDARQ` | `blocos.py` | Associação de arquivos (SAV, PLT, RELA, DCDU) | v0.4.0 |
| `BlocoDOPC` | `blocos.py` | Opções globais de execução | v0.4.0 |
| `BlocoDSIM` | `blocos.py` | Parâmetros de simulação | v0.4.0 |
| `BlocoDEVT` | `blocos.py` | Eventos (curtos, aberturas, chaveamentos, steps) | v0.4.0 |
| `BlocoDPLT` | `blocos.py` | Variáveis de saída/plotagem | v0.4.0 |
| `BlocoDMDG` | `blocos.py` | Modelos predefinidos de geradores | v0.4.1 |
| `BlocoDMAQ` | `blocos.py` | Associação máquina ↔ modelo | v0.4.2 |
| `BlocoSVC`, `BlocoTCSC`, `BlocoSTATCOM`, `BlocoHVDC` | `blocos.py` | FACTS e elo HVDC | v0.4.3 |
| `BlocoCDU` | `cdu/blocos.py` | Bloco de Controlador Definido pelo Usuário | v0.4.4 |
| `ControladorCDU` | `cdu/dsl.py` | DSL fluente para construir CDU (Python → texto) | v0.4.4 |
| `BlocoDCDU` | `blocos.py` | Container completo (múltiplos controladores) | v0.4.5 |
| **Pós-processamento** | `posprocessamento.py` | Leitura de saídas | — |
| `LeitorPLT` / `ResultadoPLT` | `posprocessamento.py` | Lê `.plt` (formato texto) e oferece acesso tabular/dataframe | v0.4.0 |
| `LeitorRelatorio` / `ResultadoExecucao` | `posprocessamento.py` | Lê `.rela` / `.log` de execução | v0.4.0 |
| `LeitorSAV` / `ResultadoSAV` | `anarede.py` | Parser básico de `.sav` do ANAREDE | v0.4.7 |
| **Parser** | `parser/stb.py` | Lê `.stb` de texto para árvore de Python | — |
| `ParserSTB` | `parser/stb.py` | Parser principal (linha a linha, reconstrói blocos) | — |

---

## 🔍 Encontrar Informação Rápido

### "Preciso entender como CDU funciona"
→ `markdowns_reference/blocos_CDU_completo.md` (definição teórica)  
→ `v0.14.2/src/pyanatem/cdu/` (implementação)  
→ `v0.14.2/README.md` seção "Confiabilidade dos códigos" (validação v0.14.2)

### "Preciso adicionar suporte a novo tipo de bloco"
→ `v0.14.2/src/pyanatem/blocos.py` (procure classe `BlocoXXX`)  
→ `markdowns_reference/` (manual do ANATEM para o bloco específico)  
→ `v0.14.2/tests/` (veja como outros blocos são testados)

### "Preciso de uma variável de plotagem"
→ `markdowns_reference/DPLT_completo.md` (catálogo completo)  
→ `v0.14.2/src/pyanatem/blocos.py` método `BlocoDPLT.tensao_barra()` (exemplo)

### "Preciso executar um lote de contingências"
→ `v0.14.2/README.md` seção "Uso rápido (c) Rodar um lote"  
→ `v0.14.2/src/pyanatem/ensaio.py` (classe `EnsaioAnatem`)

### "Preciso parsear um `.stb` existente"
→ `v0.14.2/README.md` seção "Uso rápido (b) Editar um STB existente"  
→ `v0.14.2/src/pyanatem/parser/stb.py` (implementação)

### "Preciso ler resultados (`.plt`, `.rela`)"
→ `v0.14.2/src/pyanatem/posprocessamento.py` (LeitorPLT, LeitorRelatorio)  
→ `markdowns_reference/DPLT_completo.md` (significado dos códigos)

---

## 📊 Status de Versões

| Versão | Data | Status | Notas |
|---|---|---|---|
| v0.6.0 | — | Arquivada | Primeiros marcos |
| v0.8.0 | — | Arquivada | Intermediária |
| v0.11.3 | — | Arquivada | Estável, CDU + FACTS consolidados |
| **v0.14.2** | 2026-07-07 | ✅ **ATUAL** | **Recomendada.** Robustez I/O (latin-1 garantido), parser CDU finalizado, 163 testes. |

---

## ✅ Checklist de Confiabilidade (v0.14.2)

### ✅ Totalmente Validado (Alta confiança)
- ✅ DARQ, DSIM, DOPC — Estrutura consolidada  
- ✅ DEVT (8 tipos de evento) — Nomenclatura ANATEM oficial  
- ✅ DPLT — Barras, máquinas, circuitos, cargas  
- ✅ CDU (IMPORT/EXPORT/INPUT/OUTPUT/SERIET, LOGIC, COMPAR) — Roundtrip v0.14.2  
- ✅ Codificação latin-1 — Garantida I/O, sem corrupção silenciosa  

### ✅ Testado Sinteticamente (Média confiança)
- ✅ DMDG (MD01/MD02/MD03) — Serialização/parser/roundtrip  
- ✅ DMAQ (posicional) — Roundtrip testado, todas as combinações  
- ✅ FACTS (SVC/TCSC/STATCOM), HVDC — Validado Cap. 25–27, 20–21  
- ✅ DPLT — OLTC, FACTS, HVDC, CDU (4-letra)  
- ✅ LeitorPLT — Estrutura validada Cap. 8.6  

### ⚠️ Best-effort (Use com atenção)
- ⚠️ CDU — Curvas RELINV — Referência do manual indisponível; `stip` heurístico (IEC/IEEE)

---

## 🚀 Próximos Passos (Roadmap v0.15+)

Veja `v0.14.2/ROADMAP_v8.md` para:
- Suporte a `.plt` binário (agendado v1.1.0)  
- Expansão de modelos dinâmicos  
- Integração com simuladores  
- Falhas conhecidas e soluções em aberto

---

## 📝 Notas de Desenvolvimento

### Versionamento
Formato: **MAJOR.MINOR.PATCH**
- **MAJOR** = maturidade pública (sempre 0 por enquanto)  
- **MINOR** = etapa de desenvolvimento (v0.6, v0.8, v0.11, v0.14)  
- **PATCH** = meta dentro da etapa (v0.14.1, v0.14.2)  

Veja `v0.14.2/ROADMAP_v7.md` para a estratégia completa.

### Teste e Validação
- **163 testes** cobrindo:
  - Roundtrip (exportar → ler → re-exportar sem perdas)  
  - Regressão encoding latin-1  
  - Blocos individuais (blocos.py)  
  - Parser (parser/stb.py)  
  - CDU (desambiguação por tipo)  

Rode com: `pytest tests/` (dentro de v0.14.2)

### Garantias de Confiabilidade
1. **Roundtrip**: Qualquer `.stb` lido pode ser re-exportado idêntico  
2. **Encoding**: Sem corrupção silenciosa de caracteres latin-1; erro explícito se fora do intervalo  
3. **Compatibilidade**: Manual ANATEM v12.10 é a verdade — todas as implementações validadas  

---

## 📚 Referências Rápidas

| Precisar de | Arquivo |
|---|---|
| Estrutura simulador | `v0.14.2/README.md` seção "Arquitetura" |
| API completa | `v0.14.2/README.md` seção "API pública" |
| Histórico mudanças | `v0.14.2/CHANGELOG.md` |
| Manual ANATEM oficial | `markdowns_reference/anatem.pdf` |
| Blocos dinâmicos (teoria) | `markdowns_reference/blocos_CDU_completo.md` |
| Variáveis plotagem | `markdowns_reference/DPLT_completo.md` |
| Decisões arquitetura | `v0.14.2/ROADMAP_v7.md` + `ROADMAP_v8.md` |

---

## ⚡ Comandos Rápidos

```bash
# Instalar pyanatem (dev)
pip install -e "v0.14.2/.[plt]"

# Rodar testes
cd v0.14.2 && pytest tests/ -v

# Usar biblioteca
python -c "
from pyanatem import CasoAnatem
caso = CasoAnatem.ler('seu_arquivo.stb')
caso.dsim.tfim = 15.0
caso.exportar('seu_arquivo_editado.stb')
"
```

---

**Última atualização:** 2026-07-09  
**Mantido por:** Matheus (USP)  
**Licença:** MIT
