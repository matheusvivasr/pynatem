# Roadmap — pynatem

## Status atual: **v1.10.2** ✅ (estável, lançável) — etapas v1.1–v1.10 concluídas 🎉

> **v1.10.2 (2026-07-11):** auditoria de conformidade — 16 serializadores
> validados **char-a-char** contra o manual online oficial do Cepel
> (https://see.cepel.br/manual/anatem/), com 17 testes de conformidade
> externa em `tests/test_conformidade_manual.py`. Pré-requisitos da v2.0.0
> atualizados abaixo.

Esquema de versão **v1 (SemVer)**. O ciclo `0.x` foi encerrado em v1.0.0
(lançamento oficial estável). A partir daí:

- **MINOR (v1.x.0)** — etapa temática: novas capacidades retrocompatíveis.
- **PATCH (v1.x.y)** — meta concreta e entregável (feature validada + testes).
- **MAJOR (v2.0.0)** — cobertura total do ANATEM 12.10 + 100% confiabilidade Alta.

> Filosofia: **primeiro endurecer o que já existe** (confiabilidade), depois
> preencher os fundamentos de dinâmica, e por fim expandir para equipamentos e
> modos de análise mais nichados.

---

## v1.1.0 — Confiabilidade Máxima 🥇 ✅ **CONCLUÍDA**

*Endureceu o existente sem adicionar superfície nova — maior retorno por esforço.
Inventário B zerado: tudo que estava em Média/best-effort passou a Alta.*

| Patch | Meta | Status |
|-------|------|--------|
| **v1.1.1** | Validar FACTS (DCER/DCSC/DVSI) contra o manual §46 → Alta | ✅ **Concluído** (2026-07-10) |
| **v1.1.2** | Validar HVDC (DCNV/DELO) contra o manual §46 → Alta | ✅ **Concluído** (2026-07-10) |
| **v1.1.3** | LeitorSAV robusto — colunas fixas DBAR/DLIN + DGBT → Alta | ✅ **Concluído** (2026-07-10) |
| **v1.1.4** | Curvas de tempo inverso (bloco CURVA §29.3.13, subtipos IEC/IEC2/IEEE/IEEE2) → Alta | ✅ **Concluído** (2026-07-10) |
| **v1.1.5** | Validar DPLT 4-letra (OLTC/FACTS/HVDC/CDU) contra o manual → Alta | ✅ **Concluído** (2026-07-10) |

**v1.1.1 entregou:** DCER/DCSC re-modelados como códigos de *associação de
controles* (§46.18/§46.22) e DVSI com os 15 campos reais do conversor (§46.64);
parser de leitura + roundtrip por bloco; confiabilidade Média→**Alta**.

---

## v1.2.0 — Máquina Síncrona Completa 🥈 ✅ **CONCLUÍDA**

*Sem reguladores/PSS predefinidos, casos reais de estabilidade são inviáveis.
Abordagem para modelos predefinidos: bloco genérico posicional cobrindo todos
os modelos MDxx + construtor nomeado para o modelo mais comum.*

| Patch | Meta | Status |
|-------|------|--------|
| **v1.2.1** | Reguladores de Tensão / Excitatriz predefinidos (DRGT §16.3) | ✅ **Concluído** (2026-07-10) |
| **v1.2.2** | Reguladores de Velocidade / Turbina (DRGV §16.4) | ✅ **Concluído** (2026-07-10) |
| **v1.2.3** | Estabilizadores (PSS) predefinidos (DEST §16.5) | ✅ **Concluído** (2026-07-10) |
| ~~v1.2.4~~ | ~~Modelos de máquina MD04–MD24~~ — **N/A: o DMDG tem só 3 modelos (MD01–03, §16.1), todos já implementados**. O "MD04–24" foi confusão com o DRGT. | ✅ **Sem trabalho** (revisado 2026-07-10) |
| **v1.2.5** | Curvas de saturação (DCST §16.2) | ✅ **Concluído** (2026-07-10) |
| **v1.2.6** | CAG (DCAG §46.13/§16.7) + Controle Centralizado de Tensão (DCCT §46.15/§16.8) | ✅ **Concluído** (2026-07-10) |

---

## v1.3.0 — Cargas, Shunt, OLTC e Circuitos 🥉 ✅ **CONCLUÍDA**

*Equipamentos de rede presentes em quase todo caso.*

| Patch | Meta | Status |
|-------|------|--------|
| **v1.3.1** | Cargas estáticas funcionais (DCAR §46.14, modelo ZIP) | ✅ **Concluído** (2026-07-10) |
| **v1.3.2** | Bancos Shunt — evento MDSH (§12.1) + plotagem QSHT/QBSH/NUBSH (§12.2). *Não há código DBSH; banco é dado do ANAREDE.* | ✅ **Concluído** (2026-07-10) |
| **v1.3.3** | Transformadores OLTC — controle DMTC (§14.1) + associação DLTC (§46.40) | ✅ **Concluído** (2026-07-10) |
| **v1.3.4** | Circuitos CA — Fluxo Agregado de Intercâmbio (DFLA §13.1). *Não há código DCIR; circuito é dado do ANAREDE, eventos no DEVT.* | ✅ **Concluído** (2026-07-10) |

---

## v1.4.0 — Pós-processamento Completo

*Desbloqueia análise de resultados sem depender de texto.*

| Patch | Meta |
|-------|------|
| v1.4.1 | **Leitor `.plt` binário** (engenharia reversa dedicada) |
| v1.4.2 | Plotagem de Curvas de Relés (`.rel`) |
| v1.4.3 | Snapshot (SNAP) completo + Sinal Externo (DAVS) |
| v1.4.4 | Log de Mensagens estruturado + resultados MIIF/Inércia |

---

## v1.5.0 — Geração Renovável

| Patch | Meta |
|-------|------|
| v1.5.1 | Máquinas de Indução Convencional (DMOT) |
| v1.5.2 | Geração ZIP Funcional (DGER/DFNT) |
| v1.5.3 | Geradores Eólicos DFIG (DDFM) |
| v1.5.4 | Geradores Síncronos Eólicos (DGSE) |
| v1.5.5 | Ger. Indução Diretamente Conectados + Fonte Shunt CDU |

---

## v1.6.0 — FACTS & HVDC Completos

*Eleva os blocos atuais (associação/básico) a modelos completos.*

| Patch | Meta |
|-------|------|
| v1.6.1 | Elos LCC completo (CCAT, conversores, modelos de elo) |
| v1.6.2 | Barras CC / Linhas CC |
| v1.6.3 | CER completo + CSC completo (associação a controles) |
| v1.6.4 | FACTS VSI completo + VSC-HVDC |

---

## v1.7.0 — CDU Avançado & Proteção

| Patch | Meta |
|-------|------|
| v1.7.1 | DEFVAL/DEFVDF/DEFPLT + inicialização de modelos CDU |
| v1.7.2 | Topologia de CDUs (DTDU) + Controladores Não Específicos |
| v1.7.3 | **Relés e SEP por CDU (DREL)** |
| v1.7.4 | Mensagens Personalizadas + algoritmos malha inativa (OTMx) |

---

## v1.8.0 — Modos de Análise

| Patch | Meta |
|-------|------|
| v1.8.1 | Análise de Contingências nativa (ANAC) |
| v1.8.2 | Análise de CDU isolada (ACDU) |
| v1.8.3 | Multi-Infeed (DMIF/EAMI) |
| v1.8.4 | Interação Fontes Shunt (EAIF) |
| v1.8.5 | Séries Temporais (DSTR/DSTO) |

---

## v1.9.0 — Opções de Execução & Robustez Final

| Patch | Meta |
|-------|------|
| v1.9.1 | Cobertura completa opções de controle (Cap. 47, ~112) |
| v1.9.2 | Linguagem de Seleção (Cap. 42) |
| v1.9.3 | Definição Automática de Arquivos + USIHID/SUISHI |
| v1.9.4 | Diagnóstico de convergência/desempenho (Cap. 41) |

---

## 🏁 v2.0.0 — Primeiro Lançamento Público (PyPI) ✅ **LANÇADA**

Marco **MAJOR** — `pip install pynatem`. Entregue: conformidade char-a-char
de 16 serializadores com o manual oficial, 280 testes, CI verde e repositório
público limpo. A cobertura total do manual passa a ser perseguida nos patches
v2.0.x abaixo e culmina no marco v3.0.0.

## v2.0.x — Backlog de Conformidade (patches) ✅ **CONCLUÍDO**

| Patch | Meta |
|-------|------|
| v2.0.1 | **Réguas por variante MDxx** — ✅ entregue (14 variantes com régua oficial: DMDG 3/3, DMTC 1/1, DRGT 3, DRGV 2, DEST 2 + DECS/DMCE/DMCS); demais variantes sem régua publicada no manual online seguem no formato genérico (documentado) |
| v2.0.2 | **Blocos FACTS/HVDC/indução** — ✅ entregue (DVSI, DCNV, DDFM, DGSE, DMOT nas colunas oficiais; bug de perda de precisão corrigido no Cnvk do DVSI; DMOT reescrito para a régua de linha única oficial) |
| v2.0.3 | **DCER/DFNT/DCSC** — ✅ entregue (DCER e DFNT nas colunas oficiais; DCSC documentado com a mesma inconsistência de transcrição do manual vista no DDFM). Todos os blocos que reivindicavam "Confiança: Alta" foram auditados; DMCV (exemplo degenerado, multi-registro) e cobertura exaustiva do Cap. 46 ficam para v3.0.0 |

Método estabelecido: reproduzir o exemplo oficial via API e comparar com os
fontes `_sources/*.rst.txt` do manual online; estender
`tests/test_conformidade_manual.py` a cada código coberto. **295 testes
passando, lint/mypy zerados** ao final da série.

---

## v2.1.0 — Pós-processamento Consolidado 🔍

*Completa a narrativa v1.4 (nunca formalizada). Integra leitura de resultados
binários e estruturados.*

| Patch | Meta | Deps |
|-------|------|------|
| **v2.1.1** | **Leitor `.plt` binário** — engenharia reversa de `plt_binario.py`, parser estruturado, testes contra exemplos oficiais | `plt_binario.py` (107 linhas, 0% → 100% cobertura) |
| **v2.1.2** | **Relatórios Estruturados** (`.rel` + `.out`) — análise de convergência, erros/avisos, resultados numéricos | `posprocessamento_v2.py` (230 linhas, 0% → 100%) |
| **v2.1.3** | **Snapshots + Sinal Externo** (SNAP, DAVS) — estados intermediários e sinais de análise | Integra SNAP/DAVS ao `LeitorPLT` |

**Saída:** LeitorPLT/LeitorRelatorio/LeitorSAV com suporte binário e `.out`; pipeline de
pós-processamento completo; 320+ testes.

---

## v2.2.0 — CDU Avançado Integrado 🔌

*Completa a narrativa v1.7 (planejada mas não formalizada). Eleva `cdu_v17.py`
de 0% para integração plena.*

| Patch | Meta | Deps |
|-------|------|------|
| **v2.2.1** | **Inicialização de Modelos CDU** (DEFVAL/DEFVDF/DEFPLT) — construtores tipados, validação de valores iniciais | `cdu_v17.py` (408 linhas, 0% → cobertura) |
| **v2.2.2** | **Topologia e Controladores Genéricos** (DTDU/ACDU) — desambiguação de controladores não-específicos, malha inativa | Extends `BlocoCDU` |
| **v2.2.3** | **Relés e SEP** (DREL) — relés de proteção, esquemas especiais de proteção integrados a CDU | Novo `BlocoREL` |
| **v2.2.4** | **Mensagens e Algoritmos OTM** (DMSG, OTMx) — malha inativa, lógica de controle não-linear | Integra `OTM*` blocos |

**Saída:** CDU com inicialização, topologia, proteção e mensagens; API fluente para definir
controladores avançados; 340+ testes.

---

## v2.3.0 — Modos de Análise Estruturados 📊

*Completa a narrativa v1.8 (planejada mas não formalizada). Integra `analise_v18.py`.*

| Patch | Meta | Deps |
|-------|------|------|
| **v2.3.1** | **Análise de Contingências N-1** (ANAC) — perturbação automática de equipamentos, iteração sobre casos variados | `analise_v18.py` base |
| **v2.3.2** | **Análise de CDU Isolada** (ACDU) — teste de controlador sem simulação da rede | Reusa `ControladorCDU` |
| **v2.3.3** | **Multi-Infeed** (DMIF/EAMI) — análise de interação entre infeedores CA | Novos blocos DMIF/EAMI |
| **v2.3.4** | **Interação Fontes Shunt** (EAIF) — acoplamento dinâmico de shunts/FACTS | Novo `BlocoEAIF` |
| **v2.3.5** | **Séries Temporais** (DSTR/DSTO) — varrida paramétrica, análise temporal | Novos `BlocoDSTR/DSTO` |

**Saída:** Framework de análises nativas; automação de contingências; 360+ testes.

---

## v2.4.0 — Opções de Execução & Linguagem de Seleção 🎛️

*Completa a narrativa v1.9 (planejada mas não formalizada). Endurecimento final
de opções e seleção.*

| Patch | Meta | Deps |
|-------|------|------|
| **v2.4.1** | **Opções de Controle Completas** (Cap. 47, ~112 opções) — parseador estruturado, construtores tipados | `BlocoOPC` expansion |
| **v2.4.2** | **Linguagem de Seleção** (Cap. 42) — parser de seleção (barras, equipamentos, cargas) por critério; integração com DCAR | Novo `ParserSelecao`, extends `DCAR` |
| **v2.4.3** | **Definição Automática de Arquivos** (USIHID/SUISHI) — geração automática de caminhos e nomes | Novo `GeradorCaminhos` |
| **v2.4.4** | **Diagnóstico de Convergência** (Cap. 41) — análise de MXIT, NPAS, tempo de simulação | Novo `AnalisadorConvergencia` |

**Saída:** API para todas as opções globais; seleção estruturada; automação de arquivos;
diagnósticos; 380+ testes.

---

## v2.5.0 — Algoritmos de Estabilidade Integrados ⚡

*Integra `estabilidade_v19.py` (planejada como v1.9 estendida). Análise pós-falta
e dinâmica de sincronismo.*

| Patch | Meta | Deps |
|-------|------|------|
| **v2.5.1** | **Critérios de Pós-Falta** (v1.9 original) — ângulo máximo, tempo de recuperação, taxa de amortecimento | `estabilidade_v19.py` base |
| **v2.5.2** | **Sincronismo Pós-Falta** — coerência de máquinas, clustering, velocidade de recuperação | Extends `estabilidade_v19.py` |
| **v2.5.3** | **Análise de Frequência & Inércia** — modos eletromecânicos, amortecimento, ROCOF | Novo `AnalisadorFrequencia` |

**Saída:** Critérios numéricos de estabilidade; análise modal; 400+ testes.

---

## v2.6.0 — DSA Consolidado 🛡️

*Completa a narrativa v1.10 (planejada mas não formalizada). Integra `dsa_v110.py`.*

| Patch | Meta | Deps |
|-------|------|------|
| **v2.6.1** | **Snapshots Estruturados** (SNAP, estados intermediários) — salvamento de estados, reinicialização a partir de snapshots | `dsa_v110.py` base |
| **v2.6.2** | **Avaliação de Segurança Dinâmica** (RSEG) — limites de operação dinâmica, margens de segurança | Novo `RSEG` em `dsa_v110.py` |
| **v2.6.3** | **Sinal Externo Integrado** (DAVS) — sincronização com medições externas, feedback em tempo real | Novo `BlocoDAVS` |
| **v2.6.4** | **Batch de Análises DSA** — varredura de cenários, relatórios consolidados | Automação em `EnsaioAnatem` |

**Saída:** Pipeline completo de DSA; snapshots; RSEG; 420+ testes.

---

## 🏁 v3.0.0 — Cobertura Total ANATEM 12.10

Marco **MAJOR**. Critérios de aceite:

- [ ] 100% dos 74 códigos de execução (Cap. 46)
- [ ] 100% das opções de controle (Cap. 47)
- [ ] Todos os equipamentos (Cap. 10–38) modelados
- [ ] `.plt` binário + todos os formatos de saída lidos
- [ ] Confiabilidade Alta/Absoluta em tudo, validado contra casos reais CEPEL
- [ ] Suíte de testes ≥ 500, cobertura ≥ 92%
- [ ] Documentação teórica cobrindo cada equipamento
- [ ] Migração para o manual 12.11

---

## Contribuindo

Veja [CONTRIBUTING.md](CONTRIBUTING.md) para começar.
