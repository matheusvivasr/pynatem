# 📑 Índice do Repositório — pynatem

**Versão:** v2.0.0 · **Status:** primeiro lançamento público (PyPI)

---

## 🎯 O que é o pynatem?

**Biblioteca Python** para geração, manipulação, parsing e execução automatizada
de arquivos `.stb` (casos de simulação) do simulador **ANATEM**
(CEPEL — Centro de Pesquisas de Energia Elétrica).

- ✅ Lê e escreve arquivos `.stb` com garantia de *roundtrip*
- ✅ API Python fluente para criar/editar casos programaticamente
- ✅ Suporte a CDU (Controladores Definidos pelo Usuário)
- ✅ Serialização validada char-a-char contra o Manual ANATEM 12.10 oficial
- ✅ Execução em lotes (contingências, ensaios paralelos)
- ✅ Pós-processamento (`.plt` texto e binário, `.out`, `.rel`, `.sav`)

**Dependências:** Python ≥ 3.9 (stdlib pura; `pandas` opcional para dataframes)

---

## 📂 Estrutura do Repositório

```
pynatem/                        ⭐ Código-fonte da biblioteca
├── caso.py                     • CasoAnatem — API fluente do caso .stb
├── blocos.py                   • Blocos serializáveis (DMAQ, DEVT, DSIM, ...)
├── ensaio.py                   • EnsaioAnatem — automação de lotes
├── anarede.py                  • Validação cruzada STB ↔ SAV (ANAREDE)
├── posprocessamento.py         • Leitores .plt/.rela/.sav
├── posprocessamento_v2.py      • Leitores .out estruturados
├── cdu/                        • DSL de Controladores Definidos pelo Usuário
├── cdu_v17.py                  • CDU avançado (DEFVAL, topologia, relés/SEP)
├── analise_v18.py              • Contingência N-1, multi-infeed, séries temporais
├── estabilidade_v19.py         • Critérios de pós-falta e sincronismo
├── dsa_v110.py                 • Avaliação de Segurança Dinâmica (DSA)
└── parser/                     • ParserSTB (.stb) e leitor .plt binário

tests/                          • 280 testes
├── test_pynatem.py             • Unitários e integração
├── test_conformidade_manual.py ⭐ Conformidade com o manual oficial
└── test_*_extended.py          • Roundtrip, validação e pós-processamento

examples/                       • 13 exemplos numerados (01 básico → 13 DSA)
docs/                           • Site MkDocs (getting-started, tutorial, API)
benchmarks/                     • Medições de desempenho
.github/workflows/              • CI (testes, lint) e publicação PyPI por tag
```

Arquivos de referência na raiz: [README.md](README.md) ⭐ ·
[CHANGELOG.md](CHANGELOG.md) · [ROADMAP.md](ROADMAP.md) ·
[CONTRIBUTING.md](CONTRIBUTING.md) (inclui o fluxo de branches/versões) ·
[TEORIA.md](TEORIA.md) · [LICENSE](LICENSE)

---

## 🧩 Componentes Principais

| Classe / Símbolo | Módulo | Descrição |
|---|---|---|
| `CasoAnatem` | `caso.py` | Caso completo (`.stb`): API fluente + serialização + validação |
| `CasoAnatem.ler()` / `.exportar()` | `caso.py` | Roundtrip `.stb` (latin-1 garantido) |
| `CasoAnatem.validar_contra_sav()` | `anarede.py` | Cruza barras/circuitos STB ↔ SAV |
| `EnsaioAnatem` | `ensaio.py` | Lotes sequenciais/paralelos; contingências N-1 |
| `BlocoDEVT` | `blocos.py` | Eventos (APCB/RMCB, ABCI/FECI, APCL/RMCL, MDSH, TRGT/TRGV) |
| `BlocoDMAQ`, `BlocoDMDG`, `BlocoDRGT/DRGV/DEST` | `blocos.py` | Máquinas síncronas e controles |
| `BlocoSVC/TCSC/STATCOM/HVDC`, `BlocoDELO/DMEL/DCLI` | `blocos.py` | FACTS e HVDC |
| `ControladorCDU` | `cdu/` | DSL fluente para construir CDUs |
| `LeitorPLT` / `LeitorPLTBinario` | `posprocessamento*.py`, `parser/` | Séries de resultado |
| `AnalisadorContingencia`, `AnalisadorMultiInfeed` | `analise_v18.py` | Modos de análise |
| `AnalisadorEstabilidade`, `MonitorSincronismo` | `estabilidade_v19.py` | Pós-falta |
| `AvaliadorDSA`, `RecomendadorDSA` | `dsa_v110.py` | Segurança dinâmica |

---

## 📖 Por onde começar

1. **Instalar:** `pip install pynatem`
2. **Primeiro caso:** [examples/01_basic_case_creation.py](examples/01_basic_case_creation.py)
3. **Tutorial completo:** [docs/tutorial.md](docs/tutorial.md)
4. **Referência técnica:** o formato dos blocos segue o
   [Manual ANATEM 12.10 oficial](https://see.cepel.br/manual/anatem/) —
   os testes de conformidade comparam a saída char-a-char com os exemplos dele.

## 🔒 Garantias de conformidade

`tests/test_conformidade_manual.py` reproduz os exemplos oficiais do manual e
compara a serialização caractere a caractere. Se um serializador regredir de
formato, a suíte falha. Os blocos ainda não cobertos por essa validação estão
listados no [ROADMAP.md](ROADMAP.md) (backlog v2.0.x).
