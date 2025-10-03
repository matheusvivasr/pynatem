# pyanatem (v0.8.0)

Biblioteca Python para **geração, manipulação, parsing e execução automatizada** de arquivos de caso do simulador de estabilidade eletromecânica transitória **ANATEM** (CEPEL).

> **Versão:** 0.8.0  
> **Status:** Etapa 8 completa (cobertura de testes CDU)  
> Referência técnica: Manual ANATEM 12.10 — 903 páginas  

---

## Estado Atual

✅ **Pronto para uso em produção** (com ressalvas)

- **Etapa 1–2:** Blocos básicos, parser, ensaios — Completo
- **Etapa 3:** FACTS, HVDC, CDU — Implementado (best-effort)
- **Etapa 4:** Modelos de geradores (DMDG) — Completo
- **Etapa 5:** Associação máquina (DMAQ) — Posicional, completo
- **Etapa 6:** Integração FACTS/HVDC/CDU — Completo
- **Etapa 7:** Validações cruzadas — Completo ✨
- **Etapa 8:** Cobertura de testes CDU — Completo ✨

**Proximas etapas:** Limpeza estrutural (v0.9), documentação (v0.10), polimento (v0.11), v1.0 público.

---

## Sumário

- [O que é o ANATEM](#o-que-é-o-anatem)
- [Instalação](#instalação)
- [Uso rápido](#uso-rápido)
- [Arquitetura](#arquitetura)
- [Confiabilidade dos códigos](#confiabilidade-dos-códigos)

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

## Confiabilidade dos códigos

Para transparência sobre validação (v0.8.0):

| Componente | Confiança | Base de Validação |
|---|---|---|
| **DARQ** (10 subtipos) | Alta | Índice manual ANATEM confirmado |
| **DSIM** (parâmetros) | Alta | Índice manual confirmado |
| **DEVT** (8 tipos evento) | Alta | Nomenclatura ANATEM consolidada |
| **DPLT** — barras, máquinas, circuitos, cargas | Alta | Nomenclatura consolidada, amplamente documentada |
| **DMDG** (MD01–MD03) | Média | Serialização/parser/roundtrip testados sinteticamente |
| **DMAQ** (posicional) | Média | Roundtrip posicional testado (v0.5–v0.8, 46+ testes) |
| **DPLT** — OLTC, FACTS, HVDC, CDU | Best-effort | Padrão nomenclatura 4-letra, sem confirmação página específica |
| **Validação cruzada** (v0.7) | Média | DMAQ ↔ DMDG validado, caminho do relatório corrigido |
| **Cobertura CDU** (v0.8) | Média | Testes de múltiplas entradas, INTRES, roundtrip de controlador completo |
| **LeitorPLT** (formato texto) | Média | Estrutura validada, múltiplas leituras testadas |
| **LeitorRelatorio** | Média | Reconhecimento de palavras-chave validado |
| **Formato `.plt` binário** | Não implementado | Estrutura de bytes desconhecida |

**Recomendação:** Valide os códigos marcados como *best-effort* contra um arquivo `.stb`/`.plt` real ou contra o manual em mãos, antes de uso em produção. O método `linha_bruta()` (disponível em `BlocoDEVT` e `BlocoDPLT`) é a alternativa segura para qualquer código que necessite confirmação.

**Novidades em v0.7–v0.8:**
- ✅ Validação cruzada automática entre blocos (DMAQ referencia modelos válidos do DMDG)
- ✅ Cobertura expandida de testes CDU (46+ testes de roundtrip e múltiplas entradas)
- ✅ Caminho correto do relatório em `executar_contingencias()`

---

## Componentes Principais

| Classe | Módulo | Descrição | Desde |
|---|---|---|---|
| `CasoAnatem` | `caso.py` | Caso completo (`.stb`); API fluente, serialização, validação | v0.4.0 |
| `CasoAnatem.ler()` | `caso.py` | Abre `.stb` existente, reconstrói árvore de blocos | v0.4.0 |
| `CasoAnatem.exportar()` | `caso.py` | Serializa para `.stb` | v0.4.0 |
| `CasoAnatem.validar()` | `caso.py` | Validação com verificações cruzadas (DMAQ ↔ DMDG) | v0.4.0 |
| `EnsaioAnatem` | `ensaio.py` | Automação de lotes sequenciais e paralelos | v0.4.0 |
| `BlocoDARQ` | `blocos.py` | Arquivos associados (SAV, PLT, RELA, DCDU) | v0.4.0 |
| `BlocoDSIM` | `blocos.py` | Parâmetros de simulação | v0.4.0 |
| `BlocoDEVT` | `blocos.py` | Eventos (8 tipos) | v0.4.0 |
| `BlocoDPLT` | `blocos.py` | Variáveis de plotagem (barras, máquinas, FACTS, HVDC, CDU) | v0.4.0 |
| `BlocoDMDG` | `blocos.py` | Modelos predefinidos de geradores (MD01–MD03) | v0.4.1 |
| `BlocoDMAQ` | `blocos.py` | Associação máquina ↔ modelo dinâmico (posicional) | v0.5.0 |
| `BlocoSVC`, `BlocoTCSC`, `BlocoSTATCOM`, `BlocoHVDC` | `blocos.py` | FACTS e elo HVDC | v0.4.3 |
| `BlocoCDU`, `ControladorCDU`, `BlocoDCDU` | `cdu/` | Controladores Definidos pelo Usuário | v0.4.4 |
| `LeitorPLT` | `posprocessamento.py` | Lê `.plt` formato texto, oferece acesso tabular/dataframe | v0.4.0 |
| `LeitorRelatorio` | `posprocessamento.py` | Lê `.rela`/`.log` com status de convergência | v0.4.0 |
| `LeitorSAV` | `anarede.py` | Parser `.sav` do ANAREDE para validação cruzada | v0.4.7 |
| `ParserSTB` | `parser/stb.py` | Parser `.stb` com roundtrip garantido | v0.4.0 |

---

## Testes

```bash
# Rodar suite de testes
pytest tests/ -v

# Com cobertura
pytest tests/ --cov=pyanatem
```

---

## Histórico de Versões

| Versão | Data | Status | Destaques |
|--------|------|--------|----------|
| **v0.8.0** | 2026-06-XX | ⭐ Atual | Cobertura CDU expandida, validação cruzada DMAQ ↔ DMDG, 46+ testes |
| v0.7.x | 2026-06-XX | Estável | Validações cruzadas, correção de caminhos |
| **v0.6.0** | 2026-06-XX | Estável | FACTS, HVDC, CDU completo, pós-processamento |
| v0.5.x | — | Arquivada | Serialização posicional DMAQ |
| v0.4.x | — | Arquivada | MVP: blocos básicos, parser, ensaios |

**Nota:** Todas as versões estão disponíveis no repositório como referência histórica. Use v0.8.0 para novos projetos.

---

## Licença

MIT

---

## Referências

- Manual ANATEM v12.10 (CEPEL)
- Simulador: https://www.cepel.br
