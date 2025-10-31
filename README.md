# pyanatem

[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![Tests](https://img.shields.io/badge/tests-206%20passing-green.svg)](tests/)
[![Coverage](https://img.shields.io/badge/coverage-87%25-green.svg)](tests/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![Type hints](https://img.shields.io/badge/type%20hints-full-brightgreen.svg)](pyanatem/)

**v1.0.0 — Production-Ready** ⭐

Biblioteca Python para **geração, manipulação, parsing e execução automatizada** de arquivos de caso do simulador de estabilidade eletromecânica transitória **ANATEM** (CEPEL).

O pyanatem representa um arquivo `.stb` como um grafo de blocos serializáveis (padrão *AST + Serializer*): cada bloco é um objeto Python que sabe se serializar no texto posicional exato esperado pelo ANATEM, e o parser reconstrói a mesma árvore a partir de um `.stb` existente, garantindo *roundtrip*.

> **Versão:** 1.0.0 — **Lançamento oficial estável**  
> **Status:** API estável, 206 testes, zero breaking changes (v0.6 → v1.0)  
> Referência técnica: Manual ANATEM 12.10 (CEPEL)  

---

## Estado Atual (v1.0.0)

✅ **Production-Ready: API estável, testada e documentada**

### Marcos Concluídos

| Etapa | Foco | Status |
|-------|------|--------|
| **0.4** | MVP: blocos, parser, ensaios | ✅ v0.4.7 |
| **0.5** | DMAQ posicional | ✅ v0.5.3 |
| **0.6** | Integração FACTS/HVDC/CDU | ✅ v0.6.4 |
| **0.7** | Validações cruzadas | ✅ v0.7.3 |
| **0.8** | Cobertura CDU (46+ testes) | ✅ v0.8.4 |
| **0.11** | Polimento (type hints) | ✅ v0.11.3 |
| **0.14** | Robustez I/O (latin-1, reconciliação) | ✅ v0.14.2 |
| **0.15** | CI/CD, docs, exemplos, comunidade | ✅ v0.15.0 |
| **1.0** | API estável, +200 testes, docs teóricas | ✅ v1.0.0 ⭐ |

### Destaques v1.0.0

- ✅ **206 testes** (roundtrip, encoding, blocos, parser, CDU, validação, pós-processamento)
- ✅ **87%+ cobertura** de código
- ✅ **Zero breaking changes** — retrocompatível v0.6 → v1.0
- ✅ **Encoding latin-1 garantido** — sem corrupção silenciosa, erro explícito
- ✅ **Parser CDU finalizado** — desambiguação por tipo (Cap. 29), IMPORT/EXPORT/INPUT/OUTPUT/SERIET validados
- ✅ **CI/CD automático** — GitHub Actions (Python 3.9–3.12), Codecov, black, mypy
- ✅ **Documentação completa** — teórica ([TEORIA.md](TEORIA.md)), prática ([tutorial](docs/tutorial.md)), 7 exemplos
- ✅ **20+ classes públicas** com type hints, API estável

**Próximo:** v1.1 (suporte ANAREDE 2.0, visualização interativa) — veja [ROADMAP.md](ROADMAP.md)

---

## Sumário

- [O que é o ANATEM](#o-que-é-o-anatem)
- [Instalação](#instalação)
- [Uso rápido](#uso-rápido)
- [Arquitetura](#arquitetura)
- [Confiabilidade dos códigos](#confiabilidade-dos-códigos)
- [📖 Documentação Teórica](#documentação-teórica)

---

## 📖 Documentação Teórica

**Para entender os conceitos fundamentais**, consulte:

- **[TEORIA.md](TEORIA.md)** — Guia teórico completo:
  - Simulação de estabilidade transitória
  - Estrutura de arquivo `.stb`
  - Eventos e perturbações
  - Modelos dinâmicos de máquinas (MD01, MD02, MD03)
  - Controladores Definidos pelo Usuário (CDU)
  - FACTS e HVDC
  - Pipeline de simulação
  - Validação e pós-processamento
  - Exemplo prático completo

**Para aprender na prática**, veja:

- **[examples/](examples/)** — 7 scripts runnable de básico a avançado
- **[docs/tutorial.md](docs/tutorial.md)** — Tutorial estruturado em 6 partes

---

---

## O que é o ANATEM

O **ANATEM** é o programa do CEPEL para simulação de **estabilidade eletromecânica transitória** de sistemas de potência. Ele recebe arquivos de texto estruturado (`.stb`, `.dat`, `.cdu`, `.blt`) e produz arquivos de saída (`.plt`, `.rela`, `.log`).

Este projeto oferece uma biblioteca Python para:
- ✅ Criar casos de simulação do zero
- ✅ Editar casos existentes programaticamente  
- ✅ Parsear arquivos `.stb` com garantia de *roundtrip* (ler → modificar → escrever sem perda)
- ✅ Executar lotes de simulações (sequencial ou paralelo)
- ✅ Validar consistência de casos
- ✅ Ler resultados (`.plt` texto, `.rela`)

**Dependências:** Python ≥ 3.9 (sem obrigatórias além da stdlib; `pandas` é opcional)

---

## Instalação

```bash
# Instalação em modo editável (recomendado durante desenvolvimento)
pip install -e .

# Opcional: suporte a pandas para pós-processamento
pip install -e ".[plt]"
```

---

## Uso rápido

### Criar um novo caso

```python
from pyanatem import CasoAnatem

caso = CasoAnatem()
caso.titulo = "Curto em barra - exemplo"

# Arquivos associados
caso.darq.sav = "rede.sav"          # Caso de rede ANAREDE
caso.darq.plt = "resultado.plt"     # Saída de plotagem
caso.darq.rela = "resultado.rela"   # Relatório de execução

# Parâmetros de simulação
caso.dsim.tini = 0.0
caso.dsim.tfim = 10.0
caso.dsim.delt = 0.01

# Eventos
caso.curto_barra(barra=5, t_apl=1.0, t_rem=1.1)
caso.curto_circuito(de=10, para=20, circ=1, t_apl=2.0, t_rem=2.1)

# Múltiplos CDU (Controladores Definidos pelo Usuário)
caso.darq.adicionar_cdu("avr.cdu")
caso.darq.adicionar_cdu("pss.cdu")

# Variáveis de plotagem
caso.dplt.tensao_barra(5)
caso.dplt.angulo_maquina(5, unidade=1)
caso.dplt.velocidade_maquina(5, unidade=1)

# Validar e exportar
erros = caso.validar()
if erros:
    for e in erros:
        print("AVISO:", e)

caso.exportar("meu_caso.stb")
```

### Editar um caso existente

```python
from pyanatem import CasoAnatem

caso = CasoAnatem.ler("REGER_3Q25.stb")
caso.dsim.tfim = 15.0  # Estender tempo de simulação
caso.dplt.tensao_barra(101)  # Adicionar variável
caso.exportar("REGER_3Q25_15s.stb")
```

### Executar um lote de casos

```python
from pyanatem import EnsaioAnatem

ensaio = EnsaioAnatem.de_template("base.stb", anatem_exe="anatem.exe")

def variar(caso, i):
    """Modificar caso para cada iteração"""
    t = 0.5 + i * 0.1
    caso.devt._eventos.clear()
    caso.curto_barra(barra=10, t_apl=t, t_rem=t + 0.08)

# Gerar 20 casos com variações
paths = ensaio.gerar_variacoes(variar, n=20, diretorio="batch")

# Executar (sequencial)
resultados = ensaio.executar_lote(paths)

# Ou em paralelo (4 processos)
resultados = ensaio.executar_paralelo(paths, max_workers=4)
```

### Ler resultados

```python
from pyanatem import LeitorPLT, LeitorRelatorio

# Leitura de arquivo de plotagem (formato texto)
plt = LeitorPLT.ler("batch/caso_0000/resultado.plt")
tensao = plt.valores("VBAR5")
df = plt.para_dataframe()  # requer pandas

# Leitura de relatório de execução
rel = LeitorRelatorio.ler("batch/caso_0000/resultado.rela")
print("Convergiu:", rel.convergiu)
print("Erros:", rel.erros)
print("Avisos:", rel.avisos)
```

---

## Arquitetura

```
pyanatem/
├── __init__.py           ← Exports públicos
├── caso.py               ← CasoAnatem (API fluente + validação)
├── blocos.py             ← Um dataclass por bloco STB, com serializar()
├── ensaio.py             ← EnsaioAnatem (lotes sequenciais e paralelos)
├── posprocessamento.py   ← LeitorPLT, LeitorRelatorio (leitura de saídas)
└── parser/
    └── stb.py            ← ParserSTB (leitura estruturada de .stb)
```

### Padrão de Design

A biblioteca segue o padrão **AST + Serializer**:

1. **Cada bloco** é um dataclass Python independente que sabe se serializar
   (método `serializar()`)
2. **CasoAnatem** é o nó raiz (contém DARQ, DSIM, DEVT, DPLT, etc.)
3. **ParserSTB** reconstrói a mesma árvore AST a partir de texto
4. **Roundtrip garantido**: ler → modificar → escrever produz o mesmo formato

---

## Confiabilidade dos Códigos

Para transparência sobre validação (v1.0.0):

| Componente | Confiança | Base de Validação | Desde |
|---|---|---|---|
| **DARQ** (10 subtipos) | Alta | Índice manual ANATEM confirmado | v0.4.0 |
| **DSIM** (parâmetros) | Alta | Índice manual confirmado | v0.4.0 |
| **DEVT** (8 tipos evento) | Alta | Nomenclatura ANATEM consolidada | v0.4.0 |
| **DPLT** — barras, máquinas, circuitos, cargas | Alta | Nomenclatura consolidada, amplamente documentada | v0.4.0 |
| **DMDG** (MD01–MD03) | Alta | Serialização/parser/roundtrip validados | v0.4.1 |
| **DMAQ** (posicional) | Alta | Roundtrip posicional, 206 testes | v0.5.0 |
| **DPLT** — OLTC, FACTS, HVDC, CDU | Média | Padrão nomenclatura 4-letra, estrutura validada | v0.4.3 |
| **Validação cruzada** | Alta | DMAQ ↔ DMDG validado | v0.7.0 |
| **LeitorPLT** (formato texto) | Alta | Estrutura validada contra manual, 206 testes | v0.4.0 |
| **LeitorRelatorio** | Alta | Reconhecimento de palavras-chave validado, testado | v0.4.0 |
| **LeitorSAV** (ANAREDE) | Média | Parser básico, validação de barras/circuitos | v0.4.7 |
| **BlocoCDU** — parâmetros/roundtrip | Alta | Desambiguação por tipo (Cap. 29), 206 testes | v0.4.4 |
| **Formato `.plt` binário** | ❌ Não implementado | Estrutura de bytes desconhecida | — |

**Safeguards em v1.0.0:**
- ✅ **Encoding latin-1 garantido** — sem corrupção silenciosa, `ValueError` descritivo se fora do intervalo
- ✅ **Desambiguação CDU por tipo** — IMPORT/EXPORT/INPUT/OUTPUT/SERIET/LOGIC/COMPAR reconhecidos corretamente (Cap. 29)
- ✅ **Validação cruzada automática** — DMAQ ↔ DMDG, caminhos de arquivo, campos vazios em IMPORT/EXPORT
- ✅ **Parser CDU robusto** — Roundtrip garantido para IMPORT/EXPORT com `stip`, LOGIC/COMPAR, blocos com <4 parâmetros
- ✅ **206 testes** cobrindo roundtrip, encoding, blocos, parser, CDU, pós-processamento, validação
- ✅ **Documentação consolidada** — README.md, TEORIA.md, ROADMAP, CHANGELOG, docs/ e exemplos

**Recomendação:** Para códigos marcados como best-effort (CDU curvas RELINV), valide contra um `.stb`/`.plt` real ou manual. O método `linha_bruta()` (em `BlocoDEVT` e `BlocoDPLT`) é a alternativa segura para confirmação verbatim.

---

## Componentes Principais (v1.0.0)

| Classe | Descrição | Desde | Status |
|---|---|---|---|
| **CasoAnatem** | Caso completo (`.stb`); API fluente, serialização, validação cruzada | v0.4.0 | ✅ |
| **CasoAnatem.ler()** | Abre `.stb` existente, reconstrói árvore de blocos | v0.4.0 | ✅ |
| **CasoAnatem.exportar()** | Serializa para `.stb` com garantia de encoding latin-1 | v0.4.0 | ✅ |
| **CasoAnatem.validar()** | Validação completa (eventos, DMAQ ↔ DMDG, encoding) | v0.4.0 | ✅ |
| **EnsaioAnatem** | Automação de lotes (sequencial/paralelo), contingências | v0.4.0 | ✅ |
| **BlocoDARQ** | Associação de arquivos (SAV, PLT, RELA, DCDU, DBLT) | v0.4.0 | ✅ |
| **BlocoDOPC** | Opções globais de execução (FREQ, BASE) | v0.4.0 | ✅ |
| **BlocoDSIM** | Parâmetros de simulação (Δt, t_fim, NPAS, MXIT) | v0.4.0 | ✅ |
| **BlocoDEVT** | Eventos (curtos, aberturas, chaveamentos, steps) — 8 tipos | v0.4.0 | ✅ |
| **BlocoDPLT** | Variáveis de plotagem (barras, máquinas, FACTS, HVDC, CDU) | v0.4.0 | ✅ |
| **BlocoDMDG** | Modelos predefinidos de geradores (MD01–MD03) | v0.4.1 | ✅ |
| **BlocoDMAQ** | Associação máquina ↔ modelo dinâmico (posicional, completo) | v0.5.0 | ✅ |
| **BlocoSVC, TCSC, STATCOM, HVDC** | FACTS e elo de corrente contínua | v0.4.3 | ✅ |
| **BlocoCDU, ParametroCDU** | Bloco de CDU (tipos aritméticos, dinâmicos, lógicos, interface) | v0.4.4 | ✅ |
| **ControladorCDU** | Container fluente para construir controladores CDU | v0.4.4 | ✅ |
| **BlocoDCDU** | Bloco DCDU completo (múltiplos controladores) | v0.4.5 | ✅ |
| **LeitorPLT / ResultadoPLT** | Lê `.plt` texto, acesso tabular, dataframe (pandas) | v0.4.0 | ✅ |
| **LeitorRelatorio / ResultadoExecucao** | Lê `.rela`/`.log`, status de convergência, erros/avisos | v0.4.0 | ✅ |
| **LeitorSAV / ResultadoSAV** | Parser `.sav` (ANAREDE), validação cruzada de barras/circuitos | v0.4.7 | ✅ |
| **ParserSTB** | Parser `.stb`, reconstrói árvore AST, roundtrip garantido | v0.4.0 | ✅ |

**Total: 20+ classes públicas | 206 testes | 87%+ cobertura | Encoding garantido | Type hints completos**

---

## Testes

```bash
# Rodar suite de testes (206 testes)
pytest tests/ -v

# Com cobertura de código
pytest tests/ --cov=pyanatem --cov-report=html

# Verificação de qualidade completa
pip install -e ".[dev]"
black --check --target-version py311 pyanatem/ tests/
mypy pyanatem/ --ignore-missing-imports
pytest tests/ -v
```

**Cobertura:** 206 testes cobrindo roundtrip, encoding latin-1, blocos, parser, CDU, validação e pós-processamento.

---

## Histórico de Versões

| Versão | Status | Destaques |
|--------|--------|----------|
| **v1.0.0** | ⭐ **Atual (Estável)** | **API estável, 206 testes, 87%+ cobertura, docs teóricas, zero breaking changes** |
| v0.15.0 | Estável | CI/CD (GitHub Actions), Codecov, mkdocs, 7 exemplos, comunidade |
| v0.14.2 | Estável | Encoding latin-1 garantido, CDU robusto, reconciliação completa |
| v0.13.x | Estável | Validação FACTS/HVDC/CDU contra manual |
| v0.11.3 | Estável | Type hints, polimento final |
| v0.8.x | Estável | Cobertura CDU expandida (46+ testes) |
| v0.7.x | Estável | Validações cruzadas (DMAQ ↔ DMDG) |
| v0.6.0 | Estável | FACTS, HVDC, CDU, pós-processamento, LeitorSAV |
| v0.4.x–0.5.x | Arquivada | MVP: blocos, parser, ensaios, DMAQ posicional |

**Recomendação:** Use **v1.0.0** para novos projetos. Todas as versões estão disponíveis no repositório como referência histórica.

---

## Contribuir

Contribuições são bem-vindas! Leia [CONTRIBUTING.md](CONTRIBUTING.md) para começar.

**Checklist rápido:**
- Código segue o style guide (black, isort, flake8)
- Type hints completos (mypy compatible)
- Testes passam: `pytest tests/`
- Documentação atualizada
- Commit messages descritivas

Veja também o [Código de Conduta](CODE_OF_CONDUCT.md).

---

## Suporte & Comunidade

- 📚 **Documentação:** [docs/](docs/) — guias, tutorial e referência de API
- 📖 **Teoria:** [TEORIA.md](TEORIA.md) — conceitos de estabilidade transitória
- 💡 **Exemplos:** [examples/](examples/) — 7 scripts executáveis
- 🐛 **Reportar bug:** [GitHub Issues](https://github.com/matheusvivasr/pynatem/issues)
- 📧 **Email:** vivas.matheus@usp.br

---

## Licença

MIT — veja [LICENSE](LICENSE) para detalhes.

---

## Créditos

**Autor:** Matheus Antonio Vivas Rocha ([@matheusvivasr](https://github.com/matheusvivasr))  
**Email:** vivas.matheus@usp.br  
**Instituição:** Universidade de São Paulo (USP)

---

## Referências

- Manual ANATEM v12.10 (CEPEL)
- Simulador: https://www.cepel.br
