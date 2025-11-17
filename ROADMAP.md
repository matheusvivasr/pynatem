# Roadmap — pyanatem

## Status atual: **v1.1.1** ✅ (estável, lançável)

Esquema de versão **v1 (SemVer)**. O ciclo `0.x` foi encerrado em v1.0.0
(lançamento oficial estável). A partir daí:

- **MINOR (v1.x.0)** — etapa temática: novas capacidades retrocompatíveis.
- **PATCH (v1.x.y)** — meta concreta e entregável (feature validada + testes).
- **MAJOR (v2.0.0)** — cobertura total do ANATEM 12.10 + 100% confiabilidade Alta.

> Filosofia: **primeiro endurecer o que já existe** (confiabilidade), depois
> preencher os fundamentos de dinâmica, e por fim expandir para equipamentos e
> modos de análise mais nichados.

---

## v1.1.0 — Confiabilidade Máxima 🥇 *(em andamento)*

*Endurece o existente sem adicionar superfície nova — maior retorno por esforço.*

| Patch | Meta | Status |
|-------|------|--------|
| **v1.1.1** | Validar FACTS (DCER/DCSC/DVSI) contra o manual §46 → Alta | ✅ **Concluído** (2026-07-10) |
| v1.1.2 | Validar HVDC (DCNV/DELO) contra caso real → Alta | ⏳ |
| v1.1.3 | LeitorSAV robusto — cobrir todos os registros `.sav` → Alta | ⏳ |
| v1.1.4 | Resolver `stip` das curvas RELINV (localizar spec) → Alta | ⏳ |
| v1.1.5 | Validar DPLT 4-letra (OLTC/FACTS/HVDC/CDU) → Alta | ⏳ |

**v1.1.1 entregou:** DCER/DCSC re-modelados como códigos de *associação de
controles* (§46.18/§46.22) e DVSI com os 15 campos reais do conversor (§46.64);
parser de leitura + roundtrip por bloco; confiabilidade Média→**Alta**.

---

## v1.2.0 — Máquina Síncrona Completa 🥈

*Sem reguladores/PSS predefinidos, casos reais de estabilidade são inviáveis.*

| Patch | Meta |
|-------|------|
| v1.2.1 | Reguladores de Tensão / Excitatriz predefinidos |
| v1.2.2 | Reguladores de Velocidade / Turbina |
| v1.2.3 | Estabilizadores (PSS) predefinidos |
| v1.2.4 | Modelos de máquina MD04–MD24 (hoje só MD01–03) |
| v1.2.5 | Curvas de saturação (DMCV) + CAG + Controle Centralizado de Tensão |

---

## v1.3.0 — Cargas, Shunt, OLTC e Circuitos 🥉

*Equipamentos de rede presentes em quase todo caso.*

| Patch | Meta |
|-------|------|
| v1.3.1 | Cargas estáticas/dinâmicas (DCAR) + eventos + ERAC |
| v1.3.2 | Bancos Shunt (DBSH) + eventos + relés |
| v1.3.3 | Transformadores OLTC (DLTC) built-in + associação |
| v1.3.4 | Circuitos CA — fluxo agregado + eventos completos |

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

## 🏁 v2.0.0 — Cobertura Total ANATEM 12.10

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
